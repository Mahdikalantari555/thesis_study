# Design

## Context

The platform's year-by-year export is deliberately untracked. Some otherwise
source-only suites read it or the locked data when selected by the quickstart.

## Goals / Non-Goals

- Separate tests by whether they need artifacts outside Git.
- Do not change platform inputs, runtime, build policy, or contract assertions.

## Decisions

- Register a `real_data` marker and mark individual tests (or a homogeneous
  suite), rather than skipping based on presence. Split mixed source/export
  assertions into separate tests.
- Document the quickstart selector and the strict `pytest -m real_data` gate.
  Leave unfiltered `pytest` and the existing explicit platform files strict.

## Risks / Trade-offs

New archive-dependent tests must carry the marker. The two selections and the
existing real-data build/runtime gates remain separately reported.
