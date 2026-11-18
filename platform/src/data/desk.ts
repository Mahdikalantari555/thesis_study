// ── Anomaly desk payload — replay of the stage-conditioned run ──────────────
// desk_khuzestan.json is produced ONLY by scripts/export_platform_data.py
// (desk export section) from reports/stage_conditioned_anomaly/*.parquet +
// summary.json + the farm registry (add-halqeh-anomaly-desk, design D2).
// The view never computes case data itself; this module parses the payload
// once (`?raw` + JSON.parse, same pattern as the ~86 MB series payload) and
// exposes typed accessors.
//
// Honesty contract (spec platform-anomaly-desk): every value here originates
// from the run artifacts; the desk renders flags as stage-conditioned NDVI
// anomalies UNDER REVIEW — never as confirmed stress. Validation ladder:
// L2–L3 evidence browsing only.
import deskRaw from "./desk_khuzestan.json?raw";

export type DeskStageId = "S1" | "S2" | "S3" | "S4";
/** Review verdicts are annotations, not labels (spec: "Verdicts are annotations"). */
export type DeskVerdict = "stress" | "delay" | "gap" | "clear";
export type DeskCaseKind = "slip" | "spared";
export type DeskFilter = "all" | "slip" | "spared" | "unread";
export type DeskMode = "envelope" | "naive";

export interface DeskBin {
  /** Original run bin index — gaps preserved (cloud gaps are not renumbered). */
  i: number;
  /** Progress through the cycle [0,1] — the ring's angle. */
  p: number;
  stage: DeskStageId;
  /** NDVI of the bin. */
  v: number;
  /** Stage floor (median − 2×MAD); negative floors exist (S3). */
  lo: number;
  hi: number;
  med: number;
  /** Bin date (ISO). */
  d: string;
  /** Flagged by the envelope (NDVI < stage floor). */
  f: boolean;
}

export interface DeskCase {
  id: string;
  field: number;
  fieldId: string;
  /** Registry identity — null when the registry has no value (never invented). */
  code: string | null;
  name: string | null;
  farm: string | null;
  municipality: string | null;
  variety: string | null;
  areaHa: number | null;
  lat: number | null;
  lng: number | null;
  cycle: number;
  lengthDays: number;
  censored: boolean;
  start: string;
  end: string;
  flags: number;
  /** Bins a blunt NDVI < naiveCut would mark (computed in the exporter). */
  naive: number;
  deepest: number;
  s2max: number | null;
  s3min: number | null;
  kind: DeskCaseKind;
  bins: DeskBin[];
}

export interface DeskEnvelope {
  median: number;
  mad: number;
  lo: number;
  hi: number;
  /** Pooled valid observations behind the envelope (from summary.json). */
  n: number;
}

export interface DeskStageRow {
  s: DeskStageId;
  /** Rows assigned to the stage in the replayed parquet. */
  n: number;
  flags: number;
  naive: number;
}

export interface DeskTotals {
  fieldsInRun: number;
  fieldsInRegistry: number;
  cycles: number;
  /** Published denominator: valid observations of the run (18,505). */
  validObsReported: number;
  /** Stage-assigned rows in the replayed parquet (17,143). */
  rows: number;
  flags: number;
  /** Published flag rate (over validObsReported), carried from summary.json. */
  flagRate: number;
  binDays: number;
  envelopeK: number;
  naiveCut: number;
  naiveOnly: number;
  envelopeOnly: number;
  overlap: number;
}

export interface DeskProvenance {
  gitSha: string | null;
  generatedAt: string;
  dataSource: string;
  seed: number;
  binDays: number;
  envelopeK: number;
  naiveCut: number;
  parquet: string;
  summary: string;
  registry: string;
  exporter: string;
}

export interface DeskPlace {
  n: number;
  lat: number;
  lng: number;
}

export interface DeskCorpus {
  contractVersion: number;
  /** Run date (YYYY-MM-DD, from summary.json generated_at). */
  generated: string;
  source: string;
  provenance: DeskProvenance;
  totals: DeskTotals;
  envelopes: Record<DeskStageId, DeskEnvelope>;
  stageRows: DeskStageRow[];
  cases: DeskCase[];
  places: DeskPlace[];
}

const desk = JSON.parse(deskRaw) as DeskCorpus;

export const DESK = desk;
export const DESK_CASES: DeskCase[] = desk.cases;
export const DESK_NAIVE_CUT = desk.totals.naiveCut;

/** Stage geometry (progress fractions) mirrors the run's stage assignment
 *  (scripts/stage_conditioned_anomaly.py STAGE_BOUNDS). Names/notes are i18n
 *  keys — see desk.stage.* in i18n/en.ts + fa.ts. */
export const DESK_STAGES: { id: DeskStageId; from: number; to: number; nameKey: string; noteKey: string }[] = [
  { id: "S1", from: 0.0, to: 0.25, nameKey: "desk.stage.s1.name", noteKey: "desk.stage.s1.note" },
  { id: "S2", from: 0.25, to: 0.6, nameKey: "desk.stage.s2.name", noteKey: "desk.stage.s2.note" },
  { id: "S3", from: 0.6, to: 0.85, nameKey: "desk.stage.s3.name", noteKey: "desk.stage.s3.note" },
  { id: "S4", from: 0.85, to: 1.0, nameKey: "desk.stage.s4.name", noteKey: "desk.stage.s4.note" },
];

export const deskCaseById = (id: string): DeskCase | undefined =>
  DESK_CASES.find(c => c.id === id);

/** First flagged bin position of a case — the review desk opens a slip on its
 *  deepest evidence instead of an empty selection. */
export const firstFlaggedIdx = (c: DeskCase): number => {
  const i = c.bins.findIndex(b => b.f);
  return i >= 0 ? i : 0;
};

/** Nearest scene date (ISO) to `binDate` from the tile server's scene index,
 *  within ±`windowDays` (the run's bin_days). Prefers scenes that serve the
 *  requested layer. Returns null when no scene qualifies. */
export function nearestScene(
  scenes: { date: string; has_rgb: boolean; has_ndvi: boolean }[],
  binDate: string,
  layer: "ndvi" | "rgb",
  windowDays: number,
): { date: string; has_rgb: boolean; has_ndvi: boolean } | null {
  const bin = Date.parse(binDate);
  if (!Number.isFinite(bin)) return null;
  let best: { date: string; has_rgb: boolean; has_ndvi: boolean; delta: number } | null = null;
  for (const s of scenes) {
    const delta = Math.abs(Date.parse(s.date) - bin);
    if (delta > windowDays * 86400000) continue;
    if (!(layer === "ndvi" ? s.has_ndvi : s.has_rgb)) continue;
    if (!best || delta < best.delta) best = { ...s, delta };
  }
  return best;
}
