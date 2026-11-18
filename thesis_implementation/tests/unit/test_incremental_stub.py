"""Incremental-training stub (task 9.1): exists, documented, raises."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.train.incremental import fine_tune  # noqa: E402


def test_fine_tune_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="docs/vision.md"):
        fine_tune("checkpoints/masked_transformer_main.pt", object(), trim_top_frac=0.1)


def test_docstring_documents_trim_and_active_learning() -> None:
    import ssl_anomaly.train.incremental as mod

    doc = mod.fine_tune.__doc__ or ""
    assert "trim" in doc.lower()
    src = (Path(mod.__file__).read_text(encoding="utf-8")).lower()
    assert "active learning" in src or "active-learning" in src
    assert "docs/vision.md" in src
