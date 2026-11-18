"""Read-only study orchestration, resumable at benchmark/epoch/challenge boundaries."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from contextlib import ExitStack
from dataclasses import asdict
from functools import partial
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from ssl_anomaly.decomposition_study import decompose as dec
from ssl_anomaly.decomposition_study import features as ft
from ssl_anomaly.decomposition_study import scoring as sc
from ssl_anomaly.decomposition_study import validation as ev
from ssl_anomaly.decomposition_study.data import BANDS, BRANCHES, INDICES, NIR, Panel, Split

SEEDS = (13, 42, 2026)
REPO = Path(__file__).resolve().parents[3]


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def arrays_digest(*arrays: np.ndarray) -> str:
    sha = hashlib.sha256()
    for a in arrays:
        sha.update(str((a.shape, a.dtype.str)).encode())
        sha.update(np.ascontiguousarray(a).tobytes())
    return sha.hexdigest()


def json_save(path: Path, value: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def npz_save(path: Path, **arrays) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("wb") as f:
        np.savez_compressed(f, **arrays)
    tmp.replace(path)


class Run:
    def __init__(
        self, out: Path, panel: Panel, split: Split, settings: dict, *, resume: bool, quiet: bool
    ):
        self.out = out.resolve()
        self.quiet = quiet
        self.start = time.perf_counter()
        self.panel = panel
        self.split = split
        self.settings = settings
        protected = [
            REPO / p
            for p in (
                "platform",
                "src",
                "conf",
                "scripts",
                "tests",
                "openspec",
                "checkpoints",
                "data/processed",
                "data/interim",
                ".git",
            )
        ]
        if "source_path" in panel.provenance:
            protected.append(Path(panel.provenance["source_path"]))
        if any(self.out.is_relative_to(p.resolve()) for p in protected):
            raise ValueError("Use a separate study output directory, not an input or pipeline path")
        source_paths = list(Path(__file__).parent.glob("*.py")) + [
            REPO / p
            for p in (
                "scripts/run_decomposition_study.py",
                "src/ssl_anomaly/models/gru_ae.py",
                "src/ssl_anomaly/monitor/holdout.py",
            )
        ]
        code_digest = hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(source_paths))
        ).hexdigest()
        plan = {
            **panel.provenance,
            **settings,
            "splits": split.describe(panel.dates),
            "input_sha256": arrays_digest(panel.fields, panel.dates, panel.optical, panel.quality),
            "split_sha256": arrays_digest(
                panel.fields, panel.dates, np.array([split.train_end, split.cal_end])
            ),
            "code_sha256": code_digest,
            "versions": {p: version(p) for p in ("numpy", "statsmodels", "pandas", "scikit-learn")},
            "n_fields": len(panel.fields),
            "n_acquisitions": len(panel.dates),
            "date_range": [str(panel.dates[0]), str(panel.dates[-1])],
            "observed_channel_cells": {
                name: int(np.isfinite(panel.branch(name)).sum()) for name in BRANCHES
            },
            "features": {
                "bands": BANDS,
                "indices": INDICES,
                "ablations": ft.ARMS,
                "statistics_per_level": ft.STAT_NAMES,
            },
            "decomposition": {
                "grid_days": dec.GRID_DAYS,
                "period_bins": dec.PERIOD,
                "max_gap_bins": dec.MAX_GAP_BINS,
                "refresh_days": dec.REFRESH_DAYS,
                "max_causal_age_days": dec.MAX_CAUSAL_AGE_DAYS,
            },
            "synthetic": {
                "seed": ev.PERTURBATION_SEED,
                "doses": ev.DOSES,
                "families": ev.FAMILIES,
                "provenance": "design-choice NIR perturbations",
            },
        }
        fingerprint = digest(plan)
        manifest = self.out / "run.json"
        if self.out.exists() and any(self.out.iterdir()):
            if not resume or not manifest.is_file():
                raise ValueError(
                    f"Output {self.out} is not empty; use --resume with the same run or a new path"
                )
            self.manifest = json.loads(manifest.read_text(encoding="utf-8"))
            if self.manifest["run_sha256"] != fingerprint:
                raise ValueError(
                    "Resume refused: study inputs, settings, environment or code changed"
                )
        else:
            self.out.mkdir(parents=True, exist_ok=True)
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
            self.manifest = {
                **plan,
                "run_sha256": fingerprint,
                "git_sha": sha,
                "claim": "research anomalies, not verified agricultural stress",
            }
            json_save(manifest, self.manifest)

    def record(self, **event) -> None:
        with (self.out / "progress.jsonl").open("a", encoding="utf-8") as f:
            print(
                json.dumps(
                    {"invocation_seconds": time.perf_counter() - self.start, **event},
                    allow_nan=False,
                ),
                file=f,
            )

    @property
    def provenance(self) -> dict:
        return {
            key: self.manifest[key]
            for key in (
                "data_source",
                "input_sha256",
                "split_sha256",
                "run_sha256",
                "git_sha",
                "device",
                "seeds",
                "date_range",
                "n_fields",
                "n_acquisitions",
                "holdout_manifest_sha256",
            )
            if key in self.manifest
        }


def benchmark(run: Run, methods: tuple[str, ...], protocols: tuple[str, ...]) -> dict:
    """Fit and cache the raw benchmark once, with no neural dependencies."""
    split, panel = run.split, run.panel
    report: dict = {"provenance": run.provenance, "evidence_scope": "decomposition fit diagnostic"}
    out = run.out / "decomposition"
    out.mkdir(exist_ok=True)
    all_components = {}
    for branch in BRANCHES:
        raw = panel.branch(branch)
        records, times = {}, {}
        options = [(p, m) for p in protocols for m in methods]
        for protocol, method in tqdm(options, desc=f"Decomposition {branch}", disable=run.quiet):
            path = out / f"{branch}_{protocol}_{method}.npz"
            if path.is_file():
                with np.load(path, allow_pickle=False) as store:
                    comp = dec.Components(
                        **{k: store[k] for k in dec.Components.__dataclass_fields__}
                    )
                    seconds = store["fit_seconds"].item()
            else:
                start = time.perf_counter()
                comp = dec.decompose(panel.days, raw, split, method, protocol)
                seconds = time.perf_counter() - start
                npz_save(
                    path,
                    **vars(comp),
                    fit_seconds=seconds,
                    fields=panel.fields,
                    days=panel.days,
                    observed=np.isfinite(raw),
                    channels=BANDS if branch == "bands" else INDICES,
                )
            records[protocol, method], times[protocol, method] = comp, seconds
            run.record(
                event="decomposition",
                branch=branch,
                protocol=protocol,
                method=method,
                fit_seconds=seconds,
            )
        actual = np.isfinite(raw)
        common = actual.copy()
        for comp in records.values():
            common &= np.isfinite(comp.residual)
        exp = split.blocks[-1]
        scale = ft.Normalizer.fit(raw, split.train_end).scale
        common &= np.isfinite(scale)
        result = {
            "observed_eval_cells": int(actual[:, exp].sum()),
            "common_eval_cells": int(common[:, exp].sum()),
            "arms": {},
        }
        for (protocol, method), comp in records.items():
            normalized = np.abs(comp.residual / scale)[:, exp]
            result["arms"][f"{protocol}/{method}"] = {
                "wall_seconds": times[protocol, method],
                "eval_observed_component_cells": int(np.isfinite(comp.residual[:, exp]).sum()),
                "individual_absolute_residual_scaled": ev.describe(normalized),
                "paired_absolute_residual_scaled": ev.describe(
                    np.where(common[:, exp], normalized, np.nan)
                ),
                "raw_absolute_residual_by_channel": {
                    name: ev.describe(np.abs(comp.residual[:, exp, c]))
                    for c, name in enumerate(BANDS if branch == "bands" else INDICES)
                },
                "component_stability_scaled": {
                    name: ev.stability(
                        np.where(common, getattr(comp, name) / scale, np.nan)[:, exp],
                        panel.days[exp],
                    )
                    for name in ("trend", "seasonal", "residual")
                },
                "grid_observed_cells_over_fits": int((comp.grid_states == 1).sum()),
                "grid_interpolated_cells_over_fits": int((comp.grid_states == 2).sum()),
                "leakage_status": "as_of_refresh" if protocol == "causal" else "offline_lookahead",
            }
            if method == run.settings["method"] and run.settings["stage"] != "benchmark":
                # Drop the large provenance grids from memory after writing them to disk.
                all_components[branch, protocol] = dec.Components(
                    comp.trend,
                    comp.seasonal,
                    comp.residual,
                    comp.fit_before,
                    np.empty(0, dtype=np.uint8),
                    comp.grid_fit_before,
                )
        report[branch] = result
    json_save(run.out / "benchmark.json", report)
    return all_components


def target_support(raw: np.ndarray, comp: dec.Components, train_end: int) -> np.ndarray:
    """Native support of one mode, with no dependency on the other protocol."""
    return (
        np.isfinite(raw)
        & np.isfinite(ft.Normalizer.fit(raw, train_end).scale)
        & np.isfinite(comp.residual)
    )


def compare_protocols(run: Run, components: dict) -> None:
    """After scoring, restrict descriptive contrasts to identical target-channel sets."""
    split, panel = run.split, run.panel
    exp = split.blocks[-1]
    report = {
        "provenance": run.provenance,
        "note": "Post-hoc comparison only; the retrospective "
        "mask never affects causal training, calibration, or scores.",
        "branches": {},
    }
    for branch in BRANCHES:
        raw = panel.branch(branch)
        causal, retro = [
            target_support(raw, components[branch, mode], split.train_end)[:, exp]
            for mode in dec.PROTOCOLS
        ]
        matched = ((causal == retro).all(axis=-1) & causal.any(axis=-1)).ravel()
        left, right = [
            pd.read_parquet(run.out / f"{branch}_{mode}/field_date_scores.parquet")
            for mode in dec.PROTOCOLS
        ]
        if not left[["field_id", "date"]].equals(right[["field_id", "date"]]):
            raise ValueError("Causal and retrospective result coordinates do not match")
        rows = {}
        for key in left.columns[3:]:
            a, b = (frame[key].to_numpy()[matched] for frame in (left, right))
            joint = np.isfinite(a) & np.isfinite(b)
            rows[key] = {
                "causal": ev.describe(a[joint]),
                "retrospective": ev.describe(b[joint]),
                "retrospective_minus_causal": ev.describe(b[joint] - a[joint]),
            }
        report["branches"][branch] = {
            "n_field_dates_same_target_channels": int(matched.sum()),
            "scores": rows,
        }
    json_save(run.out / "protocol_comparison.json", report)


def _model_name(arm: str, seed: int) -> str:
    return f"D1_{arm}_seed{seed}"


def _write_scores(path: Path, panel: Panel, block: slice, scores: dict, limits: dict) -> None:
    """Write wide observed-score tables, plus symmetric field/date rollups."""
    field_ids, dates = panel.fields, panel.dates[block]
    base = {
        "field_id": np.repeat(field_ids, len(dates)),
        "date": np.tile(dates, len(field_ids)),
        "valid_frac": panel.quality[:, block].ravel(),
    }
    data = {**base, **{k: v[:, block].ravel() for k, v in scores.items()}}
    pd.DataFrame(data).to_parquet(path / "field_date_scores.parquet", index=False)
    for label, coordinate, axis in (("field", field_ids, 1), ("date", dates, 0)):
        columns = {label if label == "date" else "field_id": coordinate}
        for key, val in scores.items():
            x = val[:, block]
            columns[f"{key}_max"] = sc.maxima(x, axis=axis)
            columns[f"{key}_n"] = np.isfinite(x).sum(axis=axis)
            thr = limits[key]
            if thr is not None:
                columns[f"{key}_n_over_date_threshold"] = (x > thr).sum(axis=axis)
        pd.DataFrame(columns).to_parquet(path / f"{label}_summary.parquet", index=False)


def _spread(x) -> dict:
    values = [v for v in x if v is not None]
    return {
        "n_seeds": len(values),
        "mean": float(np.mean(values)) if values else None,
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else None,
    }


def _seed_rollups(clean: dict, cases: dict, seeds: tuple[int, ...]) -> dict:
    if not seeds:
        return {}
    arms = (*ft.ARMS, "random_B1")
    return {
        arm: {
            "raw_holdout_mse": _spread(clean[_model_name(arm, seed)]["mean"] for seed in seeds),
            "paired_mse_delta_vs_raw": _spread(
                clean[_model_name(arm, seed)]["mean"] - clean[_model_name("B1", seed)]["mean"]
                if clean[_model_name(arm, seed)]["mean"] is not None
                else None
                for seed in seeds
            ),
            "ap_date_by_scenario": {
                key: _spread(sample["arms"][_model_name(arm, seed)]["ap_date"] for seed in seeds)
                for key, sample in cases.items()
            },
        }
        for arm in arms
    }


def _gate(source: str, protocol: str, clean: dict, cases: dict, seeds: tuple[int, ...]) -> dict:
    if source == "simulated_smoke" or protocol != "causal" or seeds != SEEDS:
        return {
            "status": "not_eligible",
            "reason": "requires real causal evidence at all registered seeds",
        }
    qualified = []
    for arm in tuple(ft.ARMS)[1:]:
        if arm == "C1":  # C1 can support a stats hypothesis, not the decomposition gate.
            continue
        passes = []
        for seed in seeds:
            raw, candidate = _model_name("B1", seed), _model_name(arm, seed)
            ra, ca = clean[raw], clean[candidate]
            if (
                ca["n_fields"] < 20
                or ca["n"] < 100
                or ra["mean"] is None
                or ca["mean"] is None
                or ca["mean"] >= ra["mean"]
            ):
                passes.append(False)
                continue
            paired = [(s["arms"][candidate], s["arms"][raw]) for s in cases.values()]
            deltas = [
                x["ap_date"] - y["ap_date"]
                for x, y in paired
                if min(x["n_positive_fields"], y["n_positive_fields"]) >= 20
                and x["n_positive"] == y["n_positive"]
                and x["n_common"] == y["n_common"]
                and x["ap_date"] is not None
                and y["ap_date"] is not None
            ]
            passes.append(len(deltas) == len(ev.FAMILIES) * len(ev.DOSES) and np.mean(deltas) > 0)
        if all(passes):
            qualified.append(arm)
    return {
        "status": "eligible_for_review" if qualified else "not_met",
        "arms": qualified,
        "decision_is_development_only": True,
        "trained_multi_branch": False,
    }


def study_case(
    run: Run,
    branch: str,
    protocol: str,
    comp: dec.Components,
    indicator_path: Path | None,
    adjacency_path: Path | None,
) -> dict:
    """Fit on natural train rows, freeze on calibration, then evaluate challenges."""
    panel, split = run.panel, run.split
    seeds = tuple(run.settings["seeds"])
    device, method = run.settings["device"], run.settings["method"]
    train, cal, exp = split.blocks
    folder = run.out / f"{branch}_{protocol}"
    folder.mkdir(exist_ok=True)
    summary_file = folder / "summary.json"
    if summary_file.is_file():
        return json.loads(summary_file.read_text(encoding="utf-8"))
    start = time.perf_counter()
    log = partial(run.record, branch=branch, protocol=protocol)
    raw = panel.branch(branch)
    matched = target_support(raw, comp, split.train_end)
    drift = sc.trend_drift(panel.days, comp.trend, split.train_end)
    phase_channel = NIR if branch == "bands" else INDICES.index("ndvi")
    ref = sc.reference_groups(panel.days, raw[..., phase_channel], split.train_end)
    banks = sc.fit_banks(sc.score_inputs(raw, comp, drift), ref, split.train_end)
    norms, models, model_report, slots = {}, {}, {}, {}
    gaps = np.diff(panel.days, prepend=panel.days[0])
    if seeds:
        from ssl_anomaly.decomposition_study import ssl

        for name, block in zip(("training", "calibration", "evaluation"), split.blocks):
            if not matched[:, block].any():
                raise ValueError(
                    f"No common observed {name} targets for {branch}; inspect benchmark coverage"
                )
        stats = ft.statistics(panel.days, raw, split.train_end)
        residual_z = ft.residual_local_z(panel.days, comp.residual)
        groups = ft.feature_groups(raw, comp, stats, residual_z)
        norms = ft.fit_feature_norms(groups, split.train_end)
        feats = ft.feature_tokens(groups, norms)
        target = np.where(matched, norms["raw"].apply(raw), np.nan)
        slots = {a: ft.arm_slots(a, groups) for a in ft.ARMS}
        npz_save(
            folder / "feature_norms.npz",
            fields=panel.fields,
            **{
                f"{k}_{part}": getattr(n, part)
                for k, n in norms.items()
                for part in ("center", "scale")
            },
        )
        jobs = [(a, s) for a in ft.ARMS for s in seeds]
        for arm, seed in tqdm(jobs, desc=f"Train {branch}/{protocol}", disable=run.quiet):
            name = _model_name(arm, seed)
            model, random_model, meta = ssl.train_model(
                feats,
                slots[arm],
                gaps,
                target,
                train.stop,
                seed,
                run.settings["epochs"],
                device,
                folder / f"{name}.pt",
                partial(log, arm=arm, seed=seed),
                show_progress=not run.quiet,
            )
            models[name] = (model, slots[arm])
            json_save(
                folder / f"{name}.json",
                {
                    **run.provenance,
                    **meta,
                    "seed": seed,
                    "arm": arm,
                    "branch": branch,
                    "protocol": protocol,
                },
            )
            model_report[name] = meta
            if arm == "B1":
                models[_model_name("random_B1", seed)] = (random_model, slots[arm])
    else:
        stats = None

    def score(view: Panel, model_comp: dec.Components, *, natural: bool) -> dict[str, np.ndarray]:
        x = view.branch(branch)
        valid = matched & np.isfinite(x) & np.isfinite(model_comp.residual)
        groups = (
            ref
            if natural
            else sc.reference_groups(view.days, x[..., phase_channel], split.train_end)
        )
        independent = sc.component_scores(
            sc.score_inputs(x, model_comp, drift), groups, valid, banks
        )
        if not models:
            return independent
        if natural:
            feat = feats
        else:
            g, loc = stats
            changed_stats = ft.statistics(
                view.days,
                x,
                split.train_end,
                changed_from=exp.start,
                local_baseline=loc,
                global_baseline=g,
            )
            changed_z = ft.residual_local_z(
                view.days, model_comp.residual, start=exp.start, baseline=residual_z
            )
            feat = ft.feature_tokens(
                ft.feature_groups(x, model_comp, changed_stats, changed_z), norms
            )
        wanted = np.where(valid, norms["raw"].apply(x), np.nan)
        for name, (model, active) in models.items():
            # Start evaluation blocks at the same date in both counterfactuals,
            # so a changed warm-up boundary is never mistaken for a signal.
            error = ssl.predict(model, feat, active, gaps, wanted, exp.start, exp.stop, device)
            if natural:
                err_cal = ssl.predict(
                    model, feat, active, gaps, wanted, cal.start, cal.stop, device
                )
                error[:, cal] = err_cal[:, cal]
            independent[name] = ft.masked_mean(error, axis=-1)
        return independent

    clean = score(panel, comp, natural=True)
    hybrids = {}
    for ref_name in sc.REFERENCES:
        for seed in seeds:
            keys = [_model_name("B7", seed), *(f"D{i}_{ref_name}" for i in (2, 3, 4))]
            hybrids[ref_name, seed] = (
                keys,
                sc.HybridCalibration.fit([clean[k] for k in keys], cal),
            )

    def combine(scores: dict) -> dict:
        for (ref_name, seed), (keys, calib) in hybrids.items():
            vals = (
                calib.apply([scores[k] for k in keys])
                if calib
                else {k: np.full_like(scores[keys[0]], np.nan) for k in sc.WEIGHTS}
            )
            scores.update({f"hybrid_{ref_name}_{k}_seed{seed}": v for k, v in vals.items()})
        return scores

    clean = combine(clean)
    limits = {k: sc.alarm_threshold(v, cal) for k, v in clean.items()}
    evaluation = {
        k: ev.holdout_score(v[:, exp], panel.days[exp], limits[k]) for k, v in clean.items()
    }
    comparison = {
        f"{ref_name}_components": [f"D{i}_{ref_name}" for i in (2, 3, 4)]
        for ref_name in sc.REFERENCES
    }
    for ref_name in sc.REFERENCES:
        for seed in seeds:
            keys = [
                *hybrids[ref_name, seed][0],
                *(f"hybrid_{ref_name}_{w}_seed{seed}" for w in sc.WEIGHTS),
            ]
            comparison[f"{ref_name}_seed{seed}"] = keys

    def paired_sets(left: dict, right: dict | None = None):
        for name, keys in comparison.items():
            joint = np.logical_and.reduce([np.isfinite(left[k][:, exp]) for k in keys])
            if right is not None:
                joint &= np.logical_and.reduce([np.isfinite(right[k][:, exp]) for k in keys])
            yield name, keys, joint

    _write_scores(folder, panel, exp, clean, limits)
    # Evidence is joined only after every model, scale, and threshold is fixed.
    if panel.provenance["data_source"] == "simulated_smoke":
        indicators = adjacency = None
    else:
        indicators = ev.read_evidence(indicator_path)
        adjacency = ev.read_evidence(adjacency_path, adjacency=True)
    evidence = {
        k: ev.evidence_metrics(v[:, exp], panel.fields, panel.dates[exp], indicators, adjacency)
        for k, v in clean.items()
    }
    challenges = folder / "challenges"
    challenges.mkdir(exist_ok=True)
    cases = {}
    missing = {}
    jobs = [(f, d) for f in ev.FAMILIES for d in ev.DOSES] + [("missing_20pct", None)]
    for family, dose in tqdm(jobs, desc=f"Validation {branch}/{protocol}", disable=run.quiet):
        key = f"{family}_{dose:g}" if dose is not None else family
        result_path = challenges / f"{key}.json"
        uplift_path = challenges / f"{key}_uplift.npz"
        if result_path.exists() and (dose is None or uplift_path.is_file()):
            result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            changed = None
            if dose is None:
                altered = ev.with_gaps(panel, split)
            else:
                altered, changed = ev.perturb(panel, split, family, dose)
            current = dec.decompose(
                panel.days,
                altered.branch(branch),
                split,
                method,
                protocol,
                baseline=comp,
                capture_grid=False,
            )
            challenged = combine(score(altered, current, natural=False))
            if changed is None:
                result = {
                    "removed_field_dates": int(
                        (
                            np.isfinite(raw).any(axis=-1)
                            & ~np.isfinite(altered.branch(branch)).any(axis=-1)
                        ).sum()
                    ),
                    "arms": {
                        k: {
                            **ev.correlation(v[:, exp], challenged[k][:, exp]),
                            "absolute_change": ev.describe(
                                np.abs(v[:, exp] - challenged[k][:, exp])
                            ),
                        }
                        for k, v in clean.items()
                    },
                }
            else:
                result = {
                    "family": family,
                    "dose_train_scale": dose,
                    "arms": {
                        k: ev.synthetic_metrics(
                            v[:, exp], challenged[k][:, exp], changed[:, exp], limits[k]
                        )
                        for k, v in clean.items()
                    },
                    "matched_D_and_hybrid": {
                        name: {
                            k: ev.synthetic_metrics(
                                np.where(joint, clean[k][:, exp], np.nan),
                                np.where(joint, challenged[k][:, exp], np.nan),
                                changed[:, exp],
                                limits[k],
                            )
                            for k in keys
                        }
                        for name, keys, joint in paired_sets(clean, challenged)
                    },
                }
                # Commit the row-level dose support before the completed metric JSON.
                npz_save(
                    uplift_path,
                    **{
                        k: ev.changed_uplift(v[:, exp], challenged[k][:, exp], changed[:, exp])
                        for k, v in clean.items()
                    },
                )
            json_save(result_path, result)
        log(event="challenge", family=family, dose=dose)
        if dose is None:
            missing = result
        else:
            cases[key] = result
    dose_response: dict[str, dict] = {k: {} for k in clean}
    for family in ev.FAMILIES:
        with ExitStack() as stack:
            by_dose = [
                stack.enter_context(np.load(challenges / f"{family}_{d:g}_uplift.npz"))
                for d in ev.DOSES
            ]
            for k in clean:
                dose_response[k][family] = ev.matched_dose_response(
                    np.asarray(ev.DOSES), [data[k] for data in by_dose]
                )
    report = {
        "provenance": run.provenance,
        "branch": branch,
        "protocol": protocol,
        "method": method,
        "ladder_rung_ceiling": "engineering_smoke_only"
        if panel.provenance["data_source"] == "simulated_smoke"
        else "L2_synthetic_only_no_stress_truth",
        "wall_seconds": time.perf_counter() - start,
        "models": model_report,
        "historical_holdout": evaluation,
        "calibration": {
            k: {"threshold": limits[k], **ev.holdout_score(v[:, cal], panel.days[cal], limits[k])}
            for k, v in clean.items()
        },
        "matched_D_and_hybrid_holdout": {
            name: {
                k: ev.holdout_score(
                    np.where(joint, clean[k][:, exp], np.nan), panel.days[exp], limits[k]
                )
                for k in keys
            }
            for name, keys, joint in paired_sets(clean)
        },
        "hybrid_scaling": {
            f"{r}_seed{s}": asdict(c) if c else None for (r, s), (_, c) in hybrids.items()
        },
        "hybrid_weights": sc.WEIGHTS,
        "synthetic_sensitivity": cases,
        "dose_response": dose_response,
        "missingness": missing,
        "validation_evidence": evidence,
        "indicator_caveat": "Agreement only: METRIC indicators may share optical inputs, acquisition and weather. "
        "No indicator, synthetic target, or final test data selected weights or thresholds.",
        "seed_summary": _seed_rollups(evaluation, cases, seeds),
        "multi_branch_gate": _gate(
            panel.provenance["data_source"], protocol, evaluation, cases, seeds
        ),
    }
    json_save(summary_file, report)
    log(event="case_complete", seconds=report["wall_seconds"])
    return report
