"""Tests for SQLite checkpoint manifest."""

from __future__ import annotations

from ssl_anomaly.utils.manifest import STATUS_FAILED, Manifest


def test_mark_done_and_pending(tmp_path):
    m = Manifest(tmp_path / "mf.sqlite")
    assert m.pending(["a", "b", "c"]) == ["a", "b", "c"]
    m.mark_done("a")
    assert m.pending(["a", "b", "c"]) == ["b", "c"]
    assert m.is_done("a")
    assert not m.is_done("b")


def test_context_marks_failure(tmp_path):
    m = Manifest(tmp_path / "mf.sqlite")
    try:
        with m.run("x"):
            raise ValueError("boom")
    except ValueError:
        pass
    assert m.status("x") == STATUS_FAILED
    assert "boom" in (m.failures()[0][1])


def test_reset_and_reset_failed(tmp_path):
    m = Manifest(tmp_path / "mf.sqlite")
    m.mark_failed("a", "err1")
    m.mark_done("b")
    assert m.pending(["a", "b"]) == ["a"]
    n = m.reset_failed()
    assert n == 1
    assert m.pending(["a", "b"]) == ["a"]
