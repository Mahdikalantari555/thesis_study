import { useMemo, useState } from "react";
import { ComposedChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Brush, Legend, Area } from "recharts";
import { Panel, Label, Select, Badge, EmptyState } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { FIELDS, MODELS, INDICATORS, getSeries, DATES, LAST_IDX, ANOMALY_THRESHOLD, tickInterval, type ModelId, type IndicatorId } from "../data/data";
import { useLocale, useT } from "../i18n";

const VAR_COLORS: Record<string, string> = { ndvi: "#16a34a", evi: "#65a30d", savi: "#059669", ndmi: "#0891b2", tvdi: "#ea580c", cwsi: "#dc2626", eta: "#0284c7", lst: "#9333ea", precip: "#64748b", temp: "#b45309" };

export default function Temporal() {
  const { selectedField, setSelectedField, model, setModel, range, setRange } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();
  const [showModels, setShowModels] = useState<ModelId[]>([model]);
  const [showVars, setShowVars] = useState<IndicatorId[]>(["ndvi", "tvdi", "cwsi", "eta"]);
  const [normalize, setNormalize] = useState(false);
  const [showMissing, setShowMissing] = useState(true);

  const series = getSeries(selectedField);
  const data = useMemo(
    () =>
      series.map(o => {
        const row: Record<string, string | number | null> = { date: o.date.slice(0, 7), idx: o.idx, missing: o.missing ? 1 : 0, sampleDate: o.sampleDate, acquisitionDate: o.acquisitionDate, stale: o.missing && o.stalenessReason ? o.stalenessReason : null };
        showModels.forEach(m => {
          const sv = o.scores?.[m];
          row[`m_${m}`] = o.missing || sv == null ? null : +Number(sv).toFixed(3);
        });
        showVars.forEach(v => {
          let val = (o as unknown as Record<string, number | null>)[v];
          if (val == null || o.missing) {
            row[`v_${v}`] = null;
            return;
          }
          if (normalize) {
            const ind = INDICATORS.find(i => i.id === v)!;
            val = (val - ind.range[0]) / (ind.range[1] - ind.range[0]);
          }
          row[`v_${v}`] = Number.isFinite(val) ? +Number(val).toFixed(3) : null;
        });
        return row;
      }),
    [series, showModels, showVars, normalize]
  );

  const toggle = <T,>(list: T[], v: T, setter: (l: T[]) => void) => setter(list.includes(v) ? list.filter(x => x !== v) : [...list, v]);

  const filtered = data.filter(d => (d.idx as number) >= range[0] && (d.idx as number) <= range[1]);

  // Year presets are derived from the loaded axis, not hard-coded offsets.
  const years = useMemo(() => {
    const out: { year: string; range: [number, number] }[] = [];
    DATES.forEach((d, i) => {
      const y = d.slice(0, 4);
      const last = out[out.length - 1];
      if (last && last.year === y) last.range[1] = i;
      else out.push({ year: y, range: [i, i] });
    });
    return out;
  }, []);

  if (!FIELDS.length || !series.length) {
    return <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("temporal.config.title")} className="col-span-12 lg:col-span-3">
          <div className="space-y-4">
            <div>
              <Label>{t("temporal.config.field")}</Label>
              <Select value={selectedField} onChange={setSelectedField} className="w-full">
                {FIELDS.map(f => (
                  <option key={f.id} value={f.id}>
                    {f.code} — {f.name} ({f.municipality})
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("temporal.config.primaryModel")}</Label>
              <Select
                value={model}
                onChange={v => {
                  setModel(v as ModelId);
                  if (!showModels.includes(v as ModelId)) setShowModels([...showModels, v as ModelId]);
                }}
                className="w-full"
              >
                {MODELS.map(m => (
                  <option key={m.id} value={m.id}>
                    {t(`model.${m.id}.name`)}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>{t("temporal.config.modelsOverlay")}</Label>
              <div className="space-y-1">
                {MODELS.map(m => (
                  <label key={m.id} className="flex items-center gap-2 text-[12px] cursor-pointer">
                    <input type="checkbox" checked={showModels.includes(m.id)} onChange={() => toggle(showModels, m.id, setShowModels)} className="accent-teal-700" />
                    <span className="w-2.5 h-2.5 shrink-0" style={{ background: m.color }} />
                    {t(`model.${m.id}.name`)}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <Label>{t("temporal.config.indicators")}</Label>
              <div className="space-y-1 max-h-48 overflow-auto">
                {INDICATORS.map(i => (
                  <label key={i.id} className="flex items-center gap-2 text-[12px] cursor-pointer">
                    <input type="checkbox" checked={showVars.includes(i.id)} onChange={() => toggle(showVars, i.id, setShowVars)} className="accent-teal-700" />
                    <span className="w-2.5 h-2.5 shrink-0" style={{ background: i.color }} />
                    {i.name} <span className="text-slate-400 text-[10px]">{i.unit}</span>
                  </label>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 text-[12px] cursor-pointer">
              <input type="checkbox" checked={normalize} onChange={e => setNormalize(e.target.checked)} className="accent-teal-700" /> {t("temporal.config.normalise")}
            </label>
            <label className="flex items-center gap-2 text-[12px] cursor-pointer">
              <input type="checkbox" checked={showMissing} onChange={e => setShowMissing(e.target.checked)} className="accent-teal-700" /> {t("temporal.config.showMissing")}
            </label>
            <div className="border border-slate-200 dark:border-slate-800 p-2 text-[11px] text-slate-500 leading-relaxed">
              <b className="text-slate-700 dark:text-slate-300">{t("temporal.config.readingTitle")}</b> {t("temporal.config.readingBody")}
            </div>
          </div>
        </Panel>

        <div className="col-span-12 lg:col-span-9 space-y-4">
          <Panel
            title={t("temporal.chart.title", { field: selectedField })}
            subtitle={t("temporal.chart.subtitle", { farm: FIELDS.find(f => f.id === selectedField)?.farm ?? "—", n: fmt.integer(filtered.length) })}
            right={
              <Badge color="#0f766e">
                {DATES[range[0]]?.slice(0, 7) ?? "—"} → {DATES[range[1]]?.slice(0, 7) ?? "—"}
              </Badge>
            }
          >
            <div dir="ltr" className="h-[420px]">
              <ResponsiveContainer width="100%" height="100%">
                {/* Recharts must stay LTR even under dir="rtl" or axes mirror (spec: charts render under RTL). */}
                <ComposedChart data={data} margin={{ top: 10, right: 50, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} interval={tickInterval(DATES.length, 16)} />
                  <YAxis yAxisId="left" domain={[0, 1]} tick={{ fontSize: 10 }} label={{ value: t("temporal.chart.anomalyScore"), angle: -90, position: "insideLeft", fontSize: 10 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} hide={normalize} />
                  <Tooltip content={
  (p: any) => p.active && p.payload && p.payload.length ? (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded px-2 py-1.5 text-[11px] shadow-sm">
      <div className="font-medium">{p.payload[0]?.payload?.sampleDate ?? ""}</div>
      <div className="text-slate-400">{p.payload[0]?.payload?.acquisitionDate ? t("map.inspector.acquired", { sample: p.payload[0]?.payload?.sampleDate ?? "", acquired: p.payload[0]?.payload?.acquisitionDate ?? "" }) : ""}</div>
      {p.payload.map((e: any) => (
        <div key={String(e.dataKey)}>
          <span style={{ color: e.color ?? e.stroke }}>{e.name}: </span>
          <span className="font-mono">{e.value == null ? "-" : e.value}</span>
        </div>
      ))}
    </div>
  ) : null
} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <ReferenceLine yAxisId="left" y={ANOMALY_THRESHOLD} stroke="#ea580c" strokeDasharray="5 4" label={{ value: t("temporal.chart.threshold"), fontSize: 9, fill: "#ea580c" }} />
                  {showModels.map(m => (
                    <Line key={m} yAxisId="left" type="monotone" dataKey={`m_${m}`} name={t(`model.${m}.name`)} stroke={MODELS.find(x => x.id === m)?.color} strokeWidth={m === model ? 2.5 : 1.5} dot={false} connectNulls={false} />
                  ))}
                  {showVars.map((v, i) => (
                    <Line
                      key={v}
                      yAxisId={normalize ? "left" : "right"}
                      type="monotone"
                      dataKey={`v_${v}`}
                      name={(INDICATORS.find(x => x.id === v)?.name ?? v) + (normalize ? t("temporal.chart.normalisedSuffix") : "")}
                      stroke={VAR_COLORS[v]}
                      strokeWidth={1.4}
                      dot={false}
                      strokeDasharray={i % 2 ? "5 3" : undefined}
                      connectNulls={false}
                    />
                  ))}
                  {showMissing && <Area yAxisId="left" type="step" dataKey="missing" fill="#f59e0b" fillOpacity={0.15} stroke="none" name={t("temporal.chart.missing")} />}
                  <Brush dataKey="date" height={24} tickFormatter={() => ""} onChange={(r: { startIndex?: number; endIndex?: number } | null) => { if (r && r.startIndex !== undefined && r.endIndex !== undefined) setRange([r.startIndex, r.endIndex]); }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              <button onClick={() => setRange([0, LAST_IDX])} className="h-7 px-2 border border-slate-300 dark:border-slate-700 text-[11px]">
                {t("temporal.chart.fullPeriod")}
              </button>
              {years.map(y => (
                <button key={y.year} onClick={() => setRange(y.range)} className="h-7 px-2 border border-slate-300 dark:border-slate-700 text-[11px]">
                  {y.year}
                </button>
              ))}
              <span className="text-[11px] text-slate-500 self-center ms-auto">{t("temporal.chart.footnote")}</span>
            </div>
          </Panel>

          {/* Small multiples */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {showVars.slice(0, 4).map(v => {
              const ind = INDICATORS.find(i => i.id === v)!;
              const d = series.map(o => {
                const rawVal = (o as unknown as Record<string, number | null>)[v];
                return {
                  date: o.date.slice(0, 7),
                  val: o.missing || rawVal == null || !Number.isFinite(rawVal) ? null : +Number(rawVal).toFixed(3),
                  score: o.scores?.[model] != null && Number.isFinite(o.scores[model]) ? +Number(o.scores[model]).toFixed(3) : null,
                };
              });
              return (
                <Panel key={v} title={t("temporal.smallMultiples.title", { indicator: ind.name, model: t(`model.${model}.name`) })} subtitle={t("temporal.smallMultiples.subtitle", { desc: t(ind.descKey), unit: ind.unit })} pad={false}>
                  <div dir="ltr" className="h-40 p-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={d} margin={{ top: 5, right: 30, left: -15, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={tickInterval(series.length, 8)} />
                        <YAxis yAxisId="l" domain={[0, 1]} tick={{ fontSize: 9 }} />
                        <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ fontSize: 11 }} />
                        <Line yAxisId="l" type="monotone" dataKey="score" stroke={MODELS.find(m => m.id === model)?.color} strokeWidth={2} dot={false} name={t("temporal.chart.score")} />
                        <Line yAxisId="r" type="monotone" dataKey="val" stroke={ind.color} strokeWidth={1.5} dot={false} name={ind.name} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </Panel>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
