# ssl_anomaly_rs (Gate G3 Rust Acceleration)

PyO3 + `numpy` + `ndarray` Rust extension implementing the `PhenologyBackend`
interface (`ssl_anomaly.backends.get_backend("rust")`):

- `RustBackend.robust_baseline(X, min_n=5)`: per-`(bin, band)` median and scaled
  MAD (`MAD * 1.4826`) over 3-D `(cycles, bins, bands)` arrays with NaN filtering
  and `min_n` masking.
- `RustBackend.whittaker_batch(y, w, lam)`: exact $O(T)$ symmetric pentadiagonal
  $\text{LDL}^\top$ solver for second-order Whittaker-Eilers smoothing ($d = 2$)
  over batched `(B, T)` irregular time series.
- Standalone functions `ssl_anomaly_rs.robust_baseline` and
  `ssl_anomaly_rs.whittaker_batch` are also exported at the module root.

## Prerequisites

- Python `>=3.11,<3.13` with project virtualenv (`.venv`) activated
- Rust toolchain (`rustc` + `cargo`, edition 2021)
- `maturin >= 1.5` (`uv pip install maturin`)

## Build & Install (WSL / Linux)

```bash
# Activate project virtualenv from repo root
source .venv/bin/activate
uv pip install maturin

# 1. Verify standalone Rust release build
cargo build --release --manifest-path rust/Cargo.toml

# 2. Build wheel and install into active virtualenv
maturin develop --release --manifest-path rust/Cargo.toml
```

## Build & Install (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
uv pip install maturin
cargo build --release --manifest-path rust\Cargo.toml
maturin develop --release --manifest-path rust\Cargo.toml
```

## Parity Verification

`tests/parity/test_backends_parity.py` enforces numerical agreement against
`NumpyBackend` within `rtol=1e-6` across 20 randomized seeds for both
`robust_baseline` and `whittaker_batch`:

```bash
pytest tests/parity -m parity
```
