#!/usr/bin/env python3
"""Build data/processed/splits_490.json: LOYO by year + 20 spatial blocks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

BASE_DATE = pd.Timestamp("2013-03-30")
OUT_PATH = Path("data/processed/splits_490.json")
CYCLES_PATH = Path("data/processed/cycles_490.parquet")
N_BLOCKS = 20


def assign_block(field_id: int, n_blocks: int = N_BLOCKS) -> int:
    h = hashlib.sha256(str(field_id).encode()).hexdigest()
    return int(h, 16) % n_blocks


def main() -> int:
    df = pd.read_parquet(CYCLES_PATH)
    non_censored = df[~df["censored"]].copy()

    # Convert t_start (days from BASE_DATE) to year
    non_censored["start_date"] = non_censored["t_start"].apply(
        lambda d: BASE_DATE + pd.Timedelta(days=int(d))
    )
    non_censored["start_year"] = non_censored["start_date"].dt.year

    # Assign deterministic spatial blocks by hash of field ID
    non_censored["spatial_block"] = non_censored["field"].apply(assign_block)

    # Invariant: no field appears in two spatial blocks
    field_blocks = non_censored.groupby("field")["spatial_block"].nunique()
    assert (field_blocks == 1).all(), "Some fields appear in multiple blocks!"

    years = sorted(non_censored["start_year"].unique())

    splits: dict = {
        "n_fields": int(non_censored["field"].nunique()),
        "n_cycles": int(len(non_censored)),
        "n_spatial_blocks": N_BLOCKS,
        "n_loyo_years": len(years),
        "years": [int(y) for y in years],
        "spatial_blocks": {},
        "loyo_splits": {},
        "sha256": "",
    }

    # Spatial blocks
    for b in range(N_BLOCKS):
        block_fields = sorted(
            non_censored[non_censored["spatial_block"] == b]["field"].unique().tolist()
        )
        splits["spatial_blocks"][f"block_{b}"] = {
            "n_fields": len(block_fields),
            "fields": block_fields,
        }

    # LOYO splits: train on all years except test year
    for yr in years:
        train_years = [y for y in years if y != yr]
        train_cycles = non_censored[non_censored["start_year"].isin(train_years)]
        test_cycles = non_censored[non_censored["start_year"] == yr]
        splits["loyo_splits"][str(int(yr))] = {
            "test_year": int(yr),
            "train_years": [int(y) for y in train_years],
            "n_train_cycles": int(len(train_cycles)),
            "n_test_cycles": int(len(test_cycles)),
            "train_field_ids": sorted(train_cycles["field"].unique().tolist()),
            "test_field_ids": sorted(test_cycles["field"].unique().tolist()),
        }

    # SHA-256 over everything except sha256 itself
    splits_for_hash = {k: v for k, v in splits.items() if k != "sha256"}
    splits_json_no_sha = json.dumps(splits_for_hash, sort_keys=True)
    splits["sha256"] = hashlib.sha256(splits_json_no_sha.encode()).hexdigest()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(splits, indent=2))

    print(f"Wrote {OUT_PATH}")
    print(f"SHA-256: {splits['sha256']}")
    print(f"Fields: {splits['n_fields']}, Cycles: {splits['n_cycles']}, Years: {years}")
    print(
        f"Fields with >= 2 cycles: {int((non_censored.groupby('field').size() >= 2).sum())}"
    )
    print(
        f"Fields with exactly 1 cycle: {int((non_censored.groupby('field').size() == 1).sum())}"
    )
    print(f"Censored cycles: {int(df['censored'].sum())}, Non-censored: {int((~df['censored']).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
