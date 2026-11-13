from __future__ import annotations

import os

import numpy as np

from ssl_anomaly.utils.seeds import seed_everything


def test_seed_reproducibility():
    seed_everything(123)
    a = np.random.rand(5)
    seed_everything(123)
    b = np.random.rand(5)
    np.testing.assert_array_equal(a, b)
    assert os.environ["PYTHONHASHSEED"] == "123"
