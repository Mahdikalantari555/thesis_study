"""Patch-level attribution: bands, time windows, and the spatial pattern.

Change ``patch-xai-attribution``. The field-level XAI module answers "which
bands and which months"; the patch model needs the same answers **plus** the
spatial one, because that is the only dimension the patch representation adds.

Four methods, all on the patch grid:

1. :func:`band_occlusion` — replace one band's value plane with its in-field
   median everywhere (the "median baseline" the spec names) and measure the
   score change. Cheap, deterministic, and immune to gradient noise.
2. :func:`temporal_occlusion` — the same for one bin window.
3. :func:`spatial_occlusion` — the same for a pixel block, which is what makes
   "does the model look at the anomaly's SHAPE or just at the field's mean?"
   answerable.
4. :func:`gradient_x_input` — a differentiable attribution, with a
   finite-difference agreement check so a broken gradient cannot pass silently.

Faithfulness: :func:`deletion_insertion_curves` adapts the field-level
deletion/insertion idea to the patch grid — delete the top-attributed cells
and the score must collapse faster than under a random order. Randomization
sanity (re-initialised weights must destroy the attribution's advantage) is
the standard guard against a method that "explains" noise.

The pre-registered sample definition (task 1.3: 50 events, stratified by
family/severity, hash-recorded) lives in :func:`attribution_sample_plan`, so
the sample cannot be chosen after seeing the results.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from ssl_anomaly.monitor.patch_scores import TOP_FRAC
from ssl_anomaly.xai.attribution import SUGARCANE_STAGE_BINS

HASH_METHODS: tuple[str, ...] = (
    "band_occlusion", "temporal_occlusion", "spatial_occlusion", "gradient_x_input",
)

# The pre-registered attribution sample (task 1.3).
SAMPLE_SIZE = 50
SAMPLE_STRATA: tuple[str, ...] = ("family", "severity")


# ---------------------------------------------------------------------------
# Occlusion primitives
# ---------------------------------------------------------------------------
def _median_baseline(values: np.ndarray, mask: np.ndarray) -> float:
    v = values[np.asarray(mask, dtype=bool)]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else 0.0


def band_occlusion(
    values: np.ndarray,     # (T, C, S, S)
    mask: np.ndarray,       # (T, C, S, S)
    score_fn,               # (values, mask) -> float
    *,
    baseline: str = "median",
) -> dict:
    """Per-band score drop when that band is replaced by its in-field median.

    ``delta[c] = score(original) - score(band c occluded)``: a positive value
    means band c SUPPORTS the alarm. The baseline is the band's own in-field
    median (spec: "median baseline"), which keeps the occlusion physically
    plausible — occluding to zero would create an impossible reflectance.
    """
    if baseline != "median":
        raise ValueError(f"unsupported baseline {baseline!r} (only 'median')")
    s0 = float(score_fn(values, mask))
    deltas = np.zeros(values.shape[1])
    for c in range(values.shape[1]):
        occ = values.copy()
        b = _median_baseline(values[:, c], mask[:, c])
        occ[:, c] = np.where(mask[:, c], b, occ[:, c])
        deltas[c] = s0 - float(score_fn(occ, mask))
    order = np.argsort(-deltas)
    return {
        "method": "band_occlusion",
        "score": s0,
        "delta": deltas.tolist(),
        "rank": order.tolist(),
        "top_band": int(order[0]) if order.size else None,
        "baseline": baseline,
    }


def _raw_unit(values: np.ndarray, mask: np.ndarray, baseline: str) -> float:
    """Occlusion target for a whole window/block: ``median`` or ``zero``.

    A per-bin median would make a window of a smoothly varying signal
    uneventful by construction (each replaced bin lands on the field's usual
    level for that bin), so window/block occlusions default to ZERO in the
    MODEL's units — which for standardized patch tensors already means "the
    field's own typical value". The band occlusion keeps the per-band median,
    where the median is the meaningful physical baseline.
    """
    if baseline == "zero":
        return 0.0
    if baseline != "median":
        raise ValueError(f"unsupported baseline {baseline!r} (use 'median' or 'zero')")
    return _median_baseline(values, mask)


def temporal_occlusion(
    values: np.ndarray,
    mask: np.ndarray,
    score_fn,
    *,
    window: int = 3,
    baseline: str = "zero",
) -> dict:
    """Per-bin-window score drop (windows of ``window`` bins, stride 1).

    ``delta[start]`` = score(original) - score(window ``start..start+window``
    replaced by ``baseline``), so a positive value marks a window that
    SUPPORTS the alarm. Note the interaction: a window overlapping only part
    of a real anomaly can INCREASE the score (the series becomes jagged), so
    the caller must read the ranked maxima, not just the raw ordering.
    """
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")
    T = values.shape[0]
    s0 = float(score_fn(values, mask))
    target = _raw_unit(values, mask, baseline)
    deltas = []
    starts = []
    for start in range(0, max(1, T - window + 1)):
        occ = values.copy()
        m = np.asarray(mask, dtype=bool)
        sl = slice(start, start + window)
        occ[sl] = np.where(m[sl], target, occ[sl])
        deltas.append(s0 - float(score_fn(occ, m)))
        starts.append(start)
    order = np.argsort(-np.array(deltas))
    return {
        "method": "temporal_occlusion",
        "score": s0,
        "baseline": baseline,
        "window": int(window),
        "starts": starts,
        "delta": [float(d) for d in deltas],
        "rank": order.tolist(),
        "top_window_start": int(starts[int(order[0])]) if order.size else None,
    }


def spatial_occlusion(
    values: np.ndarray,
    mask: np.ndarray,
    score_fn,
    *,
    block: int = 8,
    baseline: str = "zero",
) -> dict:
    """Per-pixel-block score drop — the dimension the patch arm adds.

    A model that looks at the anomaly's SPATIAL structure produces a
    concentrated map; a model that only reads the field's mean produces a flat
    one. :func:`spatial_pattern_summary` quantifies which happened.
    """
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    T, C, S, _ = values.shape
    s0 = float(score_fn(values, mask))
    m = np.asarray(mask, dtype=bool)
    target = _raw_unit(values, m, baseline)
    ny = len(range(0, S, block))
    nx = len(range(0, S, block))
    deltas = np.zeros((ny, nx))
    for iy, y0 in enumerate(range(0, S, block)):
        for ix, x0 in enumerate(range(0, S, block)):
            occ = values.copy()
            sl = (slice(None), slice(None), slice(y0, y0 + block), slice(x0, x0 + block))
            occ[sl] = np.where(m[sl], target, occ[sl])
            deltas[iy, ix] = s0 - float(score_fn(occ, m))
    return {
        "method": "spatial_occlusion",
        "score": s0,
        "baseline": baseline,
        "block": int(block),
        "delta": deltas.tolist(),
        "spatial_pattern": spatial_pattern_summary(deltas),
    }


def spatial_pattern_summary(deltas: np.ndarray) -> dict:
    """Concentration of an attribution map: is it localized or flat?

    ``concentration`` = share of the total positive attribution held by the
    top-``TOP_FRAC`` blocks. A flat map scores ≈ ``TOP_FRAC``; a localized one
    approaches 1. ``gini`` is the standard inequality measure. Both are
    reported because a single block (concentration 1.0, gini 1.0) can mean one
    pixel dominates, which is a speckle, not a pattern — so ``n_effective``
    (1 / sum(p²)) is reported next to them.
    """
    d = np.asarray(deltas, dtype=np.float64).ravel()
    d = d[np.isfinite(d)]
    pos = d[d > 0]
    if pos.size == 0:
        return {"concentration": 0.0, "gini": 0.0, "n_effective": 0.0, "n_blocks": int(d.size)}
    k = max(1, int(np.ceil(TOP_FRAC * pos.size)))
    top = np.sort(pos)[-k:]
    p = pos / pos.sum()
    return {
        "concentration": float(top.sum() / pos.sum()),
        "gini": _gini(pos),
        "n_effective": float(1.0 / np.sum(p ** 2)),
        "n_blocks": int(d.size),
    }


def _gini(x: np.ndarray) -> float:
    v = np.sort(np.asarray(x, dtype=np.float64))
    n = v.size
    if n == 0 or v.sum() <= 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * v)) / (n * np.sum(v)) - (n + 1) / n)


# ---------------------------------------------------------------------------
# Gradient-based attribution + agreement check
# ---------------------------------------------------------------------------
def gradient_x_input(
    values: np.ndarray,     # (T, C, S, S) numpy
    mask: np.ndarray,
    torch_score_fn,         # (tensor, mask_tensor) -> scalar tensor
) -> dict:
    """Gradient x input attribution, ``(T, C, S, S)``.

    Attributions are taken on the MASKED input, so out-of-field padding can
    never accrue attribution (the farm-boundary invariant extends to the
    explanation, not just to the score).

    Two maps come back: ``gradient`` (∂score/∂x, the quantity a finite
    difference approximates) and ``attr = gradient ⊙ input`` (the attribution
    a human reads). They differ by the input factor, which is exactly the
    confusion a scale-blind agreement check would let pass — so
    :func:`gradient_finite_difference_agreement` compares against
    ``gradient`` and the tests pin ``attr`` against the closed form
    ``2x²·s/N``.

    ``attr = grad ⊙ detach(masked input)`` — the standard formulation. The
    detach is for graph hygiene (the result must not carry the score's graph
    into a caller's backward pass); the VALUE is identical either way, and
    ``test_gradient_attribution_matches_the_analytic_derivative`` pins it
    against the closed form.

    Axis note for callers: the batched tensor is ``(1, T, C, S, S)``, so a
    band index is axis 2 of the BATCHED tensor but axis 1 of the unbatched
    numpy input. Every score function used here must therefore index the
    batched tensor with ``t[:, :, c]``; the finite-difference agreement check
    is what catches a mismatch, and it did during development.
    """
    import torch

    x = torch.from_numpy(np.asarray(values, dtype=np.float32)).unsqueeze(0)
    m = torch.from_numpy(np.asarray(mask, dtype=bool)).unsqueeze(0)
    x = x.clone().requires_grad_(True)
    # The multiplication happens on the GRADIENT with the DETACHED masked
    # input: multiplying the live tensor would push d(xm)/dx = m·(1 + x·δ)
    # through the product rule and double-count / shift the attribution.
    xm = torch.where(m, x, torch.zeros_like(x))
    s = torch_score_fn(xm, m)
    s.backward()
    grad = x.grad.detach() * m                        # zero outside the field
    xm_det = xm.detach()
    attr = (grad * xm_det).numpy()[0]                 # grad ⊙ input
    return {
        "method": "gradient_x_input",
        "score": float(s.detach()),
        "attr": attr,
        "gradient": grad.numpy()[0],                  # ∂score/∂x, for FD checks
        "band_sum": attr.sum(axis=(0, 2, 3)).tolist(),
        "temporal_sum": attr.sum(axis=(1, 2, 3)).tolist(),
    }


def gradient_finite_difference_agreement(
    values: np.ndarray,
    mask: np.ndarray,
    score_fn,               # numpy score function
    gradient: np.ndarray,   # (T, C, S, S) ∂score/∂x — NOT gradxinput
    *,
    n_probe: int = 8,
    eps: float = 1e-2,
    seed: int = 0,
    probe: str = "informative",
) -> dict:
    """Compare a GRADIENT map against finite differences.

    ``probe``:
    ``informative`` (default) — sample among cells with a non-zero GRADIENT,
        because a uniform sample can land entirely on channels the score does
        not read; both sides are then constant zero, the correlation is
        undefined, and the check would report a false failure. Selection by
        the gradient's magnitude introduces no directional bias (the sign is
        not used), so a broken gradient still shows up.
    ``uniform`` — sample every observed non-zero cell (the strict variant).

    Compare a GRADIENT map against finite differences.

    Pass ``out["gradient"]`` from :func:`gradient_x_input`, never
    ``out["attr"]``: the attribution is scaled by the input, so comparing it
    to a finite difference would flag a correct implementation as wrong (and,
    worse, could let a wrongly-scaled one pass).


    A broken gradient can produce a plausible-looking map, so the spec asks
    for agreement on a small case. Only OBSERVED, non-zero cells are probed;
    the reported statistic is the Pearson correlation over them, with the sign
    concordance rate next to it (a correlation can be positive overall while
    individual signs are wrong).
    """
    if probe not in ("informative", "uniform"):
        raise ValueError(f"unknown probe mode {probe!r}")
    v = np.asarray(values, dtype=np.float64)
    m = np.asarray(mask, dtype=bool)
    grad = np.asarray(gradient, dtype=np.float64)
    if grad.shape != v.shape:
        raise ValueError(f"gradient shape {grad.shape} != values shape {v.shape}")
    idx = np.argwhere(m & (np.abs(v) > 1e-6))
    if probe == "informative":
        informative = idx[np.abs(grad[tuple(idx.T)]) > 1e-12] if idx.size else idx
        if informative.size:
            idx = informative
    if idx.size == 0:
        return {"usable": False, "reason": "no observed non-zero cell to probe"}
    rng = np.random.default_rng(seed)
    if len(idx) > n_probe:
        idx = idx[rng.choice(len(idx), size=n_probe, replace=False)]

    base = float(score_fn(v, m))
    fd, gv = [], []
    for i in idx:
        t = tuple(int(k) for k in i)
        vp = v.copy()
        vp[t] += eps
        fd.append((float(score_fn(vp, m)) - base) / eps)
        gv.append(float(grad[t]))
    fd_a = np.array(fd)
    gv_a = np.array(gv)
    ok = np.isfinite(fd_a) & np.isfinite(gv_a)
    if ok.sum() < 2:
        return {"usable": False, "reason": "too few finite probes"}
    # Correlation is undefined when either side is constant; a constant
    # gradient is itself a failure, so refusal (NaN) is the honest answer and
    # `agrees` is False by construction.
    if np.std(gv_a[ok]) > 0 and np.std(fd_a[ok]) > 0:
        corr = float(np.corrcoef(fd_a[ok], gv_a[ok])[0, 1])
    else:
        corr = float("nan")
    sign = float(np.mean(np.sign(fd_a[ok]) == np.sign(gv_a[ok])))
    return {
        "usable": True,
        "n_probe": int(ok.sum()),
        "probe": probe,
        "pearson": corr,
        "sign_concordance": sign,
        "eps": float(eps),
        "agrees": bool(np.isfinite(corr) and corr > 0.5 and sign > 0.7),
    }


# ---------------------------------------------------------------------------
# Faithfulness
# ---------------------------------------------------------------------------
def deletion_insertion_curves(
    values: np.ndarray,
    mask: np.ndarray,
    score_fn,
    attr: np.ndarray,
    *,
    steps: int = 8,
    seed: int = 0,
) -> dict:
    """Deletion/insertion AUC on the patch grid vs a random order.

    Deletion replaces the top-attributed cells by their median and tracks the
    score; insertion restores them from the median baseline. A faithful map
    makes deletion fall faster than random (``deletion_gain > 0``) and
    insertion rise faster (``insertion_gain > 0``).
    """
    v = np.asarray(values, dtype=np.float64)
    m = np.asarray(mask, dtype=bool)
    a = np.asarray(attr, dtype=np.float64)
    flat_attr = np.where(m, a, -np.inf).ravel()
    n = int(m.sum())
    if n == 0:
        return {"usable": False, "reason": "empty mask"}
    order = np.argsort(-flat_attr)[:n]
    rng = np.random.default_rng(seed)
    rand_order = rng.permutation(order)

    median = _median_baseline(v, m)
    flat_v = v.ravel().copy()
    flat_m = m.ravel()
    s_full = float(score_fn(v, m))

    fracs = np.linspace(0.0, 1.0, steps + 1)

    def _curve(seq: np.ndarray, mode: str) -> np.ndarray:
        out = []
        for f in fracs:
            k = int(round(f * n))
            arr = flat_v.copy()
            if mode == "deletion":
                arr[seq[:k]] = np.where(flat_m[seq[:k]], median, arr[seq[:k]])
            else:
                arr[seq[:k]] = flat_v[seq[:k]]
                arr[seq[k:]] = np.where(flat_m[seq[k:]], median, arr[seq[k:]])
            out.append(float(score_fn(arr.reshape(v.shape), m)))
        return np.array(out)

    _trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
    del_c = _curve(order, "deletion")
    ins_c = _curve(order, "insertion")
    r_del = _curve(rand_order, "deletion")
    r_ins = _curve(rand_order, "insertion")
    s_base = float(score_fn(np.where(m, median, v), m))
    denom = max(s_full - s_base, 1e-9)

    def _auc(c):
        return float(_trapz((c - s_base) / denom, fracs))

    return {
        "usable": True,
        "deletion_auc": _auc(del_c),
        "random_deletion_auc": _auc(r_del),
        "deletion_gain": _auc(r_del) - _auc(del_c),
        "insertion_auc": _auc(ins_c),
        "random_insertion_auc": _auc(r_ins),
        "insertion_gain": _auc(ins_c) - _auc(r_ins),
        "n_cells": n,
        "steps": int(steps),
    }


# ---------------------------------------------------------------------------
# Stage aggregation + artifact writers
# ---------------------------------------------------------------------------
def aggregate_to_stages(temporal_attr: np.ndarray) -> dict[str, float]:
    """Sum a per-bin attribution into the shared sugarcane stage bins."""
    a = np.asarray(temporal_attr, dtype=np.float64).ravel()
    out: dict[str, float] = {}
    for name, (lo, hi) in SUGARCANE_STAGE_BINS.items():
        lo = max(0, int(lo))
        hi = min(a.size, int(hi))
        out[name] = float(a[lo:hi].sum()) if hi > lo else 0.0
    return out


def band_table(band_attr: list[float], channel_names: list[str]) -> str:
    """Markdown band-attribution table (artifact writer)."""
    order = np.argsort(-np.asarray(band_attr))
    lines = ["| rank | band | attribution |", "|---|---|---|"]
    for r, i in enumerate(order, start=1):
        name = channel_names[i] if i < len(channel_names) else f"ch{i}"
        lines.append(f"| {r} | `{name}` | {band_attr[i]:.4f} |")
    return "\n".join(lines)


def temporal_table(stage_attr: dict[str, float]) -> str:
    total = sum(abs(v) for v in stage_attr.values()) or 1.0
    lines = ["| stage | attribution | share |", "|---|---|---|"]
    for name, v in sorted(stage_attr.items(), key=lambda kv: -abs(kv[1])):
        lines.append(f"| {name} | {v:.4f} | {abs(v) / total:.2%} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pre-registered sample
# ---------------------------------------------------------------------------
def attribution_sample_plan(
    events: list[dict],   # each: {"event_id", "family", "severity", "field_id"}
    *,
    n: int = SAMPLE_SIZE,
    seed: int = 13,
) -> dict:
    """Stratified, hash-recorded sample of events for attribution.

    Stratified by ``family`` x ``severity`` so a rare family cannot be
    represented by one event, and the resulting sample is hashed so the
    selection cannot be revised after the results are seen (the
    pre-registration discipline the spec requires).
    """
    if not events:
        raise ValueError("no events to sample from")
    rng = np.random.default_rng(seed)
    by_stratum: dict[tuple, list[dict]] = {}
    for e in events:
        key = (e.get("family"), e.get("severity"))
        by_stratum.setdefault(key, []).append(e)
    strata = sorted(by_stratum, key=lambda k: (str(k[0]), str(k[1])))
    per = max(1, int(np.ceil(n / max(1, len(strata)))))
    chosen: list[dict] = []
    for key in strata:
        pool = by_stratum[key]
        take = min(per, len(pool))
        idx = rng.choice(len(pool), size=take, replace=False)
        chosen.extend(pool[int(i)] for i in idx)
    chosen = chosen[:n]
    ids = sorted(str(e.get("event_id")) for e in chosen)
    blob = json.dumps({"ids": ids, "n": len(ids), "strata": [str(s) for s in strata],
                       "seed": int(seed)}, sort_keys=True)
    return {
        "n_requested": int(n),
        "n_selected": len(chosen),
        "strata": [str(s) for s in strata],
        "per_stratum_target": int(per),
        "coverage": {
            str(k): sum(1 for e in chosen if (e.get("family"), e.get("severity")) == k)
            for k in strata
        },
        "seed": int(seed),
        "event_ids": ids,
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "events": chosen,
    }


__all__ = [
    "HASH_METHODS",
    "SAMPLE_SIZE",
    "SAMPLE_STRATA",
    "aggregate_to_stages",
    "attribution_sample_plan",
    "band_occlusion",
    "band_table",
    "deletion_insertion_curves",
    "gradient_finite_difference_agreement",
    "gradient_x_input",
    "spatial_occlusion",
    "spatial_pattern_summary",
    "temporal_occlusion",
    "temporal_table",
]
