# Spec Delta

## Purpose

Distinguish reproducible source verification from verification of the authorized real archive and its exported platform data.

## ADDED Requirements

### Requirement: Explicit verification gates

The documented checkout test selection SHALL run without the external archive or
an untracked export. The distinct `real_data` selection SHALL perform its original
contract and scientific checks against the authorized artifacts. A missing artifact
SHALL cause the corresponding real-data check to fail, not skip or substitute data.
Passing the checkout gate SHALL NOT certify the platform build or real data.

#### Scenario: Clean checkout
- **WHEN** the documented checkout test command is run without the archive
- **THEN** source-only registry and bilingual checks and fixture-based tests run
  without selecting tests that read the external archive or generated payload

#### Scenario: Real-data gate without inputs
- **WHEN** the real-data gate is run with a required real artifact missing
- **THEN** it fails with the missing prerequisite and no generated placeholder
  or passing real-data result is produced
