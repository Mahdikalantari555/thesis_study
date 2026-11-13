"""Faithfulness, Sanity & Plant-Physiology Validation for Temporal XAI (RQ6 / Gap G6)."""

from __future__ import annotations

import copy
from collections.abc import Callable

import numpy as np
import torch

from ..eval.stats import spearman_correlation
from ..models.pretexts import PretextTransformer
from .attribution import differentiable_cycle_score


@torch.no_grad()
def deletion_insertion_auc(
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    attr_tb: np.ndarray,
    *,
    steps: int = 12,
    seed: int = 42,
) -> dict[str, float]:
    """Compute Deletion AUC, Insertion AUC, and Random-Order Deletion baseline.

    A faithful attribution map causes:
      - ``deletion_auc`` << ``random_deletion_auc`` (removing top-attributed cells rapidly kills anomaly score)
      - ``insertion_auc`` >> ``random_insertion_auc`` (inserting top-attributed cells rapidly restores anomaly score)
    """
    model.eval()
    T, nb = attr_tb.shape
    M = T * nb
    order = np.argsort(-attr_tb.reshape(-1))  # sort by largest positive anomaly contribution first!
    rng = np.random.default_rng(seed)
    rand_order = rng.permutation(M)

    fracs = np.linspace(0.0, 1.0, steps + 1)

    def _trace(ord_idx: np.ndarray, mode: str) -> np.ndarray:
        base_flat = baseline_tok[:, :nb].copy().reshape(-1)
        orig_flat = x_tok[:, :nb].copy().reshape(-1)
        batch = []
        for f in fracs:
            k = int(round(f * M))
            if mode == "deletion":
                arr = x_tok.copy()
                if k > 0:
                    sub = orig_flat.copy()
                    sub[ord_idx[:k]] = base_flat[ord_idx[:k]]
                    arr[:, :nb] = sub.reshape(T, nb)
            else:
                arr = baseline_tok.copy()
                arr[:, nb:] = x_tok[:, nb:]
                if k > 0:
                    sub = base_flat.copy()
                    sub[ord_idx[:k]] = orig_flat[ord_idx[:k]]
                    arr[:, :nb] = sub.reshape(T, nb)
            batch.append(arr)
        bt = torch.from_numpy(np.stack(batch, axis=0).astype(np.float32))
        sc = differentiable_cycle_score(model, bt).numpy().astype(np.float64)
        # Normalize curve between baseline score s0 and full anomaly score s1
        s_full = float(
            differentiable_cycle_score(
                model, torch.from_numpy(x_tok.astype(np.float32)).unsqueeze(0)
            ).item()
        )
        s_base = float(
            differentiable_cycle_score(
                model, torch.from_numpy(baseline_tok.astype(np.float32)).unsqueeze(0)
            ).item()
        )
        denom = max(s_full - s_base, 1e-6)
        return np.clip((sc - s_base) / denom, 0.0, 1.2)

    del_curve = _trace(order, "deletion")
    ins_curve = _trace(order, "insertion")
    r_del_curve = _trace(rand_order, "deletion")
    r_ins_curve = _trace(rand_order, "insertion")

    _trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
    del_auc = float(_trapz(del_curve, fracs))
    ins_auc = float(_trapz(ins_curve, fracs))
    r_del_auc = float(_trapz(r_del_curve, fracs))
    r_ins_auc = float(_trapz(r_ins_curve, fracs))

    return {
        "deletion_auc": del_auc,
        "random_deletion_auc": r_del_auc,
        "deletion_faithfulness_gain": r_del_auc - del_auc,
        "insertion_auc": ins_auc,
        "random_insertion_auc": r_ins_auc,
        "insertion_faithfulness_gain": ins_auc - r_ins_auc,
    }


def weight_randomization_sanity_check(
    attr_fn: Callable[[PretextTransformer, np.ndarray, np.ndarray], np.ndarray],
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    *,
    seed: int = 99,
) -> dict[str, float | bool]:
    """Adebayo et al. (2018) cascading weight-randomization sanity check."""
    a_trained = attr_fn(model, x_tok, baseline_tok)
    rand_model = copy.deepcopy(model)
    torch.manual_seed(seed)
    for p in rand_model.parameters():
        if p.ndim >= 2:
            torch.nn.init.xavier_uniform_(p)
        else:
            torch.nn.init.normal_(p, std=0.05)
    rand_model.eval()
    a_rand = attr_fn(rand_model, x_tok, baseline_tok)
    rho, _ = spearman_correlation(a_trained.reshape(-1), a_rand.reshape(-1))
    abs_rho = abs(rho) if np.isfinite(rho) else 0.0
    return {
        "spearman_trained_vs_randomized": float(rho) if np.isfinite(rho) else 0.0,
        "abs_spearman": abs_rho,
        "passes_sanity_threshold_0.35": bool(abs_rho < 0.35),
    }


def physiology_sign_concordance(
    signed_attr_tb: np.ndarray,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    band_names: list[str],
    stress_bins: np.ndarray,
) -> dict[str, float]:
    """Test whether signed attributions match agronomic plant-physiology directions on stress bins.

    During mid-season water/heat stress (``stress_bins``):
      - Canopy greenness / NIR loss (``SR_B5``, ``NDVI``, ``NDMI`` below normal baseline, i.e. ``delta < 0``)
        should increase anomaly score -> ``signed_attr > 0``!
      - Canopy heating / leaf-water loss (``ST_B10``, ``SR_B6``, ``SR_B7``, ``SR_B4`` above normal baseline,
        i.e. ``delta > 0``) should increase anomaly score -> ``signed_attr > 0``!
    """
    bmap = {b: i for i, b in enumerate(band_names)}
    checks: dict[str, list[float]] = {
        "canopy_loss_positive_attr": [],
        "thermal_heating_positive_attr": [],
        "swir_dehydration_positive_attr": [],
    }

    delta = x_tok[:, : len(band_names)] - baseline_tok[:, : len(band_names)]
    for b_name in ("SR_B5", "NDVI", "NDMI"):
        if b_name in bmap:
            bi = bmap[b_name]
            m = delta[stress_bins, bi] < -1.5
            if np.any(m):
                checks["canopy_loss_positive_attr"].extend(
                    (signed_attr_tb[stress_bins[m], bi] > 0.0).astype(float).tolist()
                )

    if "ST_B10" in bmap:
        bi = bmap["ST_B10"]
        m = delta[stress_bins, bi] > 1.5
        if np.any(m):
            checks["thermal_heating_positive_attr"].extend(
                (signed_attr_tb[stress_bins[m], bi] > 0.0).astype(float).tolist()
            )

    for b_name in ("SR_B6", "SR_B7"):
        if b_name in bmap:
            bi = bmap[b_name]
            m = delta[stress_bins, bi] > 1.5
            if np.any(m):
                checks["swir_dehydration_positive_attr"].extend(
                    (signed_attr_tb[stress_bins[m], bi] > 0.0).astype(float).tolist()
                )

    out: dict[str, float] = {}
    all_hits: list[float] = []
    for k, vals in checks.items():
        out[k] = float(np.mean(vals)) if vals else np.nan
        all_hits.extend(vals)
    out["overall_physiology_sign_concordance"] = float(np.mean(all_hits)) if all_hits else np.nan
    return out
