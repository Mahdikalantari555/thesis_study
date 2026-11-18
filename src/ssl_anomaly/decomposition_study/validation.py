"""Paired synthetic challenges and descriptive, never ground-truth, evidence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score

from ssl_anomaly.decomposition_study.data import NIR, Panel, Split
from ssl_anomaly.decomposition_study.decompose import YEAR
from ssl_anomaly.decomposition_study.features import Normalizer
from ssl_anomaly.decomposition_study.scoring import finite_vector, maxima

FAMILIES = ("abrupt_drop", "gradual_drop", "oscillation", "seasonal_change", "persistent_trend")
DOSES = (0.5, 1.0, 2.0)
PERTURBATION_SEED = 951
INDICATORS = ("tvdi", "cwsi", "eta")


def perturb(panel: Panel, split: Split, family: str, dose: float) -> tuple[Panel, np.ndarray]:
    """Change only observed NIR in evaluation, preserving the clean counterfactual."""
    if family not in FAMILIES or dose <= 0:
        raise ValueError("Unknown synthetic perturbation family or non-positive dose")
    raw = panel.optical.copy()
    nir = raw[..., NIR]
    sd = Normalizer.fit(nir[..., None], split.train_end).scale[:, 0, 0]
    start = split.cal_end
    days = panel.days
    changed = np.zeros(nir.shape, dtype=bool)
    for f, field in enumerate(panel.fields):
        if not np.isfinite(sd[f]):
            continue
        # The same onset is used for all doses, families, methods, branches and model seeds.
        rng = np.random.default_rng(np.random.SeedSequence([PERTURBATION_SEED, int(field)]))
        anchor = days[start] + rng.integers(7, 45)
        obs = np.flatnonzero((days >= anchor) & np.isfinite(nir[f]))
        if not obs.size:
            continue
        elapsed = days[obs] - days[obs[0]]
        if family == "abrupt_drop":
            delta = -(elapsed == 0).astype(float)
        elif family == "gradual_drop":
            delta = -np.where(elapsed < 90, np.minimum(1.0, (elapsed + 1) / 90), 0.0)
        elif family == "oscillation":
            delta = np.where(elapsed < 90, (-1.0) ** np.arange(len(obs)), 0.0)
        elif family == "seasonal_change":
            phase = 2 * np.pi * elapsed / YEAR
            delta = np.where(elapsed < YEAR, np.sin(phase + np.pi / 3) - np.sin(phase), 0.0)
        else:
            delta = -np.minimum(1.0, (elapsed + 1) / 120)
        affected = obs[np.abs(delta) > 1e-7]
        original = nir[f, affected].copy()
        nir[f, affected] = np.clip(original + dose * sd[f] * delta[np.abs(delta) > 1e-7], -0.1, 1.6)
        changed[f, affected] = nir[f, affected] != original
    return panel.with_optical(raw), changed


def with_gaps(panel: Panel, split: Split) -> Panel:
    raw = panel.optical.copy()
    for f, field in enumerate(panel.fields):
        eligible = np.flatnonzero(
            np.isfinite(raw[f]).any(axis=-1) & (np.arange(raw.shape[1]) >= split.cal_end)
        )
        rng = np.random.default_rng(np.random.SeedSequence([PERTURBATION_SEED, int(field), 20]))
        drop = rng.choice(eligible, size=len(eligible) // 5, replace=False)
        raw[f, drop] = np.nan
    return panel.with_optical(raw)


def correlation(x: np.ndarray, y: np.ndarray) -> dict:
    common = np.isfinite(x) & np.isfinite(y)
    a, b = x[common], y[common]
    rho = None
    if len(a) >= 3 and np.ptp(a) > 0 and np.ptp(b) > 0:
        rho = float(spearmanr(a, b).statistic)
    return {"n": len(a), "spearman": rho}


def describe(x: np.ndarray) -> dict:
    v = finite_vector(x)
    return {
        "n": len(v),
        "median": float(np.median(v)) if len(v) else None,
        "mean": float(v.mean(dtype=np.float64)) if len(v) else None,
    }


def stability(scores: np.ndarray, days: np.ndarray) -> dict:
    diff = np.abs(np.diff(scores, axis=1))
    diff[:, np.diff(days) > 60] = np.nan
    return describe(diff)


def holdout_score(scores: np.ndarray, days: np.ndarray, threshold: float | None) -> dict:
    seen = np.isfinite(scores)
    return {
        **describe(scores),
        "n_fields": int(seen.any(axis=1).sum()),
        "n_dates": int(seen.any(axis=0).sum()),
        "n_eligible_field_dates": int(scores.size),
        "alarm_fraction": (
            float((scores[seen] > threshold).mean())
            if seen.any() and threshold is not None
            else None
        ),
        "temporal_stability_abs_step": stability(scores, days),
    }


def synthetic_metrics(
    clean: np.ndarray, injected: np.ndarray, changed: np.ndarray, threshold: float | None
) -> dict:
    common = np.isfinite(clean) & np.isfinite(injected)
    positive = common & changed
    n_support, n_pos = int(common.sum()), int(positive.sum())
    out = {
        "n_common": n_support,
        "n_changed": int(changed.sum()),
        "n_positive": n_pos,
        "n_positive_fields": int(positive.any(axis=1).sum()),
        "n_positive_dates": int(positive.any(axis=0).sum()),
        "prevalence": n_pos / (2 * n_support) if n_support else None,
        "ap_date": None,
        "ap_field": None,
        "median_score_uplift": None,
        "changed_alarm_fraction": None,
    }
    if not n_pos:
        return out
    c, p = clean[common], injected[common]
    y = np.r_[np.zeros(n_support, dtype=bool), changed[common]]
    out["ap_date"] = float(average_precision_score(y, np.r_[c, p]))
    fields = positive.any(axis=1)
    cf, pf = (maxima(np.where(common, x, np.nan), axis=1)[fields] for x in (clean, injected))
    out["ap_field"] = float(
        average_precision_score(np.r_[np.zeros(len(cf)), np.ones(len(pf))], np.r_[cf, pf])
    )
    out["median_score_uplift"] = float(np.median(injected[positive] - clean[positive]))
    if threshold is not None:
        out["changed_alarm_fraction"] = float((injected[positive] > threshold).mean())
    return out


def changed_uplift(clean: np.ndarray, injected: np.ndarray, changed: np.ndarray) -> np.ndarray:
    """Uplift on field-dates actually changed and scored in both views."""
    paired = changed & np.isfinite(clean) & np.isfinite(injected)
    out = np.full(clean.shape, np.nan, dtype=np.float64)
    np.subtract(injected, clean, out=out, where=paired, dtype=np.float64)
    return out


def matched_dose_response(doses: np.ndarray, uplifts: list[np.ndarray]) -> dict:
    """Compare all doses on one observed/scored positive cohort, not just equal counts."""
    if (
        len(doses) != len(uplifts)
        or not uplifts
        or any(x.shape != uplifts[0].shape or x.ndim != 2 for x in uplifts)
    ):
        raise ValueError("dose uplift arrays must share the same (field, date) axes")
    finite = [np.isfinite(x) for x in uplifts]
    shared = np.logical_and.reduce(finite)
    n = int(shared.sum())
    medians = [float(np.median(x[shared])) if n else None for x in uplifts]
    return {
        **correlation(doses, np.array(medians, dtype=float)),
        "n_matched_field_dates": n,
        "n_matched_fields": int(shared.any(axis=1).sum()),
        "n_matched_dates": int(shared.any(axis=0).sum()),
        "doses": [
            {
                "dose_train_scale": float(dose),
                "n_positive": int(seen.sum()),
                "n_excluded_by_matching": int(seen.sum()) - n,
                "median_matched_uplift": median,
            }
            for dose, seen, median in zip(doses, finite, medians)
        ],
    }


def read_evidence(path: Path | None, *, adjacency: bool = False) -> pd.DataFrame | None:
    if path is None:
        return None
    frame = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path)
    keys = ["field_id", "neighbor_id"] if adjacency else ["field_id", "date", "indicator"]
    columns = {*keys, "source"} if adjacency else {*keys, "source", "observed", "value"}
    if not columns.issubset(frame):
        raise ValueError(f"{path} is missing evidence columns {sorted(columns - set(frame))}")
    for name in ("field_id", "neighbor_id") if adjacency else ("field_id",):
        num = pd.to_numeric(frame[name], errors="raise")
        if not (np.isfinite(num) & (num > 0) & (num % 1 == 0)).all():
            raise ValueError(f"Invalid {name} in {path}")
        frame[name] = num.astype(int)
    if frame["source"].isna().any() or frame["source"].astype(str).str.strip().eq("").any():
        raise ValueError(f"Evidence without provenance in {path}")
    if adjacency:
        frame[["field_id", "neighbor_id"]] = np.sort(frame[["field_id", "neighbor_id"]], axis=1)
        if (frame.field_id == frame.neighbor_id).any():
            raise ValueError(f"Self-neighbors in {path}")
    else:
        frame["indicator"] = frame["indicator"].astype(str).str.lower()
        frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise").dt.as_unit(
            "s"
        )
        obs = frame["observed"].astype(str).str.lower()
        if not obs.isin({"0", "1", "true", "false"}).all() or frame["date"].isna().any():
            raise ValueError(f"Invalid observed flags or dates in {path}")
        if not frame["indicator"].isin(INDICATORS).all():
            raise ValueError(f"Expected indicator names {INDICATORS} in {path}")
        frame = frame.loc[obs.isin({"1", "true"})].copy()
        frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    if frame.duplicated(keys).any():
        raise ValueError(f"Duplicate evidence keys {keys} in {path}")
    return frame


def evidence_metrics(
    scores: np.ndarray,
    fields: np.ndarray,
    dates: np.ndarray,
    indicators: pd.DataFrame | None,
    adjacency: pd.DataFrame | None,
) -> dict:
    pairs = {key: {"status": "absent", "n": 0, "spearman": None} for key in INDICATORS}
    if indicators is not None:
        score_rows = pd.DataFrame(
            {
                "field_id": np.repeat(fields, len(dates)),
                "date": np.tile(dates.astype("datetime64[s]"), len(fields)),
                "score": scores.ravel(),
            }
        )
        merged = score_rows.merge(indicators, on=["field_id", "date"])
        for key in INDICATORS:
            rows = merged.loc[
                (merged.indicator == key) & np.isfinite(merged.score) & np.isfinite(merged.value)
            ]
            if len(rows):
                pairs[key] = {
                    "status": "agreement_only",
                    **correlation(rows.score.to_numpy(), rows.value.to_numpy()),
                    "sources": sorted(rows.source.unique()),
                    "n_dates": int(rows.date.nunique()),
                    "n_fields": int(rows.field_id.nunique()),
                }
    spatial = {"status": "absent", "n": 0, "spearman": None}
    if adjacency is not None:
        row = {int(f): i for i, f in enumerate(fields)}
        eligible = adjacency.loc[adjacency.field_id.isin(row) & adjacency.neighbor_id.isin(row)]
        if len(eligible):
            # Include both directions of every undirected edge to avoid orientation effects.
            a, b = (
                scores[eligible[name].map(row).to_numpy()] for name in ("field_id", "neighbor_id")
            )
            result = correlation(np.r_[a, b], np.r_[b, a])
            result["n"] //= 2
            spatial = {
                "status": "descriptive" if result["n"] else "absent",
                **result,
                "n_edges_with_support": int((np.isfinite(a) & np.isfinite(b)).any(axis=1).sum()),
                "sources": sorted(eligible.source.unique()),
            }
    return {"indicator_agreement": pairs, "neighbor_consistency": spatial}
