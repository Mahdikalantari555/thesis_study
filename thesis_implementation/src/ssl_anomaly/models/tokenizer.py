"""Cycle tokenization for SSL.

Each cycle is represented as a sequence of tokens — one per REAL observation
(no imputation). Features per token: robust-standardized bands + optional
valid_frac, Δt since previous observation, dsh, sin/cos(DOY), sensor flag,
ratoon number, and (optional) aggregated weather.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class CycleTokenizer:
    """Builds token feature matrices from raw (irregular) cycle observations.

    Operates on numpy arrays (no torch) so the same logic can feed numpy
    baselines and parity tests.
    """

    n_bands: int
    band_names: list[str]
    include_valid_frac: bool = True
    include_dtime: bool = True
    include_dsh: bool = True
    include_doy: bool = True
    include_sensor: bool = True
    include_ratoon: bool = True
    include_weather: bool = False
    n_weather_vars: int = 0
    robust_center: np.ndarray | None = None  # (n_feat,)
    robust_scale: np.ndarray | None = None  # (n_feat,)
    dsh_max: float = 540.0

    @property
    def d_feature(self) -> int:
        d = self.n_bands
        if self.include_valid_frac:
            d += 1
        if self.include_dtime:
            d += 1
        if self.include_dsh:
            d += 2  # normalized + sqrt? we use raw dsh_max normalization
        if self.include_doy:
            d += 2  # sin/cos
        if self.include_sensor:
            d += 2  # L8/L9 one-hot
        if self.include_ratoon:
            d += 1
        if self.include_weather:
            d += self.n_weather_vars
        return d

    def fit(self, token_arrays: list[np.ndarray]) -> CycleTokenizer:
        """Estimate robust center/scale from a list of token arrays (each T_i x d_feature)."""
        if not token_arrays:
            return self
        all_tok = np.concatenate(token_arrays, axis=0)
        # Center = median, scale = MAD*1.48
        med = np.nanmedian(all_tok, axis=0)
        mad = np.nanmedian(np.abs(all_tok - med), axis=0) * 1.4826
        mad[mad < 1e-6] = 1.0
        self.robust_center = med
        self.robust_scale = mad
        return self

    def standardize(self, tokens: np.ndarray) -> np.ndarray:
        if self.robust_center is None or self.robust_scale is None:
            return tokens
        return (tokens - self.robust_center) / self.robust_scale

    def tokenize(
        self,
        bands: np.ndarray,  # (T, B) — observed band values
        times: np.ndarray,  # (T,) datetime64 or days-since-epoch
        dsh: np.ndarray,  # (T,) days-since-harvest
        *,
        valid_frac: np.ndarray | None = None,
        sensor: np.ndarray | None = None,  # (T,) string "L8"/"L9"
        ratoon_no: int = 0,
        weather: np.ndarray | None = None,  # (T, W) aggregated between obs
        doy: np.ndarray | None = None,
    ) -> np.ndarray:
        """Produce (T, d_feature) float32 token matrix for one cycle."""
        bands = np.asarray(bands, dtype=np.float32)
        T, B = bands.shape
        assert self.n_bands == B, f"expected {self.n_bands} bands, got {B}"
        feats = [bands]
        if self.include_valid_frac:
            v = np.asarray(valid_frac, dtype=np.float32)[:, None] if valid_frac is not None else np.ones((T, 1), dtype=np.float32)
            feats.append(v)
        if self.include_dtime:
            # Δt from previous observation (days); first token uses mean spacing
            t_num = np.asarray(times, dtype="datetime64[D]").astype(np.float64) if np.issubdtype(np.asarray(times).dtype, np.datetime64) else np.asarray(times, dtype=np.float64)
            if T > 1:
                dt = np.diff(t_num, prepend=t_num[0])
                dt[0] = np.median(np.diff(t_num)) if T > 1 else 16.0
            else:
                dt = np.array([16.0], dtype=np.float64)
            feats.append((dt / 30.0).astype(np.float32)[:, None])
        if self.include_dsh:
            d = np.asarray(dsh, dtype=np.float32)
            # Normalize dsh by typical cycle length and include sqrt for growth-curve-like transform
            d_norm = np.clip(d / self.dsh_max, 0.0, 1.5)
            feats.append(d_norm[:, None])
            feats.append(np.sqrt(d_norm)[:, None])
        if self.include_doy:
            if doy is None:
                # Derive DOY from times if datetime64
                t64 = np.asarray(times)
                if np.issubdtype(t64.dtype, np.datetime64):
                    doy = (t64.astype("datetime64[D]") - t64.astype("datetime64[Y]")).astype(int) + 1
                else:
                    doy = np.zeros(T, dtype=np.float32)
            else:
                doy = np.asarray(doy, dtype=np.float32)
            angle = 2 * np.pi * doy / 365.25
            feats.append(np.stack([np.sin(angle), np.cos(angle)], axis=1).astype(np.float32))
        if self.include_sensor:
            s = np.asarray(sensor) if sensor is not None else np.full(T, "L8", dtype=object)
            l8 = (s == "L8").astype(np.float32)[:, None]
            l9 = (s == "L9").astype(np.float32)[:, None]
            feats.append(np.hstack([l8, l9]))
        if self.include_ratoon:
            feats.append(np.full((T, 1), float(ratoon_no) / 10.0, dtype=np.float32))
        if self.include_weather:
            if weather is None:
                weather = np.zeros((T, self.n_weather_vars), dtype=np.float32)
            else:
                weather = np.asarray(weather, dtype=np.float32)
            feats.append(weather)
        tokens = np.concatenate(feats, axis=1).astype(np.float32)
        return tokens


def tokenize_cycle(
    field_series: dict,  # keys: bands, times, dsh, valid_frac, sensor, ratoon_no, weather
    tokenizer: CycleTokenizer,
) -> np.ndarray:
    return tokenizer.tokenize(
        bands=field_series["bands"],
        times=field_series["times"],
        dsh=field_series["dsh"],
        valid_frac=field_series.get("valid_frac"),
        sensor=field_series.get("sensor"),
        ratoon_no=int(field_series.get("ratoon_no", 0)),
        weather=field_series.get("weather"),
        doy=field_series.get("doy"),
    )


def mask_tokens(
    tokens: np.ndarray,
    mask_ratio: float = 0.25,
    block_max: int = 3,
    block_p: float = 0.3,
    mask_value: float = 0.0,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply masking: random tokens + short consecutive blocks (mimic cloud gaps).

    Returns (masked_tokens, mask_bool) where mask_bool is True for MASKED positions.
    """
    rng = rng or np.random.default_rng()
    T = tokens.shape[0]
    masked = tokens.copy()
    mask = np.zeros(T, dtype=bool)

    n_rand = int(mask_ratio * T)
    if n_rand > 0:
        rand_idx = rng.choice(T, size=n_rand, replace=False)
        mask[rand_idx] = True

    # Consecutive blocks
    if block_max > 1 and block_max < T:
        n_blocks = max(1, int(block_p * T / block_max))
        for _ in range(n_blocks):
            L = rng.integers(1, block_max + 1)
            start = rng.integers(0, T - L + 1)
            mask[start : start + L] = True

    masked[mask] = mask_value
    return masked, mask
