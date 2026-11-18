"""Patch scoring: per-pixel residuals → field-level alarm paths (task 2.2).

The patch arms must be indistinguishable from the existing arms *downstream of
the score* — that is what makes the comparison a comparison of representations
rather than of rules. So this module produces exactly the interface
``DeepCausalScorer.loo_batch`` already produces, and nothing more:

    scores  (N, T)        per-bin field score, NaN where no pixel is observed
    pred    (N, T, C, S, S) per-pixel predictions (for the sigma tables and XAI)

plus the per-pixel score maps the localization metrics need.

Design decisions that are load-bearing:

* **Per-pixel z² against a FROZEN sigma table.** sigma is ``1.4826 x MAD`` of the dev
  residual per (channel, 2-bin phenophase group, sensor), fitted on dev clean
  cycles only and hashed. Fitting on dev (not train) is deliberate: the
  residual scale of a *causal* predictor is a property of the predictor's own
  generalization error, and dev clean cycles are the closest clean proxy for
  the evaluation population. Injection and test data never enter.
* **Top-20 % aggregation, not max, not mean.** The field-level statistic is the
  mean of the largest 20 % of in-field per-pixel z² values. Max = a single
  speckle decides the alarm (the task 3.1 "maximum aggregation rule" is
  rejected for exactly this reason); mean dilutes a 30 %-footprint anomaly by
  3.3x. Top-20 % keeps a localized anomaly visible while a lone pixel cannot
  alarm.
* **The in-field mask is the only aggregation domain.** Out-of-field pixels
  are excluded before any statistic, so the farm boundary holds at scoring
  time too, not just inside the CNN.
* **CUSUM / EWMA are additive, never replaced.** ``alarm_per_cycle`` and
  ``calibrate_threshold`` stay the operating rule; the persistence
  accumulators are computed alongside so the delay/rate trade-off is reported
  rather than silently adopted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..io import patches as P

# Aggregation: mean of the largest TOP_FRAC share of in-field per-pixel z².
TOP_FRAC = 0.20

# Phenophase grouping of the sigma tables: 36 bins → 18 groups of 2 bins.
PHASE_BIN = 2

# The three components declared by the scoring-basis registry (task 2.4 lives
# in farm-local-anomaly-scoring; the labels are repeated here because the
# patch scorer is where they are attached).
BASIS_LOCAL = "locally_anchored"
BASIS_POPULATION = "population_ranked"


@dataclass
class PatchSigmaTable:
    """Frozen per-(channel, phenophase group, sensor) residual scale.

    ``sigma`` is (n_groups, n_channels, n_sensors) with NaN where a cell has
    fewer than ``min_n`` residuals; ``fallback`` is the per-channel pooled
    scale used for those cells (never NaN when any residual exists).
    """

    sigma: np.ndarray
    fallback: np.ndarray
    n: np.ndarray
    min_n: int = 20
    sha256: str = ""

    def lookup(self, bins: np.ndarray, sids: np.ndarray) -> np.ndarray:
        """(T, C) scale to divide residuals by; falls back per channel."""
        G, C, _ = self.sigma.shape
        groups = np.clip(np.asarray(bins, dtype=np.int64) // PHASE_BIN, 0, G - 1)
        sids = np.asarray(sids, dtype=np.int64)
        out = np.full((len(bins), C), np.nan)
        for t, (g, s) in enumerate(zip(groups, sids)):
            s_idx = int(s) if 0 <= int(s) < self.sigma.shape[2] else 0
            out[t] = self.sigma[g, :, s_idx]
        bad = ~np.isfinite(out) | (out <= 0)
        if bad.any():
            out = np.where(bad, np.broadcast_to(self.fallback, out.shape), out)
        return out


def fit_patch_sigma(
    residuals: np.ndarray,   # (N, T, C, S, S) signed residual, NaN where absent
    mask: np.ndarray,        # (N, T, C, S, S) bool observation mask
    sensor_ids: np.ndarray,  # (N, T) sensor id per bin
    *,
    min_n: int = 20,
    scale_floor: float = 1e-3,
    n_bins: int | None = None,
) -> PatchSigmaTable:
    """Fit :class:`PatchSigmaTable` on DEV CLEAN cycles only.

    The caller owns the "dev clean only" guarantee (there is no split
    knowledge here); ``test_patch_scores.py`` plants an injected cycle and
    proves the frozen table is unaffected by data it never received.
    """
    res = np.asarray(residuals, dtype=np.float64)
    msk = np.asarray(mask, dtype=bool)
    N, T, C = res.shape[:3]
    n_bins = int(n_bins or T)
    G = int(np.ceil(n_bins / PHASE_BIN))
    sigma = np.full((G, C, 3), np.nan)
    count = np.zeros((G, C, 3), dtype=np.int64)

    absr = np.where(msk, np.abs(res), np.nan)
    for s in range(3):
        for g in range(G):
            lo, hi = g * PHASE_BIN, min(T, (g + 1) * PHASE_BIN)
            if lo >= hi:
                continue
            sel = np.asarray(sensor_ids[:, lo:hi]) == s
            if not sel.any():
                continue
            block = absr[:, lo:hi][sel]                       # (n, bins, C, S, S)
            for c in range(C):
                v = block[:, :, c]
                v = v[np.isfinite(v)]
                count[g, c, s] = v.size
                if v.size >= min_n:
                    sigma[g, c, s] = max(1.4826 * float(np.median(v)), scale_floor)

    fallback = np.full(C, np.nan)
    for c in range(C):
        v = absr[:, :, c]
        v = v[np.isfinite(v)]
        if v.size:
            fallback[c] = max(1.4826 * float(np.median(v)), scale_floor)
    fallback = np.where(np.isfinite(fallback) & (fallback > 0), fallback, 1.0)

    return PatchSigmaTable(
        sigma=sigma, fallback=fallback, n=count,
        min_n=int(min_n), sha256=sigma_table_sha256(sigma, fallback, count),
    )


def sigma_table_sha256(sigma: np.ndarray, fallback: np.ndarray, count: np.ndarray) -> str:
    """Stable hash of the frozen sigma table (NaN-safe, dtype-normalized)."""
    import hashlib

    h = hashlib.sha256()
    for arr in (sigma, fallback.astype(np.float64), count.astype(np.int64)):
        a = np.ascontiguousarray(np.asarray(arr, dtype=np.float64))
        h.update(str(a.shape).encode())
        h.update(np.nan_to_num(a, nan=-999.0).tobytes())
    return h.hexdigest()


def pixel_scores(
    resid: np.ndarray,       # (N, T, C, S, S) residual (pred - truth) or z
    obs: np.ndarray,         # (N, T, C, S, S) bool per-channel observation
    sigma: PatchSigmaTable,
    bins: np.ndarray,        # (T,) bin index (0..35)
    sensor_ids: np.ndarray,  # (N, T) sensor id per bin
) -> np.ndarray:
    """Per-pixel squared standardized residual: (N, T, S, S), NaN where absent.

    A pixel is scored when ANY channel is observed there (matching
    ``patches.BinAggregate.pixel_valid``); the channel statistic at a pixel is
    the max over its observed channels, so a single-band anomaly is not
    diluted by the 8-channel mean.
    """
    r = np.asarray(resid, dtype=np.float64)
    o = np.asarray(obs, dtype=bool)
    N, T, C, S, _ = r.shape
    out = np.full((N, T, S, S), np.nan)
    for n in range(N):
        scale = sigma.lookup(bins, np.asarray(sensor_ids[n]))      # (T, C)
        z2 = np.where(o[n], (r[n] / scale[:, :, None, None]) ** 2, -np.inf)
        with np.errstate(invalid="ignore"):
            s = z2.max(axis=1)                                     # (T, S, S)
        s[~o[n].any(axis=1)] = np.nan
        out[n] = s
    return out


def field_paths(
    pixel_z2: np.ndarray,   # (N, T, S, S)
    in_field: np.ndarray,   # (F, S, S) or (S, S) aligned per sample, or (N, S, S)
    *,
    top_frac: float = TOP_FRAC,
    min_pixels: int = 4,
) -> np.ndarray:
    """Aggregate per-pixel z² to one field score per bin: (N, T).

    Mean of the largest ``top_frac`` share of in-field pixel scores. Bins with
    fewer than ``min_pixels`` in-field observations are NaN (no alarm from
    almost-no-data), matching the ``min_history`` spirit of the alarm rule.
    """
    p = np.asarray(pixel_z2, dtype=np.float64)
    if p.ndim != 4:
        raise ValueError(f"pixel_z2 must be (N, T, S, S), got {p.shape}")
    N, T = p.shape[:2]
    in_field = np.asarray(in_field, dtype=bool)
    if in_field.ndim == 2:
        if in_field.shape != p.shape[2:]:
            raise ValueError(
                f"in_field must be {p.shape[2:]} to match the pixel grid, got {in_field.shape}"
            )
        masks = np.broadcast_to(in_field[None, None], (N, T) + in_field.shape)
    elif in_field.ndim == 3 and in_field.shape[0] == N:
        masks = np.broadcast_to(in_field[:, None], (N, T) + in_field.shape[1:])
    elif in_field.ndim != 3 or in_field.shape[0] != N:
        raise ValueError(
            f"in_field must be (S,S) or ({N},S,S) for {N} samples, got {in_field.shape}"
        )

    out = np.full((N, T), np.nan)
    for n in range(N):
        for t in range(T):
            vals = p[n, t][masks[n, t]]
            vals = vals[np.isfinite(vals)]
            if vals.size < min_pixels:
                continue
            k = max(1, int(np.ceil(top_frac * vals.size)))
            out[n, t] = float(np.mean(np.partition(vals, vals.size - k)[vals.size - k:]))
    return out


# ---------------------------------------------------------------------------
# Persistence accumulators (task 1.3): reported beside the operating rule
# ---------------------------------------------------------------------------
def cusum_path(
    scores: np.ndarray,   # (T,) standardized per-bin score (unit scale)
    kappa: float,
    *,
    drift: float | None = None,
) -> np.ndarray:
    """One-sided CUSUM of ``score - (kappa + drift)``; (T,), NaN where unseen.

    ``kappa`` is the reference value (the tolerated standardized level); the
    drift term defaults to 0. Alarm when the path exceeds a calibrated ``h``.
    """
    s = np.asarray(scores, dtype=np.float64)
    thr = float(kappa) + float(drift or 0.0)
    out = np.full(len(s), np.nan)
    acc = 0.0
    for t, v in enumerate(s):
        if not np.isfinite(v):
            out[t] = np.nan          # unobserved: state carries, no evidence
            continue
        acc = max(0.0, acc + (v - thr))
        out[t] = acc
    return out


def ewma_path(
    scores: np.ndarray,   # (T,)
    alpha: float,
) -> np.ndarray:
    """EWMA of the per-bin score; unobserved bins carry the previous level."""
    s = np.asarray(scores, dtype=np.float64)
    out = np.full(len(s), np.nan)
    level = None
    for t, v in enumerate(s):
        if not np.isfinite(v):
            out[t] = np.nan if level is None else level
            continue
        level = v if level is None else alpha * v + (1.0 - alpha) * level
        out[t] = level
    return out


def calibrate_cusum_h(
    clean_paths: list[np.ndarray],
    *,
    far_target: float = 0.05,
    kappa: float = 0.5,
) -> dict:
    """Smallest ``h`` with cycle-level FAR ≤ target for the CUSUM rule.

    Returns ``{"h", "far_achieved", "kappa", "far_target", "n_cycles"}`` — the
    same contract as ``scoring.calibrate_threshold``, so the two rules are
    comparable at equal FAR and the choice between them is explicit.
    """
    if not clean_paths:
        raise ValueError("No clean paths for CUSUM calibration")
    maxima = np.array([
        float(np.nanmax(cusum_path(p, kappa))) if np.isfinite(p).any() else 0.0
        for p in clean_paths
    ])
    if maxima.size == 0:
        raise ValueError("All clean paths are NaN")
    cand = np.unique(maxima)
    lo, hi = 0, cand.size - 1
    best = float(cand[-1]) + 1e-9
    while lo <= hi:
        mid = (lo + hi) // 2
        far = float(np.mean(maxima > cand[mid]))
        if far <= far_target:
            best = float(cand[mid])
            hi = mid - 1
        else:
            lo = mid + 1
    far = float(np.mean(maxima > best))
    return {
        "h": best, "far_achieved": far, "kappa": float(kappa),
        "far_target": float(far_target), "n_cycles": len(clean_paths),
    }


# ---------------------------------------------------------------------------
# Task 2.4 — the eval_dev arm adapter (patch arms inside the severity sweep)
# ---------------------------------------------------------------------------
TAIL = 3          # trailing-window length of the production alarm statistic


def tail_max(path: np.ndarray, *, k: int = TAIL) -> np.ndarray:
    """Trailing maximum over ``k`` bins, NaN-tolerant (the production rule).

    ``cumulative_channel_max`` + ``choose_threshold`` are built on a trailing
    window, so any statistic handed to that machinery must be on the same
    scale-of-comparison. Bins with no observation stay NaN.
    """
    p = np.asarray(path, dtype=np.float64)
    out = np.full(p.shape, np.nan)
    for t in range(p.size):
        lo = max(0, t - k + 1)
        window = p[lo : t + 1]
        fin = window[np.isfinite(window)]
        if fin.size:
            out[t] = float(fin.max())
    return out


class PatchArmScorer:
    """Per-bin alarm path for a patch arm, in the production pipeline's form.

    The severity sweep in ``eval_dev.py`` is written against a SCORE FUNCTION:
    it computes the alarm path, calibrates ``(tau, k)`` on a calibration
    subset and then compares paths. The patch arms could not be plugged in
    before because their raw path lives on a different scale (top-20 % mean
    per-pixel z²) than the field-level paths, and no shared threshold exists
    between the two scales — a shared ``tau`` would silently favour whichever
    arm happens to have the larger numbers.

    So this adapter converts the patch path into the one quantity that IS
    comparable across arms: a **one-sided empirical p-value against the clean
    calibration paths**, computed per bin index (the phenophase position is the
    natural stratification). p = (1 + #{clean ≥ own}) / (n_clean + 1), so:

    * it is bounded in (0, 1], monotone in the raw path, and needs no shared
      unit;
    * it is calibrated by construction on the same subset the field-level arm
      uses, so ``tau`` means the same thing for both;
    * it is locally anchored — a farm's p-value is computed from its own path
      against the frozen clean reference, never from contemporaneous
      cross-farm values.

    ``score_cycles`` keeps the shape the sweep expects: a dict with a ``z2``
    entry whose downstream ``cumulative_channel_max`` call must stay a no-op.
    """

    def __init__(
        self,
        scorer: PatchDeepScorer,
        reference_paths: np.ndarray,   # (n_clean, T) clean calibration paths
        *,
        min_reference: int = 8,
    ) -> None:
        ref = np.asarray(reference_paths, dtype=np.float64)
        if ref.ndim != 2:
            raise ValueError(f"reference_paths must be (n_clean, T), got {ref.shape}")
        if ref.shape[0] < min_reference:
            raise ValueError(
                f"only {ref.shape[0]} clean calibration paths; at least {min_reference} "
                "are needed for an empirical p-value to mean anything"
            )
        self.scorer = scorer
        self.reference = ref

    def p_values(self, paths: np.ndarray) -> np.ndarray:
        """(N, T) one-sided empirical p-values against the clean reference."""
        p = np.asarray(paths, dtype=np.float64)
        if p.ndim != 2:
            raise ValueError(f"paths must be (N, T), got {p.shape}")
        N, T = p.shape
        if self.reference.shape[1] != T:
            raise ValueError(f"paths have {T} bins, reference has {self.reference.shape[1]}")
        out = np.full((N, T), np.nan)
        for t in range(T):
            ref = self.reference[:, t]
            ref = ref[np.isfinite(ref)]
            if ref.size == 0:
                continue
            own = p[:, t]
            ok = np.isfinite(own)
            if not ok.any():
                continue
            # (1 + #ref >= own) / (n + 1): never exactly 0, so a single extreme
            # bin cannot produce an infinite score downstream.
            out[ok, t] = (1.0 + np.sum(ref[None, :] >= own[ok][:, None], axis=1)) / (
                ref.size + 1.0
            )
        return out

    def score_cycles(self, X, M, doy, norm, *, idx=None, **model_inputs) -> dict:
        """Patch-arm scores in the sweep's dict form.

        Returns ``z2`` = (N, T, 1) of ``-log(p)`` so the downstream
        ``cumulative_channel_max`` (a channel max over a single channel) and
        ``cell_q95_normalizer`` remain valid, monotone transforms of the same
        ordering. Storing the p-value itself would invert the direction of the
        alarm.
        """
        scores, pred = self.scorer.loo_batch(X, M, idx=idx, **model_inputs)
        p_val = self.p_values(scores)
        with np.errstate(divide="ignore"):
            neg_log_p = -np.log(p_val)
        return {
            "score": scores,
            "z2": neg_log_p[:, :, None],
            "p_value": p_val,
            "pred_z": pred,
        }


# ---------------------------------------------------------------------------
# Task 2.2 — the eval_dev-facing adapter
# ---------------------------------------------------------------------------
class PatchDeepScorer:
    """Patch arm as a drop-in for ``DeepCausalScorer`` in ``eval_dev.py``.

    The production eval pipeline consumes exactly ``(scores (N, T),
    pred_z (N, T, C))`` from ``loo_batch``; every downstream step (causal
    offset correction, per-cell q95, trailing channel-max, τ, 5 % FAR) is
    untouched. This class therefore has ONE job: turn a patch batch into that
    pair without letting any patch-specific statistic leak into the alarm
    rule.

    Mapping, and why each choice is the conservative one:

    * The patch model is already causal by construction (its horizon-1 output
      at bin t reads bins ≤ t-1), so no leave-one-out withholding is needed —
      withholding is what ``DeepCausalScorer`` must do to make an
      *bidirectional* encoder causal. ``score_cycle``/``loo_batch`` keep the
      names for interface compatibility and document this.
    * ``scores`` is :func:`field_paths` of :func:`pixel_scores` — per-pixel z²
      against the FROZEN sigma table, aggregated by top-20 % over in-field pixels
      only. No cross-farm quantity is read (locally anchored).
    * ``pred_z`` is the per-pixel prediction collapsed to a per-field mean over
      in-field pixels. It exists only because the pipeline's ``z-space``
      bookkeeping expects a ``(T, C)`` prediction; the patch arm's real
      predictions stay available through :meth:`predict_pixels` for the sigma
      tables and the XAI change.
    * The mask used for scoring is ``pixel_valid ∧ in_field`` — derived from
      the STORE, never from the values, so a cloudy bin cannot look
      in-field-observed just because it is finite.

    Fail-closed rules: a channel count that disagrees with the sigma table, a
    missing in-field mask, or a bin count that disagrees with the sigma table's
    phenophase grouping all raise instead of silently re-indexing.
    """

    def __init__(
        self,
        model_id: str,
        model,
        sigma: PatchSigmaTable,
        *,
        in_field: np.ndarray,          # (F, S, S) or (S, S)
        n_channels: int,
        bins: np.ndarray | None = None,
        device=None,          # torch.device | str; resolved lazily
        top_frac: float = TOP_FRAC,
        min_pixels: int = 4,
    ) -> None:
        self.model_id = str(model_id)
        self.model = model.to(device) if hasattr(model, "to") else model
        self.sigma = sigma
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.in_field = np.asarray(in_field, dtype=bool)
        self.n_channels = int(n_channels)
        self.top_frac = float(top_frac)
        self.min_pixels = int(min_pixels)
        self.bins = (np.arange(P.N_BINS) if bins is None else np.asarray(bins, dtype=np.int64))
        if sigma.sigma.shape[1] != self.n_channels:
            raise ValueError(
                f"sigma table has {sigma.sigma.shape[1]} channels, scorer declares "
                f"{self.n_channels}"
            )
        if sigma.sigma.shape[0] * PHASE_BIN < int(self.bins.max(initial=0)) + 1:
            raise ValueError(
                f"sigma table covers {sigma.sigma.shape[0]} phenophase groups "
                f"({sigma.sigma.shape[0] * PHASE_BIN} bins) but scoring needs bin "
                f"{int(self.bins.max(initial=0))}"
            )
        self.last_pixel_maps: np.ndarray | None = None   # (N, T, S, S) set by predict_pixels

    # -- internals ------------------------------------------------------
    def _mask_for(self, idx: np.ndarray | None, pixel_valid: np.ndarray) -> np.ndarray:
        """(N, T, S, S) bool: observed AND in-field.

        Three accepted mask layouts, each resolved explicitly rather than by
        broadcast luck: a shared ``(S, S)`` mask; one ``(S, S)`` mask per
        SAMPLE (``in_field[n]``, for batches of field-cycles); or one per
        FIELD with ``idx`` naming each sample's field (the store's own layout,
        where the same field can appear in several cycles).
        """
        pv = np.asarray(pixel_valid, dtype=bool)
        if pv.ndim == 5:                      # (N, T, 1, S, S)
            if pv.shape[2] != 1:
                raise ValueError(f"pixel_valid channel axis must be 1, got {pv.shape}")
            pv = pv[:, :, 0]
        if pv.ndim != 4:
            raise ValueError(
                f"pixel_valid must be (N, T, S, S) or (N, T, 1, S, S), got {pv.shape}"
            )
        N, _T, S, _ = pv.shape
        m = self.in_field
        if m.ndim == 2:
            if m.shape != (S, S):
                raise ValueError(f"in_field is {m.shape}, patch grid is {(S, S)}")
            return pv & m[None, None]
        if m.ndim != 3:
            raise ValueError(f"in_field must be (S, S) or (F, S, S), got {m.shape}")
        if m.shape[1:] != (S, S):
            raise ValueError(f"in_field is {m.shape[1:]}, patch grid is {(S, S)}")
        if idx is not None:
            order = np.asarray(idx, dtype=np.int64)
            if order.shape != (N,):
                raise ValueError(f"idx must have one entry per sample ({N}), got {order.shape}")
            if order.size and (order.min() < 0 or order.max() >= m.shape[0]):
                raise ValueError(f"idx out of range for {m.shape[0]} fields")
            return pv & m[order][:, None]
        if m.shape[0] != N:
            raise ValueError(
                f"in_field has {m.shape[0]} fields for {N} samples; pass idx to select them"
            )
        return pv & m[:, None]

    @staticmethod
    def _to_tensor(x):
        import torch
        if isinstance(x, torch.Tensor):
            return x
        a = np.asarray(x)
        if a.dtype == bool:
            return torch.from_numpy(a)
        return torch.from_numpy(a.astype(np.float32))

    # -- scoring --------------------------------------------------------
    def _forward(self, X: np.ndarray, M: np.ndarray, covariates=None):
        """Run the patch model; returns (resid (N,T,C,S,S) signed, pred)."""
        import torch
        self.model.eval()
        x = self._to_tensor(X).to(self.device)
        m = self._to_tensor(M).to(self.device)
        cov = None if covariates is None else self._to_tensor(covariates).to(self.device)
        with torch.no_grad():
            out = self.model(x, m, cov)
        # horizon 0 predicts bin t (its own bin), matching the leave-one-bin-out
        # target of the field-level arms; NaN discipline is re-imposed by mask.
        pred = out["pred"][:, :, 0] if out["pred"].ndim == 6 else out["pred"]
        return (pred - x).cpu().numpy(), pred.cpu().numpy()

    def predict_pixels(
        self,
        X: np.ndarray,           # (N, T, C, S, S)
        pixel_valid: np.ndarray, # (N, T, S, S) or (N, T, 1, S, S)
        *,
        idx: np.ndarray | None = None,
        sensor_ids: np.ndarray | None = None,
        covariates=None,
        obs: np.ndarray | None = None,
    ) -> dict:
        """Full-fidelity pass: per-pixel residuals, z² maps and field paths."""
        x = np.asarray(X, dtype=np.float32)
        if x.ndim != 5:
            raise ValueError(f"X must be (N, T, C, S, S), got {x.shape}")
        N, T = x.shape[:2]
        mask = self._mask_for(idx, pixel_valid)
        observed = mask[:, :, None] & np.isfinite(x)
        if obs is not None:
            if obs.shape != x.shape:
                raise ValueError("obs must match the per-channel model input shape")
            observed &= obs
        # Zero-filled channels are not observed values. Keep both the target
        # mask and the set of input pixels aligned with the training loader.
        mask = observed.any(axis=2)
        resid, pred = self._forward(np.where(observed, x, 0.0), mask, covariates)
        bins = self.bins[:T]
        sid = (np.zeros((N, T), dtype=np.int64) if sensor_ids is None
               else np.asarray(sensor_ids, dtype=np.int64))
        if sid.shape != (N, T):
            raise ValueError(f"sensor_ids must be {(N, T)}, got {sid.shape}")
        z2 = pixel_scores(resid, observed, self.sigma, bins, sid)
        # The mask varies per (sample, bin), which field_paths' in_field
        # argument cannot express — so it is applied to the VALUES first
        # (out-of-mask pixels become NaN and are filtered), and the aggregation
        # domain is then "everything not explicitly excluded". Passing a
        # per-sample mask here instead would silently apply sample n's mask to
        # all of its bins.
        z2 = np.where(mask, z2, np.nan)
        paths = field_paths(
            z2, np.ones(z2.shape[2:], dtype=bool),
            top_frac=self.top_frac, min_pixels=self.min_pixels,
        )
        self.last_pixel_maps = z2
        return {"resid": resid, "pred": pred, "mask": mask, "pixel_z2": z2, "paths": paths}

    def predict_pixels_from_z(
        self,
        z: np.ndarray,           # (N, T, C, S, S) in the model's input space
        pixel_valid: np.ndarray,
        **kw,
    ) -> dict:
        return self.predict_pixels(z, pixel_valid, **kw)

    def loo_batch(
        self,
        z_batch: np.ndarray,   # (N, T, C, S, S) model-space values
        m_batch: np.ndarray,   # (N, T, S, S) or (N, T, 1, S, S) observed
        doy_batch: np.ndarray | None = None,
        **kw,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Interface-compatible pair for ``eval_dev.py``.

        ``scores`` (N, T) are the top-20 % in-field aggregate of per-pixel z²;
        ``pred_z`` (N, T, C) is the in-field mean prediction, provided only so
        the shared pipeline code keeps working.

        ``doy_batch`` is NOT silently reinterpreted: the patch grid already
        carries the phenophase in its bin index, and a per-bin DOY channel of
        shape (N, T, 2) is not a covariate (N, T, n_cov). Callers that trained
        with covariates must pass them explicitly as ``covariates=``; if they
        do not, the model's own check raises rather than the arm silently
        running without its inputs.
        """
        covariates = kw.pop("covariates", None)
        info = self.predict_pixels(z_batch, m_batch, covariates=covariates, **kw)
        mask = info["mask"]
        pred = info["pred"]
        n_field = np.maximum(mask.sum(axis=(2, 3)), 1)
        pred_z = (pred * mask[:, :, None]).sum(axis=(3, 4)) / n_field[:, :, None]
        scores = info["paths"]
        if not np.isfinite(scores[mask.any(axis=(2, 3))]).any():
            raise ValueError(
                "no bin produced a patch score although pixels were observed — "
                "the sigma table or the bin index is inconsistent with this batch"
            )
        return scores, pred_z.astype(np.float32)

    def score_cycle(
        self,
        z: np.ndarray,
        m: np.ndarray,
        doy: np.ndarray | None = None,
        *,
        idx: np.ndarray | None = None,
    ) -> np.ndarray:
        """(T,) field path for one cycle.

        ``idx`` names which field's in-field mask applies; it is required when
        the scorer was built with a per-field mask, since a single cycle does
        not identify its field on its own.
        """
        s, _ = self.loo_batch(
            z[None], m[None], None if doy is None else doy[None],
            **({} if idx is None else {"idx": np.asarray(idx, dtype=np.int64).reshape(1)}),
        )
        return s[0]


def component_basis() -> dict[str, str]:
    """Declared scoring basis per component (task 2.4 axis of the matrix).

    ``s_pred``/``s_rec``/``s_lat`` are locally anchored: a farm's own residual
    divided by frozen pooled scales — no contemporaneous cross-farm value is
    read. ``s_hyb`` and ``z_f(t)`` rank a farm against the population and are
    therefore population-ranked, and may never be the silent default.
    """
    return {
        "s_pred": BASIS_LOCAL,
        "s_rec": BASIS_LOCAL,
        "s_lat": BASIS_LOCAL,
        "s_hyb": BASIS_POPULATION,
        "z_f(t)": BASIS_POPULATION,
        "common_mode": BASIS_POPULATION,
        "indicator_z": BASIS_POPULATION,
    }


def require_basis(components: list[str], declared: dict[str, str] | None = None) -> None:
    """Fail the report build when a component has no declared basis (task 2.4)."""
    declared = declared if declared is not None else component_basis()
    missing = [c for c in components if c not in declared]
    if missing:
        raise ValueError(
            f"component(s) without a declared scoring basis: {missing} — every component "
            "must be labelled locally_anchored or population_ranked before it can be reported"
        )


__all__ = [
    "BASIS_LOCAL",
    "BASIS_POPULATION",
    "PHASE_BIN",
    "TAIL",
    "TOP_FRAC",
    "PatchArmScorer",
    "PatchDeepScorer",
    "PatchSigmaTable",
    "calibrate_cusum_h",
    "component_basis",
    "cusum_path",
    "ewma_path",
    "field_paths",
    "fit_patch_sigma",
    "pixel_scores",
    "require_basis",
    "sigma_table_sha256",
    "tail_max",
]
