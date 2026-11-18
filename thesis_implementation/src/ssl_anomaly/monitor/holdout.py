"""Frozen training-holdout manifest and fail-closed enforcement.

Change ``training-holdout-invariant`` (owner directive 2026-11-15): farms and
dates completely excluded from training are identified and frozen BEFORE
implementation, and every training consumer proves at runtime that no holdout
farm or holdout-period cycle reaches it.

The manifest is a **pure derivation** of the locked splits
(``data/processed/splits_locked.json``, ``9aa5eb11…``) — no new split
semantics are invented here:

- ``holdout_farms``    = the locked ``kmeans.test_block_fields`` (whole-field
  spatial holdout, including members with no eligible test rows).
- ``holdout_date_start`` = the locked ``test_period_start`` (2024-01-01):
  temporal holdout for every other field.
- future-by-default   = any farm id absent from ``known_farm_ids`` (fields
  registered after the archive freeze) and any observation after
  ``archive_end_date`` are holdout, per the 2026-11-14 product vision.

Enforcement is fail-closed: :func:`assert_train_only` raises
:class:`HoldoutViolationError` naming the offending ``(field, cycle)`` pairs
and never degrades to a warning.

Per-pixel patch stores legitimately contain holdout fields (evaluation needs
them); the invariant therefore applies **at the training consumer**, not at
extraction. See ``patch-data-pipeline`` and
``patch-level-controlled-trial`` tasks 1.3/1.4.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

log = logging.getLogger("ssl_anomaly.monitor.holdout")

REPO_ROOT = Path(__file__).resolve().parents[3]
HOLDOUT_MANIFEST_PATH = REPO_ROOT / "data/processed/holdout_manifest.json"

MANIFEST_VERSION = 1
REBUILD_HINT = (
    "the holdout manifest is derived once from the locked splits; rebuild it "
    "only with scripts/build_holdout_manifest.py --force --reason <reason>"
)

# Split-manifest keys whose union defines the farms known at freeze time.
_SPLIT_FIELD_KEYS = (
    "train_fields",
    "dev_fields",
    "test_fields",
    "monitoring_only_fields",
)


class HoldoutViolationError(RuntimeError):
    """A holdout farm or holdout-period cycle reached a training consumer."""


# ---------------------------------------------------------------------------
# Hashing (mirrors monitor/splits.py so the two manifests behave identically)
# ---------------------------------------------------------------------------
def holdout_manifest_hash(manifest: dict) -> str:
    """SHA-256 over the manifest with the ``manifest_sha256`` key removed."""
    payload = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------
def _known_farm_ids(splits_manifest: dict) -> list[int]:
    known: set[int] = set()
    for key in _SPLIT_FIELD_KEYS:
        known.update(int(f) for f in splits_manifest.get(key, ()) or ())
    # The k-means block members are the authoritative membership lists; the
    # {split}_fields arrays above are row-derived, so union both to be safe.
    kmeans = splits_manifest.get("kmeans", {}) or {}
    for key in ("test_block_fields", "dev_block_fields"):
        known.update(int(f) for f in kmeans.get(key, ()) or ())
    return sorted(known)


def _test_block_fields(splits_manifest: dict) -> set[int]:
    block = (splits_manifest.get("kmeans") or {}).get("test_block_fields")
    if not block:
        raise ValueError(
            "locked splits manifest has no kmeans.test_block_fields; refusing to infer "
            "spatial holdout from the row-derived test_fields"
        )
    return {int(f) for f in block}


def _frozen_day(value: Any, label: str) -> pd.Timestamp:
    day = pd.Timestamp(value)
    if pd.isna(day) or day.tzinfo is not None:
        raise ValueError(f"{label} must be a valid calendar date")
    return day.normalize()


def audit_frozen_holdout(manifest: dict, splits_manifest: dict) -> dict:
    """Compare a hash-verified freeze against its locked source without modifying it."""
    spatial = _test_block_fields(splits_manifest)
    frozen = {int(f) for f in manifest["holdout_farms"]}
    source = splits_manifest.get("manifest_sha256")
    return {
        "holdout_manifest_sha256": manifest.get("manifest_sha256"),
        "splits_manifest_sha256": source,
        "source_matches": bool(source) and (
            manifest.get("derived_from", {}).get("splits_manifest_sha256") == source
        ),
        "cutoff_matches": _frozen_day(manifest["holdout_date_start"], "holdout_date_start")
        == _frozen_day(splits_manifest["test_period_start"], "test_period_start"),
        "missing_spatial_fields": sorted(spatial - frozen),
        "extra_frozen_fields": sorted(frozen - spatial),
    }


def assert_frozen_holdout_matches_splits(manifest: dict, splits_manifest: dict) -> None:
    audit = audit_frozen_holdout(manifest, splits_manifest)
    if (
        not audit["source_matches"]
        or not audit["cutoff_matches"]
        or audit["missing_spatial_fields"]
        or not manifest.get("known_farm_ids")
    ):
        raise HoldoutViolationError(
            f"Frozen holdout disagrees with locked splits: {audit}. "
            "Run scripts/build_holdout_manifest.py --audit-existing; "
            "do not regenerate or weaken the freeze automatically."
        )


def build_holdout_manifest(
    splits_manifest: dict,
    *,
    created: str | None = None,
    archive_end_date: str | None = None,
) -> dict:
    """Derive the frozen holdout manifest from a locked splits manifest.

    Pure function: same input ⇒ byte-identical output (apart from ``created``).
    No new split semantics are introduced — the farm and date sets are exactly
    the locked assignment's test farms and test-period start.
    """
    if "test_period_start" not in splits_manifest:
        raise KeyError("locked splits manifest is missing test_period_start")

    test_fields = sorted(_test_block_fields(splits_manifest))
    known = _known_farm_ids(splits_manifest)
    if not known:
        raise ValueError(
            "locked splits manifest exposes no *_fields lists; refusing to build a "
            "holdout manifest that cannot detect future (unknown) fields"
        )
    date_start = _frozen_day(splits_manifest["test_period_start"], "test_period_start").date().isoformat()
    end_date = None
    if archive_end_date is not None:
        end_date = _frozen_day(archive_end_date, "archive_end_date").date().isoformat()

    manifest: dict[str, Any] = {
        "version": MANIFEST_VERSION,
        "created": created or pd.Timestamp.now().strftime("%Y-%m-%d"),
        "derived_from": {
            "source": "data/processed/splits_locked.json",
            "splits_manifest_sha256": splits_manifest.get("manifest_sha256"),
            "splits_created": splits_manifest.get("created"),
            "test_period_start": date_start,
            "n_test_fields": len(test_fields),
            "n_known_farms": len(known),
            "rule": ("holdout_farms = locked kmeans.test_block_fields (whole-field, all periods); "
                     "holdout_date_start = locked test_period_start (temporal holdout "
                     "for every other field) — no new split semantics"),
        },
        "holdout_farms": test_fields,
        "holdout_date_start": date_start,
        "archive_end_date": end_date,
        "known_farm_ids": known,
        "future_fields_rule": (
            "holdout by default — any farm id absent from known_farm_ids was registered "
            "after the archive freeze and never enters training"
        ),
        "future_dates_rule": (
            "holdout by default — any acquisition after archive_end_date "
            "is reserved for validation"
        ),
    }
    manifest["manifest_sha256"] = holdout_manifest_hash(manifest)
    return manifest


# ---------------------------------------------------------------------------
# Save / load
# ---------------------------------------------------------------------------
def save_holdout_manifest(
    manifest: dict,
    *,
    path: Path = HOLDOUT_MANIFEST_PATH,
    force: bool = False,
    reason: str | None = None,
) -> Path:
    """Write the manifest; refuse to overwrite without ``--force <reason>``.

    The locked-splits discipline applies verbatim: replacing the frozen
    manifest requires an explicit reason, which is recorded inside the new
    manifest (``rebuild_of``) rather than lost.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(
            f"holdout manifest already exists at {path}; {REBUILD_HINT}"
        )
    if force and not (reason and reason.strip()):
        raise ValueError("--force requires a non-empty --reason")
    if force and path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            manifest = dict(manifest)
            manifest["rebuild_of"] = {
                "previous_manifest_sha256": previous.get("manifest_sha256"),
                "previous_created": previous.get("created"),
                "reason": reason.strip(),
                "rebuilt_on": manifest.get("created"),
            }
            manifest["manifest_sha256"] = holdout_manifest_hash(manifest)
        except json.JSONDecodeError:  # pragma: no cover - corrupt file
            log.warning("previous holdout manifest unreadable; rebuild recorded without it")
    path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    log.info("wrote holdout manifest %s (sha256 %s)", path, manifest["manifest_sha256"][:12])
    return path


def load_holdout_manifest(
    *,
    path: Path = HOLDOUT_MANIFEST_PATH,
    verify: bool = True,
) -> dict:
    """Load the frozen manifest, verifying its self-hash (fail-closed)."""
    path = Path(path)
    if not path.exists():
        raise RuntimeError(
            f"holdout manifest missing at {path}. Build it once with "
            "`python scripts/build_holdout_manifest.py`; training paths refuse to start "
            "without it (training-holdout-invariant, fail-closed)."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if verify:
        expected = manifest.get("manifest_sha256")
        if not expected or holdout_manifest_hash(manifest) != expected:
            raise RuntimeError(
                f"holdout manifest at {path} failed its self-hash check — the file was "
                "modified after freezing. Refusing to train (fail-closed). " + REBUILD_HINT
            )
    return manifest


# ---------------------------------------------------------------------------
# Cycle / date helpers
# ---------------------------------------------------------------------------
def split_cycle_key(key: str) -> tuple[int, str]:
    """Split ``"<field>:<cycle_id>"`` into ``(field_id, cycle_id)``."""
    field, _, cycle = str(key).partition(":")
    try:
        return int(field), cycle
    except ValueError as exc:  # pragma: no cover - malformed key
        raise ValueError(f"malformed cycle key {key!r}; expected '<field>:<cycle_id>'") from exc


def _normalize_dates(values: Sequence[Any] | np.ndarray) -> pd.DatetimeIndex:
    """Coerce str / datetime64 / Timestamp values to a normalized DatetimeIndex."""
    return pd.DatetimeIndex(pd.to_datetime(list(values), format="mixed", errors="coerce")).normalize()


def _cycle_date_bounds(n: int, starts, ends):
    if starts is None:
        if ends is not None:
            raise ValueError("cycle_end_dates require cycle_start_dates")
        return None
    dates = _normalize_dates(starts)
    end_dates = dates if ends is None else _normalize_dates(ends)
    if len(dates) != n or len(end_dates) != n:
        raise ValueError("cycle_start_dates/cycle_end_dates length must match field_ids length")
    return dates, end_dates


def train_only_mask(
    field_ids: Iterable[int],
    cycle_start_dates: Sequence[Any] | None = None,
    *,
    cycle_end_dates: Sequence[Any] | None = None,
    manifest: dict | None = None,
) -> np.ndarray:
    """Boolean mask: True where a (field, cycle) pair is admissible for training.

    A pair is inadmissible when its farm is a holdout farm, is unknown at
    freeze time (future-by-default), or its observation window touches the
    holdout period or extends after the archive end. Point checks reuse the
    start date as the end; cycle consumers supply both bounds.
    """
    manifest = manifest if manifest is not None else load_holdout_manifest()
    fields = np.asarray(list(field_ids), dtype=np.int64)
    mask = np.ones(fields.shape, dtype=bool)

    holdout_farms = {int(f) for f in manifest.get("holdout_farms", ())}
    known_farms = {int(f) for f in manifest.get("known_farm_ids", ())}
    if holdout_farms:
        mask &= ~np.isin(fields, list(holdout_farms))
    if known_farms:
        mask &= np.isin(fields, list(known_farms))

    bounds = _cycle_date_bounds(len(fields), cycle_start_dates, cycle_end_dates)
    if bounds is not None:
        starts, ends = bounds
        mask &= starts.notna() & ends.notna() & (starts <= ends)
        date_start = manifest.get("holdout_date_start")
        if date_start:
            mask &= ends < _frozen_day(date_start, "holdout_date_start")
        archive_end = manifest.get("archive_end_date")
        if archive_end:
            mask &= ends <= _frozen_day(archive_end, "archive_end_date")
    return mask


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------
def assert_train_only(
    field_ids: Iterable[int] | None = None,
    cycle_keys: Sequence[str] | None = None,
    cycle_start_dates: Sequence[Any] | None = None,
    *,
    cycle_end_dates: Sequence[Any] | None = None,
    manifest: dict | None = None,
    context: str = "",
    max_listed: int = 8,
) -> None:
    """Raise :class:`HoldoutViolationError` if any input touches the holdout.

    Parameters
    ----------
    field_ids
        Farm ids about to enter training. May be omitted when ``cycle_keys``
        are given (the field id is parsed from the key).
    cycle_keys
        ``"<field>:<cycle_id>"`` keys, for naming the offending pairs.
    cycle_start_dates
        Cycle start dates aligned with ``field_ids`` (or with ``cycle_keys``),
        used for the temporal holdout check.
    cycle_end_dates
        Inclusive latest dates, mandatory for cycle consumers; omitted only
        for point-date or farm-only assertions.
    manifest
        Pre-loaded manifest (loaded hash-verified when omitted).
    context
        Names the calling training path in the error message.

    The check is fail-closed and never a warning: a violation aborts training
    before the first batch.
    """
    manifest = manifest if manifest is not None else load_holdout_manifest()

    fields = None if field_ids is None else [int(f) for f in field_ids]
    if fields is None:
        if not cycle_keys:
            raise ValueError("assert_train_only needs field_ids or cycle_keys")
        fields = [split_cycle_key(k)[0] for k in cycle_keys]
    if cycle_keys is not None and len(cycle_keys) != len(fields):
        raise ValueError(
            f"cycle_keys length {len(cycle_keys)} != field_ids length {len(fields)}"
        )

    holdout_farms = {int(f) for f in manifest.get("holdout_farms", ())}
    known_farms = {int(f) for f in manifest.get("known_farm_ids", ())}
    date_start = manifest.get("holdout_date_start")
    archive_end = manifest.get("archive_end_date")

    bounds = _cycle_date_bounds(len(fields), cycle_start_dates, cycle_end_dates)
    cutoff = _frozen_day(date_start, "holdout_date_start") if date_start else None
    last = _frozen_day(archive_end, "archive_end_date") if archive_end else None

    def _pair(i: int, why: str) -> str:
        key = cycle_keys[i] if cycle_keys is not None else f"{fields[i]}:?"
        return f"{key} ({why})"

    violations: list[str] = []
    for i, fid in enumerate(fields):
        reasons: list[str] = []
        if fid in holdout_farms:
            reasons.append("holdout farm")
        elif known_farms and fid not in known_farms:
            reasons.append("farm unknown at freeze (future-by-default holdout)")
        if bounds is not None:
            start, end = bounds[0][i], bounds[1][i]
            if pd.isna(start) or pd.isna(end) or start > end:
                reasons.append("missing or inverted date bounds")
            elif cutoff is not None and end >= cutoff:
                reasons.append(f"cycle touches the holdout period (>= {date_start})")
            elif last is not None and end > last:
                reasons.append(f"cycle extends after the archive end ({archive_end})")
        if reasons:
            violations.append(_pair(i, "; ".join(reasons)))

    if violations:
        where = f" in {context}" if context else ""
        shown = violations[:max_listed]
        more = f" … (+{len(violations) - len(shown)} more)" if len(violations) > len(shown) else ""
        raise HoldoutViolationError(
            f"Holdout leak{where}: {len(violations)} training input(s) touch the frozen "
            f"holdout — {'; '.join(shown)}{more}. Training aborted before the first batch "
            "(training-holdout-invariant, fail-closed). Holdout farms are the locked "
            "test-block fields (all periods) and every cycle touching dates on/after "
            f"{date_start}; test cycles may only be read by "
            "scripts/freeze_main_model.py --final-test."
        )


def filter_train_only(
    field_ids: Iterable[int],
    cycle_keys: Sequence[str],
    cycle_start_dates: Sequence[Any] | None = None,
    *,
    cycle_end_dates: Sequence[Any] | None = None,
    manifest: dict | None = None,
    context: str = "",
) -> list[str]:
    """Return the ``cycle_keys`` admissible for training (holdout removed).

    Pair this with :func:`assert_train_only` on the RESULT to prove the filter
    actually removed everything — the filter alone is not an enforcement
    point (silent filtering is how leaks hide).
    """
    manifest = manifest if manifest is not None else load_holdout_manifest()
    fields = [int(f) for f in field_ids]
    if len(cycle_keys) != len(fields):
        raise ValueError("cycle_keys length must match field_ids length")
    mask = train_only_mask(
        fields, cycle_start_dates, cycle_end_dates=cycle_end_dates, manifest=manifest
    )
    kept = [k for k, ok in zip(cycle_keys, mask) if ok]
    if context:
        log.info(
            "holdout filter %s: kept %d/%d cycles", context, len(kept), len(cycle_keys),
        )
    return kept


# ---------------------------------------------------------------------------
# Dataset-level guard (shared base for every future trainer)
# ---------------------------------------------------------------------------
class HoldoutGuard:
    """Mixin-style guard every training Dataset inherits.

    Subclasses call :meth:`check` in ``__init__`` (or right before the first
    batch) with the field ids and cycle start dates they are about to expose.
    Loading the manifest is hash-verified and happens once per instance.
    """

    def __init__(self, *, manifest: dict | None = None, context: str = "") -> None:
        self._holdout_manifest = manifest if manifest is not None else load_holdout_manifest()
        self._holdout_context = context
        self.holdout_manifest_sha256: str = str(
            self._holdout_manifest.get("manifest_sha256", "")
        )

    def check(
        self,
        field_ids: Iterable[int],
        cycle_keys: Sequence[str] | None = None,
        cycle_start_dates: Sequence[Any] | None = None,
        *,
        cycle_end_dates: Sequence[Any] | None = None,
        context: str | None = None,
    ) -> None:
        assert_train_only(
            field_ids,
            cycle_keys,
            cycle_start_dates,
            cycle_end_dates=cycle_end_dates,
            manifest=self._holdout_manifest,
            context=context or self._holdout_context,
        )

    def filter(
        self,
        field_ids: Iterable[int],
        cycle_keys: Sequence[str],
        cycle_start_dates: Sequence[Any] | None = None,
        *,
        cycle_end_dates: Sequence[Any] | None = None,
    ) -> list[str]:
        return filter_train_only(
            field_ids,
            cycle_keys,
            cycle_start_dates,
            cycle_end_dates=cycle_end_dates,
            manifest=self._holdout_manifest,
            context=self._holdout_context,
        )


__all__ = [
    "HOLDOUT_MANIFEST_PATH",
    "HoldoutGuard",
    "HoldoutViolationError",
    "assert_frozen_holdout_matches_splits",
    "assert_train_only",
    "audit_frozen_holdout",
    "build_holdout_manifest",
    "filter_train_only",
    "holdout_manifest_hash",
    "load_holdout_manifest",
    "save_holdout_manifest",
    "split_cycle_key",
    "train_only_mask",
]
