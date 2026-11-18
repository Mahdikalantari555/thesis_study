"""Independent Multi-Proxy Validation Gate ("Anomaly != Stress").

Enforces the strict literature-mandated boundary between:
  - ``unvalidated_spectral_thermal_anomaly``: statistical or self-supervised deviations
    from normal field-cycle trajectories that may include harvest shifts, lodging,
    cloud-shadow residuals, salinity, or management changes; and
  - ``validated_crop_stress_indicator``: anomaly scores that pass an explicit
    non-circular multi-proxy validation gate against independent agro-physical
    stress proxies (evaporative deficit ``ET0 - ETa``, LST-dropped optical score vs.
    ``CWSI``, yield/biomass deficit, and top-K event precision).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import bootstrap_ci, spearman_correlation


def evaluate_stress_validation_gate(
    *,
    full_anomaly_scores: np.ndarray,
    optical_only_anomaly_scores: np.ndarray | None = None,
    eta_deficit: np.ndarray | None = None,
    cwsi_proxy: np.ndarray | None = None,
    yield_deficit: np.ndarray | None = None,
    independent_stress_events: np.ndarray | None = None,
    min_proxy_rho: float = 0.20,
    min_top_k_precision: float = 0.50,
    top_k: int = 25,
    seed: int = 42,
) -> dict:
    """Evaluate whether anomaly scores earn independent 'crop stress' validation status.

    Crucially, ``cwsi_proxy`` (derived from ``ST_B10``) is ONLY counted as a
    non-circular validation proxy when evaluated against ``optical_only_anomaly_scores``
    (computed with ``ST_B10`` excluded from the detector).
    """
    proxies_evaluated: dict[str, dict] = {}
    passing_proxies: list[str] = []
    unmet_reasons: list[str] = []

    if eta_deficit is not None:
        rho, pval = spearman_correlation(full_anomaly_scores, eta_deficit)
        _, lo, hi = bootstrap_ci(
            lambda a, b: spearman_correlation(a, b)[0],
            full_anomaly_scores,
            eta_deficit,
            n_boot=800,
            seed=seed,
        )
        passed = bool(np.isfinite(rho) and rho >= min_proxy_rho and pval < 0.05)
        proxies_evaluated["eta_evaporative_deficit"] = {
            "non_circular": True,
            "spearman_rho": rho,
            "ci_95": [lo, hi],
            "pval": pval,
            "passed": passed,
        }
        if passed:
            passing_proxies.append("eta_evaporative_deficit")

    if cwsi_proxy is not None:
        if optical_only_anomaly_scores is not None:
            rho, pval = spearman_correlation(optical_only_anomaly_scores, cwsi_proxy)
            _, lo, hi = bootstrap_ci(
                lambda a, b: spearman_correlation(a, b)[0],
                optical_only_anomaly_scores,
                cwsi_proxy,
                n_boot=800,
                seed=seed + 1,
            )
            passed = bool(np.isfinite(rho) and rho >= min_proxy_rho and pval < 0.05)
            proxies_evaluated["non_circular_optical_vs_cwsi"] = {
                "non_circular": True,
                "spearman_rho": rho,
                "ci_95": [lo, hi],
                "pval": pval,
                "passed": passed,
            }
            if passed:
                passing_proxies.append("non_circular_optical_vs_cwsi")
        else:
            # Circular if LST is in full_anomaly_scores -> explicitly reject as independent gate!
            rho, pval = spearman_correlation(full_anomaly_scores, cwsi_proxy)
            proxies_evaluated["circular_full_vs_cwsi_diagnostic_only"] = {
                "non_circular": False,
                "spearman_rho": rho,
                "pval": pval,
                "passed": False,
                "warning": "Excluded from gate: ST_B10 appears in both full score and CWSI.",
            }

    if yield_deficit is not None:
        rho, pval = spearman_correlation(full_anomaly_scores, yield_deficit)
        _, lo, hi = bootstrap_ci(
            lambda a, b: spearman_correlation(a, b)[0],
            full_anomaly_scores,
            yield_deficit,
            n_boot=800,
            seed=seed + 2,
        )
        passed = bool(np.isfinite(rho) and rho >= min_proxy_rho and pval < 0.05)
        proxies_evaluated["agronomic_yield_deficit"] = {
            "non_circular": True,
            "spearman_rho": rho,
            "ci_95": [lo, hi],
            "pval": pval,
            "passed": passed,
        }
        if passed:
            passing_proxies.append("agronomic_yield_deficit")

    top_k_eff = min(top_k, len(full_anomaly_scores))
    top_idx = np.argsort(-full_anomaly_scores)[:top_k_eff]
    if independent_stress_events is not None and top_k_eff > 0:
        prec_k = float(np.mean(independent_stress_events[top_idx] > 0))
    else:
        prec_k = np.nan

    if len(passing_proxies) < 2:
        unmet_reasons.append(
            f"Fewer than 2 independent non-circular proxies passed rho>={min_proxy_rho} "
            f"(passed={passing_proxies})."
        )
    if np.isfinite(prec_k) and prec_k < min_top_k_precision:
        unmet_reasons.append(
            f"Top-{top_k_eff} independent stress precision {prec_k:.3f} < {min_top_k_precision:.2f}."
        )
    elif not np.isfinite(prec_k):
        unmet_reasons.append("No independent event-level labels/consensus supplied for Top-K precision.")

    gate_passed = len(unmet_reasons) == 0
    return {
        "gate_passed": gate_passed,
        "permitted_terminology": (
            "validated_crop_stress_indicator"
            if gate_passed
            else "unvalidated_spectral_thermal_anomaly"
        ),
        "n_passing_non_circular_proxies": len(passing_proxies),
        "passing_proxies": passing_proxies,
        "top_k": top_k_eff,
        "top_k_independent_stress_precision": prec_k,
        "proxies": proxies_evaluated,
        "unmet_criteria": unmet_reasons,
    }


def build_expert_event_review_packet(
    cycle_ids: np.ndarray,
    field_ids: np.ndarray,
    years: np.ndarray,
    anomaly_scores: np.ndarray,
    eta_deficit: np.ndarray | None = None,
    cwsi_proxy: np.ndarray | None = None,
    top_k: int = 30,
) -> pd.DataFrame:
    """Export stratified Top-K + median control review table for agronomy/irrigation audit."""
    order = np.argsort(-anomaly_scores)
    top_sel = order[: min(top_k, len(order))]
    med_start = len(order) // 2
    ctrl_sel = order[med_start : min(len(order), med_start + max(5, top_k // 5))]
    sel = np.concatenate([top_sel, ctrl_sel])
    stratum = ["top_k_candidate"] * len(top_sel) + ["median_control"] * len(ctrl_sel)

    df = pd.DataFrame(
        {
            "review_stratum": stratum,
            "cycle_id": cycle_ids[sel],
            "field_id": field_ids[sel],
            "year": years[sel],
            "anomaly_score": anomaly_scores[sel],
        }
    )
    if eta_deficit is not None:
        df["eta_deficit_mm_d"] = eta_deficit[sel]
    if cwsi_proxy is not None:
        df["cwsi_proxy"] = cwsi_proxy[sel]
    df["expert_label"] = "pending_agronomist_audit"
    return df
