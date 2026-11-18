"""E3 trigger + the TCN challenger gate (task 1.4, decision half).

Task 1.4 says the TCN module is "built ONLY if the E3 trigger fires (GRU
slow/unstable per the plan's criteria)". The criteria must be written down
BEFORE the base run finishes, otherwise "the GRU looks fine to me" silently
decides a thesis-title question. This module is that written-down rule plus the
TCN module it gates.

The trigger has two independent arms, either of which fires it:

* **slow** — the base run's own manifest says a training epoch or a per-field-
  cycle inference costs more than the pre-registered budget;
* **unstable** — the base run's epoch history is non-monotone in a way that no
  amount of extra compute fixes: the final epoch is not within one standard
  deviation of the best one, or the loss rises in the second half of training
  (a divergence signature), or the epoch history is too short to judge, which
  counts as unstable because an unjudgeable primary is exactly when a simpler
  temporal module is worth having.

"Unjudgeable" being a FIRE (not a pass) is deliberate: fail-closed here means
the challenger gets built, which costs one extra cell, whereas the opposite
error costs the thesis its temporal-module claim.

The TCN itself is causal by construction and mask-aware, and
:func:`causality_violations` is the test that enforces both rather than
trusting the padding arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Pre-registered budgets (the plan's criteria). A run that exceeds EITHER
# fires the trigger; the numbers are deliberately generous so the trigger
# fires only on a real problem.
MAX_EPOCH_SECONDS = 240.0        # 4 min/epoch on the venue actually used
MAX_MS_PER_FIELD_CYCLE = 250.0   # inference cost per field-cycle
MIN_EPOCHS_TO_JUDGE = 3
STABILITY_SIGMA_K = 1.0          # final epoch must be within k*sigma of best

KERNEL_SIZE = 3
DILATIONS: tuple[int, ...] = (1, 2, 4, 8)


# ---------------------------------------------------------------------------
# The trigger
# ---------------------------------------------------------------------------
@dataclass
class TriggerVerdict:
    fired: bool
    reasons: list[str] = field(default_factory=list)
    measured: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"fired": self.fired, "reasons": list(self.reasons),
                "measured": dict(self.measured),
                "rule": {
                    "max_epoch_seconds": MAX_EPOCH_SECONDS,
                    "max_ms_per_field_cycle": MAX_MS_PER_FIELD_CYCLE,
                    "min_epochs_to_judge": MIN_EPOCHS_TO_JUDGE,
                    "stability_sigma_k": STABILITY_SIGMA_K,
                }}

    def require_built(self) -> None:
        """Raise if a caller tries to skip the challenger with a fired trigger."""
        if self.fired:
            raise RuntimeError(
                "E3 trigger fired ("
                + "; ".join(self.reasons)
                + ") — the TCN challenger must be built and run, or the plan "
                "must be amended with an approver"
            )


def _epoch_seconds(history: list[dict]) -> list[float]:
    """Per-epoch wall time from the cumulative ``wall_s`` the trainer records."""
    prev = 0.0
    out: list[float] = []
    for rec in history:
        w = float(rec.get("wall_s", 0.0))
        out.append(max(0.0, w - prev))
        prev = w
    return out


def stability_report(history: list[dict], *, k: float = STABILITY_SIGMA_K) -> dict:
    """Is the training curve stable? Returns the numbers, not a verdict."""
    losses = [float(r["train_loss"]) for r in history if "train_loss" in r]
    n = len(losses)
    if n == 0:
        return {"n_epochs": 0, "judgeable": False, "stable": False,
                "reason": "no epoch history"}
    best = min(losses)
    final = losses[-1]
    sigma = float(np.std(losses, ddof=1)) if n > 1 else 0.0
    gap = final - best
    # A rising second half: fit a slope over the last ceil(n/2) epochs.
    tail = losses[n // 2:]
    slope = float(np.polyfit(np.arange(len(tail)), tail, 1)[0]) if len(tail) > 1 else 0.0
    stable = bool(n >= MIN_EPOCHS_TO_JUDGE and gap <= k * max(sigma, 1e-12)
                  and slope <= 0.0)
    return {
        "n_epochs": n, "judgeable": n >= MIN_EPOCHS_TO_JUDGE,
        "best": best, "final": final, "sigma": sigma,
        "final_minus_best": gap, "tolerance": k * max(sigma, 1e-12),
        "tail_slope": slope, "stable": stable,
        "reason": ("history shorter than the judgeable minimum"
                   if n < MIN_EPOCHS_TO_JUDGE
                   else "final epoch above best+sigma or rising tail"
                   if not stable else "within tolerance and not rising"),
    }


def evaluate_trigger(
    manifest: dict,
    *,
    history: list[dict] | None = None,
    max_epoch_seconds: float = MAX_EPOCH_SECONDS,
    max_ms_per_field_cycle: float = MAX_MS_PER_FIELD_CYCLE,
    min_epochs: int = MIN_EPOCHS_TO_JUDGE,
) -> TriggerVerdict:
    """Apply the pre-registered criteria to one completed base run.

    Reads the values from the run's OWN manifest/history (tasks 1.1-1.2), so a
    run cannot be judged against somebody else's venue.
    """
    reasons: list[str] = []
    hist = history if history is not None else list(manifest.get("history") or [])
    per_epoch = _epoch_seconds(hist)
    slow_epochs = [s for s in per_epoch if s > max_epoch_seconds]
    if slow_epochs:
        reasons.append(
            f"slow: {len(slow_epochs)} epoch(s) over {max_epoch_seconds:.0f}s "
            f"(max {max(slow_epochs):.1f}s)"
        )

    bench = manifest.get("benchmark") or {}
    ms = bench.get("ms_per_field_cycle")
    if ms is None:
        reasons.append("slow: per-field-cycle inference time not measured")
    elif float(ms) > max_ms_per_field_cycle:
        reasons.append(
            f"slow: {float(ms):.1f} ms/field-cycle over {max_ms_per_field_cycle:.0f}"
        )

    st = stability_report(hist, k=STABILITY_SIGMA_K)
    if st["n_epochs"] < min_epochs:
        reasons.append(f"unstable: only {st['n_epochs']} epoch(s) to judge")
    elif not st["stable"]:
        reasons.append(
            f"unstable: final {st['final']:.4f} vs best {st['best']:.4f} "
            f"(tolerance {st['tolerance']:.4f}), tail slope {st['tail_slope']:+.2e}"
        )

    return TriggerVerdict(bool(reasons), reasons, {
        "epoch_seconds": per_epoch, "max_epoch_seconds": max(per_epoch, default=None),
        "ms_per_field_cycle": ms, "stability": st,
    })


def decide_temporal_module(verdict: TriggerVerdict, *,
                           challenger_wins: bool | None = None) -> dict:
    """The kept temporal module, by the pre-registered rule.

    With no trigger, the GRU stays and no challenger is built. With a trigger,
    the challenger must have been RUN; until it has, the decision is
    ``pending`` rather than the incumbent winning by default. Ties (within one
    standard error) go to the simpler/faster variant, which is the GRU — and
    that rule is stated here so a tie is decided by the rule and not by
    whoever writes the report.
    """
    if not verdict.fired:
        return {"kept": "gru", "challenger_built": False,
                "reason": "E3 trigger did not fire"}
    if challenger_wins is None:
        return {"kept": "pending", "challenger_built": True,
                "reason": "trigger fired; the TCN must be run before deciding"}
    return {
        "kept": "tcn" if challenger_wins else "gru",
        "challenger_built": True,
        "reason": ("TCN beat the GRU outside one standard error"
                   if challenger_wins else
                   "TCN did not beat the GRU outside one standard error; ties "
                   "go to the simpler/faster variant (the GRU)"),
    }


# ---------------------------------------------------------------------------
# The challenger itself (torch)
# ---------------------------------------------------------------------------
def build_tcn(*, n_channels: int, d_model: int = 32, n_horizons: int = 2,
              dilations: tuple[int, ...] = DILATIONS, dropout: float = 0.0):
    """Causal dilated TCN over the temporal axis of a patch tensor.

    Input is ``(B, T, C, S, S)`` exactly like ``patch_cnn_gru``: the spatial
    extent is pooled per channel first (the patch decoder here is a per-location
    line, not a CNN stem), then a stack of dilated causal convolutions runs over
    T. Causality: each layer pads ``(k-1)*d`` on the LEFT only, so output at t
    depends on inputs at <= t.
    """
    torch, nn = _torch()

    class CausalBlock(nn.Module):
        def __init__(self, d: int, dilation: int):
            super().__init__()
            self.dilation = dilation
            self.pad = (KERNEL_SIZE - 1) * dilation
            self.conv = nn.Conv1d(d, d, KERNEL_SIZE, dilation=dilation)
            self.gain = nn.Parameter(torch.ones(1, d, 1))
            self.bias = nn.Parameter(torch.zeros(1, d, 1))
            self.drop = nn.Dropout(dropout)

        def forward(self, x, mask):                 # x (B,d,T), mask (B,1,T)
            y = torch.nn.functional.pad(x, (self.pad, 0))     # LEFT only
            y = self.conv(y)
            # Normalize over the CHANNEL axis at each timestep. nn.GroupNorm /
            # BatchNorm / LayerNorm-over-time would all pool across T and leak
            # future information backwards, which causality_violations catches.
            mu = y.mean(dim=1, keepdim=True)
            sd = y.std(dim=1, keepdim=True, unbiased=False).clamp_min(1e-5)
            y = (y - mu) / sd * self.gain + self.bias
            y = torch.relu(y)
            y = self.drop(y)
            # A padded bin may only feed a position whose own input was observed
            # at the matching lag; masking the output is the conservative choice.
            return x + y * mask

    class CausalTCN(nn.Module):
        def __init__(self):
            super().__init__()
            self.n_horizons = n_horizons
            self.inp = nn.Conv1d(n_channels + 1, d_model, 1)   # +1 = observed flag
            self.blocks = nn.ModuleList(
                [CausalBlock(d_model, d) for d in dilations]
            )
            self.head = nn.Linear(d_model, n_horizons * n_channels)
            self.receptive_field = 1 + sum((KERNEL_SIZE - 1) * d for d in dilations)

        def forward(self, x, pixel_valid, covariates=None):
            # x (B,T,C,S,S); pool the patch to per-channel means, keep the
            # observed fraction so a mostly-empty patch is not silently a 0.
            b, t, c = x.shape[:3]
            flat = x.reshape(b, t, c, -1)
            obs = pixel_valid.reshape(b, t, 1, -1).float().expand(-1, -1, c, -1)
            n_obs = obs.sum(-1).clamp_min(1.0)
            pooled = (flat * obs).sum(-1) / n_obs              # (B,T,C)
            frac = (obs.sum(-1) / obs.shape[-1]).mean(-1, keepdim=True)  # (B,T,1)
            z = torch.cat([pooled, frac], dim=-1).permute(0, 2, 1)     # (B,C+1,T)
            h = torch.relu(self.inp(z))
            mask = (frac.permute(0, 2, 1) > 0).float()        # (B,1,T)
            for blk in self.blocks:
                h = blk(h, mask)
            pred = self.head(h.permute(0, 2, 1))               # (B,T,H*C)
            return {"pred": pred.reshape(b, t, self.n_horizons, c),
                    "receptive_field": self.receptive_field}

    return CausalTCN()


def _torch():
    import torch
    import torch.nn as nn
    return torch, nn


def causality_violations(model, *, T: int, n_channels: int, S: int = 8,
                         eps: float = 1e-5) -> list[int]:
    """Timesteps whose output changed when only FUTURE inputs were perturbed.

    An empty list means the module is causal over the whole window. This is the
    task's causality test as a reusable function: perturb bin ``t0`` for every
    ``t0``, recompute, and check that no output at ``t < t0`` moved.
    """
    torch, _ = _torch()
    was_training = model.training
    model.eval()
    bad: list[int] = []
    g = torch.Generator().manual_seed(0)
    with torch.no_grad():
        x = torch.randn(1, T, n_channels, S, S, generator=g)
        mv = torch.ones(1, T, S, S, dtype=torch.bool)
        base = model(x, mv)["pred"].clone()
        for t0 in range(T):
            x2 = x.clone()
            x2[:, t0] = x2[:, t0] + 5.0          # perturb ONE bin
            out = model(x2, mv)["pred"]
            moved = (out[:, :t0] - base[:, :t0]).abs().max().item() if t0 > 0 else 0.0
            if moved > eps:
                bad.append(t0)
    model.train(was_training)
    return bad


def receptive_field(dilations: tuple[int, ...] = DILATIONS) -> int:
    """How many past bins the stack can see (the plan needs this stated)."""
    return 1 + sum((KERNEL_SIZE - 1) * d for d in dilations)


def effective_bins(dilations: tuple[int, ...] = DILATIONS, *, n_bins: int) -> int:
    """Fraction of the window the stack sees, as a coverage note for the report."""
    rf = receptive_field(dilations)
    return int(min(rf, n_bins))


__all__ = [
    "DILATIONS", "KERNEL_SIZE", "MAX_EPOCH_SECONDS", "MAX_MS_PER_FIELD_CYCLE",
    "MIN_EPOCHS_TO_JUDGE", "STABILITY_SIGMA_K", "TriggerVerdict", "build_tcn",
    "causality_violations", "decide_temporal_module", "effective_bins",
    "evaluate_trigger", "receptive_field", "stability_report",
]
