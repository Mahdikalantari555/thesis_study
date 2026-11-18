"""Declarative registry of platform data channels and anomaly scores.

Single source of truth (Python side) for the channel contract between
``scripts/export_platform_data.py`` and the platform web app. The TypeScript
mirror lives at ``platform/src/data/channels.ts``; parity is enforced by
``tests/unit/test_platform_data_contract.py``.

Each channel entry declares:
  - ``name``: channel id (matches the platform ``IndicatorId``)
  - ``unit``: display unit
  - ``physical_range``: (min, max) inclusive physical envelope
  - ``provenance_default``: ``observed`` | ``modelled`` | ``proxy`` | ``absent``
  - ``required``: whether every observation must carry the channel
  - ``kind``: spectral | thermal | water | weather
  - ``derived_from``: optional source channel when this is a documented proxy

Each score entry declares (contract v5):
  - ``name``: score key (matches the platform ``ModelId``)
  - ``provenance_default``: ``model`` | ``proxy`` | ``absent`` — ``model`` when
    a trained checkpoint backs the score. ``proxy`` is kept ONLY as the registry
    kind of the baseline-heuristic slots (``b0_calendar``, ``b1_dsh``,
    ``b1_cusum``); since contract v5 there is no CWSI proxy fallback at
    resolution time, so those slots resolve to ``absent`` unless a non-CWSI
    formula artifact exists (none does today).
  - ``checkpoint``: checkpoint stem under ``checkpoints/`` when model-backed

Contract v5 semantics (spec ``model-output-ingest`` / ``field-stress-monitoring``):
  - SSL slots (``masked_transformer``, ``gru_ae``) are scored causally from the
    ``*_main`` checkpoints (masked no-interpolation cycle tensors); they NEVER
    fall back to the CWSI proxy formula — an unmapped observation or missing
    checkpoint yields ``score = null`` + provenance ``"absent"``.
  - Per observation the payload adds ``stressFlag`` (``normal`` |
    ``suspected_stress`` | ``no_data`` | null), ``stressFlagModel`` (checkpoint
    id) and ``split`` (``train`` | ``dev`` | ``test`` | ``monitoring``); per
    field it adds ``ladderRung`` from the main checkpoint sidecar.
  - Honest naming: the positive class is "suspected stress (anomaly)" until L4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

ProvenanceState = Literal["observed", "modelled", "proxy", "absent"]
ChannelKind = Literal["spectral", "thermal", "water", "weather"]
ScoreProvenanceState = Literal["model", "proxy", "absent"]

# Contract version: v5 = v4 compact series payload + causal stress flag
# (stressFlag / stressFlagModel / split per observation, ladderRung per field)
# and NO proxy fallback anywhere (all unresolvable scores are "absent").
# v4 = compact series payload (shared acquisition-date axis + per-field numeric
# arrays + RLE provenance) over the full archive; v3 = per-observation objects.
# Farm records carry the same version number.
CONTRACT_VERSION = 5


@dataclass(frozen=True)
class ChannelSpec:
    name: str
    unit: str
    physical_range: Tuple[float, float]
    provenance_default: ProvenanceState = "observed"
    required: bool = True
    kind: ChannelKind = "spectral"
    derived_from: Optional[str] = None


# Order mirrors the platform INDICATORS list.
CHANNEL_REGISTRY: tuple[ChannelSpec, ...] = (
    # Envelopes below are the observed field-median envelope over the full
    # 2013-2026 archive (measured 2026-11-07) plus a small margin — winter
    # bare-soil/water mixes legitimately yield slightly negative NDVI/EVI/SAVI.
    ChannelSpec("ndvi", "index", (-0.5, 1.0), "observed", True, "spectral"),
    ChannelSpec("evi", "index", (-0.3, 1.0), "observed", True, "spectral"),  # computed from blue band
    ChannelSpec("savi", "index", (-0.3, 1.0), "observed", True, "spectral"),
    ChannelSpec("ndmi", "index", (-1.0, 1.0), "observed", True, "water"),
    ChannelSpec("tvdi", "index", (0.0, 1.0), "proxy", True, "thermal", "cwsi"),
    ChannelSpec("cwsi", "index", (0.0, 1.0), "observed", True, "thermal"),
    ChannelSpec("eta", "mm/d", (0.0, 8.0), "proxy", True, "water", "ndvi"),
    ChannelSpec("lst", "\u00b0C", (15.0, 55.0), "observed", False, "thermal"),  # conditional
    ChannelSpec("precip", "mm", (0.0, 300.0), "modelled", True, "weather"),
    # ERA5 daily-mean air temperature over Khuzestan spans ~7-44 degC
    # (weather_aligned.parquet 2013-2026); the old (10, 48) envelope was tuned
    # for LST-derived estimates and rejected real reanalysis rows.
    ChannelSpec("temp", "\u00b0C", (0.0, 55.0), "modelled", True, "weather"),
)

CHANNEL_NAMES: tuple[str, ...] = tuple(c.name for c in CHANNEL_REGISTRY)


@dataclass(frozen=True)
class ScoreSpec:
    name: str
    provenance_default: ScoreProvenanceState = "proxy"
    checkpoint: Optional[str] = None  # checkpoints/<stem>.pt (+ .json sidecar) when model-backed


# Order mirrors the platform MODELS list (data.ts).
# v5: masked_transformer / gru_ae are model-backed via the frozen main
# checkpoints (causal masked-reconstruction scoring, see
# scripts/load_model_checkpoints.LoadedCausalModel). b0/b1 keep the "proxy"
# registry kind as baseline-heuristic slots, but the CWSI proxy FORMULA was
# removed in v5 (circular with the model's own inputs): without a non-CWSI
# formula artifact they resolve "absent" for every observation.
SCORE_REGISTRY: tuple[ScoreSpec, ...] = (
    ScoreSpec("b0_calendar", "proxy"),
    ScoreSpec("b1_dsh", "proxy"),
    ScoreSpec("b1_cusum", "proxy"),
    ScoreSpec("masked_transformer", "model", "masked_transformer_main"),
    ScoreSpec("gru_ae", "model", "gru_ae_main"),
    ScoreSpec("sts_net", "model", "sts_net_490"),
    ScoreSpec("tiny_cnn_mamba", "model", "tiny_cnn_mamba_490"),
    ScoreSpec("time2agri", "model", "time2agri_490"),
)

SCORE_NAMES: tuple[str, ...] = tuple(s.name for s in SCORE_REGISTRY)
SCORE_CHECKPOINTS: dict[str, str] = {s.name: s.checkpoint for s in SCORE_REGISTRY if s.checkpoint}


def by_name(name: str) -> Optional[ChannelSpec]:
    for c in CHANNEL_REGISTRY:
        if c.name == name:
            return c
    return None


def score_by_name(name: str) -> Optional[ScoreSpec]:
    for s in SCORE_REGISTRY:
        if s.name == name:
            return s
    return None


def as_dict() -> list[dict]:
    out = []
    for c in CHANNEL_REGISTRY:
        out.append(
            {
                "name": c.name,
                "unit": c.unit,
                "physical_range": list(c.physical_range),
                "provenance_default": c.provenance_default,
                "required": c.required,
                "kind": c.kind,
                "derived_from": c.derived_from,
            }
        )
    return out


def scores_as_dict() -> list[dict]:
    out = []
    for s in SCORE_REGISTRY:
        out.append(
            {
                "name": s.name,
                "provenance_default": s.provenance_default,
                "checkpoint": s.checkpoint,
            }
        )
    return out


__all__ = [
    "ChannelSpec", "ScoreSpec", "CHANNEL_REGISTRY", "SCORE_REGISTRY",
    "CHANNEL_NAMES", "SCORE_NAMES", "SCORE_CHECKPOINTS", "CONTRACT_VERSION",
    "by_name", "score_by_name", "as_dict", "scores_as_dict",
]
