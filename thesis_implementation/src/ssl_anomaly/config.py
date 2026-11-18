"""Structured configuration dataclasses (Hydra-compatible).

The config tree mirrors the pipeline: profile → paths → ingest → phenology →
baseline → model → train → eval. Defaults correspond to the laptop profile
described in the implementation plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# -------------------------- enums / top-level --------------------------------


class PhaseAxis(str, Enum):
    DOY = "doy"
    DSH = "dsh"  # days-since-harvest
    GDD = "gdd"
    LANDMARK = "landmark"


class Backend(str, Enum):
    NUMPY = "numpy"
    RUST = "rust"  # gated behind G3; stub only in v1


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


@dataclass
class ProfileCfg:
    workers: int = 2
    blas_threads: int = 2
    min_free_gb: float = 2.0
    low_priority: bool = True
    device: Device = Device.CPU
    batch_size: int = 64


# ------------------------------ paths ----------------------------------------


@dataclass
class PathsCfg:
    root: str = "."
    raw_landsat: str = "data/raw/landsat"
    fields_gpkg: str = "data/geo/fields.gpkg"
    fields_parquet: str = "data/geo/fields.parquet"
    field_mask: str = "data/interim/field_mask.tif"
    zonal_dir: str = "data/interim/zonal"
    manifest: str = "data/manifests/ingest.sqlite"
    fields_zarr: str = "data/processed/fields.zarr"
    era5_zarr: str = "data/processed/era5.zarr"
    cycles_parquet: str = "data/processed/cycles.parquet"
    baseline_npz: str = "data/processed/baseline.npz"
    scores_parquet: str = "data/processed/scores.parquet"
    splits_json: str = "data/processed/splits.json"
    checkpoints: str = "checkpoints"
    releases: str = "releases"
    mlruns: str = "mlruns"
    reports: str = "reports"

    def resolve(self, root: str | Path | None = None) -> PathsCfg:
        """Return a new PathsCfg with all paths resolved against ``root``."""
        base = Path(root) if root else Path(self.root)
        return PathsCfg(
            root=str(base),
            raw_landsat=str(base / self.raw_landsat),
            fields_gpkg=str(base / self.fields_gpkg),
            fields_parquet=str(base / self.fields_parquet),
            field_mask=str(base / self.field_mask),
            zonal_dir=str(base / self.zonal_dir),
            manifest=str(base / self.manifest),
            fields_zarr=str(base / self.fields_zarr),
            era5_zarr=str(base / self.era5_zarr),
            cycles_parquet=str(base / self.cycles_parquet),
            baseline_npz=str(base / self.baseline_npz),
            scores_parquet=str(base / self.scores_parquet),
            splits_json=str(base / self.splits_json),
            checkpoints=str(base / self.checkpoints),
            releases=str(base / self.releases),
            mlruns=str(base / self.mlruns),
            reports=str(base / self.reports),
        )


# ----------------------------- ingest ----------------------------------------


@dataclass
class QualityCfg:
    cloud_shadow: bool = True
    cirrus: bool = True
    snow: bool = True
    cloud: bool = True
    dilated_cloud: bool = True
    # QA_PIXEL bit positions (Landsat 8/9 Collection 2 L2)
    bits_cloud: int = 3
    bits_cloud_shadow: int = 4
    bits_cirrus: int = 2
    bits_snow: int = 5
    bits_dilated_cloud: int = 1


@dataclass
class IngestCfg:
    bands: list[str] = field(
        default_factory=lambda: [
            "SR_B2",
            "SR_B3",
            "SR_B4",
            "SR_B5",
            "SR_B6",
            "SR_B7",
            "ST_B10",
        ]
    )
    scale_factor: float = 0.0000275  # Landsat C2 L2 SR
    add_offset: float = -0.2
    temp_scale: float = 0.00341802
    temp_offset: float = 149.0
    min_valid_fraction: float = 0.3
    quality: QualityCfg = field(default_factory=QualityCfg)


# ---------------------------- phenology --------------------------------------


@dataclass
class PhenologyCfg:
    lam: float = 100.0  # Whittaker lambda (tuned via CV in production)
    lam_cv_folds: int = 5
    smooth_daily: bool = True
    ndvi_band: str = "NDVI"
    min_prominence: float = 0.15
    min_cycle_days: int = 180  # sugarcane ~12 months
    max_cycle_days: int = 540
    plateau_frac: float = 0.7  # "high plateau" before harvest = frac of pre-trough max
    rise_frac: float = 0.15  # "followed by a rise" threshold
    replant_gap_days: int = 120
    replant_low_ndvi: float = 0.3
    phase_axis: PhaseAxis = PhaseAxis.DSH
    bin_days: int = 15
    max_interp_adjacent_bins: int = 1
    backend: Backend = Backend.NUMPY
    tbase_gdd: float = 10.0


# ---------------------------- baseline ---------------------------------------


@dataclass
class BaselineCfg:
    min_n: int = 5  # minimum normal cycles per bin before falling back
    kappa_field_offset: float = 2.5  # shrinkage strength
    floor_pct: float = 5.0  # percentile for scale floor
    score_threshold: float = 3.5
    min_run_bins: int = 2
    trim_iters: int = 3
    trim_q: float = 0.15
    use_cwsi_for_selection: bool = False  # never True (circularity)
    include_lst: bool = True
    include_weather: bool = False  # ablation default


# ----------------------------- SSL model -------------------------------------


@dataclass
class TokenizerCfg:
    standardize: bool = True
    include_valid_frac: bool = True
    include_dtime: bool = True
    include_dsh: bool = True
    include_gdd: bool = False
    include_doy: bool = True
    include_sensor: bool = True
    include_ratoon: bool = True
    include_weather: bool = False
    weather_vars: list[str] = field(default_factory=lambda: ["precip", "tmean"])


@dataclass
class GRUAECfg:
    d_model: int = 64
    n_layers: int = 2
    dropout: float = 0.1
    bidirectional_enc: bool = True


@dataclass
class TransformerCfg:
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 3
    d_ff: int = 256
    dropout: float = 0.1
    max_len: int = 128
    pos_encoding: str = "sine"  # "sine" | "learned"


@dataclass
class SSLCfg:
    """SSL training / masking config. Defaults sized for CPU laptop."""

    model: str = "transformer"  # "gru_ae" | "transformer"
    mask_ratio: float = 0.25
    mask_block_max: int = 3
    mask_block_p: float = 0.3
    huber_delta: float = 1.0
    trim_loss_frac: float = 0.10
    gate_baseline_passes: bool = True  # refuse to train SSL if baseline gate fails
    recon_weight: float = 1.0
    embed_weight: float = 0.0  # kNN loss not trained; embedding is inference-only
    knn_k: int = 15
    score_combination: str = "rank_avg_if_both_beat"
    max_epochs: int = 15
    lr: float = 3e-4
    weight_decay: float = 1e-5
    grad_clip: float = 1.0
    early_stop_patience: int = 8
    tokenizer: TokenizerCfg = field(default_factory=TokenizerCfg)
    gru_ae: GRUAECfg = field(default_factory=GRUAECfg)
    transformer: TransformerCfg = field(default_factory=TransformerCfg)


# ----------------------------- training --------------------------------------


@dataclass
class TrainCfg:
    seed: int = 42
    n_folds: int = 5
    n_seeds: int = 3
    validation_farms: list[str] = field(default_factory=list)  # e.g., Farms_subset
    block_by: str = "region"
    temporal_test_cycles: list[str] = field(default_factory=list)
    num_workers: int = 0
    log_every_n_steps: int = 10


# ----------------------------- evaluation ------------------------------------


@dataclass
class SyntheticCfg:
    ndvi_drop_depths: list[float] = field(default_factory=lambda: [0.05, 0.10, 0.20, 0.30])
    durations: list[int] = field(default_factory=lambda: [1, 2, 3, 5])
    phases: list[str] = field(default_factory=lambda: ["early", "mid", "late"])
    phenology_delay_days: list[int] = field(default_factory=lambda: [15, 30, 45])
    lst_increase_k: list[float] = field(default_factory=lambda: [1.0, 2.0, 4.0])
    n_per_stratum: int = 20
    alert_rate: float = 0.05


@dataclass
class EvalCfg:
    synthetic: SyntheticCfg = field(default_factory=SyntheticCfg)
    proxy_metrics: list[str] = field(default_factory=lambda: ["eta", "yield", "cwsi"])
    bootstrap_ci: int = 1000
    alpha: float = 0.05
    holm_correction: bool = True
    stability_deletion_fracs: list[float] = field(
        default_factory=lambda: [0.1, 0.2, 0.3, 0.5]
    )
    stability_harvest_shift_days: list[int] = field(default_factory=lambda: [-32, -16, 16, 32])
    stability_trim_qs: list[float] = field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3])


# ------------------------------ export ---------------------------------------


@dataclass
class ExportCfg:
    format: str = "safetensors"  # safetensors only for v1
    include_optimizer: bool = False
    include_config: bool = True
    include_norm_stats: bool = True
    include_git_sha: bool = True
    include_lock_hash: bool = True


# ---------------------------- top-level --------------------------------------


@dataclass
class Config:
    """Top-level configuration (Hydra-composable)."""

    profile: ProfileCfg = field(default_factory=ProfileCfg)
    paths: PathsCfg = field(default_factory=PathsCfg)
    ingest: IngestCfg = field(default_factory=IngestCfg)
    phenology: PhenologyCfg = field(default_factory=PhenologyCfg)
    baseline: BaselineCfg = field(default_factory=BaselineCfg)
    ssl: SSLCfg = field(default_factory=SSLCfg)
    train: TrainCfg = field(default_factory=TrainCfg)
    eval: EvalCfg = field(default_factory=EvalCfg)
    export: ExportCfg = field(default_factory=ExportCfg)
    verbose: int = 1

    def resolve_paths(self) -> Config:
        self.paths = self.paths.resolve(self.paths.root)
        return self


def default_config() -> Config:
    """Return a default Config (laptop profile). Useful for tests & CLIs."""
    return Config().resolve_paths()


def config_to_dict(cfg: Any) -> Any:
    """Recursively convert dataclass configs to JSON-friendly dicts."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(cfg):
        return {k: config_to_dict(v) for k, v in asdict(cfg).items()}
    if isinstance(cfg, dict):
        return {k: config_to_dict(v) for k, v in cfg.items()}
    if isinstance(cfg, (list, tuple)):
        return [config_to_dict(v) for v in cfg]
    if isinstance(cfg, Enum):
        return cfg.value
    if isinstance(cfg, Path):
        return str(cfg)
    return cfg
