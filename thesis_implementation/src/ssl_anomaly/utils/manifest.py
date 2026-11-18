"""SQLite-based checkpoint manifest for per-item (scene/cycle/fold) resume.

Provides crash-safe, atomic status tracking so long-running pipelines can
resume without redoing work. Schema is intentionally tiny — one table
``items`` with ``(key, status, seconds, error, updated_at)``.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

STATUS_PENDING = "pending"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_RUNNING = "running"


class Manifest:
    """SQLite manifest for per-item checkpoint/resume.

    Parameters
    ----------
    path:
        Path to the SQLite file. Created if missing.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                key TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                seconds REAL NOT NULL DEFAULT 0.0,
                error TEXT,
                updated_at REAL NOT NULL
            )
            """
        )

    # ---- queries -------------------------------------------------------
    def status(self, key: str) -> str | None:
        cur = self._db.execute("SELECT status FROM items WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def is_done(self, key: str) -> bool:
        return self.status(key) == STATUS_DONE

    def pending(self, keys: Iterable[str]) -> list[str]:
        """Return the subset of ``keys`` not yet marked done."""
        keys = list(keys)
        if not keys:
            return []
        done: set[str] = set()
        # Use parameterized IN (chunk to avoid giant SQL)
        for chunk_start in range(0, len(keys), 500):
            chunk = keys[chunk_start : chunk_start + 500]
            qmarks = ",".join("?" * len(chunk))
            cur = self._db.execute(
                f"SELECT key FROM items WHERE key IN ({qmarks}) AND status = ?",
                (*chunk, STATUS_DONE),
            )
            done.update(r[0] for r in cur.fetchall())
        return [k for k in keys if k not in done]

    def failures(self) -> list[tuple[str, str]]:
        cur = self._db.execute("SELECT key, error FROM items WHERE status = ?", (STATUS_FAILED,))
        return [(r[0], r[1] or "") for r in cur.fetchall()]

    # ---- mutations -----------------------------------------------------
    def mark(self, key: str, status: str, seconds: float = 0.0, error: str | None = None) -> None:
        self._db.execute(
            """
            INSERT INTO items(key, status, seconds, error, updated_at)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                status = excluded.status,
                seconds = excluded.seconds,
                error = excluded.error,
                updated_at = excluded.updated_at
            """,
            (key, status, float(seconds), error, time.time()),
        )

    def mark_done(self, key: str, seconds: float = 0.0) -> None:
        self.mark(key, STATUS_DONE, seconds=seconds)

    def mark_failed(self, key: str, error: str, seconds: float = 0.0) -> None:
        self.mark(key, STATUS_FAILED, seconds=seconds, error=error)

    def reset(self, key: str) -> None:
        self._db.execute("DELETE FROM items WHERE key = ?", (key,))

    def reset_failed(self) -> int:
        cur = self._db.execute("DELETE FROM items WHERE status = ?", (STATUS_FAILED,))
        return cur.rowcount

    @contextmanager
    def run(self, key: str) -> Iterator[None]:
        """Context manager: marks key running, done on success, failed on exception."""
        t0 = time.time()
        self.mark(key, STATUS_RUNNING)
        try:
            yield
        except Exception as exc:
            self.mark_failed(key, repr(exc), seconds=time.time() - t0)
            raise
        else:
            self.mark_done(key, seconds=time.time() - t0)

    # ---- lifecycle -----------------------------------------------------
    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Manifest:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
