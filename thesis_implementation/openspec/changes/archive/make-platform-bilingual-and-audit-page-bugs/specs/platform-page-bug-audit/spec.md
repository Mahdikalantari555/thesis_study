# Spec Delta: platform-page-bug-audit

## Purpose

Audits every page of the AgriAnomaly visualization platform for logical bugs and missing connections, fixes the issues found, and records a written bug report so reviewers can verify what was corrected and what remains, ensuring the dashboard no longer misrepresents the Khuzestan dataset or its synthetic/demonstration status.

## ADDED Requirements

### Requirement: Data source honesty
The platform SHALL clearly distinguish real Khuzestan data from synthetic/demonstration data in every view, and SHALL NOT present synthetic series as verified research results.

#### Scenario: Demo badge present
- **WHEN** the platform renders any page using synthetic or demonstration data
- **THEN** a visible badge or caption states "Demonstration data" in the active locale

#### Scenario: No stale region labels
- **WHEN** the platform renders the Overview footer or any region label
- **THEN** it does not display "Piracicaba, SP, Brazil" or any other incorrect region

### Requirement: Temporal coverage consistency
The platform SHALL make the date range and observation count consistent across all pages and controls, driven by a single source of truth.

#### Scenario: No hardcoded 48-step sliders
- **WHEN** a page renders a date slider or range control
- **THEN** its min/max are derived from the actual `DATES` array length, not a hardcoded `47`

#### Scenario: Labels match data
- **WHEN** a view displays "All N fields" or "N observations"
- **THEN** N matches the actual loaded dataset size (490 farms, not 48)

### Requirement: Consumed exported data
The platform SHALL either consume `series_khuzestan.json` produced by `export_platform_data.py` or remove the unused export, with the decision documented.

#### Scenario: No dead data artifacts
- **WHEN** the platform build completes
- **THEN** every JSON file under `platform/src/data/` is imported by at least one component, or is removed

### Requirement: MapView stability
The platform SHALL preserve map zoom level and center position when toggling dark mode.

#### Scenario: Dark mode toggle preserves view
- **WHEN** the user toggles dark mode on the map page
- **THEN** the map's zoom and center remain unchanged and only the tile layer swaps

### Requirement: Safe default selection
The platform SHALL guard against empty or undefined field lists when selecting a default field.

#### Scenario: Empty data guard
- **WHEN** `FIELDS` is empty or undefined
- **THEN** `selectedField` defaults to an empty string and no runtime error occurs

### Requirement: Bug report document
The platform SHALL include a `docs/platform_bug_audit.md` file listing every logical bug and disconnection discovered during the audit, with severity and status.

#### Scenario: Audit document exists
- **WHEN** the change is complete
- **THEN** `docs/platform_bug_audit.md` exists and contains at least one entry per audited page

### Requirement: Screenshot evidence
The platform SHALL provide Persian-language screenshots of all 8 pages under `reports/screenshots/fa/` for PR review.

#### Scenario: Screenshots generated
- **WHEN** the screenshot capture script runs
- **THEN** PNG files for Overview, Map, Temporal, Spectral, Validation, Comparison, Spatial, and Reports are saved under `reports/screenshots/fa/`
