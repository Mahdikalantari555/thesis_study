# Proposal: Separate checkout and archive verification

## Why

The synthetic quickstart runs tests that read files absent from a clean clone.
A missing archive must not look like a code regression or a passing data gate.

## What Changes

- Give checkout-only and real-data verification explicit pytest selections.
- Keep real export, split and archive assertions strict; missing inputs fail that
  selection with diagnostics. Do not make Vite build against fabricated data.

## Capabilities

### New Capabilities

- `research-verification`: Distinguish verification of repository code and
  fixtures from verification against authorized real-data artifacts.

### Modified Capabilities

None.

## Impact

Pytest markers, verification documentation and data-contract tests. No change
in the platform's generated payload, serving path or frozen data.
