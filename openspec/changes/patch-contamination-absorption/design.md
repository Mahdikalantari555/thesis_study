## Design — patch-contamination-absorption

### Absorption measurement

Reuses `monitor/diagnostics.decompose_injection` (the part-C tool) on patch
scorer outputs. For patch arms the three checkpoints are per bin on the
persistent injection; the ratio uses mean per-pixel residual z² over the
in-field footprint. Contamination training runs: base configuration from
the PoC (frozen seeds {13, 42, 2026}, same budget), one variable at a time
— contamination fraction, trimmed loss, curation — a 3×2×2 grid reduced by
running the fraction axis first at trimmed=on/curation=off (the PoC
default), then the winning fraction for the remaining cells. Everything
runs on the pre-registered PoC subset (runtime stays inside the laptop
budget; `--estimate-runtime` before each user-run batch).

### Curation round

Round 1: score all train field-cycles with the clean-trained model, remove
the top p% most extreme (p pre-registered at 2%, the document's "most
extreme few percent"), retrain. Removed cycles are recorded by id in the
run manifest — the removal list is data, never silent (AGENTS.md §2.4).
A second curation round is out of scope (diminishing returns, document
§5.4 says one round).

### Decision rule (pre-registered)

For each configuration: report A_patch (↑ = less absorption) and clean
MDM80 (must stay within one standard error of the clean-trained baseline).
Adopt the configuration with the highest A_patch whose clean MDM80 is
within one standard error; ties → simpler configuration (trimmed loss only
< trimmed + curation). If NO configuration beats trimmed-loss-on at A_patch
≥ 1.0 − ε (i.e., no meaningful absorption), record the honest negative and
escalate the documented NEXT step (memory-augmented bottleneck) to the
owner as a separate decision — not silently.

### Risks

- 5–10% contamination of ~100 subset field-cycles = 5–10 injected cycles —
  small-n absorption estimates get wide CIs; bootstrap CIs over injected
  cycles reported, and the fraction axis is re-run at full scale in the
  full-run change if CIs are too wide to decide.
- Injecting into training changes the training distribution; the clean-dev
  calibration path (σ tables, τ) is always re-fitted from the CLEAN dev
  residuals of the retrained model, never from contaminated data.
