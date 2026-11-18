from __future__ import annotations

import numpy as np

from ssl_anomaly.models.tokenizer import CycleTokenizer, mask_tokens, tokenize_cycle


def test_tokenizer_output_shape():
    n_bands = 7
    tok = CycleTokenizer(
        n_bands=n_bands,
        band_names=[f"b{i}" for i in range(n_bands)],
        include_valid_frac=True, include_dtime=True, include_dsh=True,
        include_doy=True, include_sensor=True, include_ratoon=True,
        include_weather=False,
    )
    T = 20
    bands = np.random.default_rng(0).normal(0, 1, size=(T, n_bands)).astype(np.float32)
    times = np.datetime64("2020-01-01") + np.arange(T, dtype="timedelta64[8D]")
    dsh = np.arange(0, T * 8, 8)
    tokens = tok.tokenize(bands=bands, times=times, dsh=dsh, sensor=np.array(["L8"] * T), ratoon_no=2)
    assert tokens.shape == (T, tok.d_feature)
    assert tokens.dtype == np.float32


def test_mask_tokens_ratio():
    rng = np.random.default_rng(0)
    T = 100
    d = 5
    tokens = rng.normal(0, 1, size=(T, d)).astype(np.float32)
    masked, mask = mask_tokens(tokens, mask_ratio=0.3, block_max=1, block_p=0.0, rng=rng)
    assert mask.shape == (T,)
    assert 0.25 < mask.mean() < 0.45
    # Masked positions should be set to 0
    assert np.all(masked[mask] == 0.0)


def test_mask_tokens_blocks():
    rng = np.random.default_rng(1)
    T = 100
    tokens = rng.normal(0, 1, size=(T, 3)).astype(np.float32)
    _, mask = mask_tokens(tokens, mask_ratio=0.0, block_max=3, block_p=0.5, rng=rng)
    # Check there is at least one block of >=2 consecutive True
    found_block = False
    run = 0
    for v in mask:
        run = run + 1 if v else 0
        if run >= 2:
            found_block = True
            break
    assert found_block


def test_tokenize_cycle_helper():
    tok = CycleTokenizer(n_bands=2, band_names=["a", "b"], include_valid_frac=False,
                         include_dtime=False, include_dsh=False, include_doy=False,
                         include_sensor=False, include_ratoon=False)
    rec = {
        "bands": np.ones((5, 2), dtype=np.float32),
        "times": np.datetime64("2020-01-01") + np.arange(5, dtype="timedelta64[8D]"),
        "dsh": np.arange(0, 40, 8),
    }
    out = tokenize_cycle(rec, tok)
    assert out.shape == (5, 2)
