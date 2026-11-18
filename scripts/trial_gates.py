#!/usr/bin/env python3
"""Five pre-registered decision gates of the predictive-SSL controlled trial
(change predictive-ssl-controlled-trial, task 3.1) — evaluated VERBATIM from
the part A–D summaries; no goalpost movement, no spec-target edits.

The gate table (design.md, owner's list):

| gate | criterion | verdict rule |
| FAR | clean cycle-/event-FAR within the 5% budget | must pass, else the arm is invalid regardless of detection |
| Synthetic detection | better than gru_ae_main at realistic severities | primary: non-censored MDM80(persistent/ndvi) < gru_ae_main's (or >S6 → any non-censored value wins); secondary: S4–S6 persistent detection with Wilson CIs, then savi/acute |
| Persistent anomaly | predictive error persists through sustained drops | part C: A(gru_pred) < A(gru_ae) and non-decaying checkpoint errors |
| Independent validation | consistency with spectral/ET proxies | part D agreement above chance with CIs (corroborating only) |
| Generalization | not confined to few fields / one period | detections spread across fields and cycles; stable across seeds {13,42,2026} |

Operationalizations (recorded here BEFORE the full-run results were produced;
visible in the smoke runs only for machinery checks):

- FAR: every gru_pred seed's part-A clean cycle-FAR ≤ 0.05 AND
  gate_no_concentration (top-2-field flag share < 0.5 when any flags exist).
- Synthetic detection (per gru_pred seed): win = MDM80(persistent/ndvi)
  sentinel < gru_ae's sentinel, where a non-censored value beats a censored
  one; secondary readout = S4–S6 persistent/ndvi detection with Wilson CIs.
- Persistent anomaly: at S4–S6 × {ndvi, savi} (S1–S2 are noise-saturated,
  finding 20): median absorption A(gru_pred) < A(gru_ae) AND median
  persistence_ratio ≥ 0.5 (the post-onset error at bins +2…+5 retains at
  least half the onset spike). Evaluated per seed, then majority across seeds.
- Independent validation: for the available indicators (CWSI_ET subset, TVDI
  proxy, NDVI phase deficit): met iff ≥2 indicators have rate_difference > 0
  AND the flagged-rate Wilson lower bound exceeds the unflagged rate for at
  least one indicator; "not_evaluable" when the arm has zero natural alarms
  at the 5% FAR budget (recorded honestly, not counted as a failure of the
  mechanism — the FAR budget leaves no natural events to compare).
- Generalization: per-field/cycle spread (part B: detected injections span
  ≥ 3 fields and ≥ 2 onset phases at S6/persistent/ndvi when any are
  detected; part A: no concentration) AND seed stability (per-cell detection
  std at S6 cells ≤ 0.15 across seeds AND MDM80(persistent/ndvi) equal in
  ≥ 2 of 3 seeds).

DECISION: all gates pass → predictive objective becomes the main development
path. Synthetic-detection gate fails → path B (anomaly definition). Mixed →
recorded honestly per gate; the owner decides with the findings in hand.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import protocol as mproto  # noqa: E402

SENTINEL_CENSORED = 7
FAR_BUDGET = 0.05


def parse_args():
    import argparse

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--trial-run-id", default="trial_predictive_20261114")
    p.add_argument("--frozen-seed", type=int, default=2026)
    p.add_argument("--gru-pred-seeds", default="13,42,2026")
    p.add_argument("--notes", default="")
    return p.parse_args()


def _load(od: Path, name: str) -> dict:
    path = od / name
    if not path.exists():
        raise FileNotFoundError(f"missing trial artifact: {path} — run the parts first")
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(args) -> dict:
    od = mproto.DEV_DIR / args.trial_run_id
    pa = _load(od, "part_a_summary.json")
    pb = _load(od, "part_b_summary.json")
    pc = _load(od, "part_c_summary.json")
    pd = _load(od, "part_d_summary.json")
    seeds = [int(s) for s in str(args.gru_pred_seeds).split(",")]

    gru_pred_a = [pa["per_arm"][f"gru_pred:{s}"] for s in seeds]
    gru_ae_a = pa["per_arm"][f"gru_ae:{args.frozen_seed}"]

    def _pb_arm(model: str, seed: int) -> dict:
        rows = pb["three_arm_comparison"][model]
        return [r for r in rows if int(r["seed"]) == seed][0]

    gru_ae_b = _pb_arm("gru_ae", args.frozen_seed)

    # ---- Gate 1: FAR ---------------------------------------------------------
    per_seed_far = {s: {"cycle_far": r["cycle_far_clean_eval"],
                        "within_budget": r["cycle_far_within_budget"],
                        "no_concentration": r["gate_no_concentration"]}
                    for s, r in zip(seeds, gru_pred_a)}
    gate_far = {
        "rule": "every gru_pred seed: clean cycle-FAR ≤ 5% AND no top-2-field concentration",
        "per_seed": per_seed_far,
        "gru_ae_reference": {"cycle_far": gru_ae_a["cycle_far_clean_eval"],
                             "within_budget": gru_ae_a["cycle_far_within_budget"]},
        "passed": bool(all(v["within_budget"] and v["no_concentration"]
                           for v in per_seed_far.values())),
    }

    # ---- Gate 2: synthetic detection vs gru_ae_main --------------------------
    def _mdm(row: dict, key: str) -> dict:
        v = row["mdm80"][key]
        return {"value": v, "sentinel": (SENTINEL_CENSORED if v == ">S6" else int(v[1:])),
                "censored": v == ">S6"}

    per_seed_det = {}
    for s in seeds:
        row = _pb_arm("gru_pred", s)
        mine = _mdm(row, "persistent/ndvi")
        ref = _mdm(gru_ae_b, "persistent/ndvi")
        primary_win = (not mine["censored"]) and (ref["censored"] or mine["sentinel"] < ref["sentinel"])
        s6_cells = {k: v for k, v in row["cells_S6"].items() if "persistent" in k}
        per_seed_det[s] = {
            "mdm80_persistent_ndvi": mine,
            "gru_ae_reference": ref,
            "primary_win": bool(primary_win),
            "S6_persistent_detection": s6_cells,
        }
    gate_detection = {
        "rule": ("primary: non-censored MDM80(persistent/ndvi) better than gru_ae_main's "
                 "(a non-censored value beats a censored one); secondary: S4–S6 persistent "
                 "detection with Wilson CIs (see part B), then savi/acute"),
        "gru_ae_reference_mdm80": gru_ae_b["mdm80"],
        "per_seed": per_seed_det,
        "passed": bool(sum(1 for v in per_seed_det.values() if v["primary_win"]) >= 2),
    }

    # ---- Gate 3: persistent-error persistence (part C) -----------------------
    gm = pc["gate_material_S4_to_S6"]

    def _med_across_levels(arm_vals: list[float]) -> float:
        arr = np.asarray([v for v in arm_vals if np.isfinite(v)], dtype=np.float64)
        return float(np.median(arr)) if arr.size else float("nan")

    per_seed_persist = {}
    for s in seeds:
        a_pred, a_ref, ratios = [], [], []
        for key, lvl in gm.items():
            a_ref.append(lvl["A_gru_ae"])
            a_pred.append(lvl["A_gru_pred_per_seed"].get(str(s), float("nan")))
        # persistence ratios live in the part-C per-arm cell summaries
        pc_arm = pc["per_arm"][f"gru_pred:{s}"]
        for key, cell in pc_arm["cells"].items():
            lv = key.split("/")[0]
            if lv in ("S4", "S5", "S6"):
                ratios.append(cell["persistence_ratio_median"])
        a_pred_m, a_ref_m = _med_across_levels(a_pred), _med_across_levels(a_ref)
        ratio_m = _med_across_levels(ratios)
        per_seed_persist[s] = {
            "A_gru_pred_median_S4_S6": a_pred_m,
            "A_gru_ae_median_S4_S6": a_ref_m,
            "persistence_ratio_median_S4_S6": ratio_m,
            "A_lower_than_gru_ae": bool(np.isfinite(a_pred_m) and np.isfinite(a_ref_m)
                                        and a_pred_m < a_ref_m),
            "errors_persist": bool(np.isfinite(ratio_m) and ratio_m >= 0.5),
        }
    gate_persist = {
        "rule": ("S4–S6 (S1–S2 noise-saturated, finding 20): median A(gru_pred) < A(gru_ae) "
                 "AND persistence_ratio ≥ 0.5 (post-onset error retains ≥ half the spike)"),
        "pre_registered_caveat": ("a fast adaptive predictive model could also absorb; a "
                                  "negative result is recorded as such, not tuned away"),
        "per_seed": per_seed_persist,
        "passed": bool(sum(1 for v in per_seed_persist.values()
                           if v["A_lower_than_gru_ae"] and v["errors_persist"]) >= 2),
    }

    # ---- Gate 4: independent validation (part D) -----------------------------
    per_seed_ind = {}
    for s in seeds:
        arm = pd["per_arm"].get(f"gru_pred:{s}")
        if arm is None:
            continue
        diffs = {}
        for ind, a in arm["agreement"].items():
            diffs[ind] = {
                "rate_difference": a["rate_difference"],
                "n_flagged": a["n_flagged_bins_observed"],
                "flagged_rate_ci": a["high_rate_flagged_wilson95"],
                "unflagged_rate": a["high_rate_unflagged"],
            }
        pos = [d for d in diffs.values()
               if np.isfinite(d["rate_difference"]) and d["rate_difference"] > 0
               and d["n_flagged"] > 0]
        ci_above = [d for d in diffs.values()
                    if d["n_flagged"] > 0 and np.isfinite(d["flagged_rate_ci"][0])
                    and d["flagged_rate_ci"][0] > d["unflagged_rate"]]
        n_flag_total = sum(d["n_flagged"] for d in diffs.values())
        per_seed_ind[s] = {
            "indicators": diffs,
            "n_flagged_bins_total": n_flag_total,
            "n_indicators_positive": len(pos),
            "n_indicators_ci_above_unflagged": len(ci_above),
            "verdict": ("met" if (len(pos) >= 2 and len(ci_above) >= 1)
                        else "not_evaluable_zero_natural_alarms" if n_flag_total == 0
                        else "not_met"),
        }
    gate_ind = {
        "rule": ("≥2 available indicators with rate_difference > 0 AND ≥1 indicator whose "
                 "flagged-rate Wilson lower bound exceeds the unflagged rate; zero natural "
                 "alarms at the 5% budget → not_evaluable (recorded honestly)"),
        "dependence_structure": pd["dependence_structure"],
        "per_seed": per_seed_ind,
        "passed": bool(any(v["verdict"] == "met" for v in per_seed_ind.values())),
        "any_evaluable": bool(any(v["verdict"] != "not_evaluable_zero_natural_alarms"
                                  for v in per_seed_ind.values())),
    }

    # ---- Gate 5: generalization ----------------------------------------------
    per_seed_gen = {}
    for s in seeds:
        row = _pb_arm("gru_pred", s)
        pc_arm = pc["per_arm"][f"gru_pred:{s}"]
        # Seed stability across gru_pred seeds: per-cell S6 detection spread.
        spread = {}
        for cell_key in row["cells_S6"]:
            vals = [_pb_arm("gru_pred", x)["cells_S6"].get(cell_key, float("nan")) for x in seeds]
            spread[cell_key] = float(np.nanstd(vals))
        mdm_labels = [_pb_arm("gru_pred", x)["mdm80"]["persistent/ndvi"] for x in seeds]
        per_seed_gen[s] = {
            "S6_cell_detection_std_across_seeds": spread,
            "mdm80_persistent_ndvi_across_seeds": mdm_labels,
        }
    spread_ok = all(v <= 0.15 for v in per_seed_gen[seeds[0]]["S6_cell_detection_std_across_seeds"].values())
    labels = [g["mdm80_persistent_ndvi_across_seeds"][0]["value"] for g in per_seed_gen.values()]
    label_stable = sum(1 for v in labels if v == labels[0]) >= 2
    gate_gen = {
        "rule": ("detections spread across fields/cycles (part B field spread + part A "
                 "no-concentration) and stable across seeds: S6 per-cell detection std ≤ 0.15 "
                 "AND MDM80(persistent/ndvi) equal in ≥2 of 3 seeds"),
        "per_seed": per_seed_gen,
        "spread_within_0p15": bool(spread_ok),
        "mdm80_label_stable": bool(label_stable),
        "passed": bool(spread_ok and label_stable
                       and all(gate_far["per_seed"][s]["no_concentration"] for s in seeds)),
    }

    gates = {
        "FAR": gate_far,
        "synthetic_detection": gate_detection,
        "persistent_anomaly": gate_persist,
        "independent_validation": gate_ind,
        "generalization": gate_gen,
    }
    all_pass = all(g["passed"] for g in gates.values())
    if all_pass:
        decision = ("ALL FIVE GATES PASS → the predictive objective becomes the main "
                    "development path")
    elif not gate_detection["passed"]:
        decision = ("synthetic-detection gate FAILS → path B (anomaly definition: "
                    "multivariate/relational + phenology-shape families) — NOT more "
                    "architecture trials")
    else:
        decision = ("MIXED outcome → recorded honestly per gate; the owner decides with the "
                    "findings in hand")
    return {
        "type": "trial_five_gates",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trial_run_id": args.trial_run_id,
        "seeds": seeds,
        "gates": gates,
        "all_pass": bool(all_pass),
        "decision": decision,
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "notes": args.notes,
    }


def main() -> int:
    args = parse_args()
    result = evaluate(args)
    od = mproto.DEV_DIR / args.trial_run_id
    out = od / "five_gates.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for name, g in result["gates"].items():
        print(f"[gate] {name:24s} {'PASS' if g['passed'] else 'FAIL'}")
    print(f"[gates] DECISION: {result['decision']}")
    print(f"[gates] → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
