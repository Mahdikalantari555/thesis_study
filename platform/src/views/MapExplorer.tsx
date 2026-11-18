import { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";
import MapView from "../components/MapView";
import { Panel, Badge, Label, Select, PipelineDataBadge, EmptyState, anomalyColor, fmtObs, ProvenanceChip, ProvenanceSummary, LegacyPayloadNotice, StressFlagChip, SplitTagChip } from "../components/ui";
import { useAnalysis, DEFAULT_DATE_IDX } from "../context/AnalysisContext";
import { FIELDS, MODELS, INDICATORS, getSeries, fieldById, DATES, LAST_IDX, ANOMALY_THRESHOLD, mean, COVERAGE, dateAt, clampIdx, isLegacyPayload, tickInterval, ladderRungFor } from "../data/data";
import { useLocale, useT } from "../i18n";
import scenesIndexData from "../data/scenes_index.json";
import { Eye, EyeOff, Search, GitCompareArrows } from "lucide-react";

// Scene manifest produced by scripts/build_tile_index.py (add-rgb-ndvi-tile-layer).
// Dates drive the local tile server URL; entries without rgb/ndvi bands are
// simply absent from the raster controls below.
interface SceneEntry {
  date: string;
  path: string;
  bounds: number[];
  bands: string[];
  has_rgb: boolean;
  has_ndvi: boolean;
}

const SCENES = (scenesIndexData as { scenes: SceneEntry[] }).scenes;

export default function MapExplorer() {
  const { selectedField, selectedFields, toggleField, model, setModel, indicator, setIndicator, range, setView } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();

  const [colorMode, setColorMode] = useState<"anomaly" | "indicator" | "health" | "lisa">("anomaly");
  const [dateIdx, setDateIdx] = useState(clampIdx(DEFAULT_DATE_IDX));
  const [opacity, setOpacity] = useState(0.85);
  const [showFields, setShowFields] = useState(true);
  const [query, setQuery] = useState("");
  const [compareIdx, setCompareIdx] = useState(clampIdx(DEFAULT_DATE_IDX - 12 >= 0 ? DEFAULT_DATE_IDX - 12 : 0));
  const [showCompare, setShowCompare] = useState(false);
  const [rasterLayer, setRasterLayer] = useState<"rgb" | "ndvi">("rgb");
  const [rasterOpacity, setRasterOpacity] = useState(0.7);

  const field = fieldById(selectedField);
  const series = getSeries(selectedField);
  const safeDateIdx = clampIdx(dateIdx);
  const safeCompareIdx = clampIdx(compareIdx);
  const obs = series[safeDateIdx];
  // Validation-ladder rung of the main checkpoint backing the stress flag
  // (per-field payload value; null without a checkpoint — never claimed).
  const ladderRung = ladderRungFor(selectedField);

  // One date control drives both layers: the observation-date slider selects
  // the field series point, and the raster overlay shows that observation's
  // *real* Landsat acquisition (the scenes_index entry for the same date).
  // When the observation has no acquisition (staleness guard) or the scene
  // lacks the requested bands, the overlay stays off (wire-platform-to-real-
  // data task 6.3 — the separate "Landsat raster scene" select was removed).
  const rasterSceneEntry = useMemo(
    () => (obs?.acquisitionDate ? SCENES.find(s => s.date === obs.acquisitionDate) ?? null : null),
    [obs?.acquisitionDate]
  );
  const rasterLayerActive = useMemo<"rgb" | "ndvi" | null>(() => {
    if (!rasterSceneEntry) return null;
    if (rasterLayer === "rgb" && rasterSceneEntry.has_rgb) return "rgb";
    if (rasterLayer === "ndvi" && rasterSceneEntry.has_ndvi) return "ndvi";
    if (rasterSceneEntry.has_rgb) return "rgb";
    if (rasterSceneEntry.has_ndvi) return "ndvi";
    return null;
  }, [rasterSceneEntry, rasterLayer]);
  const rasterDate = rasterLayerActive ? obs?.acquisitionDate ?? null : null;

  const chartData = series.map(o => ({
    date: o.date.slice(0, 7),
    score: o.scores?.[model] != null ? +Number(o.scores[model]).toFixed(3) : null,
    ind: (() => { const v = (o as unknown as Record<string, number | null>)[indicator]; return v != null && Number.isFinite(v) ? +Number(v).toFixed(3) : null; })(),
  }));

  const filtered = useMemo(
    () => FIELDS.filter(f => `${f.code} ${f.name} ${f.municipality} ${f.farm}`.toLowerCase().includes(query.toLowerCase())),
    [query]
  );
  const selectedStats = useMemo(() => {
    const vals = selectedFields.map(fid => getSeries(fid)[safeDateIdx]?.scores[model]).filter((v): v is number => typeof v === "number");
    if (!vals.length) return { mean: NaN, max: NaN, min: NaN };
    return { mean: mean(vals), max: Math.max(...vals), min: Math.min(...vals) };
  }, [selectedFields, safeDateIdx, model]);

  if (!FIELDS.length || !series.length) {
    return <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />;
  }

  return (
    <div className="grid grid-cols-12 gap-4">
      {/* Left controls */}
      <div className="col-span-12 lg:col-span-3 space-y-4">
        {isLegacyPayload && <LegacyPayloadNotice />}
        <Panel title={t("map.layer.title")}>
          <div className="space-y-3">
            <div>
              <Label>{t("map.layer.colourBy")}</Label>
              <Select value={colorMode} onChange={v => setColorMode(v as typeof colorMode)} className="w-full">
                <option value="anomaly">{t("map.layer.anomalyScore", { model: t(`model.${model}.name`) })}</option>
                <option value="indicator">{t("map.layer.indicator", { indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })}</option>
                <option value="health">{t("map.layer.health")}</option>
                <option value="lisa">{t("map.layer.lisa")}</option>
              </Select>
            </div>
            <div>
              <Label>{t("map.layer.model")}</Label>
              <Select value={model} onChange={v => setModel(v as typeof model)} className="w-full">
                {MODELS.map(m => (
                  <option key={m.id} value={m.id}>
                    {t(`model.${m.id}.name`)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("map.layer.indicatorLabel")}</Label>
              <Select value={indicator} onChange={v => setIndicator(v as typeof indicator)} className="w-full">
                {INDICATORS.map(i => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </Select>
            </div>
            {rasterSceneEntry && (
              <>
                <div>
                  <Label>{t("map.layer.rasterLayer")}</Label>
                  <Select value={rasterLayerActive ?? rasterLayer} onChange={v => setRasterLayer(v as "rgb" | "ndvi")} className="w-full">
                    {rasterSceneEntry.has_rgb && <option value="rgb">{t("map.layer.rasterRgb")}</option>}
                    {rasterSceneEntry.has_ndvi && <option value="ndvi">{t("map.layer.rasterNdvi")}</option>}
                  </Select>
                </div>
                <div>
                  <Label>{t("map.layer.rasterOpacity", { value: fmt.number(rasterOpacity, 2) })}</Label>
                  <input type="range" min={0} max={1} step={0.05} value={rasterOpacity} onChange={e => setRasterOpacity(+e.target.value)} aria-label={t("map.layer.rasterOpacity", { value: fmt.number(rasterOpacity, 2) })} className="w-full accent-teal-700" />
                </div>
                <div className="text-[10px] text-slate-400 font-mono" dir="ltr">
                  {t("map.layer.rasterSceneDate", { date: rasterSceneEntry.date })}
                </div>
              </>
            )}
            <div className="text-[10px] text-slate-400">{t("map.layer.rasterNote")}</div>
            <div>
              <Label>
                {t("map.layer.observationDate", { date: dateAt(safeDateIdx) })} {obs?.missing && <span className="text-orange-600">{t("field.missing")}</span>}
              </Label>
              {/* Slider bounds are derived from the shared date axis (BUG-01).
                  This single slider drives both the field series and the raster
                  overlay (task 6.3). */}
              <input type="range" min={0} max={LAST_IDX} value={safeDateIdx} onChange={e => setDateIdx(+e.target.value)} aria-label={t("map.layer.rangeStart")} className="w-full accent-teal-700" />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>{COVERAGE.first}</span>
                <span>{COVERAGE.last}</span>
              </div>
            </div>
            <div>
              <Label>{t("map.layer.opacity", { value: fmt.number(opacity, 2) })}</Label>
              {/* min 0: the field layer must be fadable to invisible (task 6.2);
                  full removal is the Hide toggle next to it. */}
              <input type="range" min={0} max={1} step={0.05} value={opacity} onChange={e => setOpacity(+e.target.value)} aria-label={t("map.layer.opacity", { value: fmt.number(opacity, 2) })} className="w-full accent-teal-700" />
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="flex items-center gap-1.5">
                {showFields ? <Eye size={13} /> : <EyeOff size={13} />} {t("map.layer.boundaries")}
              </span>
              <button onClick={() => setShowFields(!showFields)} className="text-[11px] border border-slate-300 dark:border-slate-700 px-2 py-1">
                {showFields ? t("ui.hide") : t("ui.show")}
              </button>
            </div>
            <button onClick={() => setShowCompare(!showCompare)} className="w-full flex items-center justify-center gap-2 h-8 border border-slate-300 dark:border-slate-700 text-[12px] hover:bg-slate-50 dark:hover:bg-slate-800">
              <GitCompareArrows size={13} /> {showCompare ? t("map.layer.hideCompare") : t("map.layer.compare")}
            </button>
            {showCompare && (
              <div>
                <Label>{t("map.layer.comparisonDate", { date: dateAt(safeCompareIdx) })}</Label>
                <input type="range" min={0} max={LAST_IDX} value={safeCompareIdx} onChange={e => setCompareIdx(+e.target.value)} aria-label={t("map.layer.comparisonDate", { date: dateAt(safeCompareIdx) })} className="w-full accent-orange-600" />
              </div>
            )}
          </div>
        </Panel>

        <Panel title={t("map.legend.title")}>
          {colorMode === "anomaly" && (
            <div className="space-y-1.5 text-[11px]">
              {[
                ["#be123c", t("legend.severe")],
                ["#ea580c", t("legend.high")],
                ["#d97706", t("legend.elevated")],
                ["#65a30d", t("legend.mild")],
                ["#0f766e", t("legend.nominal")],
              ].map(([c, l]) => (
                <div key={l} className="flex items-center gap-2">
                  <span className="w-3 h-3 shrink-0" style={{ background: c }} />
                  {l}
                </div>
              ))}
            </div>
          )}
          {colorMode === "lisa" && (
            <div className="space-y-1.5 text-[11px]">
              {[
                ["#be123c", t("legend.highHigh")],
                ["#2563eb", t("legend.highLow")],
                ["#7c3aed", t("legend.lowHigh")],
                ["#94a3b8", t("legend.lowLow")],
              ].map(([c, l]) => (
                <div key={l} className="flex items-center gap-2">
                  <span className="w-3 h-3 shrink-0" style={{ background: c }} />
                  {l}
                </div>
              ))}
            </div>
          )}
          {colorMode === "indicator" && <div className="text-[11px] text-slate-600 dark:text-slate-400">{t("map.legend.indicatorNote", { indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })}</div>}
          {colorMode === "health" && (
            <div className="space-y-1.5 text-[11px]">
              {[
                ["#15803d", t("legend.highBaseline")],
                ["#65a30d", t("legend.medium")],
                ["#d97706", t("legend.low")],
              ].map(([c, l]) => (
                <div key={l} className="flex items-center gap-2">
                  <span className="w-3 h-3 shrink-0" style={{ background: c }} />
                  {l}
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title={t("map.search.title")} pad={false}>
          <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <Search size={13} className="text-slate-400" />
            <input value={query} onChange={e => setQuery(e.target.value)} placeholder={t("map.search.placeholder")} className="flex-1 text-[12px] bg-transparent outline-none" />
          </div>
          <div className="max-h-64 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.map(f => {
              const s = getSeries(f.id)[safeDateIdx]?.scores[model];
              return (
                <button
                  key={f.id}
                  onClick={() => toggleField(f.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-start text-[11px] hover:bg-slate-50 dark:hover:bg-slate-800/60 ${f.id === selectedField ? "bg-teal-50 dark:bg-teal-950/40" : ""}`}
                >
                  <span className="w-2 h-2 shrink-0" style={{ background: s == null ? "#cbd5e1" : anomalyColor(s) }} />
                  <span className="flex-1 min-w-0">
                    <span className="block font-mono font-medium">{f.code}</span>
                    <span className="block text-slate-500 truncate">
                      {f.municipality} · {f.areaHa != null ? f.areaHa : "—"} {t("map.tooltip.ha")}
                    </span>
                  </span>
                  <span className="font-mono">{s == null ? "—" : fmt.number(s, 2)}</span>
                </button>
              );
            })}
            {!filtered.length && <div className="p-4 text-[11px] text-slate-500">{t("map.search.empty")}</div>}
          </div>
        </Panel>
      </div>

      {/* Map */}
      <div className="col-span-12 lg:col-span-6 space-y-4">
        <Panel
          title={t("map.canvas.title", { date: dateAt(safeDateIdx) })}
          subtitle={t("map.canvas.subtitle", { fields: fmt.integer(FIELDS.length), selected: fmt.integer(selectedFields.length) })}
          pad={false}
          right={<PipelineDataBadge />}
        >
          <div className="h-[520px] relative">
            {/* MapView stays mounted when field boundaries are hidden: only the
                polygon layer is removed, the basemap + raster overlay remain
                visible (task 6.1 — the whole map used to disappear here). */}
            <MapView colorMode={colorMode} model={model} indicator={indicator} dateIdx={safeDateIdx} opacity={opacity} showFields={showFields} rasterDate={rasterDate} rasterLayer={rasterLayerActive} rasterOpacity={rasterOpacity} height="520px" />
            <div className="absolute top-3 start-3 z-[500] bg-white/95 dark:bg-slate-900/95 border border-slate-200 dark:border-slate-700 px-3 py-2 text-[11px] shadow-sm">
              <div className="font-semibold">
                {t(`model.${model}.name`)} · {dateAt(safeDateIdx)}
              </div>
              <div className="text-slate-500">{t("map.canvas.selectionMean", { mean: fmt.number(selectedStats.mean, 3), max: fmt.number(selectedStats.max, 3) })}</div>
            </div>
          </div>
        </Panel>
        {showCompare && (
          <Panel title={t("map.compare.title")} subtitle={t("map.compare.subtitle", { left: dateAt(safeCompareIdx), right: dateAt(safeDateIdx) })} pad={false}>
            <div className="grid grid-cols-2 gap-px bg-slate-200 dark:bg-slate-800">
              <div className="h-64">
                <MapView colorMode={colorMode} model={model} indicator={indicator} dateIdx={safeCompareIdx} opacity={opacity} height="256px" />
              </div>
              <div className="h-64">
                <MapView colorMode={colorMode} model={model} indicator={indicator} dateIdx={safeDateIdx} opacity={opacity} height="256px" />
              </div>
            </div>
            <div className="p-3 text-[11px] text-slate-500">{t("map.compare.caption", { left: dateAt(safeCompareIdx), right: dateAt(safeDateIdx) })}</div>
          </Panel>
        )}
      </div>

      {/* Inspector */}
      <div className="col-span-12 lg:col-span-3 space-y-4">
        <Panel title={t("map.inspector.title")} subtitle={field.code}>
          <dl className="text-[12px] space-y-1.5">
            {[
              // Registry values verbatim; a missing registry entry renders the
              // not-recorded state "—" rather than an invented default.
              [t("field.farm"), field.farm || "—"],
              [t("field.municipality"), field.municipality || "—"],
              [t("field.area"), field.areaHa != null ? `${field.areaHa} ${t("map.tooltip.ha")}` : "—"],
              [t("field.variety"), field.variety || "—"],
              [t("field.planted"), field.planted || "—"],
              [t("field.harvest"), field.harvest || "—"],
              [t("field.centroid"), `${field.centroid[0].toFixed(4)}, ${field.centroid[1].toFixed(4)}`],
              [t("field.neighbours"), field.neighbors.join(", ") || "—"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3">
                <dt className="text-slate-500">{k}</dt>
                <dd className="font-medium text-end">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-3 grid grid-cols-3 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 text-center">
            <div className="bg-white dark:bg-slate-900 p-2">
              <div className="text-[9px] uppercase text-slate-400">{t("field.score")}</div>
              <div className="text-[13px] font-semibold" style={{ color: obs ? anomalyColor(obs.scores[model]) : "#64748b" }}>
                {obs ? <bdi>{fmt.number(obs.scores[model] ?? NaN, 3)}</bdi> : "—"}
              </div>
              {obs?.scoreProvenance && (
                <div className="mt-0.5 flex justify-center">
                  <ProvenanceChip
                    state={obs.scoreProvenance[model]}
                    title={`${model}: ${obs.scoreProvenance[model]}${obs.scoreFormulaId?.[model] ? ` · ${obs.scoreFormulaId[model]}` : ""}`}
                  />
                </div>
              )}
            </div>
            <div className="bg-white dark:bg-slate-900 p-2">
              <div className="text-[9px] uppercase text-slate-400">NDVI</div>
              <div className="text-[13px] font-semibold">{obs ? <bdi>{fmtObs(obs.ndvi, 2)}</bdi> : "—"}</div>
            </div>
            <div className="bg-white dark:bg-slate-900 p-2">
              <div className="text-[9px] uppercase text-slate-400">CWSI</div>
              <div className="text-[13px] font-semibold">{obs ? <bdi>{fmtObs(obs.cwsi, 2)}</bdi> : "—"}</div>
            </div>
          </div>
          {/* v5: causal stress flag + split-membership tag for THIS observation.
              The flag is "suspected stress (anomaly)" — honest naming until L4
              validation — and a train-split observation is in-sample: its
              scores/flag are optimistic and must be read as such. */}
          {obs && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] text-slate-500">{t("stressFlag.label")}</span>
              <StressFlagChip
                flag={obs.stressFlag}
                title={
                  obs.stressFlagModel
                    ? `${t("stressFlag.label")}: ${obs.stressFlagModel}${ladderRung ? ` · ${ladderRung}` : ""}`
                    : undefined
                }
              />
              {obs.stressFlag === "suspected_stress" && ladderRung && (
                <span className="text-[9px] font-mono text-slate-400" title="ladder rung">{ladderRung}</span>
              )}
              <SplitTagChip split={obs.split} />
            </div>
          )}
          {obs && obs.stalenessReason && (
            <div className="mt-2 text-[11px] border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-900 p-2 text-amber-800 dark:text-amber-200">
              {t("map.inspector.stale", { reason: obs.stalenessReason, sample: obs.sampleDate, acquired: obs.acquisitionDate || "" })}
            </div>
          )}
          {obs && obs.acquisitionDate && obs.acquisitionDate !== obs.sampleDate && (
            <div className="mt-1 text-[11px] text-slate-400">
              {t("map.inspector.acquired", { sample: obs.sampleDate, acquired: obs.acquisitionDate })}
            </div>
          )}
          {/* Compact grouped provenance (was ten separate chips). Hover a
              line for the exact channel: state pairs. */}
          {obs?.provenance && <ProvenanceSummary provenance={obs.provenance as unknown as Record<string, string>} />}
          <div className="mt-3 flex gap-2">
            <button onClick={() => setView("temporal")} className="flex-1 h-8 bg-teal-700 text-white text-[12px]">
              {t("map.inspector.openTemporal")}
            </button>
            <button onClick={() => setView("validation")} className="flex-1 h-8 border border-slate-300 dark:border-slate-700 text-[12px]">
              {t("map.inspector.validate")}
            </button>
          </div>
        </Panel>

        <Panel title={t("map.history.title")} subtitle={t("map.history.subtitle", { model: t(`model.${model}.name`), indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })}>
          <div dir="ltr" className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={tickInterval(DATES.length, 6)} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <ReferenceLine y={ANOMALY_THRESHOLD} stroke="#ea580c" strokeDasharray="4 3" />
                <Line type="monotone" dataKey="score" stroke={MODELS.find(m => m.id === model)?.color} strokeWidth={2} dot={false} name={t("map.history.score")} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">{t("map.history.thresholdNote", { threshold: fmt.number(ANOMALY_THRESHOLD, 2) })}</div>
        </Panel>

        <Panel title={t("map.selection.title")} subtitle={t("map.selection.subtitle", { n: fmt.integer(selectedFields.length) })}>
          <div className="flex flex-wrap gap-1.5">
            {selectedFields.map(id => (
              <button key={id} onClick={() => toggleField(id)}>
                <Badge color={id === selectedField ? "#0f766e" : undefined}>{id}</Badge>
              </button>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-slate-500">
            {t("map.selection.rangeNote", { from: DATES[range[0]]?.slice(0, 7) ?? "—", to: DATES[range[1]]?.slice(0, 7) ?? "—" })}
          </div>
          <div className="mt-2 flex gap-2">
            <button onClick={() => setView("spatial")} className="flex-1 h-7 border border-slate-300 dark:border-slate-700 text-[11px]">
              {t("map.selection.spatial")}
            </button>
            <button onClick={() => setView("spectral")} className="flex-1 h-7 border border-slate-300 dark:border-slate-700 text-[11px]">
              {t("map.selection.spectral")}
            </button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
