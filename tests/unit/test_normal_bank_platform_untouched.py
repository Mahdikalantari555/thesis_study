"""Platform-untouched guard (change normal-bank-novelty-scoring, task 3.2).

Spec scenario 'No platform drift': when this change completes without an
adoption decision, ``checkpoints/gru_ae_main.json``, the registry versions
and the exported payload are byte-identical to their pre-change state. The
bank code path (embedding extraction → bank build → scoring) must not write
any of these artifacts; this test snapshots their digests, exercises the full
bank path, and asserts the digests are unchanged.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import normal_bank as nbank  # noqa: E402

T, C, D = 36, 8, 16

GUARDED_FILES = [
    REPO_ROOT / "checkpoints" / "gru_ae_main.json",
    REPO_ROOT / "checkpoints" / "gru_ae_main.pt",
    REPO_ROOT / "scripts" / "platform_channels.py",  # channel/score registry
    REPO_ROOT / "platform" / "src" / "data" / "series_khuzestan.json",  # v5 payload
    REPO_ROOT / "platform" / "src" / "data" / "farms_khuzestan.json",
    REPO_ROOT / "platform" / "src" / "data" / "desk_khuzestan.json",
]


def _digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_bank_path_leaves_platform_artifacts_byte_identical(tmp_path: Path) -> None:
    present = [p for p in GUARDED_FILES if p.exists()]
    assert present, "no guarded artifacts found — expected the frozen sidecar at least"
    before = {p: _digest(p) for p in present}

    # Full bank code path on synthetic data (tiny GRU encoder, tmp manifest).
    import torch

    from ssl_anomaly.models.gru_ae import CausalGRUAE
    from ssl_anomaly.monitor import models as mmodels

    torch.manual_seed(0)
    model = CausalGRUAE(d_in=18, n_out=8, d_model=D, n_layers=1)
    scorer = mmodels.DeepCausalScorer("gru_ae", model, use_doy=True, device="cpu")
    emb_fn = nbank.gru_embedding_fn(scorer)

    rng = np.random.default_rng(3)
    n = 12
    m = np.ones((n, T, C), dtype=bool)
    z = rng.normal(0, 1, size=(n, T, C)).astype(np.float32)
    doy = rng.normal(0, 1, size=(n, T, 2)).astype(np.float32)
    emb = emb_fn(z, m, doy)
    keys = [f"f{i}:1" for i in range(n)]
    manifest = {"cycles": {"train": keys, "dev": [], "test": [], "monitoring_only": []},
                "counts": {"train": n}}
    bank = nbank.build_bank(
        emb, m, keys, manifest, min_class_count=8, k=5, distance="knn",
        encoder_sha256="synthetic",
    )
    scores, meta = bank.score_batch(emb[:3], m[:3], None)
    assert np.isfinite(scores).any()
    assert set(np.unique(meta["fallback"])) <= {"direct", "pooled", "global", "absent"}
    man = bank.manifest()
    assert man["manifest_sha256"]
    # bank.json sidecar write goes to the caller's directory, not the repo.
    (tmp_path / "bank.json").write_text(
        __import__("json").dumps(man), encoding="utf-8")

    for p in present:
        assert _digest(p) == before[p], f"platform artifact changed by the bank path: {p}"
