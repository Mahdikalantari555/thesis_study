"""Literature-grounded severity ladder (change literature-grounded-severity-protocol).

The S1–S6 absolute index-drop table, merged and verified against primary
sources in ``research/ssl-stress-advantage/VERIFICATION.md`` (2026-11-14):

- S2/S3 anchor on Clay et al. 2012 (wheat, NDVI drops read from the abstract
  and a citing-paper summary → ``verified_abstract``);
- S5/S6 anchor on Kiranmai et al. 2025 (maize skip-irrigation, exact NDVI
  values from the open-access full text → ``verified_full_text``);
- S1 (below documented response) and S4 (interpolation S3→S5) are honest
  ``design_choice`` levels.

CONFIG ONLY: if the advisor later supplies sugarcane-specific magnitudes, the
table changes here — no injection/evaluation code changes. Excluded claims
(VERIFICATION.md §4 — French 2020 −5 %/10-day, the uncited "2026 maize
salinity study", ESA WorldView-2 spatial σ) never appear as anchors.

Every claim produced with this table is ladder rung L2; the noun is "synthetic
anomaly", never "stress".

Units
-----
- ``delta_ndvi``: absolute index drop applied to the observed value.
- ``pct_of_grand_growth_median``: delta relative to the grand-growth median
  NDVI of the archive (≈0.66, computed 2026-11-14 from the frozen
  ``gru_ae_main`` sidecar normalization: median of the per-bin train medians
  over the mid-cycle / grand-growth bins). Per-FIELD percentages are computed
  at injection time against the field's own grand-growth median.
- ``x_across_field_mad``: delta relative to the across-field MAD of NDVI
  (0.066 = median over bins of the per-(bin, band) robust scale ÷ 1.4826,
  same source). Detection floors from finding 16 are quoted in these units.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

GRAND_GROWTH_MEDIAN_NDVI = 0.66  # archive grand-growth median NDVI (frozen sidecar, 2026-11-14)
ACROSS_FIELD_MAD_NDVI = 0.066   # across-field MAD of NDVI (frozen sidecar, 2026-11-14)

VERIFICATION_VALUES: tuple[str, ...] = (
    "verified_full_text",
    "verified_abstract",
    "design_choice",
    "rejected",
)

ACUTE_FAMILY = "acute"
PERSISTENT_FAMILY = "persistent"
# Third PRIMARY temporal shape (change gradual-severity-shape): a linear ramp
# over D bins to the level's δ, then held to cycle end. The ramp length cycles
# through these values across rounds so one sweep covers all three.
GRADUAL_FAMILY = "gradual"
GRADUAL_RAMP_BINS: tuple[int, ...] = (3, 4, 6)
PRIMARY_FAMILIES: tuple[str, ...] = (ACUTE_FAMILY, PERSISTENT_FAMILY, GRADUAL_FAMILY)
# SECONDARY diagnostic shapes — never enter a primary gate.
SECONDARY_FAMILIES: tuple[str, ...] = ("peak_disruption", "recovery_disruption")
# Persistent variant duration: design.md "4–6 bins, same Δ"; the midpoint 5
# keeps the family disjoint from every acute duration (S6 acute ends at 4).
PERSISTENT_DURATION_BINS = 5

_CLAY = "Clay et al. 2012, Agronomy Journal 104(2): doi:10.2134/agronj2012.0216"
_KIRANMAI = (
    "Kiranmai et al. 2025, Frontiers in Environmental Science 13:1651422: "
    "doi:10.3389/fenvs.2025.1651422"
)


@dataclass(frozen=True)
class SeverityLevel:
    """One rung of the verified severity ladder.

    ``duration_bins`` is the ACUTE duration used for injection (the design
    table's lower bound — the conservative end of the anchor range);
    ``duration_ranges`` records the design-table range for provenance. The
    persistent variant holds the same Δ for ``PERSISTENT_DURATION_BINS`` bins.
    """

    level_id: str
    delta_ndvi: float                 # absolute drop applied to the observed value
    duration_bins: int                # acute injection duration (bins)
    duration_ranges: tuple[int, int]  # design-table acute range (provenance)
    pct_of_grand_growth_median: float
    x_across_field_mad: float
    source: str                       # citation + DOI (or explicit design choice)
    verification: str                 # one of VERIFICATION_VALUES
    confidence: str
    notes: str


def _derived(delta: float) -> tuple[float, float]:
    return (
        round(100.0 * delta / GRAND_GROWTH_MEDIAN_NDVI, 1),
        round(delta / ACROSS_FIELD_MAD_NDVI, 3),
    )


_S1_PCT, _S1_MAD = _derived(0.02)
_S2_PCT, _S2_MAD = _derived(0.05)
_S3_PCT, _S3_MAD = _derived(0.08)
_S4_PCT, _S4_MAD = _derived(0.16)
_S5_PCT, _S5_MAD = _derived(0.28)
_S6_PCT, _S6_MAD = _derived(0.40)

SEVERITY_TABLE: tuple[SeverityLevel, ...] = (
    SeverityLevel(
        level_id="S1", delta_ndvi=0.02, duration_bins=1, duration_ranges=(1, 1),
        pct_of_grand_growth_median=_S1_PCT, x_across_field_mad=_S1_MAD,
        source="design choice — below documented response range (no external anchor)",
        verification="design_choice", confidence="high",
        notes="subtle floor of the ladder; expected undetectable at 5 % cycle FAR",
    ),
    SeverityLevel(
        level_id="S2", delta_ndvi=0.05, duration_bins=1, duration_ranges=(1, 2),
        pct_of_grand_growth_median=_S2_PCT, x_across_field_mad=_S2_MAD,
        source=f"{_CLAY} — flag-leaf NDVI −5.68 % (water stress, wheat)",
        verification="verified_abstract", confidence="medium",
        notes="Clay 2012: direction verified from abstract + citing-paper summary; "
              "exact numbers not independently re-read (paywalled)",
    ),
    SeverityLevel(
        level_id="S3", delta_ndvi=0.08, duration_bins=2, duration_ranges=(2, 2),
        pct_of_grand_growth_median=_S3_PCT, x_across_field_mad=_S3_MAD,
        source=f"{_CLAY} — stem-extension NDVI −10.26 % (water stress, wheat)",
        verification="verified_abstract", confidence="medium",
        notes="same verification status as S2",
    ),
    SeverityLevel(
        level_id="S4", delta_ndvi=0.16, duration_bins=2, duration_ranges=(2, 3),
        pct_of_grand_growth_median=_S4_PCT, x_across_field_mad=_S4_MAD,
        source="interpolation S3→S5 — design choice (no external anchor)",
        verification="design_choice", confidence="high",
        notes="geometric bridge between the verified S3 and S5 magnitudes",
    ),
    SeverityLevel(
        level_id="S5", delta_ndvi=0.28, duration_bins=3, duration_ranges=(3, 4),
        pct_of_grand_growth_median=_S5_PCT, x_across_field_mad=_S5_MAD,
        source=f"{_KIRANMAI} — double-skip irrigation −30–40 % (NDVI 0.76→0.45–0.51)",
        verification="verified_full_text", confidence="high",
        notes="Kiranmai 2025: exact values from open-access full text (p≤0.05)",
    ),
    SeverityLevel(
        level_id="S6", delta_ndvi=0.40, duration_bins=4, duration_ranges=(4, 5),
        pct_of_grand_growth_median=_S6_PCT, x_across_field_mad=_S6_MAD,
        source=f"{_KIRANMAI} — withheld irrigation ≈ −50 % (NDVI 0.76→0.37)",
        verification="verified_full_text", confidence="high",
        notes="positive control; brackets the measured 6–8×MAD detection floor (finding 16)",
    ),
)


def table_payload() -> dict:
    """Canonical JSON-serializable form of the table (hash + sidecar input)."""
    return {
        "name": "literature_grounded_severity_v1",
        "grand_growth_median_ndvi": GRAND_GROWTH_MEDIAN_NDVI,
        "across_field_mad_ndvi": ACROSS_FIELD_MAD_NDVI,
        "persistent_duration_bins": PERSISTENT_DURATION_BINS,
        "verification_values": list(VERIFICATION_VALUES),
        "levels": [asdict(lv) for lv in SEVERITY_TABLE],
    }


def severity_table_hash() -> str:
    """SHA-256 over the canonical payload (stable dict ordering)."""
    payload = json.dumps(table_payload(), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_table(payload: dict | None = None, *, enabled_ids: tuple[str, ...] | None = None) -> list[SeverityLevel]:
    """Load the table (or a payload), refusing ``rejected`` levels.

    A level whose ``verification`` is ``rejected`` cannot be enabled by
    configuration (spec scenario 'Severity provenance'); unknown level ids
    are configuration errors.
    """
    payload = payload or table_payload()
    levels: list[SeverityLevel] = []
    for row in payload["levels"]:
        lv = SeverityLevel(
            level_id=row["level_id"], delta_ndvi=float(row["delta_ndvi"]),
            duration_bins=int(row["duration_bins"]),
            duration_ranges=tuple(row["duration_ranges"]),
            pct_of_grand_growth_median=float(row["pct_of_grand_growth_median"]),
            x_across_field_mad=float(row["x_across_field_mad"]),
            source=str(row["source"]), verification=str(row["verification"]),
            confidence=str(row["confidence"]), notes=str(row.get("notes", "")),
        )
        levels.append(lv)
    rejected = [lv.level_id for lv in levels if lv.verification not in VERIFICATION_VALUES]
    if rejected:
        raise ValueError(
            f"severity table contains levels with unknown verification values: {rejected}"
        )
    rejected = [lv.level_id for lv in levels if lv.verification == "rejected"]
    if rejected:
        raise ValueError(
            f"severity levels rejected by verification cannot be enabled: {rejected}"
        )
    if enabled_ids is not None:
        known = {lv.level_id for lv in levels}
        unknown = [i for i in enabled_ids if i not in known]
        if unknown:
            raise ValueError(f"unknown level ids: {unknown}")
        levels = [lv for lv in levels if lv.level_id in set(enabled_ids)]
    return levels
