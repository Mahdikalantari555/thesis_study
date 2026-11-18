// ── Desk annotation persistence (add-halqeh-anomaly-desk, design D3) ─────────
// Verdicts and notes are device-local (labelled "kept on this device" in the
// UI) — localStorage under platform-desk namespaced keys, corrupt payloads
// start clean instead of crashing. Export (D7) is the durability path; nothing
// server-side reads these back.

import type { DeskVerdict } from "../data/desk";

export const DESK_STORAGE_KEYS = {
  verdicts: "platform.desk.verdicts",
  notes: "platform.desk.notes",
  ui: "platform.desk.ui",
} as const;

export interface DeskVerdictEntry {
  verdict: DeskVerdict;
  updatedAt: string;
}

export interface DeskNoteEntry {
  note: string;
  updatedAt: string;
}

export type DeskVerdicts = Record<string, DeskVerdictEntry>;
export type DeskNotes = Record<string, DeskNoteEntry>;

export interface DeskUiState {
  caseId: string | null;
  mode: "envelope" | "naive";
  filter: "all" | "slip" | "spared" | "unread";
}

const VERDICTS: readonly DeskVerdict[] = ["stress", "delay", "gap", "clear"];

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/** Read + validate a JSON value from localStorage; any corruption → null
 *  (callers fall back to defaults — a corrupt payload never crashes the desk). */
export function readStoredJson(key: string, validate?: (v: unknown) => boolean): unknown | null {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw == null) return null;
    const parsed: unknown = JSON.parse(raw);
    if (validate && !validate(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

/** Persist JSON; storage-disabled browsers degrade to in-memory state. */
export function writeStoredJson(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage disabled — in-memory only */
  }
}

export function validateVerdicts(v: unknown): v is DeskVerdicts {
  if (!isRecord(v)) return false;
  return Object.values(v).every(
    e => isRecord(e) && VERDICTS.includes(e.verdict as DeskVerdict) && typeof e.updatedAt === "string",
  );
}

export function validateNotes(v: unknown): v is DeskNotes {
  if (!isRecord(v)) return false;
  return Object.values(v).every(
    e => isRecord(e) && typeof e.note === "string" && typeof e.updatedAt === "string",
  );
}

export function validateUiState(v: unknown): v is DeskUiState {
  if (!isRecord(v)) return false;
  return (
    (v.caseId === null || typeof v.caseId === "string") &&
    (v.mode === "envelope" || v.mode === "naive") &&
    (v.filter === "all" || v.filter === "slip" || v.filter === "spared" || v.filter === "unread")
  );
}

export function loadDeskVerdicts(): DeskVerdicts {
  return readStoredJson(DESK_STORAGE_KEYS.verdicts, validateVerdicts) as DeskVerdicts | null ?? {};
}

export function loadDeskNotes(): DeskNotes {
  return readStoredJson(DESK_STORAGE_KEYS.notes, validateNotes) as DeskNotes | null ?? {};
}

export function loadDeskUi(): DeskUiState | null {
  return readStoredJson(DESK_STORAGE_KEYS.ui, validateUiState) as DeskUiState | null;
}

export function saveDeskVerdicts(v: DeskVerdicts): void {
  writeStoredJson(DESK_STORAGE_KEYS.verdicts, v);
}

export function saveDeskNotes(n: DeskNotes): void {
  writeStoredJson(DESK_STORAGE_KEYS.notes, n);
}

export function saveDeskUi(ui: DeskUiState): void {
  writeStoredJson(DESK_STORAGE_KEYS.ui, ui);
}
