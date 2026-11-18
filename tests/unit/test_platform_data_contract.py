"""Platform data contract parity test (contract v5).

Verifies that the exported JSON payloads satisfy the channel registry contract:
every channel name in platform_channels.py matches channels.ts, every
observation carries the contract v3/v4 fields (per-score provenance + formula
ids) PLUS the v5 stress-flag fields (stressFlag / stressFlagModel / split per
observation, ladderRung per field), and ranges are valid. The v5 score
resolution (model or absent — no CWSI proxy) is exercised with synthetic
checkpoints in temporary directories, including the causal main checkpoint
format (``causal_monitor_v1`` .pt + JSON sidecar).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from platform_channels import (  # type: ignore
    CONTRACT_VERSION,
    CHANNEL_REGISTRY,
    SCORE_CHECKPOINTS,
    SCORE_NAMES,
    SCORE_REGISTRY,
    by_name,
)

DATA_DIR = ROOT / "platform" / "src" / "data"
FARMS_PATH = DATA_DIR / "farms_khuzestan.json"
SERIES_PATH = DATA_DIR / "series_khuzestan.json"

VALID_SPLITS = {"train", "dev", "test", "monitoring"}
VALID_FLAGS = {"normal", "suspected_stress", "no_data"}

# ── Contract v5 reader ────────────────────────────────────────────────────────
# The v4/v5 payload stores a shared axis + per-field arrays + RLE provenance;
# these helpers reconstruct the per-observation dicts so the semantic checks
# below stay written against observations. Mirrors the decoder in
# platform/src/data/data.ts exactly.


def _expand_rle(runs: list, n: int) -> list:
    out: list = []
    for state, count in runs:
        out.extend([state] * count)
    assert len(out) == n, f"RLE length {len(out)} != axis length {n}"
    return out


def load_series_obs_view() -> dict[str, list[dict]]:
    raw = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert raw["contractVersion"] == 5, f"expected contract v5 payload, got {raw.get('contractVersion')}"
    axis = raw["axis"]
    n = len(axis)
    checkpoints = raw["checkpoints"]
    score_formulas = raw["scoreFormulas"]
    out: dict[str, list[dict]] = {}
    for fid, f in raw["fields"].items():
        chan_prov = {c: _expand_rle(r, n) for c, r in f["channelProvenance"].items()}
        score_prov = {k: _expand_rle(r, n) for k, r in f["scoreProvenance"].items()}
        stress_flags = _expand_rle(f["stressFlag"], n)
        stress_models = _expand_rle(f["stressFlagModel"], n)
        splits = _expand_rle(f["split"], n)
        obs_list: list[dict] = []
        for i, date in enumerate(axis):
            missing = f["channels"]["ndvi"][i] is None
            obs_list.append({
                "date": date,
                "sampleDate": date,
                "idx": i,
                "acquisitionDate": date,
                "missing": missing,
                "stalenessReason": "invalid acquisition" if missing else None,
                **{c: f["channels"][c][i] for c in f["channels"]},
                "scores": {k: f["scores"][k][i] for k in f["scores"]},
                "scoreProvenance": {k: score_prov[k][i] for k in score_prov},
                "scoreFormulaId": {
                    k: (score_formulas.get(k, f"{checkpoints.get(k, k)}:bin_mse_1mexp")
                        if score_prov[k][i] == "model" else None)
                    for k in score_prov
                },
                "provenance": {c: chan_prov[c][i] for c in chan_prov},
                "scoreCollinearity": raw["collinearity"],
                "stressFlag": stress_flags[i],
                "stressFlagModel": stress_models[i],
                "split": splits[i],
            })
        out[fid] = obs_list
    return out


def _series() -> dict[str, list[dict]]:
    return load_series_obs_view()


def _farms() -> list[dict]:
    return json.loads(FARMS_PATH.read_text(encoding="utf-8"))



def test_farms_contract_version():
    farms = _farms()
    assert len(farms) == 490
    for f in farms:
        assert f["contractVersion"] == 5
        assert f["planted"] is None
        assert f["harvest"] is None


def test_contract_version_is_v5():
    assert CONTRACT_VERSION == 5


@pytest.mark.real_data
def test_series_has_contract_v3_fields():
    series = _series()
    obs = next(iter(series.values()))[0]
    expected = {
        "date", "sampleDate", "idx", "acquisitionDate", "missing",
        "stalenessReason", "ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi",
        "eta", "lst", "precip", "temp", "scores", "scoreProvenance",
        "scoreFormulaId", "provenance", "scoreCollinearity",
        # v5 additions
        "stressFlag", "stressFlagModel", "split",
    }
    assert expected.issubset(obs.keys()), f"missing: {expected - set(obs.keys())}"
    assert obs["scoreCollinearity"] == "cwsi"


@pytest.mark.real_data
def test_v5_payload_stress_fields():
    """v5 payload carries stressFlag / stressFlagModel / split + ladderRung."""
    raw = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert raw["contractVersion"] == 5
    axis_len = len(raw["axis"])
    for fid, f in raw["fields"].items():
        assert "ladderRung" in f, f"{fid} missing ladderRung"
        assert f["ladderRung"] is None or f["ladderRung"] in ("L1", "L2", "L3", "L4", "L5")
        for field_name, valid in (
            ("stressFlag", VALID_FLAGS | {None}),
            ("stressFlagModel", {None} | set(SCORE_CHECKPOINTS.values())),
            ("split", VALID_SPLITS),
        ):
            runs = f[field_name]
            total = sum(count for _, count in runs)
            assert total == axis_len, f"{fid}.{field_name}: RLE covers {total} != {axis_len}"
            for value, _count in runs:
                assert value in valid, f"{fid}.{field_name}: invalid value {value!r}"
    # Without a main checkpoint no flag is fabricated: null model -> null flag.
    main_ids = {"masked_transformer_main", "gru_ae_main"}
    for fid, f in raw["fields"].items():
        models = {v for v, _ in f["stressFlagModel"]}
        flags = {v for v, _ in f["stressFlag"]}
        if not (models & main_ids):
            assert flags == {None}, f"{fid}: flags {flags} without a main checkpoint"


@pytest.mark.real_data
def test_provenance_matches_registry():
    series = _series()
    obs = next(iter(series.values()))[0]
    prov = obs["provenance"]
    for ch in ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst", "precip", "temp"]:
        spec = by_name(ch)
        assert prov[ch] in ("observed", "modelled", "proxy", "absent", "legacy")


@pytest.mark.real_data
def test_channel_range_validation():
    series = _series()
    for fid, obs_list in series.items():
        for obs in obs_list:
            for ch in ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst"]:
                v = obs[ch]
                if v is not None:
                    lo, hi = by_name(ch).physical_range
                    assert lo <= v <= hi, f"{fid} {ch} {v} not in [{lo},{hi}]"
            if obs["precip"] is not None:
                lo, hi = by_name("precip").physical_range
                assert lo <= obs["precip"] <= hi
            if obs["temp"] is not None:
                lo, hi = by_name("temp").physical_range
                assert lo <= obs["temp"] <= hi


@pytest.mark.real_data
def test_staleness_guard():
    series = _series()
    obs_list = next(iter(series.values()))
    missing = [o for o in obs_list if o["missing"]]
    assert len(missing) > 0
    for o in missing:
        assert o["stalenessReason"] is not None


def test_neighbors_ranked():
    farms = _farms()
    for f in farms:
        assert len(f["neighbors"]) <= 4
        assert all(n != f["id"] for n in f["neighbors"])


def test_registry_parity_ts():
    """Python registry has 10 channels; check names match expected set."""
    names = [c.name for c in CHANNEL_REGISTRY]
    assert names == ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst", "precip", "temp"]
    assert len(names) == 10
    assert by_name("lst").required is False
    assert by_name("precip").provenance_default == "modelled"
    assert by_name("temp").provenance_default == "modelled"
    assert by_name("temp").physical_range == (0.0, 55.0)
    assert by_name("tvdi").derived_from == "cwsi"
    assert by_name("eta").derived_from == "ndvi"


def test_score_registry_parity():
    """Score registry (contract v5): masked_transformer/gru_ae model-backed, no proxy formula."""
    from load_model_checkpoints import score_formula_id

    assert SCORE_NAMES == (
        "b0_calendar", "b1_dsh", "b1_cusum", "masked_transformer", "gru_ae",
        "sts_net", "tiny_cnn_mamba", "time2agri",
    )
    assert SCORE_CHECKPOINTS == {
        "masked_transformer": "masked_transformer_main",
        "gru_ae": "gru_ae_main",
        "sts_net": "sts_net_490",
        "tiny_cnn_mamba": "tiny_cnn_mamba_490",
        "time2agri": "time2agri_490",
    }
    for spec in SCORE_REGISTRY:
        if spec.checkpoint is not None:
            assert spec.provenance_default == "model"
        else:
            # Baseline heuristic slots keep the "proxy" registry KIND but the
            # CWSI proxy formula is gone: they resolve "absent" in v5.
            assert spec.name in ("b0_calendar", "b1_dsh", "b1_cusum")
            assert spec.provenance_default == "proxy"
    # Formula ids: causal main checkpoints vs legacy literature checkpoints.
    assert score_formula_id("masked_transformer") == "masked_transformer_main:causal_bin_mse"
    assert score_formula_id("gru_ae") == "gru_ae_main:causal_bin_mse"
    assert score_formula_id("sts_net") == "sts_net_490:bin_mse_1mexp"
    assert score_formula_id("b0_calendar") is None


@pytest.mark.real_data
def test_exported_score_registry_matches_source():
    from load_model_checkpoints import score_formula_id

    # v5 payload self-description mirrors the registry
    raw = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert raw["checkpoints"] == SCORE_CHECKPOINTS
    assert raw["scoreFormulas"] == {k: v for k, v in (
        (s.name, score_formula_id(s.name)) for s in SCORE_REGISTRY) if v is not None}
    assert raw["axis"][0] == "2013-03-30" and raw["axis"][-1] == "2026-09-10"
    assert len(set(raw["axis"])) == len(raw["axis"])
    # The removed CWSI proxy formula must not appear anywhere in the payload.
    assert "cwsi_affine_v1" not in SERIES_PATH.read_text(encoding="utf-8")
    assert "proxyFormulaId" not in raw


@pytest.mark.real_data
def test_score_provenance_values_in_series():
    """Every observation restricts score provenance to model|absent (v5: no proxy)."""
    series = _series()
    for fid, obs_list in series.items():
        for obs in obs_list:
            prov = obs["scoreProvenance"]
            if prov is None:
                continue
            assert set(prov.keys()) == set(SCORE_NAMES), f"{fid} score provenance keys"
            for key, value in prov.items():
                assert value in ("model", "absent"), f"{fid} {key}: {value}"


@pytest.mark.real_data
def test_score_formula_ids_in_series():
    """Formula ids match provenance: model -> registered formula, absent -> None."""
    from load_model_checkpoints import score_formula_id

    series = _series()
    for fid, obs_list in series.items():
        for obs in obs_list:
            prov = obs.get("scoreProvenance")
            formula = obs.get("scoreFormulaId")
            if prov is None or formula is None:
                assert obs["scores"] is None, f"{fid} missing scoreProvenance with scores present"
                continue
            for key in SCORE_NAMES:
                st, fid_id = prov[key], formula[key]
                if st == "model":
                    assert obs["scores"][key] is not None, f"{fid} {key} model score missing"
                    assert fid_id == score_formula_id(key), f"{fid} {key}: {fid_id}"
                else:  # absent (v5 has no proxy state)
                    assert st == "absent"
                    assert obs["scores"][key] is None, f"{fid} {key} absent with score {obs['scores'][key]}"
                    assert fid_id is None, f"{fid} {key} absent with formula {fid_id}"


# ── wire-platform-to-real-data: real weather + real metadata + honest labels ──


@pytest.mark.real_data
def test_weather_channels_carry_real_values():
    """Task 2.1: precip/temp non-null fraction > 0 over dated observations (target ≥ 90%)."""
    series = _series()
    dated = [
        (o["precip"], o["temp"])
        for obs_list in series.values()
        for o in obs_list
        if o.get("acquisitionDate")
    ]
    n = len(dated)
    assert n > 0, "no dated observations to check weather against"
    precip_nn = sum(1 for p, _ in dated if p is not None)
    temp_nn = sum(1 for _, t in dated if t is not None)
    assert precip_nn / n > 0.9, f"precip non-null fraction {precip_nn / n:.3f} over {n} dated obs"
    assert temp_nn / n > 0.9, f"temp non-null fraction {temp_nn / n:.3f} over {n} dated obs"


@pytest.mark.real_data
def test_null_channel_is_never_labelled_modelled_or_measured():
    """Spec: a null value's provenance is absent/legacy — never modelled/measured —
    and a present value is never labelled absent."""
    series = _series()
    channels = ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst", "precip", "temp"]
    for fid, obs_list in series.items():
        for obs in obs_list:
            prov = obs["provenance"]
            for ch in channels:
                v, st = obs[ch], prov[ch]
                if v is None:
                    assert st in ("absent", "legacy"), f"{fid} {ch}: null labelled {st}"
                else:
                    assert st in ("observed", "modelled", "proxy"), f"{fid} {ch}: value {v} labelled {st}"


def test_no_synthesized_farm_strings():
    """Spec: zero matches for the previously synthesized patterns in the farms payload."""
    blob = FARMS_PATH.read_text(encoding="utf-8")
    for pattern in ("Khuzestan Unit", "Amir Kabir", "Debal Khazai"):
        assert pattern not in blob, f"synthesized pattern {pattern!r} still in farms payload"


def test_no_dead_stress_event_field():
    farms = _farms()
    assert all("stressEvent" not in f for f in farms), "stressEvent must not ship in the payload"


@pytest.mark.real_data
def test_farm_metadata_matches_registry():
    """Task 3.2: spot-parity of farm/municipality/variety against farms.parquet."""
    import pandas as pd

    farms = {f["code"]: f for f in json.loads(FARMS_PATH.read_text(encoding="utf-8"))}
    reg = pd.read_parquet(ROOT.parent / "Data" / "Processed" / "coordinates" / "farms.parquet")
    assert len(farms) == len(reg) == 490

    def clean(v) -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        s = str(v).strip()
        return "" if s.lower() in ("nan", "none") else s

    for _, r in reg.sample(30, random_state=20261107).iterrows():
        f = farms.get(str(r["farm"]))
        assert f is not None, f"registry farm {r['farm']} missing from payload"
        assert f["farm"] == clean(r["block"]), f"{f['code']} farm != registry block"
        expected_muni = " · ".join(x for x in (clean(r["office"]), clean(r["management"])) if x)
        assert f["municipality"] == expected_muni, f"{f['code']} municipality != registry office+management"
        variety = clean(r["variety"])
        if variety:
            assert f["variety"] == variety, f"{f['code']} variety != registry"
        else:
            assert f["variety"] is None, f"{f['code']} variety should be null (registry empty)"
        assert f["areaHa"] is not None and abs(f["areaHa"] - float(r["area_ha"])) < 0.05, f"{f['code']} area != registry"


# ── synthetic checkpoints (legacy + causal main format) ───────────────────────


def _synthetic_checkpoint(tmp_path: Path, model_id: str = "sts_net") -> Path:
    """Write a tiny valid <model_id>_490.pt checkpoint (random-init weights)."""
    import torch

    sys.path.insert(0, str(ROOT / "src"))
    from load_model_checkpoints import _build_model

    n_bands, n_bins = 2, 6
    shape = (n_bins, n_bands)
    model = _build_model(model_id, n_bands, shape)
    ckpt = {
        "architecture": model_id,
        "state_dict": model.state_dict(),
        "center": np.zeros(n_bands, dtype=np.float64),
        "scale": np.ones(n_bands, dtype=np.float64),
        "shape": shape,
        "n_bands": n_bands,
        "parameter_count": sum(p.numel() for p in model.parameters()),
    }
    path = tmp_path / f"{model_id}_490.pt"
    torch.save(ckpt, path)
    return path


def _synthetic_main_checkpoint(
    tmp_path: Path,
    stem: str = "masked_transformer_main",
    family: str = "masked_transformer",
    tau: float = 0.5,
    k: int = 1,
) -> Path:
    """Write a tiny causal main checkpoint (causal_monitor_v1 .pt + JSON sidecar).

    Same save format as scripts/train_main.py / freeze_main_model.py: the .pt
    carries {"format", "model_id", "state_dict", "config", ...} and the sidecar
    the normalization (36x8 median/scale), threshold, persistence k and ladder
    rung. Random-init weights — the test exercises the LOADING + scoring path,
    not learned behaviour.
    """
    import torch

    sys.path.insert(0, str(ROOT / "src"))
    from ssl_anomaly.monitor.models import DEFAULT_CONFIGS, build_model, count_parameters

    n_bins, n_channels = 36, 8
    cfg = dict(DEFAULT_CONFIGS[family])
    d_in = n_channels * 2 + 2  # values + mask flags + sin/cos DOY (use_doy)
    torch_model = build_model(family, d_in=d_in, n_out=n_channels, cfg=cfg)
    ckpt = {
        "format": "causal_monitor_v1",
        "model_id": family,
        "state_dict": torch_model.state_dict(),
        "config": {"d_in": d_in, "n_out": n_channels, "use_doy": True, **cfg},
        "seed": 42,
        "mask_ratio": 0.4,
        "epoch": 1,
        "best_dev_loss": 0.5,
    }
    pt_path = tmp_path / f"{stem}.pt"
    torch.save(ckpt, pt_path)

    band_order = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
    sidecar = {
        "model_id": stem,
        "family": family,
        "formula_id": f"{stem}:causal_bin_mse",
        "band_order": band_order,
        "n_bins": n_bins,
        "bin_days": 15,
        "architecture_config": cfg,
        "parameter_count": count_parameters(torch_model),
        "use_doy_channels": True,
        "normalization": {
            "median": np.zeros((n_bins, n_channels), dtype=np.float64).tolist(),
            "scale": np.ones((n_bins, n_channels), dtype=np.float64).tolist(),
            "robust_range": np.ones(n_channels, dtype=np.float64).tolist(),
            "norm_stats_file": "reports/dev/synthetic/norm_stats.npz",
            "computed_from": "train split only",
        },
        "threshold": {
            "tau": tau, "k": k, "far_target": 0.05,
            "far_achieved": 0.04, "calibration_n_cycles": 10,
        },
        "persistence_k": k,
        "ladder_rung": "L2",
        "splits_locked_sha256": "0" * 64,
        "seeds": [42],
        "frozen_seed": 42,
        "dev_metrics_summary": {},
        "training_run_id": "synthetic",
    }
    (tmp_path / f"{stem}.json").write_text(json.dumps(sidecar), encoding="utf-8")
    return pt_path


def _masked_cycle_rows(n_rows: int = 2) -> list:
    """Masked cycle tensors covering day numbers 100..459 (harvest day 100)."""
    from cycle_inputs import MaskedCycleTensor

    rng = np.random.default_rng(42)
    rows = []
    for r in range(n_rows):
        x = rng.uniform(0.0, 0.5, size=(36, 8)).astype(np.float32)
        m = np.ones((36, 8), dtype=bool)
        x[20:, :] = np.nan  # unobserved tail bins
        m[20:, :] = False
        rows.append(MaskedCycleTensor(
            field_id=r + 1, t_start=100, t_end=460, harvest_day=100,
            censored=False, cycle_ordinal=r, x=x, mask=m,
        ))
    return rows


def test_resolve_scores_v5_causal_with_synthetic_main_checkpoint(tmp_path):
    """A causal main checkpoint present -> masked_transformer slot resolves 'model'
    with the causal formula id; missing slots (gru_ae, baselines) stay absent."""
    from cycle_inputs import resolve_observation_scores_v5, resolve_stress_flag
    from load_model_checkpoints import load_model_checkpoints, squash_bin_error

    _synthetic_main_checkpoint(tmp_path)
    models, status = load_model_checkpoints(tmp_path)
    assert status["masked_transformer"] == "loaded"
    assert status["gru_ae"] == "missing"
    loaded = models["masked_transformer"]
    assert loaded is not None

    rows = _masked_cycle_rows()
    X = np.stack([c.x for c in rows])
    M = np.stack([c.mask for c in rows])
    H = np.array([c.harvest_day for c in rows], dtype=np.int64)
    raw = loaded.score_cycles(X, M, H)
    assert raw.shape == (2, 36)
    assert np.isnan(raw[:, 20:]).all(), "unobserved bins must score NaN"
    assert np.isfinite(raw[:, :20]).all()

    scores, prov, formula = resolve_observation_scores_v5(
        150, rows, [], new_raw_errs={"masked_transformer": raw}, legacy_squashed_errs={},
    )
    assert prov["masked_transformer"] == "model"
    assert formula["masked_transformer"] == "masked_transformer_main:causal_bin_mse"
    expected = round(float(squash_bin_error(raw[0, (150 - 100) // 15])), 3)
    assert scores["masked_transformer"] == expected
    # Unmapped SSL slots and baselines are absent (no proxy fallback in v5).
    for key in ("gru_ae", "b0_calendar", "b1_dsh", "b1_cusum", "sts_net"):
        assert prov[key] == "absent", f"{key}: {prov[key]}"
        assert scores[key] is None
        assert formula[key] is None

    # Stress flag from the sidecar threshold (tau=0.5, k=1): a valid enum value.
    hit_bin = (150 - 100) // 15
    flag = resolve_stress_flag(raw[0, : hit_bin + 1], 0.5, 1, bool(np.isfinite(raw[0, hit_bin])))
    assert flag in ("normal", "suspected_stress", "no_data")


def test_resolve_scores_v5_legacy_checkpoint(tmp_path):
    """A legacy checkpoint present -> its slot resolves 'model' with the legacy
    formula; masked_transformer / baselines stay absent."""
    from cycle_inputs import CycleTensor, resolve_observation_scores_v5
    from load_model_checkpoints import load_model_checkpoints, squash_bin_error

    _synthetic_checkpoint(tmp_path, "sts_net")
    models, status = load_model_checkpoints(tmp_path)
    assert status["sts_net"] == "loaded"
    assert status["masked_transformer"] == "missing"
    loaded = models["sts_net"]
    assert loaded is not None

    X = np.linspace(0.0, 0.5, 2 * 6 * 2, dtype=np.float32).reshape(2, 6, 2)
    err = loaded.score_cycles(X)
    assert err.shape == (2, 6)
    assert np.isfinite(err).all()

    cycles = [CycleTensor(field_id=1, t_start=100, t_end=400, harvest_day=100,
                          x=np.full((6, 3), np.nan, dtype=np.float32))]
    scores, prov, formula = resolve_observation_scores_v5(
        150, [], cycles, new_raw_errs={}, legacy_squashed_errs={"sts_net": squash_bin_error(err)},
    )
    assert prov["sts_net"] == "model"
    assert formula["sts_net"] == "sts_net_490:bin_mse_1mexp"
    assert scores["sts_net"] == round(float(1.0 - np.exp(-err[0, (150 - 100) // 15])), 3)
    # v5: masked_transformer and the baselines never fall back to the proxy rule.
    assert prov["masked_transformer"] == "absent"
    assert prov["b0_calendar"] == "absent"
    assert scores["b0_calendar"] is None


def test_resolve_scores_v5_absent_without_models():
    """No checkpoints at all -> EVERY slot is null + 'absent' (no proxy, no crash)."""
    from cycle_inputs import CycleTensor, resolve_observation_scores_v5

    cycles = [CycleTensor(field_id=1, t_start=100, t_end=400, harvest_day=100,
                          x=np.full((6, 3), np.nan, dtype=np.float32))]
    scores, prov, formula = resolve_observation_scores_v5(
        150, [], cycles, new_raw_errs={}, legacy_squashed_errs={},
    )
    for key in SCORE_NAMES:
        assert prov[key] == "absent", f"{key}: {prov[key]}"
        assert scores[key] is None
        assert formula[key] is None


def test_build_field_cycles_masked_keeps_gaps_uninterpolated(rng):
    """The masked builder keeps unobserved bin/band cells NaN + mask False —
    interior gaps are NOT interpolated (unlike the legacy builder), matching
    monitor.inputs.rebuild_masked_cycles semantics."""
    from cycle_inputs import build_field_cycles_masked

    # Sugarcane-like trapezoid (same fixture pattern as test_cycles.py) sampled
    # at exactly the 15-day bin cadence -> ~1 observation per phase bin.
    def trapezoid(length):
        y = np.full(length, 0.2)
        p1, p2 = length // 4, (3 * length) // 4
        y[:p1] = np.linspace(0.2, 0.85, p1)
        y[p1:p2] = 0.85
        y[p2:] = np.linspace(0.85, 0.2, length - p2)
        return np.clip(y + rng.normal(0, 0.005, size=length), 0.0, 1.0)

    daily_ndvi = np.concatenate([trapezoid(360), trapezoid(360)])
    times = np.arange(0, daily_ndvi.size, 15, dtype=np.int64)
    ndvi = daily_ndvi[times]
    cube = np.stack([np.full(times.size, 0.3), np.full(times.size, 0.4)], axis=-1)
    band_index = {"blue": 0, "green": 1}

    cycles = build_field_cycles_masked(7, times, ndvi, np.ones(times.size), cube, band_index,
                                       include_censored=True)
    assert cycles, "no cycles segmented from the synthetic trapezoid series"
    mid = next((c for c in cycles if not c.censored), cycles[len(cycles) // 2])

    # Pick an interior observation of this cycle that maps to a valid bin and
    # blank its blue-band value: that bin/band must stay NaN + mask False.
    obs_idx = [i for i, t in enumerate(times)
               if mid.t_start <= t < mid.t_end and 0 <= t - mid.harvest_day < 36 * 15]
    assert len(obs_idx) >= 10
    k = obs_idx[len(obs_idx) // 2]
    cube_gap = cube.copy()
    cube_gap[k, band_index["blue"]] = np.nan

    built = build_field_cycles_masked(7, times, ndvi, np.ones(times.size), cube_gap, band_index,
                                      include_censored=True)
    target = next(c for c in built if (c.t_start, c.t_end) == (mid.t_start, mid.t_end))
    b = (int(times[k]) - target.harvest_day) // 15
    assert 0 <= b < 36
    blue_ch = 1 + band_index["blue"]
    assert not target.mask[b, blue_ch], "gap bin/band must be mask-False (no interpolation)"
    assert np.isnan(target.x[b, blue_ch]), "gap bin/band must stay NaN (no interpolation)"
    # The NDVI channel of the SAME bin stays observed; neighbouring blue bins
    # keep their own values instead of receiving interpolated fill.
    assert bool(target.mask[b, 0])
    assert np.isfinite(target.x[b, 0])
    neighbours = [bb for bb in (b - 1, b + 1) if 0 <= bb < 36 and target.mask[bb, blue_ch]]
    assert neighbours, "expected at least one observed neighbouring blue bin"
    for bb in neighbours:
        expected = 0.3  # every blue observation is the constant 0.3
        assert target.x[bb, blue_ch] == expected, "neighbouring bins must not absorb the gap"


def test_lookup_masked_cycle_bin():
    from cycle_inputs import lookup_masked_cycle_bin

    rows = _masked_cycle_rows(1)
    hit = lookup_masked_cycle_bin(rows, 150)
    assert hit == (0, (150 - 100) // 15)
    assert lookup_masked_cycle_bin(rows, 99) is None  # before the cycle span
    assert lookup_masked_cycle_bin(rows, 460) is None  # after the cycle span
    # Beyond the 540-day bin range inside a long span -> None.
    long_row = rows[0]
    hit = lookup_masked_cycle_bin([long_row], 100 + 36 * 15)
    assert hit is None


def test_resolve_stress_flag_alarm_semantics():
    """k-bin run ending at the current bin, causal (prefix only), honest no_data."""
    from cycle_inputs import resolve_stress_flag

    # k=1: above tau -> suspected, below -> normal.
    assert resolve_stress_flag(np.array([0.9]), 0.5, 1, True) == "suspected_stress"
    assert resolve_stress_flag(np.array([0.1]), 0.5, 1, True) == "normal"
    # k=2: the run ENDING here must be entirely above tau.
    assert resolve_stress_flag(np.array([0.1, 0.9, 0.9]), 0.5, 2, True) == "suspected_stress"
    assert resolve_stress_flag(np.array([0.9, 0.9, 0.1]), 0.5, 2, True) == "normal"
    assert resolve_stress_flag(np.array([0.9]), 0.5, 2, True) == "normal"  # run incomplete
    # A NaN (unobserved) bin breaks the run.
    assert resolve_stress_flag(np.array([0.9, np.nan, 0.9]), 0.5, 2, True) == "normal"
    # Unobserved current bin -> no_data (never fabricated).
    assert resolve_stress_flag(np.array([0.9]), 0.5, 1, False) == "no_data"
    assert resolve_stress_flag(np.array([]), 0.5, 1, True) == "no_data"
    # Causality: the status for bin b depends only on bins <= b — the value
    # computed from the prefix is unchanged when future bins arrive (the
    # function never sees them; only the prefix is passed).
    prefix = np.array([0.9, 0.9])
    assert resolve_stress_flag(prefix, 0.5, 2, True) == "suspected_stress"
    extended = np.concatenate([prefix, [0.1]])
    assert resolve_stress_flag(extended[: len(prefix)], 0.5, 2, True) == "suspected_stress"


@pytest.mark.real_data
def test_build_cycle_split_map():
    """Split tagging reads the locked manifest; unmapped cycles count as monitoring."""
    from cycle_inputs import build_cycle_split_map, cycle_split_tag

    split_map = build_cycle_split_map(ROOT)
    assert split_map, "split map empty — data/processed files missing?"
    assert set(split_map.values()) <= VALID_SPLITS
    manifest = json.loads((ROOT / "data/processed/splits_locked.json").read_text(encoding="utf-8"))
    assert sum(1 for v in split_map.values() if v == "train") == len(manifest["cycles"]["train"])
    assert sum(1 for v in split_map.values() if v == "test") == len(manifest["cycles"]["test"])
    assert sum(1 for v in split_map.values() if v == "monitoring") == len(manifest["cycles"]["monitoring_only"])
    # Unmapped (field, t_start, t_end) -> monitoring, never an in-sample claim.
    from cycle_inputs import MaskedCycleTensor

    c = MaskedCycleTensor(
        field_id=999999, t_start=1, t_end=2, harvest_day=1,
        censored=True, cycle_ordinal=0,
        x=np.zeros((36, 8), dtype=np.float32), mask=np.zeros((36, 8), dtype=bool),
    )
    assert cycle_split_tag(c, split_map) == "monitoring"


# ── Anomaly desk payload contract (add-halqeh-anomaly-desk) ──────────────────
# The desk payload must be a complete, honest replay of the frozen
# stage-conditioned run: every case (no curation), values from the parquet,
# totals recomputed (naive counts computed, never quoted), envelopes +
# provenance from summary.json, registry identity equal to the farms payload.

DESK_PATH = DATA_DIR / "desk_khuzestan.json"
STAGE_PARQUET_PATH = ROOT / "reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet"
STAGE_SUMMARY_PATH = ROOT / "reports/stage_conditioned_anomaly/summary.json"
DESK_STAGE_SHORT = {
    "S1_establishment_growth": "S1",
    "S2_vegetative_reproductive": "S2",
    "S3_maturity_senescence": "S3",
    "S4_harvest_dormancy": "S4",
}
DESK_NAIVE_CUT = 0.40


def _desk() -> dict:
    return json.loads(DESK_PATH.read_text(encoding="utf-8"))


def _stage_rows() -> pd.DataFrame:
    return pd.read_parquet(STAGE_PARQUET_PATH)


def test_desk_payload_exists_and_is_nan_free():
    raw = DESK_PATH.read_text(encoding="utf-8")
    for token in ("NaN", "Infinity", "-Infinity"):
        assert token not in raw, f"desk payload contains literal {token}"
    desk = _desk()
    assert desk["contractVersion"] == 1
    assert set(desk) >= {"totals", "envelopes", "stageRows", "cases", "places", "provenance"}


def test_desk_complete_replay_no_curation():
    """One case per (field, cycle); every parquet bin appears exactly once, in order."""
    desk = _desk()
    df = _stage_rows()
    cases = {c["id"]: c for c in desk["cases"]}
    parquet_ids = {f"{int(f)}-{int(c)}" for f, c in df.groupby(["field", "cycle_id"]).groups}
    assert len(desk["cases"]) == len(parquet_ids) == 799
    assert set(cases) == parquet_ids
    seen_bins: set[tuple] = set()
    for case in desk["cases"]:
        bin_ids = [b["i"] for b in case["bins"]]
        assert bin_ids == sorted(bin_ids), f"{case['id']}: bins not in bin order"
        for b in case["bins"]:
            key = (case["field"], case["cycle"], b["i"])
            assert key not in seen_bins, f"bin {key} appears twice in the payload"
            seen_bins.add(key)
    parquet_bins = set(zip(df["field"].astype(int), df["cycle_id"].astype(int), df["bin_index"].astype(int)))
    assert seen_bins == parquet_bins, "payload bins ≠ parquet bins (dropped or invented rows)"
    assert len(seen_bins) == len(df) == 17143


def test_desk_bin_values_match_parquet():
    desk = _desk()
    df = _stage_rows()
    lookup = {
        (int(r.field), int(r.cycle_id), int(r.bin_index)): r
        for r in df.itertuples()
    }
    for case in desk["cases"]:
        for b in case["bins"]:
            row = lookup[(case["field"], case["cycle"], b["i"])]
            assert b["stage"] == DESK_STAGE_SHORT[row.stage]
            for key, expected in (
                ("p", round(float(row.progress), 4)),
                ("v", round(float(row.ndvi), 4)),
                ("lo", round(float(row.envelope_lower), 4)),
                ("hi", round(float(row.envelope_upper), 4)),
                ("med", round(float(row.envelope_median), 4)),
                ("d", str(row.bin_date)),
                ("f", bool(row.is_anomaly)),
            ):
                assert b[key] == expected, f"{case['id']} bin {b['i']} {key}: {b[key]} != {expected}"


def test_desk_totals_recompute_from_parquet():
    desk = _desk()
    df = _stage_rows()
    summary = json.loads(STAGE_SUMMARY_PATH.read_text(encoding="utf-8"))
    totals = desk["totals"]
    flags = int(df["is_anomaly"].sum())
    naive = int((df["ndvi"] < DESK_NAIVE_CUT).sum())
    overlap = int(((df["ndvi"] < DESK_NAIVE_CUT) & df["is_anomaly"].astype(bool)).sum())
    assert totals["rows"] == len(df) == 17143
    assert totals["flags"] == flags == 1774
    assert totals["cycles"] == df.groupby(["field", "cycle_id"]).ngroups == 799
    assert totals["fieldsInRun"] == df["field"].nunique() == 370
    assert totals["fieldsInRegistry"] == len(_farms()) == 490
    assert totals["validObsReported"] == summary["n_valid_obs"] == 18505
    # The published rate is the run's own denominator (valid obs), carried from
    # summary.json — the replay rate over stage-assigned rows is different by
    # construction and must NOT silently replace it.
    assert totals["flagRate"] == summary["flag_rate"]
    # Naive-cut counts are computed from the parquet, not quoted.
    assert totals["overlap"] == overlap
    assert totals["naiveOnly"] == naive - overlap
    assert totals["envelopeOnly"] == flags - overlap
    assert totals["naiveCut"] == DESK_NAIVE_CUT
    assert totals["binDays"] == summary["bin_days"] == 15
    assert totals["envelopeK"] == summary["envelope_k"] == 2.0


def test_desk_envelopes_match_summary():
    desk = _desk()
    summary = json.loads(STAGE_SUMMARY_PATH.read_text(encoding="utf-8"))
    for long_id, short_id in DESK_STAGE_SHORT.items():
        s_env = summary["stage_envelopes"][long_id]
        p_env = desk["envelopes"][short_id]
        assert p_env["n"] == s_env["n"]
        for p_key, s_key in (("median", "median"), ("mad", "mad"), ("lo", "lower"), ("hi", "upper")):
            assert abs(p_env[p_key] - float(s_env[s_key])) <= 1e-4, f"{short_id}.{p_key}"


def test_desk_stage_rows_match_parquet():
    desk = _desk()
    df = _stage_rows()
    for row in desk["stageRows"]:
        g = df[df["stage"] == [k for k, v in DESK_STAGE_SHORT.items() if v == row["s"]][0]]
        assert row["n"] == len(g)
        assert row["flags"] == int(g["is_anomaly"].sum())
        assert row["naive"] == int((g["ndvi"] < DESK_NAIVE_CUT).sum())
    assert sum(r["n"] for r in desk["stageRows"]) == len(df)


def test_desk_case_derived_fields_match_bins():
    desk = _desk()
    df = _stage_rows()
    cycle_meta = {
        (int(f), int(c)): (int(g["cycle_length_days"].iloc[0]), bool(g["censored"].iloc[0]))
        for (f, c), g in df.groupby(["field", "cycle_id"])
    }
    for case in desk["cases"]:
        bins = case["bins"]
        assert case["start"] == bins[0]["d"] and case["end"] == bins[-1]["d"]
        length, censored = cycle_meta[(case["field"], case["cycle"])]
        assert case["lengthDays"] == length
        assert case["censored"] == censored
        assert case["flags"] == sum(1 for b in bins if b["f"])
        assert case["naive"] == sum(1 for b in bins if b["v"] < DESK_NAIVE_CUT)
        assert case["kind"] == ("slip" if case["flags"] else "spared")
        if case["flags"]:
            deepest = round(max(b["lo"] - b["v"] for b in bins if b["f"]), 3)
            assert case["deepest"] == deepest
        else:
            assert case["deepest"] == 0.0
        s2 = [b["v"] for b in bins if b["stage"] == "S2"]
        s3 = [b["v"] for b in bins if b["stage"] == "S3"]
        assert case["s2max"] == (round(max(s2), 3) if s2 else None)
        assert case["s3min"] == (round(min(s3), 3) if s3 else None)


def test_desk_case_metadata_matches_farms_payload():
    """Registry identity equals the farms payload row, or is null — never invented."""
    desk = _desk()
    farms = {f["id"]: f for f in _farms()}
    for case in desk["cases"]:
        farm = farms[case["fieldId"]]
        assert case["code"] == (farm["code"] or None)
        assert case["name"] == (farm["name"] or None)
        assert case["farm"] == (farm["farm"] or None)
        assert case["municipality"] == (farm["municipality"] or None)
        assert case["variety"] == farm["variety"]
        assert case["areaHa"] == farm["areaHa"]
        assert case["lat"] == farm["centroid"][0] and case["lng"] == farm["centroid"][1]


def test_desk_provenance_matches_summary():
    desk = _desk()
    summary = json.loads(STAGE_SUMMARY_PATH.read_text(encoding="utf-8"))
    prov = desk["provenance"]
    assert prov["gitSha"] == summary["git_sha"]
    assert prov["generatedAt"] == summary["generated_at"]
    assert prov["dataSource"] == summary["data_source"]
    assert prov["seed"] == summary["seed"]
    assert prov["binDays"] == summary["bin_days"]
    assert prov["envelopeK"] == summary["envelope_k"]
    assert prov["naiveCut"] == DESK_NAIVE_CUT
    assert desk["generated"] == str(summary["generated_at"])[:10]
    # Source paths point at the tracked run artifacts.
    assert (ROOT / prov["parquet"]).exists()
    assert (ROOT / prov["summary"]).exists()
    assert prov["parquet"].endswith("stage_conditioned_anomaly.parquet")


def test_desk_places_match_farms_payload():
    desk = _desk()
    farms = _farms()
    places = {p["n"]: p for p in desk["places"]}
    assert len(places) == len(farms) == 490
    assert set(places) == set(range(1, 491))
    for f in farms:
        p = places[int(f["id"][2:])]
        assert p["lat"] == f["centroid"][0] and p["lng"] == f["centroid"][1]
