# Spec Delta: platform-page-bug-audit

## Purpose

Extends the page-level bug audit from the eight platform views to the artifact boundary — the
exporter and the bundled JSON — and tightens what “Fixed” is allowed to mean, after the
previous change (`make-platform-bilingual-and-audit-page-bugs`) marked a defect fixed that the
shipped code does not fix.

> **Archive note.** This delta contains only ADDED requirements so that it can be archived
> either on its own or after the predecessor change, in which case the requirements merge into
> the single `platform-page-bug-audit` capability. Archiving the predecessor first is the
> intended order.

## ADDED Requirements

### Requirement: Audited surface includes the exporter and the payload

The audit SHALL cover every producer of displayed data, not only the components that render
it: `scripts/export_platform_data.py`, the JSON payloads under `platform/src/data/`, and every
platform module that transforms them.

#### Scenario: Exporter defects are in scope
- **WHEN** a displayed value is absent, out of range, unit-inconsistent or temporally
  misaligned
- **THEN** the audit records it with severity and names the exporter code path that causes it

#### Scenario: Payload is verified, not assumed
- **WHEN** a value is described as measured
- **THEN** the audit confirms the key is actually present in the shipped payload

### Requirement: “Fixed” requires re-verification of the shipped artifact

A defect SHALL be marked “Fixed” only when the shipped code path has been re-checked after the
fix, and the audit entry SHALL state how it was verified.

#### Scenario: Regression of a claimed fix
- **WHEN** a defect previously marked “Fixed” is found still present in the shipped build
- **THEN** its status is corrected, the entry names the verification that failed, and a
  regression test is added where the defect is testable

#### Scenario: Verification is stated
- **WHEN** an entry is marked “Fixed”
- **THEN** it names the command, test or manual check that demonstrates the fix

### Requirement: Data-integrity findings are recorded

Every data-integrity defect discovered during this audit SHALL appear in
`docs/platform_bug_audit.md` with severity, evidence, and status.

#### Scenario: Missing channel documented
- **WHEN** the platform advertises an indicator the payload does not contain
- **THEN** the audit records it as a defect with the affected observation count

#### Scenario: Unit inconsistency documented
- **WHEN** a channel's values are inconsistent with its declared unit or physical range
- **THEN** the audit records the observed range, the declared range, and the number of
  offending samples

#### Scenario: Temporal misalignment documented
- **WHEN** a sample's date does not match the acquisition it derives from
- **THEN** the audit records the mechanism and the worst-case offset

### Requirement: Contract tests gate future payload changes

The repository SHALL contain automated checks that fail when a payload violates the data
contract.

#### Scenario: Out-of-range payload fails CI
- **WHEN** a regenerated payload contains a value outside its declared physical range
- **THEN** the data-contract test fails

#### Scenario: Skipped check is loud
- **WHEN** the contract test is skipped because the committed payload predates the contract
- **THEN** the skip message states the payload version and the regeneration command, and the
  platform surfaces the same state in the UI
