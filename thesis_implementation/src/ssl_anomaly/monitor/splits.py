"""Locked train/dev/test/monitoring splits (design D2, spec model-development-protocol).

The split is built ONCE by ``scripts/build_locked_splits.py`` and written to
``data/processed/splits_locked.json``. Every later script loads it through
:func:`load_splits_locked`, which re-verifies the manifest self-hash and the
cycle-file hash; any drift is a hard error (manifest-drift requirement).

Split rules (design D2):
- test: every uncensored cycle starting on or after 2024-01-01, plus every
  cycle of one spatially contiguous field block (k-means over field centroids).
- dev: uncensored cycles starting in 2023 outside the test block, plus every
  cycle of a second contiguous block. Non-block dev cycles must also END
  before 2024-01-01 (same temporal-leakage rationale as train; deviation from
  D2's wording recorded in the manifest as ``dev_temporal_cutoff``).
- train: everything else that ends before 2024-01-01.
- monitoring_only: censored / in-progress cycles plus uncensored cycles that
  miss the temporal cutoffs (display-only, never metrics).

Test isolation: :func:`assert_no_test_cycles` guards every training /
evaluation code path. Only ``scripts/freeze_main_model.py --final-test`` may
pass ``allow_test=True``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("ssl_anomaly.monitor.splits")

REPO_ROOT = Path(__file__).resolve().parents[3]
SPLITS_LOCKED_PATH = REPO_ROOT / "data/processed/splits_locked.json"
CYCLES_PARQUET_PATH = REPO_ROOT / "data/processed/cycles_490.parquet"
CYCLES_NPZ_PATH = REPO_ROOT / "data/interim/growth_cycles_490.npz"
FARMS_GEOJSON_PATH = REPO_ROOT.parent / "Data/RoI/Farms.geojson"

BASE_DATE = pd.Timestamp("2013-03-30")
TEST_PERIOD_START = pd.Timestamp("2024-01-01")

SPLIT_NAMES = ("train", "dev", "test", "monitoring_only")

CYCLE_AUDIT_EXCLUSION_PATH = REPO_ROOT / "reports/cycle_audit/exclusion_cycles.csv"

# Fixed for reproducibility; recorded in the manifest.
KMEANS_SEED = 13
N_BLOCKS = 10
TEST_BLOCK_TARGET_FRAC = 0.10


def load_audit_exclusions(path: Path = CYCLE_AUDIT_EXCLUSION_PATH) -> dict:
    """Load the cycle-audit exclusion list (finding 14 D2 outcome).

    Returns {"keys": ["<field>:<cycle_id>", …], "sha256": …} or empty when the
    file is absent (the audit has not produced a final list yet).
    """
    if not Path(path).exists():
        return {"keys": [], "sha256": None}
    df = pd.read_csv(path)
    keys = [f"{int(r['field'])}:{int(r['cycle_id'])}" for _, r in df.iterrows()]
    return {
        "keys": keys,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }


# ---------------------------------------------------------------------------
# Manifest hashing
# ---------------------------------------------------------------------------
def manifest_hash(manifest: dict) -> str:
    """SHA-256 over the manifest with the ``manifest_sha256`` key removed."""
    payload = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def cycle_file_hashes(cycles_parquet_path: Path = CYCLES_PARQUET_PATH,
                      cycles_npz_path: Path = CYCLES_NPZ_PATH) -> dict[str, str]:
    """SHA-256 of the two cycle source files (parquet metadata + NPZ tensors)."""
    return {
        "cycles_parquet_sha256": hashlib.sha256(Path(cycles_parquet_path).read_bytes()).hexdigest(),
        "cycles_npz_sha256": hashlib.sha256(Path(cycles_npz_path).read_bytes()).hexdigest(),
    }


# ---------------------------------------------------------------------------
# Contiguous blocks (k-means over projected field centroids)
# ---------------------------------------------------------------------------
def compute_contiguous_blocks(
    *,
    farms_path: Path = FARMS_GEOJSON_PATH,
    n_blocks: int = N_BLOCKS,
    seed: int = KMEANS_SEED,
) -> dict:
    """Cluster field centroids with k-means in projected UTM coordinates.

    Returns a dict with the block assignment per field id, the seed, and the
    cluster sizes. The EPSG:32639 projection is recorded so the clustering is
    reproducible without re-reading the geojson.
    """
    import geopandas as gpd

    gdf = gpd.read_file(farms_path)
    if gdf.crs is None:
        raise ValueError(f"No CRS on {farms_path}")
    utm = gdf.to_crs(epsg=32639)
    cents = utm.geometry.centroid
    xy = np.column_stack([cents.x.to_numpy(), cents.y.to_numpy()])
    # Archive field ids are 1-based over geojson row order: the field mask was
    # rasterized with sequential ids 1..490 (io/field_mask.py fallback), so
    # stats.zarr field f ↔ geojson row f−1 (OGC_FID f−1).
    field_ids = gdf["OGC_FID"].astype(int).to_numpy() + 1

    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=n_blocks, random_state=seed, n_init=10)
    labels = km.fit_predict(xy)

    sizes: dict[int, int] = {}
    blocks: dict[str, list[int]] = {}
    for b in range(n_blocks):
        members = sorted(int(f) for f in field_ids[labels == b])
        blocks[f"block_{b}"] = members
        sizes[b] = len(members)

    return {
        "seed": seed,
        "n_blocks": n_blocks,
        "crs_target": "EPSG:32639",
        "n_fields": int(len(field_ids)),
        "block_sizes": {str(b): int(s) for b, s in sizes.items()},
        "blocks": blocks,
    }


def pick_blocks(blocks_info: dict, *, target_frac: float = TEST_BLOCK_TARGET_FRAC) -> dict[str, int]:
    """Pick the test block (size closest to target fraction) and the dev block
    (closest among the remaining blocks). Returns {"test": b, "dev": b}."""
    n_fields = blocks_info["n_fields"]
    sizes = {int(k): int(v) for k, v in blocks_info["block_sizes"].items()}
    target = target_frac * n_fields
    test_b = min(sizes, key=lambda b: abs(sizes[b] - target))
    rest = {b: s for b, s in sizes.items() if b != test_b}
    dev_b = min(rest, key=lambda b: abs(sizes[b] - target))
    return {"test": int(test_b), "dev": int(dev_b)}


# ---------------------------------------------------------------------------
# Split construction
# ---------------------------------------------------------------------------
def build_splits_locked(
    *,
    farms_path: Path = FARMS_GEOJSON_PATH,
    cycles_parquet_path: Path = CYCLES_PARQUET_PATH,
    n_blocks: int = N_BLOCKS,
    seed: int = KMEANS_SEED,
    exclusion_path: Path = CYCLE_AUDIT_EXCLUSION_PATH,
) -> dict:
    """Build the locked split manifest (design D2 + finding-14 D2 exclusions).

    The cycle-audit exclusion list (segmentation-error cycles: merged/split/
    out-of-range sanity flags) is applied per the finding-14 outcome: excluded
    cycles go to monitoring_only (never metrics; display-only).
    """
    df = pd.read_parquet(cycles_parquet_path)
    blocks_info = compute_contiguous_blocks(farms_path=farms_path, n_blocks=n_blocks, seed=seed)
    picked = pick_blocks(blocks_info)
    test_fields = set(blocks_info["blocks"][f"block_{picked['test']}"])
    dev_fields = set(blocks_info["blocks"][f"block_{picked['dev']}"])

    exclusions = load_audit_exclusions(exclusion_path)
    excluded_keys = set(exclusions["keys"])

    start = BASE_DATE + pd.to_timedelta(df["t_start"].astype("int64"), unit="D")
    end = BASE_DATE + pd.to_timedelta(df["t_end"].astype("int64"), unit="D")
    df = df.assign(start_date=start, end_date=end)

    split_of: list[str] = []
    n_excluded = 0
    n_dropped_train_cutoff = 0
    n_dropped_dev_cutoff = 0
    for _, row in df.iterrows():
        fid = int(row["field"])
        uncensored = not bool(row["censored"])
        key = f"{fid}:{int(row['cycle_id'])}"
        # Cycle-audit exclusions (finding 14 D2): segmentation-error cycles
        # never enter metric splits — monitoring_only, display-only.
        if key in excluded_keys:
            split_of.append("monitoring_only")
            n_excluded += 1
            continue
        # Censored (in-progress) cycles ALWAYS go to monitoring_only — design
        # D2: "they never enter metrics"; the block rule applies to a field's
        # uncensored cycles only (they carry the tensors).
        if not uncensored:
            split_of.append("monitoring_only")
            continue
        if fid in test_fields:
            split_of.append("test")
            continue
        if fid in dev_fields:
            split_of.append("dev")
            continue
        if row["start_date"] >= TEST_PERIOD_START:
            split_of.append("test")
            continue
        if row["end_date"] < TEST_PERIOD_START:
            if row["start_date"].year == 2023:
                split_of.append("dev")
            else:
                split_of.append("train")
            continue
        # Uncensored cycle crossing the test period: excluded from train/dev by
        # the temporal cutoff (same rationale as D2's train rule).
        if row["start_date"].year == 2023:
            n_dropped_dev_cutoff += 1
        else:
            n_dropped_train_cutoff += 1
        split_of.append("monitoring_only")

    df = df.assign(split=split_of)

    # Cycle ids: stable string "<field>:<cycle_id>".
    def cycle_ids(sub: pd.DataFrame) -> list[str]:
        return [f"{int(r['field'])}:{int(r['cycle_id'])}" for _, r in sub.iterrows()]

    manifest: dict = {
        "version": 1,
        "created": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "git_sha": _git_sha(),
        "base_date": BASE_DATE.strftime("%Y-%m-%d"),
        "test_period_start": TEST_PERIOD_START.strftime("%Y-%m-%d"),
        "kmeans": {
            "seed": blocks_info["seed"],
            "n_blocks": blocks_info["n_blocks"],
            "crs_target": blocks_info["crs_target"],
            "block_sizes": blocks_info["block_sizes"],
            "test_block": int(picked["test"]),
            "dev_block": int(picked["dev"]),
            # Immutable block-member lists (the {split}_fields below are
            # row-derived and can legitimately overlap for non-block fields).
            "test_block_fields": sorted(test_fields),
            "dev_block_fields": sorted(dev_fields),
        },
        "test_fields": sorted(test_fields),
        "dev_fields": sorted(dev_fields),
        "dev_temporal_cutoff": (
            "non-block dev cycles must also end before the test period start "
            "(recorded deviation from design D2 wording; rationale: avoid "
            "calibrating thresholds on the test period's weather)"
        ),
        "n_dropped_train_cutoff": int(n_dropped_train_cutoff),
        "n_dropped_dev_cutoff": int(n_dropped_dev_cutoff),
        "audit_exclusions": {
            "file": str(exclusion_path.name),
            "sha256": exclusions["sha256"],
            "n_excluded_from_metrics": int(n_excluded),
            "source": "finding 14 D2 outcome (cycle audit); segmentation-error cycles "
                      "-> monitoring_only (display-only, never metrics)",
        },
        "counts": {},
        "cycles": {},
        "cycle_file_hashes": cycle_file_hashes(cycles_parquet_path=cycles_parquet_path),
    }

    for name in SPLIT_NAMES:
        sub = df[df["split"] == name]
        manifest["counts"][name] = int(len(sub))
        manifest["cycles"][name] = cycle_ids(sub)
        manifest[f"{name}_fields"] = sorted(int(f) for f in sub["field"].unique())

    # Guard: pairwise disjoint.
    id_sets = {name: set(manifest["cycles"][name]) for name in SPLIT_NAMES}
    for a in SPLIT_NAMES:
        for b in SPLIT_NAMES:
            if a < b and id_sets[a] & id_sets[b]:
                raise AssertionError(f"Splits {a} and {b} overlap")

    manifest["manifest_sha256"] = manifest_hash(manifest)
    log.info(
        "Split counts: %s (dropped by cutoff: train %d, dev %d)",
        manifest["counts"], n_dropped_train_cutoff, n_dropped_dev_cutoff,
    )
    return manifest


def _git_sha() -> str:
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()[:8]
    except Exception:
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Loading and guards
# ---------------------------------------------------------------------------
def load_splits_locked(
    *,
    path: Path = SPLITS_LOCKED_PATH,
    verify_cycle_files: bool = True,
    cycles_parquet_path: Path = CYCLES_PARQUET_PATH,
    cycles_npz_path: Path = CYCLES_NPZ_PATH,
) -> dict:
    """Load the locked manifest, verifying its self-hash (and file hashes).

    Raises RuntimeError on any drift — the manifest-drift requirement.
    """
    if not Path(path).exists():
        raise RuntimeError(
            f"splits_locked.json missing at {path}. Run scripts/build_locked_splits.py once; "
            "the split is never regenerated inside this change."
        )
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = manifest.get("manifest_sha256")
    if not expected or manifest_hash(manifest) != expected:
        raise RuntimeError(
            "splits_locked.json manifest hash mismatch — the split was modified or "
            "corrupted. Refusing to run (manifest-drift requirement)."
        )
    if verify_cycle_files:
        current = cycle_file_hashes(
            cycles_parquet_path=cycles_parquet_path, cycles_npz_path=cycles_npz_path,
        )
        for key, cur in current.items():
            rec = manifest.get("cycle_file_hashes", {}).get(key)
            if rec is not None and rec != cur:
                raise RuntimeError(
                    f"{key} drift: splits_locked.json was built from a different cycle file "
                    f"(recorded {rec[:12]}…, current {cur[:12]}…). Refusing to run."
                )
    return manifest


def split_of_cycle(manifest: dict, field_id: int, cycle_id: int) -> str | None:
    """Return the split name of a cycle, or None if the cycle is unknown."""
    key = f"{int(field_id)}:{int(cycle_id)}"
    for name in SPLIT_NAMES:
        if key in manifest["cycles"].get(name, ()):  # lists; fine at n=1755
            return name
    return None


def assert_no_test_cycles(
    cycle_keys: list[str] | set[str],
    manifest: dict,
    *,
    context: str = "",
) -> None:
    """Raise RuntimeError if any cycle key belongs to the locked test split.

    ``cycle_keys`` are ``"<field>:<cycle_id>"`` strings. The error names the
    allowed entry point (test-isolation requirement).
    """
    test = set(manifest["cycles"]["test"])
    leaked = sorted(test & set(cycle_keys))
    if leaked:
        where = f" in {context}" if context else ""
        raise RuntimeError(
            f"Test-split cycle access forbidden{where}: {leaked[:5]}"
            f"{'…' if len(leaked) > 5 else ''}. Test cycles may only be read by "
            "scripts/freeze_main_model.py --final-test."
        )
