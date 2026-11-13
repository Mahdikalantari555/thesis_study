"""Unified CLI entry point for the ssl_anomaly pipeline.

Each subcommand delegates to thin scripts under ``scripts/`` via
``ssl_anomaly.cli``. Usage::

    ssl-anomaly ingest   --config conf/base.yaml
    ssl-anomaly segment  --config conf/base.yaml
    ssl-anomaly baseline --config conf/base.yaml
    ssl-anomaly train    --config conf/base.yaml
    ssl-anomaly evaluate --config conf/base.yaml
    ssl-anomaly export   --config conf/base.yaml --run-id <id>

In this v1 we keep the CLI minimal (click) rather than full Hydra plumbing;
Hydra configs are loaded via omegaconf for richer composition when needed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
import pandas as pd

from .utils.seeds import seed_everything
from .utils.throttle import limit_threads, lower_priority

log = logging.getLogger("ssl_anomaly.cli")


def _bootstrap(threads: int = 2, seed: int = 42, low_pri: bool = True) -> None:
    limit_threads(threads)
    seed_everything(seed)
    if low_pri:
        lower_priority()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@click.group()
@click.option("--threads", default=2, type=int, help="BLAS/OpenMP thread cap.")
@click.option("--seed", default=42, type=int, help="Global RNG seed.")
@click.option("--low-priority/--no-low-priority", default=True)
def cli(threads: int, seed: int, low_priority: bool) -> None:
    """ssl_anomaly — self-supervised phenology-aware anomaly detection."""
    _bootstrap(threads=threads, seed=seed, low_pri=low_priority)


@cli.command("ingest")
@click.option("--fields", default="data/geo/fields.gpkg", type=Path)
@click.option("--landsat-dir", default="data/raw/landsat", type=Path)
@click.option("--out-mask", default="data/interim/field_mask.tif", type=Path)
@click.option("--zonal-dir", default="data/interim/zonal", type=Path)
@click.option("--out-zarr", default="data/processed/fields.zarr", type=Path)
@click.option("--manifest", default="data/manifests/ingest.sqlite", type=Path)
@click.option("--force-mask/--no-force-mask", default=False)
def ingest_cmd(fields: Path, landsat_dir: Path, out_mask: Path, zonal_dir: Path,
               out_zarr: Path, manifest: Path, force_mask: bool) -> None:
    """Build field mask, run zonal stats, aggregate fields.zarr."""
    from .io import aggregate_to_zarr, build_field_mask
    build_field_mask(fields, out_mask, force=force_mask)
    log.info("Field mask ready at %s", out_mask)
    # Per-scene zonal runs would iterate landsat_dir here; v1 CLI checks that
    # pre-computed zonal parquets exist.
    if zonal_dir.exists() and list(zonal_dir.glob("*.parquet")):
        aggregate_to_zarr(zonal_dir, out_zarr)
    else:
        log.warning(
            "No zonal parquets found in %s. Run per-scene processing via "
            "ssl_anomaly.io.zonal.zonal_scene on actual Landsat scenes.", zonal_dir,
        )
    log.info("Ingest step complete.")


@cli.command("segment")
@click.option("--zarr", default="data/processed/fields.zarr", type=Path)
@click.option("--out", default="data/processed/cycles.parquet", type=Path)
@click.option("--lam", type=float, default=None, help="Whittaker lambda; auto-tuned if not set.")
def segment_cmd(zarr: Path, out: Path, lam: float | None) -> None:
    """Segment cycles from NDVI for every field and write cycles.parquet."""
    if not zarr.exists():
        log.error("fields.zarr not found at %s", zarr)
        raise SystemExit(1)
    import xarray as xr

    from .phenology import add_spectral_indices, segment_cycles

    ds = xr.open_zarr(zarr)
    ds = add_spectral_indices(ds)
    med = ds["median"]
    bands = list(med.coords["band"].values)
    ndvi_idx = bands.index("NDVI")
    times = ds.coords["time"].values
    fields = ds.coords["field"].values
    vf = ds["valid_frac"].values
    records = []
    for fi, fid in enumerate(fields):
        ndvi = med[fi, :, ndvi_idx].values
        q = vf[fi]
        t_days = (times - times.min()).astype("timedelta64[D]").astype(int)
        cycles = segment_cycles(int(fid), t_days, ndvi, quality=q, lam=lam)
        for c in cycles:
            records.append(c.to_dict())
    df = pd.DataFrame(records)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    log.info("Wrote %d cycles for %d fields to %s", len(df), len(fields), out)


@cli.command("baseline")
@click.option("--zarr", default="data/processed/fields.zarr", type=Path)
@click.option("--cycles", default="data/processed/cycles.parquet", type=Path)
@click.option("--out-npz", default="data/processed/baseline.npz", type=Path)
@click.option("--out-scores", default="data/processed/scores.parquet", type=Path)
def baseline_cmd(zarr: Path, cycles: Path, out_npz: Path, out_scores: Path) -> None:
    """Fit a robust baseline and score all cycles (B1)."""
    log.warning("CLI baseline command is a placeholder; run via scripts/build_baseline.py")


@cli.command("train")
@click.option("--zarr", default="data/processed/fields.zarr", type=Path)
@click.option("--cycles", default="data/processed/cycles.parquet", type=Path)
@click.option("--baseline", default="data/processed/baseline.npz", type=Path)
@click.option("--out", default="releases", type=Path, help="Release dir root.")
@click.option("--model", default="transformer", type=click.Choice(["gru_ae", "transformer"]))
def train_cmd(zarr: Path, cycles: Path, baseline: Path, out: Path, model: str) -> None:
    """Train SSL model on normal cycles (gated by baseline)."""
    log.warning("CLI train command is a placeholder; run via scripts/train_ssl.py")


@cli.command("evaluate")
@click.option("--scores", default="data/processed/scores.parquet", type=Path)
@click.option("--out", default="reports/metrics.json", type=Path)
def evaluate_cmd(scores: Path, out: Path) -> None:
    """Evaluate baseline/SSL with synthetic injection + proxies."""
    log.warning("CLI evaluate command is a placeholder; run via scripts/evaluate.py")


@cli.command("export")
@click.option("--ckpt", required=True, type=Path)
@click.option("--out", required=True, type=Path)
def export_cmd(ckpt: Path, out: Path) -> None:
    """Export a checkpoint to SafeTensors release."""
    log.warning("CLI export command is a placeholder; run via scripts/export_model.py")


# Aliases for the project.scripts table
def ingest() -> None:
    cli(["ingest"], standalone_mode=False)


def segment() -> None:
    cli(["segment"], standalone_mode=False)


def baseline() -> None:
    cli(["baseline"], standalone_mode=False)


def train() -> None:
    cli(["train"], standalone_mode=False)


def evaluate() -> None:
    cli(["evaluate"], standalone_mode=False)


def export() -> None:
    cli(["export"], standalone_mode=False)


if __name__ == "__main__":
    cli()
