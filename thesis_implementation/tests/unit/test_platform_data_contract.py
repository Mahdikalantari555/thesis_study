"""Platform data contract parity test.

Verifies that the exported JSON payloads satisfy the channel registry contract:
every channel channel name in platform_channels.py matches channels.ts,
every observation carries the contract v3 fields (per-score provenance +
formula ids), and ranges are valid.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from platform_channels import (  # type: ignore
    CONTRACT_VERSION,
    PROXY_SCORE_FORMULA_ID,
    CHANNEL_REGISTRY,
    SCORE_CHECKPOINTS,
    SCORE_NAMES,
    SCORE_REGISTRY,
    by_name,
)

DATA_DIR = ROOT / "platform" / "src" / "data"
FARMS_PATH = DATA_DIR / "farms_khuzestan.json"
SERIES_PATH = DATA_DIR / "series_khuzestan.json"

# ── Contract v4 reader ────────────────────────────────────────────────────────
# The v4 payload stores a shared axis + per-field arrays + RLE provenance;
# these helpers reconstruct the v3-shaped per-observation dicts so the semantic
# checks below stay written against observations. Mirrors the decoder in
# platform/src/data/data.ts exactly.


def _expand_rle(runs: list, n: int) -> list:
    out: list = []
    for state, count in runs:
        out.extend([state] * count)
    assert len(out) == n, f"RLE length {len(out)} != axis length {n}"
    return out


def load_series_v3view() -> dict[str, list[dict]]:
    raw = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert raw["contractVersion"] == 4, f"expected contract v4 payload, got {raw.get('contractVersion')}"
    axis = raw["axis"]
    n = len(axis)
    checkpoints = raw["checkpoints"]
    proxy_id = raw["proxyFormulaId"]
    out: dict[str, list[dict]] = {}
    for fid, f in raw["fields"].items():
        chan_prov = {c: _expand_rle(r, n) for c, r in f["channelProvenance"].items()}
        score_prov = {k: _expand_rle(r, n) for k, r in f["scoreProvenance"].items()}
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
                    k: (f"{checkpoints.get(k, k)}:bin_mse_1mexp" if score_prov[k][i] == "model"
                        else proxy_id if score_prov[k][i] == "proxy" else None)
                    for k in score_prov
                },
                "provenance": {c: chan_prov[c][i] for c in chan_prov},
                "scoreCollinearity": raw["collinearity"],
            })
        out[fid] = obs_list
    return out


def _series() -> dict[str, list[dict]]:
    return load_series_v3view()


def _farms() -> list[dict]:
    return json.loads(FARMS_PATH.read_text(encoding="utf-8"))



def test_farms_contract_version():
    farms = _farms()
    assert len(farms) == 490
    for f in farms:
        assert f["contractVersion"] == 4
        assert f["planted"] is None
        assert f["harvest"] is None


def test_contract_version_is_v4():
    assert CONTRACT_VERSION == 4


def test_series_has_contract_v3_fields():
    series = _series()
    obs = next(iter(series.values()))[0]
    expected = {
        "date", "sampleDate", "idx", "acquisitionDate", "missing",
        "stalenessReason", "ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi",
        "eta", "lst", "precip", "temp", "scores", "scoreProvenance",
        "scoreFormulaId", "provenance", "scoreCollinearity",
    }
    assert expected.issubset(obs.keys()), f"missing: {expected - set(obs.keys())}"
    assert obs["scoreCollinearity"] == "cwsi"


def test_provenance_matches_registry():
    series = _series()
    obs = next(iter(series.values()))[0]
    prov = obs["provenance"]
    for ch in ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst", "precip", "temp"]:
        spec = by_name(ch)
        assert prov[ch] in ("observed", "modelled", "proxy", "absent", "legacy")


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
    assert by_name("tvdi").derived_from == "cwsi"
    assert by_name("eta").derived_from == "ndvi"


def test_score_registry_parity():
    """Score registry (contract v3) mirrors the platform MODELS ids and checkpoints."""
    assert SCORE_NAMES == (
        "b0_calendar", "b1_dsh", "b1_cusum", "masked_transformer",
        "sts_net", "tiny_cnn_mamba", "time2agri",
    )
    assert SCORE_CHECKPOINTS == {
        "sts_net": "sts_net_490",
        "tiny_cnn_mamba": "tiny_cnn_mamba_490",
        "time2agri": "time2agri_490",
    }
    for spec in SCORE_REGISTRY:
        if spec.checkpoint is not None:
            assert spec.provenance_default == "model"
        else:
            assert spec.provenance_default == "proxy"
    # v4 payload self-description mirrors the registry
    raw = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert raw["checkpoints"] == SCORE_CHECKPOINTS
    assert raw["axis"][0] == "2013-03-30" and raw["axis"][-1] == "2026-09-10"
    assert len(set(raw["axis"])) == len(raw["axis"])


def test_score_provenance_values_in_series():
    """Every observation restricts score provenance to model|proxy|absent."""
    series = _series()
    for fid, obs_list in series.items():
        for obs in obs_list:
            prov = obs["scoreProvenance"]
            if prov is None:
                continue
            assert set(prov.keys()) == set(SCORE_NAMES), f"{fid} score provenance keys"
            for key, value in prov.items():
                assert value in ("model", "proxy", "absent"), f"{fid} {key}: {value}"


def test_score_formula_ids_in_series():
    """Formula ids match provenance: model -> checkpoint id, proxy -> cwsi_affine_v1, absent -> None."""
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
                    assert fid_id == f"{key}_490:bin_mse_1mexp", f"{fid} {key}: {fid_id}"
                elif st == "proxy":
                    assert obs["scores"][key] is not None, f"{fid} {key} proxy score missing"
                    assert fid_id == PROXY_SCORE_FORMULA_ID, f"{fid} {key}: {fid_id}"
                else:  # absent
                    assert st == "absent"
                    assert obs["scores"][key] is None, f"{fid} {key} absent with score {obs['scores'][key]}"
                    assert fid_id is None, f"{fid} {key} absent with formula {fid_id}"


# ── wire-platform-to-real-data: real weather + real metadata + honest labels ──


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


def test_resolve_scores_model_with_synthetic_checkpoint(tmp_path):
    """With a checkpoint present, mapped observations carry provenance 'model'."""
    from load_model_checkpoints import load_model_checkpoints, model_formula_id, squash_bin_error
    from cycle_inputs import CycleTensor, resolve_observation_scores

    _synthetic_checkpoint(tmp_path, "sts_net")
    models, status = load_model_checkpoints(tmp_path)
    assert status["sts_net"] == "loaded"
    loaded = models["sts_net"]
    assert loaded is not None

    X = np.linspace(0.0, 0.5, 2 * 6 * 2, dtype=np.float32).reshape(2, 6, 2)
    err = loaded.score_cycles(X)
    assert err.shape == (2, 6)
    assert np.isfinite(err).all()

    cycles = [CycleTensor(field_id=1, t_start=100, t_end=400, harvest_day=100,
                          x=np.full((6, 3), np.nan, dtype=np.float32))]
    errs = {"sts_net": squash_bin_error(err)}
    scores, prov, formula = resolve_observation_scores(
        150, cycles, model_errs=errs, model_status=status, cwsi=0.8,
    )
    assert prov["sts_net"] == "model"
    assert formula["sts_net"] == model_formula_id("sts_net")
    assert scores["sts_net"] == round(float(1.0 - np.exp(-err[0, (150 - 100) // 15])), 3)
    # Baselines / masked_transformer have no checkpoints and stay proxy.
    assert prov["b0_calendar"] == "proxy"
    assert formula["b0_calendar"] == PROXY_SCORE_FORMULA_ID
    assert prov["masked_transformer"] == "proxy"


def test_resolve_scores_proxy_without_models():
    """Missing checkpoints / --no-models yield proxy scores with formula id, no crash."""
    from cycle_inputs import CycleTensor, resolve_observation_scores

    cycles = [CycleTensor(field_id=1, t_start=100, t_end=400, harvest_day=100,
                          x=np.full((6, 3), np.nan, dtype=np.float32))]
    for model_status, force_proxy in (({}, False), ({}, True)):
        scores, prov, formula = resolve_observation_scores(
            150, cycles, model_errs={}, model_status=model_status,
            cwsi=0.8, force_proxy=force_proxy,
        )
        for key in SCORE_NAMES:
            assert prov[key] == "proxy", f"{key}: {prov[key]}"
            assert formula[key] == PROXY_SCORE_FORMULA_ID
            assert 0.05 <= scores[key] <= 0.95
        # cwsi=0.8 -> stress_sig = 0.8 - 0.45 (same float arithmetic as the rule)
        # -> b0 = 0.18 + stress_sig * 0.65 (matches the old exporter rule)
        assert scores["b0_calendar"] == round(0.18 + (0.8 - 0.45) * 0.65, 3)


def test_resolve_scores_absent_when_checkpoint_failed():
    """A checkpoint that exists but fails to reconstruct yields 'absent', not a faked score."""
    from cycle_inputs import CycleTensor, resolve_observation_scores

    cycles = [CycleTensor(field_id=1, t_start=100, t_end=400, harvest_day=100,
                          x=np.full((6, 3), np.nan, dtype=np.float32))]
    scores, prov, formula = resolve_observation_scores(
        150, cycles, model_errs={}, model_status={"sts_net": "failed"}, cwsi=0.8,
    )
    assert prov["sts_net"] == "absent"
    assert scores["sts_net"] is None
    assert formula["sts_net"] is None
    assert prov["tiny_cnn_mamba"] == "proxy"
    assert prov["b1_dsh"] == "proxy"
