"""Severity-table tests (change literature-grounded-severity-protocol, task 1.1).

The S1–S6 ladder is VERIFIED CONFIG: every level must carry its source
(citation + DOI), verification status (matching
research/ssl-stress-advantage/VERIFICATION.md verbatim) and confidence.
Excluded claims (VERIFICATION.md §4) must never appear as design anchors.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import severity_table as sev  # noqa: E402


def test_levels_are_s1_to_s6_with_verified_deltas() -> None:
    """The merged verified ladder (design.md): absolute NDVI drops."""
    deltas = [lv.delta_ndvi for lv in sev.SEVERITY_TABLE]
    assert deltas == [0.02, 0.05, 0.08, 0.16, 0.28, 0.40]
    assert [lv.level_id for lv in sev.SEVERITY_TABLE] == ["S1", "S2", "S3", "S4", "S5", "S6"]


def test_every_level_has_provenance_fields() -> None:
    for lv in sev.SEVERITY_TABLE:
        assert lv.verification in sev.VERIFICATION_VALUES, lv.level_id
        assert lv.confidence, lv.level_id
        assert lv.source.strip(), lv.level_id
        assert lv.duration_bins >= 1, lv.level_id


def test_verification_matches_verification_md() -> None:
    """Per-level verification status must match VERIFICATION.md §3 verbatim:
    Clay 2012 numbers verified from the abstract; Kiranmai 2025 from full
    text; S1/S4 are design choices."""
    by_id = {lv.level_id: lv for lv in sev.SEVERITY_TABLE}
    assert by_id["S1"].verification == "design_choice"
    assert by_id["S2"].verification == "verified_abstract"
    assert by_id["S3"].verification == "verified_abstract"
    assert by_id["S4"].verification == "design_choice"
    assert by_id["S5"].verification == "verified_full_text"
    assert by_id["S6"].verification == "verified_full_text"


def test_sources_carry_dois_for_verified_levels() -> None:
    by_id = {lv.level_id: lv for lv in sev.SEVERITY_TABLE}
    assert "10.2134/agronj2012.0216" in by_id["S2"].source
    assert "10.2134/agronj2012.0216" in by_id["S3"].source
    assert "10.3389/fenvs.2025.1651422" in by_id["S5"].source
    assert "10.3389/fenvs.2025.1651422" in by_id["S6"].source


def test_excluded_claims_absent_from_design_anchors() -> None:
    """VERIFICATION.md §4: French 2020 numbers, the uncited '2026 maize
    salinity study' and the ESA spatial σ must not anchor any level."""
    blob = " | ".join(lv.source for lv in sev.SEVERITY_TABLE)
    for excluded in ("French", "French et al", "2026 maize salinity", "WorldView"):
        assert excluded.lower() not in blob.lower(), excluded


def test_derived_columns_consistent() -> None:
    """% of the grand-growth median and × across-field MAD reproduce the
    design-table columns (grand-growth median 0.66, MAD 0.066)."""
    design_pct = {"S1": 3.0, "S2": 7.6, "S3": 12.1, "S4": 24.2, "S5": 42.4, "S6": 60.6}
    design_mad = {"S1": 0.30, "S2": 0.76, "S3": 1.21, "S4": 2.42, "S5": 4.24, "S6": 6.06}
    for lv in sev.SEVERITY_TABLE:
        assert lv.pct_of_grand_growth_median == pytest.approx(design_pct[lv.level_id], abs=0.05)
        assert lv.x_across_field_mad == pytest.approx(design_mad[lv.level_id], abs=0.005)


def test_families_and_durations() -> None:
    """Acute durations are the design-table lower bounds; the persistent
    variant is a fixed duration inside the 4–6-bin design range."""
    by_id = {lv.level_id: lv for lv in sev.SEVERITY_TABLE}
    assert [by_id[f"S{i}"].duration_bins for i in range(1, 7)] == [1, 1, 2, 2, 3, 4]
    assert 4 <= sev.PERSISTENT_DURATION_BINS <= 6
    # Family separation: the persistent duration must differ from every acute
    # duration so the two MDM families stay disjoint.
    assert sev.PERSISTENT_DURATION_BINS not in [lv.duration_bins for lv in sev.SEVERITY_TABLE]


def test_hash_stable() -> None:
    """The sidecar hash must be deterministic across calls and processes
    (no dict ordering / float repr drift)."""
    h1 = sev.severity_table_hash()
    h2 = sev.severity_table_hash()
    assert h1 == h2
    assert len(h1) == 64
    # The hash covers every level's provenance fields.
    payload = sev.table_payload()
    assert payload["levels"][0]["level_id"] == "S1"
    assert len(payload["levels"]) == 6


def test_rejected_levels_refuse_to_load() -> None:
    """A level marked `rejected` cannot be enabled by configuration (spec
    scenario 'Severity provenance')."""
    # The shipped table contains no rejected level...
    assert all(lv.verification != "rejected" for lv in sev.SEVERITY_TABLE)
    # ...but a configuration attempting to enable a rejected one is refused.
    doctored = sev.table_payload()
    doctored["levels"][0] = {**doctored["levels"][0], "verification": "rejected"}
    with pytest.raises(ValueError, match="rejected"):
        sev.load_table(doctored)


def test_load_table_by_ids() -> None:
    subset = sev.load_table(sev.table_payload(), enabled_ids=("S1", "S6"))
    assert [lv.level_id for lv in subset] == ["S1", "S6"]
    with pytest.raises(ValueError, match="unknown level"):
        sev.load_table(sev.table_payload(), enabled_ids=("S9",))
