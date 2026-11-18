"""Small, explicitly synthetic locked split provenance for patch tests."""

from ssl_anomaly.io import patches as P
from ssl_anomaly.monitor import holdout as H
from ssl_anomaly.monitor import splits as S


def bind_patch_store(
    root,
    *,
    spatial=(103,),
    train_keys=None,
    dev_keys=(),
    known=(101, 102, 103),
    cutoff="2024-01-01",
):
    if train_keys is None:
        train_keys = [
            c.key
            for c in P.patch_cycle_index(root).values()
            if c.field_id in known and c.field_id not in spatial and c.key not in dev_keys
        ]
    splits = {
        "base_date": "2013-03-30",
        "test_period_start": cutoff,
        "cycle_file_hashes": {"cycles_parquet_sha256": "a" * 64},
        "kmeans": {"test_block_fields": list(spatial)},
        "train_fields": sorted(set(known) - set(spatial)),
        "test_fields": list(spatial),
        "cycles": {"train": list(train_keys), "dev": list(dev_keys), "test": []},
    }
    splits["manifest_sha256"] = S.manifest_hash(splits)
    root.attrs.update(
        {
            "cycle_epoch": splits["base_date"],
            "cycle_source_sha256": "a" * 64,
            "splits_manifest_sha256": splits["manifest_sha256"],
        }
    )
    return splits, H.build_holdout_manifest(splits)
