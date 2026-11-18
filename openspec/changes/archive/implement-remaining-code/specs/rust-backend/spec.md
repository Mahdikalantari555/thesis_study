# Spec Delta

## Purpose

Provide an accelerated PyO3/maturin Rust backend implementing the phenology backend contract with verified numerical parity against the NumPy reference backend.

## ADDED Requirements

### Requirement: PyO3 backend binding
The Rust extension module SHALL expose a `RustBackend` class implementing `robust_baseline` on 3-D `(cycles, bins, bands)` arrays and `whittaker_batch` on batched signals with missing-value handling.

#### Scenario: Backend selection
- **WHEN** `get_backend("rust")` is invoked with the compiled extension installed
- **THEN** it returns a `RustBackend` instance whose methods accept the same inputs and shapes as `NumpyBackend`

### Requirement: Maturin build configuration
The Rust directory SHALL include a `pyproject.toml` maturin configuration enabling repeatable local builds and wheel installation on Linux/WSL and Windows.

#### Scenario: Maturin development install
- **WHEN** `maturin develop` is executed against the Rust crate
- **THEN** the compiled `ssl_anomaly_rs` extension module is installed into the active Python environment

### Requirement: Numerical parity with NumPy
Both `robust_baseline` and `whittaker_batch` in the Rust backend MUST match the NumPy reference backend within a relative tolerance of `1e-6`, including NaN and under-sampled bin behavior.

#### Scenario: Randomized parity suite
- **WHEN** parity tests run across randomized cycle tensors with NaNs and batched irregular signals
- **THEN** Rust outputs match NumPy outputs within `rtol=1e-6`
