## 1. Verify with and without archive inputs

- [x] 1.1 Classify data-dependent tests and keep source-only assertions in the checkout suite.
- [x] 1.2 Document both commands and verify the checkout selection and strict missing-data behavior.

The checkout suite passed (1,022 passed, 2 optional Rust skips), including the
tracked golden fixture, without the archive or generated payload. The documented
baseline quickstart ran in scratch space. The strict
selection failed on missing inputs (20 failures, 10 setup errors); it is still
required on the archive machine. Platform TypeScript passed, but build/runtime
remain blocked by the missing export. This change does not certify either.
