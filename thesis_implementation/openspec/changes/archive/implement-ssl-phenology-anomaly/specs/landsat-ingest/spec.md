# Spec Delta

## Purpose
Provide a resumable, resource-throttled Landsat ingest pipeline that converts raw scenes into field-level Zarr stores and metadata for downstream phenology and anomaly analysis.

## ADDED Requirements

### Requirement: Field mask construction
The system SHALL build a one-time raster mask mapping each 30 m pixel to a field identifier, and SHALL reuse it for all scene processing.

#### Scenario: Mask exists
- **WHEN** ingest runs and `field_mask.tif` already exists
- **THEN** the pipeline reuses the existing mask and does not rebuild it

### Requirement: Per-scene zonal statistics
The system SHALL compute per-field mean and median for each band using pixels not flagged as cloud, shadow, cirrus, or snow, and SHALL record the valid pixel fraction.

#### Scenario: Cloudy scene
- **WHEN** a scene has a field with valid fraction below the configured threshold
- **THEN** that field observation is either excluded or down-weighted according to configuration

### Requirement: Checkpoint and resume
The system SHALL track each scene's processing status in a SQLite manifest and SHALL skip scenes already marked done.

#### Scenario: Interrupted run
- **WHEN** ingest is restarted after a crash
- **THEN** only pending or failed scenes are reprocessed

### Requirement: Atomic output writes
The system SHALL write each scene's zonal parquet to a temporary file and atomically replace the final file.

#### Scenario: Write failure
- **WHEN** writing a scene parquet fails midway
- **THEN** no partial final parquet file remains for that scene

### Requirement: Resource throttling
The system SHALL limit BLAS threads and process priority by default and SHALL wait for minimum free memory before processing each scene.

#### Scenario: Low memory
- **WHEN** available memory is below the configured threshold
- **THEN** processing pauses until memory headroom is restored

### Requirement: Zarr aggregation
The system SHALL aggregate zonal outputs into a version 3 Zarr store with dimensions field, time, and band, including a sensor coordinate.

#### Scenario: Build fields.zarr
- **WHEN** aggregation runs
- **THEN** `fields.zarr` contains median values, valid fractions, field/time/band coordinates, and sensor labels
