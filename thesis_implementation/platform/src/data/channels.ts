// ── Channel registry (mirror of scripts/platform_channels.py) ─────────────────
// Single source of truth for the data contract between the exporter and the
// platform. Keep this in sync with scripts/platform_channels.py; parity is
// enforced by tests/unit/test_platform_data_contract.py.

export type ProvenanceState = 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';

export type ChannelKind = 'spectral' | 'thermal' | 'water' | 'weather';

export interface ChannelSpec {
  name: string;
  unit: string;
  physicalRange: [number, number];
  provenanceDefault: ProvenanceState;
  required: boolean;
  kind: ChannelKind;
  derivedFrom?: string;
}

export const CHANNELS: ChannelSpec[] = [
  // Envelopes mirror scripts/platform_channels.py: observed 2013-2026 archive
  // envelope + margin (winter medians go slightly negative).
  { name: 'ndvi', unit: 'index', physicalRange: [-0.5, 1], provenanceDefault: 'observed', required: true, kind: 'spectral' },
  { name: 'evi', unit: 'index', physicalRange: [-0.3, 1], provenanceDefault: 'observed', required: true, kind: 'spectral' },
  { name: 'savi', unit: 'index', physicalRange: [-0.3, 1], provenanceDefault: 'observed', required: true, kind: 'spectral' },
  { name: 'ndmi', unit: 'index', physicalRange: [-1, 1], provenanceDefault: 'observed', required: true, kind: 'water' },
  { name: 'tvdi', unit: 'index', physicalRange: [0, 1], provenanceDefault: 'proxy', required: true, kind: 'thermal', derivedFrom: 'cwsi' },
  { name: 'cwsi', unit: 'index', physicalRange: [0, 1], provenanceDefault: 'observed', required: true, kind: 'thermal' },
  { name: 'eta', unit: 'mm/d', physicalRange: [0, 8], provenanceDefault: 'proxy', required: true, kind: 'water', derivedFrom: 'ndvi' },
  { name: 'lst', unit: '°C', physicalRange: [15, 55], provenanceDefault: 'observed', required: false, kind: 'thermal' },
  { name: 'precip', unit: 'mm', physicalRange: [0, 300], provenanceDefault: 'modelled', required: true, kind: 'weather' },
  { name: 'temp', unit: '°C', physicalRange: [0, 55], provenanceDefault: 'modelled', required: true, kind: 'weather' },
];

export const channelByName = (name: string): ChannelSpec | undefined =>
  CHANNELS.find(c => c.name === name);

export const CHANNEL_NAMES = CHANNELS.map(c => c.name);

export type ChannelId = (typeof CHANNELS)[number]['name'];

// ── Score registry (contract v5) ─────────────────────────────────────────────
// Provenance of an anomaly score for one observation: "model" when computed by
// a loaded checkpoint, "absent" when no score exists (missing/failed checkpoint
// or unmapped acquisition). Contract v5 removed the CWSI proxy fallback — no
// observation ever carries "proxy"; the baseline slots keep "proxy" only as
// their registry kind (they would need a non-CWSI formula artifact to score).
export type ScoreProvenanceState = 'model' | 'proxy' | 'absent';

/** Contract version recorded on every exported farm record (v5: stress flag). */
export const CONTRACT_VERSION = 5;

export interface ScoreSpec {
  name: string;
  provenanceDefault: ScoreProvenanceState;
  /** Checkpoint stem under checkpoints/ (pt + json sidecar) when model-backed. */
  checkpoint?: string;
}

// Order mirrors the platform MODELS list (data.ts); mirror of
// scripts/platform_channels.py::SCORE_REGISTRY.
export const SCORES: ScoreSpec[] = [
  { name: 'b0_calendar', provenanceDefault: 'proxy' },
  { name: 'b1_dsh', provenanceDefault: 'proxy' },
  { name: 'b1_cusum', provenanceDefault: 'proxy' },
  { name: 'masked_transformer', provenanceDefault: 'model', checkpoint: 'masked_transformer_main' },
  { name: 'gru_ae', provenanceDefault: 'model', checkpoint: 'gru_ae_main' },
  { name: 'sts_net', provenanceDefault: 'model', checkpoint: 'sts_net_490' },
  { name: 'tiny_cnn_mamba', provenanceDefault: 'model', checkpoint: 'tiny_cnn_mamba_490' },
  { name: 'time2agri', provenanceDefault: 'model', checkpoint: 'time2agri_490' },
];

export const scoreByName = (name: string): ScoreSpec | undefined =>
  SCORES.find(s => s.name === name);

export const SCORE_NAMES = SCORES.map(s => s.name);
