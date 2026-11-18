## ADDED Requirements

### Requirement: Patch tensor store

The canonical `Data/Processed/satellite/patches.zarr` SHALL store patches for
admitted field-cycles, with the eight B1 channels, observation and polygon masks,
bounding-box origins, observation counts and sensor IDs. Training-compatible
stores SHALL record the verified source cycle and split hashes, stable cycle IDs,
epoch and offsets. Bins SHALL use only acquisitions inside the source cycle.

#### Scenario: Geometry is field-aligned

- **WHEN** patches are extracted for a field
- **THEN** the patch is the field's bounding box cropped from the scene and
  padded to 32×32, the stored polygon mask excludes pixels of neighbouring
  fields, and no resampling of pixel values occurs. The channels are NDVI,
  blue, green, red, NIR, SWIR1, SWIR2 and LST, stored with per-bin counts and
  majority sensor ID.

#### Scenario: A cycle ends before the patch grid

- **WHEN** the source cycle is `[t_start, t_end)` and the fixed patch grid extends
  into the next cycle
- **THEN** `cycle_start_day` and `cycle_end_day` are the inclusive bounds
  `t_start` and `t_end - 1`, and acquisitions on or after `t_end` cannot enter
  its bins. A training or normalization consumer rejects counts recorded in
  bins wholly past that bound.

#### Scenario: Invalid pixels stay invalid

- **WHEN** a pixel fails the QA mask (io/landsat.py quality_mask) in every
  acquisition inside a bin
- **THEN** the stored value for that pixel-bin is NaN, pixel_valid is 0,
  and no interpolation or zero-fill is stored. Model fills are only allowed
  under the observation mask; they never become fitting or scoring targets.

### Requirement: Leakage-free frozen normalization

The `stats` sidecar SHALL contain per-channel, per-sensor median and IQR
from verified, admissible locked train cycles only. It SHALL record the locked
split and holdout hashes and its own SHA-256. Training and scoring SHALL load
that frozen artifact, not refit it or accept a malformed or incompatible
sidecar.

#### Scenario: Normalization never sees dev/test statistics

- **WHEN** the normalization artifact is built
- **THEN** only train-split fields inside train periods contribute, the
  artifact records the splits sha and its own sha256, and perturbing a dev
  or test field's values does not change the artifact

#### Scenario: A frozen channel scale is available

- **WHEN** a patch is loaded for training or scoring with matching preprocessing
  provenance and a valid per-sensor median and positive IQR
- **THEN** the observed values are transformed by `(x - median) / IQR`, missing
  pixels remain unobserved, and no consumer refits or ignores the scale

### Requirement: Exporter operability

The exporter SHALL support `--smoke` (tiny subset with verified shapes and
counts), `--estimate-runtime` (measured extrapolation printed BEFORE any
full run), and `--resume` (per-field completion manifest; completed fields
skipped), SHALL run on CPU, and SHALL write a provenance manifest (source
products, QA bit list, scale factors, git sha, cycles sha, splits sha,
output sha256). Failures SHALL abort with a non-zero exit and a verbatim
error message — never a partial-success report.

#### Scenario: Smoke before full run

- **WHEN** the agent hands over the full extraction command
- **THEN** a `--smoke` run has been executed and reviewed first (shapes, QA
  fraction plausibility, bin coverage, zero NaN inside valid regions)

#### Scenario: Interrupted extraction resumes

- **WHEN** the exporter is interrupted and relaunched with `--resume`
- **THEN** completed fields are skipped and the final store equals an
  uninterrupted run's store for the same inputs; changes to the locked cycle
  binding, scene selection, mask, patch size or scale mode require a new store
