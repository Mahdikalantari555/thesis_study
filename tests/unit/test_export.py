from __future__ import annotations

import torch
from torch import nn

from ssl_anomaly.export import export_release, load_release


class TinyModel(nn.Module):
    def __init__(self, d_in=4, d=8):
        super().__init__()
        self.fc = nn.Linear(d_in, d)
        self.out = nn.Linear(d, d_in)

    def forward(self, x):
        return self.out(torch.relu(self.fc(x)))


def test_export_roundtrip(tmp_path):
    torch.manual_seed(0)
    model = TinyModel()
    release_dir = tmp_path / "release"
    cfg = {"d_in": 4, "d": 8, "arch": "tiny"}
    norm = {"band_names": ["b0", "b1"], "center": [0.0, 0.0], "scale": [1.0, 1.0]}
    export_release(model, cfg, norm, out_dir=release_dir, seed=42)
    assert (release_dir / "model.safetensors").exists()
    assert (release_dir / "norm_stats.json").exists()
    assert (release_dir / "meta.json").exists()

    def build(c):
        assert c["arch"] == "tiny"
        return TinyModel(c["d_in"], c["d"])

    m2, norm2, meta = load_release(build, release_dir)
    assert isinstance(m2, TinyModel)
    assert m2.fc.weight.shape == model.fc.weight.shape
    # Weights match
    torch.testing.assert_close(m2.fc.weight, model.fc.weight)
    assert norm2["band_names"] == ["b0", "b1"]


def test_load_missing_norm_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        load_release(lambda c: TinyModel(), tmp_path / "nope")
