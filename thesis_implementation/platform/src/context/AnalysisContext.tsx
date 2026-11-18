import React, { createContext, useContext, useMemo, useState } from "react";
import type { IndicatorId, ModelId } from "../data/data";
import { DATES, FIELDS, LAST_IDX } from "../data/data";

export interface Experiment {
  id: string;
  /** Model name + indicator name at save time (already localized when saved). */
  name: string;
  created: string;
  model: ModelId;
  indicator: IndicatorId;
  fields: string[];
  range: [number, number];
  note: string;
  stats: string;
}

interface Ctx {
  view: string; setView: (v: string) => void;
  dark: boolean; setDark: (d: boolean) => void;
  selectedField: string; setSelectedField: (id: string) => void;
  selectedFields: string[]; setSelectedFields: (ids: string[]) => void;
  toggleField: (id: string) => void;
  model: ModelId; setModel: (m: ModelId) => void;
  compareModels: ModelId[]; setCompareModels: (m: ModelId[]) => void;
  indicator: IndicatorId; setIndicator: (i: IndicatorId) => void;
  range: [number, number]; setRange: (r: [number, number]) => void;
  experiments: Experiment[]; addExperiment: (e: Experiment) => void; removeExperiment: (id: string) => void;
  showDemoBanner: boolean; setShowDemoBanner: (b: boolean) => void;
}

const AnalysisCtx = createContext<Ctx>(null!);
export const useAnalysis = () => useContext(AnalysisCtx);

/**
 * Default selection, derived from whatever data is actually loaded.
 *
 * The previous implementation hard-coded `FIELDS[9].id` / `FIELDS[10]` /
 * `FIELDS[18]`, which throws on an empty or short dataset (BUG-05). Every
 * access is now optional-chained and falls back to `''`, satisfying the
 * "Empty data guard" scenario of the bug-audit spec.
 */
const defaultFieldId = FIELDS[0]?.id ?? "";
const defaultSelectedFields = FIELDS.slice(0, 3).map(f => f.id);

const defaultRange: [number, number] = [0, LAST_IDX];

/** Comfortable default view: the stress window of the demonstration series. */
const defaultDateIdx = (() => {
  if (!DATES.length) return 0;
  const i = DATES.findIndex(d => d.startsWith("2023-06"));
  return i >= 0 ? i : Math.min(LAST_IDX, Math.floor(LAST_IDX / 2));
})();

export const DEFAULT_DATE_IDX = defaultDateIdx;

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [view, setView] = useState("overview");
  const [dark, setDark] = useState(false);
  const [selectedField, setSelectedField] = useState(defaultFieldId);
  const [selectedFields, setSelectedFields] = useState<string[]>(defaultSelectedFields);
  const [model, setModel] = useState<ModelId>("b1_dsh");
  const [compareModels, setCompareModels] = useState<ModelId[]>([
    "b1_dsh",
    "b1_cusum",
    "masked_transformer",
    "sts_net",
    "tiny_cnn_mamba",
    "time2agri",
  ]);
  const [indicator, setIndicator] = useState<IndicatorId>("ndvi");
  const [range, setRangeState] = useState<[number, number]>(defaultRange);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [showDemoBanner, setShowDemoBanner] = useState(true);

  /** Keep the shared range inside the loaded date axis, ordered and non-empty. */
  const setRange = (next: [number, number]) => {
    const lo = Math.max(0, Math.min(LAST_IDX, Math.min(next[0], next[1])));
    const hi = Math.max(0, Math.min(LAST_IDX, Math.max(next[0], next[1])));
    setRangeState([lo, hi]);
  };

  const toggleField = (id: string) => {
    if (!id) return;
    setSelectedField(id);
    setSelectedFields(prev => (prev.includes(id) ? prev : [...prev, id].slice(-8)));
  };

  const value = useMemo<Ctx>(
    () => ({
      view, setView, dark, setDark, selectedField, setSelectedField, selectedFields, setSelectedFields, toggleField,
      model, setModel, compareModels, setCompareModels, indicator, setIndicator, range, setRange,
      experiments,
      addExperiment: e => setExperiments(p => [e, ...p]),
      removeExperiment: id => setExperiments(p => p.filter(x => x.id !== id)),
      showDemoBanner, setShowDemoBanner,
    }),
    // `setRange`/`toggleField` only close over setState functions (stable).
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [view, dark, selectedField, selectedFields, model, compareModels, indicator, range, experiments, showDemoBanner]
  );

  return <AnalysisCtx.Provider value={value}>{children}</AnalysisCtx.Provider>;
}
