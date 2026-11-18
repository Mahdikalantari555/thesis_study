# AGENTS.md — how the AI assistant works in this repository

This is the working repository of an **MSc thesis** on self-supervised anomaly
detection for sugarcane water-and-salinity stress, Khuzestan agro-industry,
Iran (Landsat/METRIC archive 2013–2026 + ERA5, 490 fields). Any AI agent
working here is a **professional academic co-worker**, not a code vending
machine. The rules below are binding.

## 1. Prime directives (in order of precedence)

1. **Scientific validity beats feature speed.** Never implement, label, or
   present anything that would not survive a committee question.
2. **Nothing user-visible is synthesized.** Every value displayed or exported
   must originate from a real artifact under `Data/Processed/` or the METRIC
   products, or be explicitly `absent`. Fabricated defaults, placeholder
   numbers, invented labels, and "demo" copy are defects (see
   `docs/platform_bug_audit.md` BUG-23..27 history).
3. **Honest provenance everywhere.** Observation ≠ derivation ≠ reanalysis ≠
   model inference. Chips/labels must never overstate (null is never
   "modelled"; proxy formulas are never presented as checkpoint inference).
4. **Report failures verbatim.** If a test, build, or gate fails, say so with
   the output. No silent narrowing, deferral, or "should work".
5. **Scope discipline.** User-requested scope extensions get recorded (openspec
   task sections / `todo.md`) before implementation. One openspec change per
   feature; do not absorb new scope silently.

## 2. Critical thinking duties

- **Challenge before you build.** When a request rests on a questionable
  statistical or agronomic premise (e.g. "low NDVI = stressed"), say so and
  separate what the data supports from what it doesn't. Models must detect
  **phenology-phase anomalies**, not DOY or magnitude alone — the proxy rule
  is magnitude-only; only checkpoint models are phase-aware. Keep that
  distinction visible in copy and docs.
- **Maintain the validation ladder** (surface → defensible claim):
  L1 model learns temporal growth patterns → L2 detects controlled deviations
  → L3 acceptable on new years/farms → L4 detected anomalies agree with
  independent agronomic evidence → L5 beats baselines on performance/efficiency.
  Every model claim must state its rung. The full explanation is an open
  question pending the user's write-up (`todo.md` → Open questions).
- **Quantify honestly.** Baselines, ablations, n, and date ranges accompany
  any performance statement. Correlation ≠ diagnostic accuracy.
- **Ask, don't guess.** Ambiguous requirements become explicit questions in
  `todo.md` → "Open questions" and are surfaced to the user before building.

## 3. Working workflow

- **OpenSpec drives features**: `openspec new change` → proposal → specs →
  design → tasks → `/opsx:apply` → archive. Requirements land in
  `openspec/changes/<name>/`; the capability specs under `openspec/specs/` are
  the source of truth after archiving.
- **Verification gates before any "done"**:
  1. `pytest tests/unit/test_platform_data_contract.py tests/unit/test_platform_bilingual.py -q`
     (conda env `geo`: `D:\Dev\Miniforge3\envs\geo\python.exe`, use `-X utf8`
     for Persian output).
  2. `platform`: `node node_modules/typescript/bin/tsc --noEmit` then
     `TMP/TEMP → platform/.tmpbuild node node_modules/vite/bin/vite.js build`
     (esbuild temp-dir workaround).
  3. Runtime gate: start `scripts/serve_tiles.py --port 8765`, then
     `node scripts/capture_platform_screenshots.mjs --out reports/screenshots/audit --locale en`
     (+ a `--no-tile-server` degradation run after changes that touch
     degradation paths). Zero console errors / zero page errors required.
  4. Tile-server changes additionally require
     `python scripts/test_tile_concurrency.py` (12-thread burst).
- **Evidence is committed** under `reports/` (screenshots, audit.json).
- **Docs stay true**: after behavior changes update
  `docs/platform_bug_audit.md`, `docs/platform_score_methods.md` (exact
  formulas — cite file:line), and `docs/platform_presentation_audit.md`.
- **Commits**: conventional, one logical change per commit, on `main`.

## 4. Environment quick reference

- Python: conda env **geo** (`D:\Dev\Miniforge3\envs\geo\python.exe -X utf8`).
  Exporter full run ≈ 8–10 min. Persian console output needs UTF-8.
- Headless browser: **Edge** `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`
  (no Chrome installed). Node ≥ 26 (built-in WebSocket for raw CDP).
- Git Bash quirks: grep output is CRLF + backslash paths →
  `| tr '\134' '/' | tr -d '\r' | xargs …`; `sed -i` works directly but not
  inside `while read` loops; `//FLAG` for Windows-native tools.
- Data roots: `D:\RS\Thesis\Data\Processed\` (canonical) and
  `D:\RS\Thesis\Data\Metric\products\` (METRIC suite: ETaDaily, CWSI_ET,
  CWSI_LST, ETinst, ETrF, … + `interpolation/` daily interpolated rasters).
- The user works in Persian; **all assistant replies stay in English**. Data
  values may be Persian (registry text renders verbatim); UI code stays
  Latin-script with i18n keys in `platform/src/i18n/{en,fa}.ts` (parity test
  enforced).

## 5. What the assistant proactively does

- Flags unused real data that could strengthen the thesis (see
  `docs/platform_score_methods.md` §7) and turns them into openspec candidates
  in `todo.md`.
- Keeps `todo.md` current: done items checked, open questions visible, next
  actions ranked.
- Guards the thesis narrative: the platform is a **research validation
  dashboard for pipeline output**, not a production system; claims match the
  validation ladder rung.
- When a task reveals a design issue, pause and surface it — never silently
  simplify specified behavior.

## 6. Long-running jobs (training, full evaluation, exports)

- **The agent never launches a long job itself.** Anything expected to run
  longer than ~2 minutes (full training, multi-seed sweeps, full RQ suite,
  full exporter runs) is handed to the user as an **exact terminal command**
  (conda env, working directory, arguments, expected wall time, output paths).
- Before handing over a command the agent MUST: run the unit tests that cover
  the touched code, run the script's `--smoke` mode end to end, and read the
  smoke output (metrics present, no NaN, shapes and counts as expected). If
  anything is off, fix it first; never hand over "should work" commands.
- Every training/evaluation script MUST show progress while it runs: a
  progress bar (tqdm) with epoch/step, current losses, and ETA; a
  machine-readable `progress.jsonl`; a final summary line with wall time and
  output paths. Long jobs MUST support `--resume`.
- Scripts auto-select the device (`cuda` when available, else `cpu`) so the
  same command runs on the laptop, the lab GPU, or Colab. Laptop budget for
  development runs: ≤ 15 min per seed, ≤ 500 k parameters.
- **Save model weights** (state_dict + optimizer/scheduler/rng) per seed so
  `--resume` works; never ship a run without its checkpoint and sidecar.
- When the user reports results, the agent reads the produced files (not only
  the console summary) and reviews them with §7 before proposing the next step.
- **Scientific validity of outputs:** every training/evaluation/export run must
  write a complete, publication-ready report (metrics with mean ± std over
  seeds, n, date range, seeds, device, wall time, git SHA, data_source, split
  hashes) and never emit placeholder/NaN-filled numbers; reports missing any of
  these fields are defects, not "done".

## 7. Critical ML/AI review checklist (apply to every method, script and result)

Act as a senior ML researcher reviewing a paper. Before building on a result,
and whenever code or reports are touched, check the items below and **warn the
user explicitly** (file:line, why it matters, what would fix it). A silent pass
is a defect.

**Data and splits**
- Leakage: test/dev data used for training, normalization statistics, early
  stopping, threshold calibration, feature selection or model choice.
- Temporal leakage: train periods overlapping the test period; future
  observations used for a past decision in a "causal"/early-warning claim.
- Spatial leakage: neighbouring fields split across train/test (shared weather,
  irrigation, management); hash-based "blocks" are not spatial blocks.
- Duplicates or near-duplicates (same field-cycle in two splits, overlapping
  cycles).
- Missing data: NaN silently filled with 0/mean and treated as observed; masks
  dropped; invalid acquisitions counted as valid.
- Band/index mistakes: wrong band index (e.g. swir2 used as LST), unit errors
  (K vs °C, scale factors), values outside physical ranges.

**Targets and evaluation**
- Synthetic or derived targets presented as real (targets built from model
  inputs plus noise, placeholder labels, `absent → zeros`).
- Circularity: the validation proxy is computed from the model's own inputs
  (e.g. CWSI from LST when the model sees LST) or the model was tuned on the
  proxy it is later validated against.
- Train/test perturbation overlap: the same injected anomaly type used as a
  pretext and as the evaluation target.
- Proxy labels named as validated ground truth; "anomaly" named "stress"
  before L4.
- Metric fit to question: AUC-ROC on heavy class imbalance (use AUC-PR), a
  metric that cannot rank methods (saturated at 1.0), threshold-dependent
  metrics without the threshold rule.

**Statistics and reporting**
- Small n, single seed, too few epochs; no seed spread or confidence interval;
  CI including zero reported as an effect.
- Missing baselines: every model result needs the simple reference (B0, B1)
  and, for SSL, a random-init encoder of the same architecture.
- Comparisons at unequal compute or parameter counts.
- Stale reports: report JSON disagrees with the findings text, n, dates, or
  current code; numbers quoted without `data_source`, n, date range, seeds,
  git SHA.
- Every claim states its validation-ladder rung (L1–L5) and nothing more.

**Code hygiene that changes results**
- `rng` / seeds not fixed or not recorded; non-determinism ignored.
- Silent fallbacks (simulator, proxy formula, default values) when real data
  or a checkpoint is missing — must fail or be labelled `absent`.
- Exceptions swallowed so a script reports success on partial work.
- Platform/OS issues that change results (e.g. Windows joblib
  PermissionError leading to an n = 1 run).
