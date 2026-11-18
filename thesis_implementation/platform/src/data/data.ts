// ── Khuzestan sugarcane farm data, exported time series & model scores ───────
// Both JSON payloads are produced by scripts/export_platform_data.py:
//   farms_khuzestan.json   — field polygons + metadata (490 fields)
//   series_khuzestan.json  — 48 monthly observations per field (2021-01 … 2024-12)
// The series file used to be exported but never imported (the views generated
// synthetic values with a seeded RNG instead). It is now the single data source.
// (Renamed from mock.ts: this is the typed loader for real pipeline output,
// not mock data — wire-platform-to-real-data task 4.3.)
// The series payload covers every acquisition date of the archive (~538 obs
// per field, ~86 MB): imported `?raw` and parsed once at startup — JSON.parse
// of a string literal is far faster for the browser than an 86 MB object
// literal, and keeps the single-file offline build intact.
import farmsKhuzestanData from './farms_khuzestan.json';
import khuSeriesRaw from './series_khuzestan.json?raw';
import { CHANNELS, CHANNEL_NAMES, type ChannelSpec, type ScoreProvenanceState } from './channels';

export type ModelId =
  | 'b0_calendar'
  | 'b1_dsh'
  | 'b1_cusum'
  | 'masked_transformer'
  | 'gru_ae'
  | 'sts_net'
  | 'tiny_cnn_mamba'
  | 'time2agri';

export type IndicatorId =
  | 'ndvi'
  | 'evi'
  | 'savi'
  | 'ndmi'
  | 'tvdi'
  | 'cwsi'
  | 'eta'
  | 'lst'
  | 'precip'
  | 'temp';

export interface ModelDef {
  id: ModelId;
  /** Latin display name — model names are proper nouns and stay in Latin script. */
  name: string;
  short: string;
  color: string;
  /** i18n keys: `t(typeKey)` / `t(descKey)` so every locale renders. */
  typeKey: string;
  descKey: string;
}

export const MODELS: ModelDef[] = [
  { id: 'b0_calendar', name: 'B0 Calendar DOY', short: 'B0-DOY', color: '#64748b', typeKey: 'model.b0_calendar.type', descKey: 'model.b0_calendar.desc' },
  { id: 'b1_dsh', name: 'B1 Phenological DSH', short: 'B1-DSH', color: '#0f766e', typeKey: 'model.b1_dsh.type', descKey: 'model.b1_dsh.desc' },
  { id: 'b1_cusum', name: 'B1 CUSUM Filter', short: 'B1-CUSUM', color: '#0284c7', typeKey: 'model.b1_cusum.type', descKey: 'model.b1_cusum.desc' },
  { id: 'masked_transformer', name: 'SSL Masked Transformer', short: 'Masked-TF', color: '#7c3aed', typeKey: 'model.masked_transformer.type', descKey: 'model.masked_transformer.desc' },
  { id: 'gru_ae', name: 'GRU Autoencoder', short: 'GRU-AE', color: '#65a30d', typeKey: 'model.gru_ae.type', descKey: 'model.gru_ae.desc' },
  { id: 'sts_net', name: 'STS-Net 3D-CAE', short: 'STS-Net', color: '#d97706', typeKey: 'model.sts_net.type', descKey: 'model.sts_net.desc' },
  { id: 'tiny_cnn_mamba', name: 'Tiny-CNN-Mamba', short: 'CNN-Mamba', color: '#2563eb', typeKey: 'model.tiny_cnn_mamba.type', descKey: 'model.tiny_cnn_mamba.desc' },
  { id: 'time2agri', name: 'Time2Agri Contrastive', short: 'Time2Agri', color: '#be123c', typeKey: 'model.time2agri.type', descKey: 'model.time2agri.desc' },
];

export const modelById = (id: ModelId) => MODELS.find(m => m.id === id) || MODELS[0];

export interface IndicatorDef {
  id: IndicatorId;
  /** Latin symbol (NDVI, CWSI, ETa, …) — used verbatim in both locales. */
  name: string;
  /** Unit symbol; localized unit names are not needed at this granularity. */
  unit: string;
  color: string;
  range: [number, number];
  /** i18n keys so descriptions + kind chips translate. */
  descKey: string;
  kind: 'spectral' | 'thermal' | 'water' | 'weather';
  kindKey: string;
  /** Optional declared derivation relationship (mirrors channel registry). */
  derivedFrom?: string;
  provenanceDefault?: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
}

const INDICATOR_COLOR: Record<string, string> = {
  ndvi: '#16a34a', evi: '#65a30d', savi: '#059669', ndmi: '#0891b2',
  tvdi: '#ea580c', cwsi: '#dc2626', eta: '#0284c7', lst: '#9333ea',
  precip: '#475569', temp: '#b45309',
};
const INDICATOR_NAME: Record<string, string> = {
  ndvi: 'NDVI', evi: 'EVI', savi: 'SAVI', ndmi: 'NDMI', tvdi: 'TVDI',
  cwsi: 'CWSI', eta: 'ETa', lst: 'LST', precip: 'Precipitation', temp: 'Air Temp.',
};

export const INDICATORS: IndicatorDef[] = CHANNELS.map((c: ChannelSpec) => ({
  id: c.name as IndicatorId,
  name: INDICATOR_NAME[c.name] ?? c.name.toUpperCase(),
  unit: c.unit,
  color: INDICATOR_COLOR[c.name] ?? '#64748b',
  range: c.physicalRange,
  descKey: `indicator.${c.name}.desc`,
  kind: c.kind,
  kindKey: `kind.${c.kind}`,
  derivedFrom: c.derivedFrom,
  provenanceDefault: c.provenanceDefault,
}));

export const indicatorById = (id: IndicatorId) => INDICATORS.find(i => i.id === id) || INDICATORS[0];

/**
 * Field attributes come straight from the registry (`farms.parquet`). A value
 * the registry does not have is `null` — the UI renders a "not recorded" state
 * instead of substituting an invented default (wire-platform-to-real-data:
 * "no synthesized strings in the payload").
 */
export interface Field {
  id: string;
  code: string;
  name: string;
  farm: string;
  municipality: string;
  block: string | null;
  areaHa: number | null;
  variety: string | null;
  planted: string | null;
  harvest: string | null;
  centroid: [number, number];
  polygon: [number, number][]; // [lat, lng]
  baselineHealth: number | null;
  neighbors: string[];
  contractVersion?: number;
}


type RawFarm = {
  id?: string; code?: string; name?: string; farm?: string; municipality?: string; block?: string;
  areaHa?: number; variety?: string; planted?: string | null; harvest?: string | null;
  centroid?: [number, number]; polygon?: [number, number][]; baselineHealth?: number;
  neighbors?: string[]; contractVersion?: number;
};

export const KHUZESTAN_CENTROID: [number, number] = [31.0217, 48.2794];

export const FIELDS: Field[] = ((farmsKhuzestanData ?? []) as unknown as RawFarm[]).map((f, i) => ({
  id: f.id ?? `F-${String(i + 1).padStart(3, '0')}`,
  code: f.code ?? '',
  name: f.name ?? '',
  farm: f.farm ?? '',
  municipality: f.municipality ?? '',
  block: f.block || null,
  areaHa: typeof f.areaHa === 'number' && Number.isFinite(f.areaHa) ? f.areaHa : null,
  variety: f.variety || null,
  planted: f.planted ?? null,
  contractVersion: f.contractVersion ?? 3,
  harvest: f.harvest ?? null,
  centroid: f.centroid ?? KHUZESTAN_CENTROID,
  polygon: f.polygon ?? [],
  baselineHealth: typeof f.baselineHealth === 'number' && Number.isFinite(f.baselineHealth) ? f.baselineHealth : null,
  neighbors: f.neighbors ?? [],
}));

export const hasFields = FIELDS.length > 0;

/** True when any field was loaded without contractVersion >= 4 (legacy payload;
 * v5 farm records carry the same version number as the series payload). */
export const isLegacyPayload = !FIELDS.length
  ? false
  : (farmsKhuzestanData as any[]).some(f => (f?.contractVersion ?? 0) < 4);

const PLACEHOLDER_FIELD: Field = {
  id: '', code: '—', name: '—', farm: '—', municipality: '—', block: null, areaHa: null,
  variety: null, planted: null, harvest: null, centroid: KHUZESTAN_CENTROID, polygon: [],
  baselineHealth: null, neighbors: [],
};

/**
 * Field lookup that never returns `undefined` for an empty dataset — callers
 * guard on `hasFields`, and the inspector falls back to a placeholder record
 * instead of crashing on `FIELDS[0].id` (BUG-05 in docs/platform_bug_audit.md).
 */
export const fieldById = (id: string): Field => FIELDS.find(f => f.id === id) ?? FIELDS[0] ?? PLACEHOLDER_FIELD;


// ── Time axis: single source of truth ────────────────────────────────────────
// The axis is EVERY acquisition date of the archive (contract v4/v5 payload,
// first row -> last row); every slider, chart and label derives from it.
const KHU_SERIES = JSON.parse(khuSeriesRaw) as SeriesPayload;

/**
 * Causal stress flag per observation (contract v5): "normal" /
 * "suspected_stress" / "no_data" from the main checkpoint's raw bin scores
 * vs the sidecar tau with persistence k; `null` = a model-backed flag exists
 * in the contract but is unavailable (no main checkpoint loaded);
 * `undefined` = v4 payload (flag concept absent → UI shows "unavailable").
 */
export type StressFlag = 'normal' | 'suspected_stress' | 'no_data';

/** Split membership tag per observation (contract v5). Train cycles are
 * in-sample: their scores/flags are optimistic and must be read as such. */
export type SplitTag = 'train' | 'dev' | 'test' | 'monitoring';

function decodeField(payload: SeriesPayload, fid: string): Obs[] {
  const f = payload.fields[fid] as SeriesFieldEntry | undefined;
  if (!f) return [];
  const n = payload.axis.length;
  const channelOrder = CHANNEL_NAMES;
  // v5 payloads carry stressFlag/stressFlagModel/split; v4 payloads do not
  // (the fields stay undefined → the UI shows the flag as unavailable).
  const isV5 = payload.contractVersion >= 5;
  const stressArr = isV5 && f.stressFlag ? expandRle(f.stressFlag as [string, number][], n) : null;
  const stressModelArr = isV5 && f.stressFlagModel ? expandRle(f.stressFlagModel as [string, number][], n) : null;
  const splitArr = isV5 && f.split ? expandRle(f.split as [string, number][], n) : null;
  const scoreFormulas = isV5 ? (payload as V5Payload).scoreFormulas : undefined;
  {
    const chanProv: Record<string, string[]> = {};
    for (const c of channelOrder) chanProv[c] = expandRle(f.channelProvenance[c], n);
    const scoreProv: Record<string, string[]> = {};
    for (const k of SCORE_KEYS) scoreProv[k] = expandRle(f.scoreProvenance[k], n);
    const ndviArr = f.channels.ndvi;
    const obs: Obs[] = [];
    for (let i = 0; i < n; i++) {
      const date = payload.axis[i];
      const missing = ndviArr[i] == null;
      const scores = {} as Record<ModelId, number | null>;
      const scoreProvMap = {} as Record<ModelId, ScoreProvenanceState>;
      const scoreFormula = {} as Record<ModelId, string | null>;
      for (const k of SCORE_KEYS) {
        scores[k] = f.scores[k][i];
        const st = scoreProv[k][i];
        scoreProvMap[k] = (st === "model" || st === "proxy" || st === "absent" ? st : "absent") as ScoreProvenanceState;
        // Derived from provenance exactly as the exporter records it:
        // v5 model -> payload.scoreFormulas[k] ("<stem>:causal_bin_mse" for the
        // causal main checkpoints, "<stem>_490:bin_mse_1mexp" for legacy),
        // v4 model -> "<model>_490:bin_mse_1mexp", v4 proxy -> proxyFormulaId,
        // absent -> null.
        scoreFormula[k] =
          st === "model"
            ? scoreFormulas?.[k] ?? `${payload.checkpoints[k] ?? k}:bin_mse_1mexp`
            : st === "proxy" ? (payload as V4Payload).proxyFormulaId : null;
      }
      const channels = {} as Record<string, number | null>;
      for (const c of channelOrder) channels[c] = f.channels[c][i];
      const provenance = {} as ObsProvenance;
      for (const c of channelOrder) (provenance as unknown as Record<string, string>)[c] = chanProv[c][i];
      obs.push({
        date,
        sampleDate: date,
        idx: i,
        acquisitionDate: date,
        missing,
        stalenessReason: missing ? "invalid acquisition" : null,
        ndvi: channels.ndvi,
        evi: channels.evi,
        savi: channels.savi,
        ndmi: channels.ndmi,
        tvdi: channels.tvdi,
        cwsi: channels.cwsi,
        eta: channels.eta,
        lst: channels.lst,
        precip: channels.precip,
        temp: channels.temp,
        scores,
        scoreProvenance: scoreProvMap,
        scoreFormulaId: scoreFormula,
        provenance,
        scoreCollinearity: payload.collinearity,
        stressFlag: stressArr ? (stressArr[i] as StressFlag | null) : undefined,
        stressFlagModel: stressModelArr ? (stressModelArr[i] as string | null) : undefined,
        split: splitArr ? (splitArr[i] as SplitTag) : undefined,
      });
    }
    return obs;
  }
}

export const DATES: string[] = KHU_SERIES.axis;
export const N = DATES.length;
/** Last valid index for the shared date axis (0 when empty — never `NaN`). */
export const LAST_IDX = Math.max(0, N - 1);

/** Clamp an arbitrary index into the shared date axis. */
export const clampIdx = (i: number) => Math.max(0, Math.min(LAST_IDX, Math.round(Number.isFinite(i) ? i : 0)));

/** Convenience: ISO month for an index, or "" when the axis is empty. */
export const dateAt = (i: number) => DATES[clampIdx(i)] ?? "";

// ── Data provenance ──────────────────────────────────────────────────────────
// `series_khuzestan.json` (contract v5) samples EVERY Landsat/METRIC
// acquisition date. Scores come ONLY from trained checkpoints where the
// acquisition maps to a cycle bin (v5 removed the CWSI proxy fallback — see
// scripts/load_model_checkpoints.py and spec model-output-ingest); everything
// else is null + "absent". `scoresAreProxy` is derived from the payload so the
// pipeline-output labelling stays honest.
const payloadHasModelScores = Object.values(KHU_SERIES.fields).some(f =>
  Object.values(f.scoreProvenance).some(runs => runs.some(([state]) => state === "model")),
);
export const DATA_PROVENANCE = {
  /** Series actually rendered by the views. */
  source: "series_khuzestan.json",
  exporter: "scripts/export_platform_data.py",
  /** True while NO observation carries a model-backed score (v5: slots are
   * absent, not proxy — there is no proxy fallback anymore). */
  scoresAreProxy: !payloadHasModelScores,
  /** Number of fields that carry a time series. */
  fieldCount: Object.keys(KHU_SERIES.fields).length,
  /** Observation dates represented by the shared axis. */
  months: N,
  /** First and last date on the axis (ISO). */
  firstDate: DATES[0] ?? "",
  lastDate: DATES[N - 1] ?? "",
} as const;

export interface ObsProvenance {
  ndvi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  evi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  savi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  ndmi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  tvdi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  cwsi: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  eta: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  lst: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  precip: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
  temp: 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy';
}

export interface Obs {
  date: string;
  sampleDate: string;
  idx: number;
  acquisitionDate: string | null;
  missing: boolean;
  stalenessReason: string | null;
  ndvi: number | null;
  evi: number | null;
  savi: number | null;
  ndmi: number | null;
  tvdi: number | null;
  cwsi: number | null;
  eta: number | null;
  lst: number | null;
  precip: number | null;
  temp: number | null;
  /** Null when no score exists (no acquisition / absent provenance) — never a
   * substituted constant. Charts skip null points. */
  scores: Record<ModelId, number | null>;
  /** Per-score provenance: "model" | "proxy" | "absent" (v5 payloads only
   * ever use model|absent — the proxy fallback was removed). */
  scoreProvenance: Record<ModelId, ScoreProvenanceState> | null;
  /** Per-score formula id: checkpoint formula for "model", null otherwise. */
  scoreFormulaId: Record<ModelId, string | null> | null;
  provenance: ObsProvenance | null;
  scoreCollinearity: string | null;
  /** Causal stress flag (v5): normal | suspected_stress | no_data; null when
   * no main checkpoint backs the flag; undefined on v4 payloads. */
  stressFlag?: StressFlag | null;
  /** Checkpoint id that produced the stress flag (null when unavailable). */
  stressFlagModel?: string | null;
  /** Split membership of the observation's cycle (v5); undefined on v4. */
  split?: SplitTag | null;
}

const SCORE_KEYS = MODELS.map(m => m.id);

/**
 * Contract v4 payload: a shared acquisition-date axis plus per-field numeric
 * arrays and run-length-encoded provenance. Decoding reconstructs the exact
 * per-observation objects the views consume (the v3 `Obs` shape) without any
 * of the string redundancy that made the full-archive payload ~292 MB.
 */
interface V4Payload {
  contractVersion: number;
  axis: string[];
  collinearity: string;
  checkpoints: Record<string, string>;
  proxyFormulaId: string;
  fields: Record<string, {
    channels: Record<string, (number | null)[]>;
    scores: Record<string, (number | null)[]>;
    channelProvenance: Record<string, [string, number][]>;
    scoreProvenance: Record<string, [string, number][]>;
  }>;
}

/**
 * Contract v5 payload: extends v4 with the causal stress-flag fields —
 * `stressFlag` / `stressFlagModel` / `split` per observation (string-RLE like
 * the provenance series; null values RLE-encode as `[null, count]`) and
 * `ladderRung` per field from the main checkpoint sidecar. v5 has no
 * `proxyFormulaId`: no observation carries the removed CWSI proxy formula.
 */
interface V5Payload {
  contractVersion: number;
  axis: string[];
  collinearity: string;
  checkpoints: Record<string, string>;
  /** Per score key: the formula id its "model"-provenance observations carry. */
  scoreFormulas: Record<string, string>;
  fields: Record<string, {
    channels: Record<string, (number | null)[]>;
    scores: Record<string, (number | null)[]>;
    channelProvenance: Record<string, [string, number][]>;
    scoreProvenance: Record<string, [string, number][]>;
    stressFlag: [string | null, number][];
    stressFlagModel: [string | null, number][];
    split: [string, number][];
    ladderRung: string | null;
  }>;
}

type SeriesPayload = V4Payload | V5Payload;

/** Field entry as read from either payload version (v5 fields are optional). */
type SeriesFieldEntry = V4Payload['fields'][string] & Partial<V5Payload['fields'][string]>;

/**
 * Ladder rung of the main checkpoint sidecar for a field ("L1".."L5"; null
 * when no main checkpoint backs the payload or the field). Validation-ladder
 * semantics: every claim the UI makes about stress flags is bounded by this
 * rung (v5 spec: honest naming until L4).
 */
export function ladderRungFor(fieldId: string): string | null {
  const f = KHU_SERIES.fields[fieldId] as V5Payload['fields'][string] | undefined;
  return f && 'ladderRung' in f ? (f.ladderRung ?? null) : null;
}

/** Expand `[state, count]` runs into a per-index state array. */
function expandRle(runs: [string, number][], length: number): string[] {
  const out: string[] = [];
  for (const [state, count] of runs) {
    for (let i = 0; i < count; i++) out.push(state);
  }
  if (out.length !== length) {
    // A malformed payload must fail loudly, not silently mislabel observations.
    throw new Error(`RLE length ${out.length} != axis length ${length}`);
  }
  return out;
}


/**
 * Normalise one exported observation. Exported payloads are read with
 * `as unknown` because JSON imports are untyped; this keeps the rest of the
 * app on the strongly-typed `Obs` shape. Missing channels become `null` and
 * carry `provenance: "absent"` — no constant substitutions.
 */

/**
 * `value(obs, channel)` returns the measurement or `NaN` for null/missing.
 * Route every statistics call site through this helper instead of reading
 * raw channel numbers directly.
 */
export function value(obs: Obs | undefined | null, channel: keyof ObsProvenance): number {
  if (!obs) return NaN;
  const v = obs[channel];
  return typeof v === 'number' && Number.isFinite(v) ? v : NaN;
}


const fieldCache = new Map<string, Obs[]>();

/** Fields that actually carry a time series — data-driven replacement for "48 fields" labels. */
// A field carries a series iff the payload contains it — checked on the raw
// parsed payload so startup does no per-field decoding at all.
export const FIELDS_WITH_SERIES: Field[] = FIELDS.filter(f => KHU_SERIES.fields[f.id] !== undefined);

/**
 * Time series for a field, read from the exported `series_khuzestan.json`.
 * An unknown/absent field returns the empty array rather than throwing, so the
 * views' empty-state guards stay reachable (spec: "Empty data guard").
 */
export function getSeries(fieldId: string): Obs[] {
  const cached = fieldCache.get(fieldId);
  if (cached) return cached;
  // Lazy per-field decode of the compact payload: a field costs ~1 ms, so
  // startup only parses the JSON (no 263k-object construction).
  const obs = decodeField(KHU_SERIES, fieldId);
  fieldCache.set(fieldId, obs);
  return obs;
}

/** Safe observation accessor — clamps the index and tolerates empty series. */
export function obsAt(series: Obs[], idx: number): Obs | undefined {
  if (!series.length) return undefined;
  return series[clampIdx(idx)];
}

// ── Statistical Helper Functions ──────────────────────────────────────────────
export function pearson(xs: number[], ys: number[]): number {
  const n = xs.length;
  if (n < 3) return NaN;
  const mx = mean(xs), my = mean(ys);
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < n; i++) {
    num += (xs[i] - mx) * (ys[i] - my);
    dx += (xs[i] - mx) ** 2;
    dy += (ys[i] - my) ** 2;
  }
  return dx && dy ? num / Math.sqrt(dx * dy) : NaN;
}

export function ranks(xs: number[]): number[] {
  const sorted = [...xs].map((v, i) => [v, i] as const).sort((a, b) => a[0] - b[0]);
  const r = new Array(xs.length);
  sorted.forEach(([, i], rank) => { r[i] = rank + 1; });
  return r;
}

export const spearman = (xs: number[], ys: number[]) => pearson(ranks(xs), ranks(ys));

export function kendall(xs: number[], ys: number[]): number {
  let c = 0, d = 0;
  for (let i = 0; i < xs.length; i++) {
    for (let j = i + 1; j < xs.length; j++) {
      const s = Math.sign(xs[j] - xs[i]) * Math.sign(ys[j] - ys[i]);
      if (s > 0) c++; else if (s < 0) d++;
    }
  }
  return (c + d) ? (c - d) / (c + d) : NaN;
}

export const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / (xs.length || 1);

export function std(xs: number[]) {
  const m = mean(xs);
  return Math.sqrt(mean(xs.map(x => (x - m) ** 2)));
}

export function quantile(xs: number[], q: number) {
  if (!xs.length) return NaN;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(q * s.length))];
}

export function linReg(xs: number[], ys: number[]) {
  const mx = mean(xs), my = mean(ys);
  let num = 0, den = 0;
  for (let i = 0; i < xs.length; i++) {
    num += (xs[i] - mx) * (ys[i] - my);
    den += (xs[i] - mx) ** 2;
  }
  const slope = den ? num / den : 0;
  return { slope, intercept: my - slope * mx, r2: pearson(xs, ys) ** 2 };
}

export function pValue(r: number, n: number): number {
  if (isNaN(r) || n < 4) return NaN;
  const t = r * Math.sqrt((n - 2) / Math.max(1e-9, 1 - r * r));
  const p = 2 * (1 - normCdf(Math.abs(t)));
  return Math.max(0.0001, Math.min(1, p));
}

function normCdf(x: number) {
  return 0.5 * (1 + erf(x / Math.SQRT2));
}

function erf(x: number) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return x < 0 ? -y : y;
}

export function fisherCI(r: number, n: number): [number, number] {
  if (isNaN(r) || n < 4) return [NaN, NaN];
  const z = Math.atanh(Math.max(-0.999, Math.min(0.999, r)));
  const se = 1 / Math.sqrt(n - 3);
  return [Math.tanh(z - 1.96 * se), Math.tanh(z + 1.96 * se)];
}

export function laggedCorr(xs: number[], ys: number[], maxLag = 6) {
  const out: { lag: number; r: number }[] = [];
  for (let lag = -maxLag; lag <= maxLag; lag++) {
    const a: number[] = [], b: number[] = [];
    for (let i = 0; i < xs.length; i++) {
      const j = i + lag;
      if (j >= 0 && j < ys.length) { a.push(xs[i]); b.push(ys[j]); }
    }
    out.push({ lag, r: pearson(a, b) });
  }
  return out;
}

export function partialCorr(xs: number[], ys: number[], zs: number[]): number {
  const rxy = pearson(xs, ys), rxz = pearson(xs, zs), ryz = pearson(ys, zs);
  const den = Math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2));
  return den ? (rxy - rxz * ryz) / den : NaN;
}

/**
 * Moran's I over areal units. Complete-case: pairs where either value is
 * missing are *skipped*, not folded in as fabricated zeros (the old
 * `?? 0` substitution in Spatial.tsx biased the statistic toward 0).
 */
export function moransI(values: (number | null)[], weights: Map<string, string[]>): number {
  const vals = values.map(v => (typeof v === "number" && Number.isFinite(v) ? v : NaN));
  const finite = vals.filter(v => Number.isFinite(v));
  if (finite.length < 2) return NaN;
  const m = mean(finite);
  let num = 0, den = 0, wsum = 0;
  vals.forEach(v => {
    if (Number.isFinite(v)) den += (v - m) ** 2;
  });
  weights.forEach((nbs, iStr) => {
    const i = parseInt(iStr, 10);
    const vi = vals[i];
    if (!Number.isFinite(vi)) return;
    nbs.forEach(jStr => {
      const j = parseInt(jStr, 10);
      const vj = vals[j];
      if (!Number.isFinite(vj)) return;
      num += (vi - m) * (vj - m);
      wsum++;
    });
  });
  if (!den || !wsum) return NaN;
  return (finite.length / wsum) * (num / den);
}

export function getPairs(model: ModelId, indicator: IndicatorId, fieldIds: string[], range: [number, number]) {
  const xs: number[] = [], ys: number[] = [], meta: { field: string; date: string }[] = [];
  const lo = Math.min(range[0], range[1]), hi = Math.max(range[0], range[1]);
  fieldIds.forEach(fid => {
    getSeries(fid).forEach(o => {
      if (o.idx < lo || o.idx > hi) return;
      const ind = (o as any)[indicator];
      const score = o.scores[model];
      if (typeof ind === 'number' && Number.isFinite(ind) && typeof score === 'number' && Number.isFinite(score)) {
        xs.push(score);
        ys.push(ind);
        meta.push({ field: fid, date: o.date });
      }
    });
  });
  return { xs, ys, meta };
}

export const ANOMALY_THRESHOLD = 0.55;

export function fmtDate(d: string) {
  return d.slice(0, 7);
}

export function downloadCSV(filename: string, rows: (string | number)[][]) {
  const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revoking synchronously can cancel the download in Chromium; defer one tick.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/**
 * Recharts x-axis `interval` for ~`target` labelled ticks over `n` points.
 * The full-archive axis has 538 dates — fixed intervals tuned for 48 points
 * produced 60–180 cramped, unreadable ticks.
 */
export const tickInterval = (n: number, target = 12) => (n <= target ? 0 : Math.ceil(n / target) - 1);

/**
 * Deterministic stride downsample for *displaying* scatter points. Statistics
 * (r, rho, regression, event tables) are always computed on the FULL series —
 * only the SVG layer is thinned, because Recharts renders one node per point
 * and 263k circles stall the page. `total` lets captions state what was shown.
 */
export function downsampleForDisplay<T>(points: T[], max = 5000): { points: T[]; total: number } {
  if (points.length <= max) return { points, total: points.length };
  const stride = Math.ceil(points.length / max);
  const out: T[] = [];
  for (let i = 0; i < points.length; i += stride) out.push(points[i]);
  return { points: out, total: points.length };
}

/** ISO month (`YYYY-MM`) used by every chart axis in both locales. */
export const monthAt = (i: number) => (dateAt(i) ? dateAt(i).slice(0, 7) : '—');

/** First/last ISO month on the shared axis, for captions. */
export const COVERAGE = {
  first: DATES[0]?.slice(0, 7) ?? '—',
  last: DATES[N - 1]?.slice(0, 7) ?? '—',
  yearStart: (DATES[0] ?? '').slice(0, 4) || '—',
  yearEnd: (DATES[N - 1] ?? '').slice(0, 4) || '—',
};
