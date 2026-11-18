## Design — patch-level-controlled-trial

### Data flow

`patches.zarr` (patch-data-pipeline) → Dataset in
`src/ssl_anomaly/train/patch_data.py`: one sample = one admitted
field-cycle; tensors X (36, 8, 32, 32) fp16, M pixel-valid (36, 1, 32, 32),
F in-field (1, 32, 32), covariates u (36, 7) derived from cycle metadata
(cycle start + bin index → DOY; n_obs, sensor_id from the store).
Normalization: the store's frozen per-channel per-sensor median/IQR.
NaN policy: invalid pixel-bins are zeroed only after masking and excluded
from every loss and metric (AGENTS.md §8: never silently observed).

### Model (document §7.1, adapted to the 36-bin cycle grid)

- **Stem (shared over bins):** concat[X·M, M] (9 ch) → conv3×3 →32 GN GELU
  → conv3×3 32→32 GN GELU (e1) → maxpool2×2 → conv3×3 32→64 GN GELU →
  bilinear ×2 → concat e1 (96) → conv1×1 →32 → s (B, 36, 32, S, S). ≈33k.
- **Temporal:** GRU(input 32+7+1 = 40, hidden 96, 1 layer) applied per
  location ((B×1024) rows over T = 36); state carried unchanged where the
  pixel is invalid at t. ≈40k.
- **Heads:** for k∈{1,2,3}: concat[h_t, u_{t+k}] (103) → conv1×1 64 GELU →
  conv1×1 → 8 = x̂_{t+k} in input space (de-normalized output → residuals
  in physical units, connecting to the MDM protocol). ≈8k. Aux
  masked-reconstruction head (h_t, u_t → 8) at masked positions. ≈7k.
  Total ≈90k ≤ 500k budget, GroupNorm throughout (masked pixels corrupt
  batch statistics).
- **Causality invariant (tested):** prediction at bin t+k uses only bins ≤ t.

### Objective and budget

Loss = Σ_k w_k·Huber(x_{t+k}, x̂_{t+k}) over valid in-field pixels,
w = (1, 0.5, 0.25), + 0.3·Huber masked-reconstruction; burn-in bins 0–7
contribute no loss; trimmed loss drops the top 5% per-batch pixel losses
after a 10-epoch warm-up (the contamination countermeasure that partially
worked in the aerial MIM study, document §5). AdamW 2e-3, cosine decay,
wd 1e-2, clip 1.0, 40 epochs default, batch 8 (CPU-safe; `--batch-size`).
The subset run must fit the ≤15 min/seed laptop budget — verified by
`--estimate-runtime` before handover; if the FULL run exceeds it, the
estimate decides CPU vs GPU/Colab and the user launches it (AGENTS.md §7).

### Scoring (document §8, adapted)

Per-pixel residual z(p, t, c, k) = (x − x̂) / σ(c, φ, sensor); σ =
1.4826 × MAD of dev residuals binned by 2-bin (≈30 d) phenophase groups ×
sensor, frozen + sha. Pixel score s_pred = mean z² over k∈{1,2,3} and
channels. Field-cycle aggregation S_f(t) = mean of the top 20% valid
in-field pixel scores → (N, 36, C) z-space tensor feeding the EXISTING
alarm rule (monitor/scoring.py τ/k/q95 calibration at 5% cycle-FAR)
through a `PatchDeepScorer` adapter implementing the `DeepCausalScorer`
interface — so eval_dev.py protocol `severity`, dev_log and MDM80
censoring run UNCHANGED. Pixel-localization AUPRC is computed directly on
per-pixel scores for the footprint-0.3 probe (perturbations must return
injection masks — they already do for the field-level sweep).

### Injection machinery

`monitor/perturbations.py` gains a patch-tensor applier: same severity
ladder S1–S6, families {acute, persistent}, indices {ndvi, savi}, same δ
values and durations, applied per-pixel coherently over the in-field
footprint (footprint ∈ {1.0 protocol, 0.3 localization probe}) using the
existing sum-preserving red/nir SAVI solver per pixel. Injection-set
hashes must equal the field-level protocol's so arm comparison is exact.

### Sequencing and decision logic

- This trial runs INDEPENDENTLY of the pending gru_pred training, but the
  path-C decision structure stays: whether the predictive objective becomes
  the main path is decided by the gru_pred gates; THIS trial decides the
  SPATIAL question (E1) and the FLOOR question (G3) under the same
  objective family.
- Subset = pre-registered hashed subset of locked train-split fields
  (default: two KMeans train blocks, ≈100 fields) recorded in the run
  manifest; `--max-fields` for scaling experiments. Dev eval = locked dev
  subset (38 dev fields), exactly as eval_dev.py uses today. Test split
  untouched.
- Honest-negative protocol: if G3 fails (no finite MDM80 below censoring),
  finding 23 records the floor result verbatim; no goalpost movement, no
  spec-target edits after the first training run starts (same discipline
  as predictive-ssl-controlled-trial).

### Risks

- **CPU training speed at S=32/T=36** (document §11 estimates are
  T4-based): `--estimate-runtime` measures first; subset mode keeps the PoC
  inside the laptop budget; the full run may need the lab GPU/Colab
  (device auto-select is already required).
- **Per-bin median smoothing** can attenuate single-date sudden drops
  before the model sees them (deviation #2 in patch-data-pipeline design):
  the severity protocol defines acute injections in bin units, so
  injections and the input pipeline see the same binning — internally
  consistent, with the cost documented in finding 23.
- **Patch-level absorption of persistent anomalies** may be WORSE than
  field-level (neighbours inside the same field carry the anomaly in
  context — the aerial-MIM failure mode, document §2.3): trimmed loss +
  prediction objective are the v1 countermeasures; part C machinery is
  reused in the full run to measure α_patch.

### Audit follow-up: causal inputs

Use the fixed encoding bound (uint8, 255) for `log1p(n_obs)` rather than the
full-cycle maximum. The current-bin count cannot depend on the suffix. Version
the input protocol in patch runs/checkpoints; do not reinterpret older weights
under corrected normalization or causality. Train, calibration and challenge
scoring use the same preprocessing; severity deltas remain in physical units.
