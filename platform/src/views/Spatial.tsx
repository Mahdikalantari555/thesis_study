import { useMemo, useState } from "react";
import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, ScatterChart, Scatter } from "recharts";
import MapView from "../components/MapView";
import { Panel, Label, Select, Stat, Badge, EmptyState, fmtObs } from "../components/ui";
import { useAnalysis, DEFAULT_DATE_IDX } from "../context/AnalysisContext";
import { FIELDS, MODELS, INDICATORS, getSeries, moransI, pearson, mean, DATES, LAST_IDX, fieldById, clampIdx, monthAt, tickInterval } from "../data/data";
import { useLocale, useT } from "../i18n";

export default function Spatial() {
  const { model, setModel, indicator, setIndicator, selectedField, setSelectedField } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();
  const [dateIdx, setDateIdx] = useState(clampIdx(DEFAULT_DATE_IDX));
  const [mode, setMode] = useState<"anomaly" | "indicator" | "lisa">("anomaly");
  const safeIdx = clampIdx(dateIdx);

  // Missing scores stay null — Moran's I skips them (complete-case) instead of
  // folding fabricated zeros into the statistic.
  const values = useMemo(() => FIELDS.map(f => getSeries(f.id)[safeIdx]?.scores[model] ?? null), [model, safeIdx]);
  const weights = useMemo(() => {
    const index = new Map(FIELDS.map((f, i) => [f.id, i]));
    const m = new Map<string, string[]>();
    FIELDS.forEach((f, i) => {
      // `findIndex` used to produce "-1" for neighbour ids missing from FIELDS,
      // which then indexed `values[-1]` (silently NaN) inside Moran's I (BUG-09).
      m.set(String(i), f.neighbors.map(n => index.get(n)).filter((j): j is number => typeof j === "number").map(String));
    });
    return m;
  }, []);
  const moran = moransI(values, weights);

  // Spatial correlation: field score vs indicator (field means)
  const fieldMeans = useMemo(
    () =>
      FIELDS.map(f => {
        const s = getSeries(f.id);
        const nbScores = f.neighbors.flatMap(n => getSeries(n).map(o => o.scores[model])).filter((v): v is number => typeof v === "number");
        return {
          field: f.code,
          score: +mean(s.map(o => o.scores[model]).filter((v): v is number => typeof v === "number")).toFixed(3),
          ind: +mean(s.map(o => (o as unknown as Record<string, number | null>)[indicator]).filter((v): v is number => typeof v === "number")).toFixed(3),
          nbScore: +mean(nbScores).toFixed(3),
        };
      }),
    [model, indicator]
  );
  const spatialR = pearson(fieldMeans.map(d => d.score), fieldMeans.map(d => d.ind));
  const nbR = pearson(fieldMeans.map(d => d.score), fieldMeans.map(d => d.nbScore));

  // Variogram-like: correlation by neighbour distance proxy (grid distance)
  const variogram = useMemo(() => {
    const bins = [0, 1, 2, 3, 4, 5].map(d => ({ dist: d, pairs: [] as number[] }));
    FIELDS.forEach((a, i) =>
      FIELDS.forEach((b, j) => {
        if (j <= i) return;
        const vi = values[i], vj = values[j];
        if (typeof vi !== "number" || typeof vj !== "number") return;
        const dist = Math.round(Math.hypot(a.centroid[0] - b.centroid[0], a.centroid[1] - b.centroid[1]) * 120);
        bins[Math.min(5, dist)].pairs.push(Math.abs(vi - vj));
      })
    );
    return bins.map(b => ({ dist: b.dist, semivar: b.pairs.length ? +(mean(b.pairs) / 2).toFixed(3) : 0, n: b.pairs.length }));
  }, [values]);

  const field = fieldById(selectedField);
  const selfObs = getSeries(field.id)[safeIdx];
  const neighborRows = field.neighbors
    .filter(nid => FIELDS.some(f => f.id === nid))
    .map(nid => {
      const nf = fieldById(nid);
      const o = getSeries(nid)[safeIdx];
      return { id: nid, code: nf.code, score: o?.scores[model], ndvi: o?.ndvi, cwsi: o?.cwsi };
    });

  // Moran's I per month — computed once per model instead of on every render.
  const moranTrend = useMemo(
    () =>
      DATES.map((d, i) => {
        const vals = FIELDS.map(f => getSeries(f.id)[i]?.scores[model] ?? null);
        return { date: d.slice(0, 7), moran: +moransI(vals, weights).toFixed(3) };
      }),
    [model, weights]
  );

  if (!FIELDS.length) {
    return <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-end border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
        <div>
          <Label>{t("spatial.controls.model")}</Label>
          <Select value={model} onChange={v => setModel(v as typeof model)}>
            {MODELS.map(m => (
              <option key={m.id} value={m.id}>
                {t(`model.${m.id}.name`)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("spatial.controls.indicator")}</Label>
          <Select value={indicator} onChange={v => setIndicator(v as typeof indicator)}>
            {INDICATORS.map(i => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("spatial.controls.mode")}</Label>
          <Select value={mode} onChange={v => setMode(v as typeof mode)}>
            <option value="anomaly">{t("spatial.controls.modeAnomaly")}</option>
            <option value="indicator">{t("spatial.controls.modeIndicator")}</option>
            <option value="lisa">{t("spatial.controls.modeLisa")}</option>
          </Select>
        </div>
        <div className="flex-1 min-w-48">
          <Label>{t("spatial.controls.date", { date: monthAt(safeIdx) })}</Label>
          <input type="range" min={0} max={LAST_IDX} value={safeIdx} onChange={e => setDateIdx(+e.target.value)} aria-label={t("spatial.controls.date", { date: monthAt(safeIdx) })} className="w-full accent-teal-700" />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
        <Stat
          label={t("spatial.stat.moran")}
          value={fmt.number(moran, 3)}
          sub={moran > 0.3 ? t("spatial.stat.moranStrong") : moran > 0.1 ? t("spatial.stat.moranModerate") : t("spatial.stat.moranWeak")}
        />
        <Stat label={t("spatial.stat.correlation")} value={fmt.number(spatialR, 3)} sub={t("spatial.stat.correlationSub", { n: fmt.integer(FIELDS.length) })} />
        <Stat label={t("spatial.stat.neighbour")} value={fmt.number(nbR, 3)} sub={t("spatial.stat.neighbourSub")} />
        <Stat label={t("spatial.stat.fields")} value={fmt.integer(FIELDS.length)} sub={t("spatial.stat.fieldsSub", { n: fmt.integer(FIELDS.length) })} />
      </div>

      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("spatial.map.title")} subtitle={t("spatial.map.subtitle")} className="col-span-12 xl:col-span-7" pad={false}>
          <div className="h-[460px]">
            <MapView colorMode={mode} model={model} indicator={indicator} dateIdx={safeIdx} opacity={0.85} height="460px" />
          </div>
        </Panel>

        <div className="col-span-12 xl:col-span-5 space-y-4">
          <Panel title={t("spatial.neighbours.title", { field: field.code })} subtitle={t("spatial.neighbours.subtitle")}>
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-slate-400">
                  <th className="text-start py-1 font-medium">{t("spatial.neighbours.field")}</th>
                  <th className="text-end py-1 font-medium">{t("spatial.neighbours.score")}</th>
                  <th className="text-end py-1 font-medium">NDVI</th>
                  <th className="text-end py-1 font-medium">CWSI</th>
                </tr>
              </thead>
              <tbody>
                <tr className="bg-teal-50 dark:bg-teal-950/40 font-medium">
                  <td className="py-1.5">
                    {field.code} ({t("field.selected")})
                  </td>
                  <td className="text-end font-mono">{selfObs ? <bdi>{fmt.number(selfObs.scores[model] ?? NaN, 3)}</bdi> : "—"}</td>
                  <td className="text-end font-mono">{selfObs ? fmtObs(selfObs.ndvi, 2) : "—"}</td>
                  <td className="text-end font-mono">{selfObs ? fmtObs(selfObs.cwsi, 2) : "—"}</td>
                </tr>
                {neighborRows.map(r => (
                  <tr key={r.id} className="border-t border-slate-100 dark:border-slate-800 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50" onClick={() => setSelectedField(r.id)}>
                    <td className="py-1.5">{r.code}</td>
                    <td className="text-end font-mono">{r.score == null ? "—" : <bdi>{fmtObs(r.score, 3)}</bdi>}</td>
                    <td className="text-end font-mono">{fmtObs(r.ndvi ?? null, 2)}</td>
                    <td className="text-end font-mono">{fmtObs(r.cwsi ?? null, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="text-[11px] text-slate-500 mt-2">{t("spatial.neighbours.note")}</div>
          </Panel>

          <Panel title={t("spatial.variogram.title")} subtitle={t("spatial.variogram.subtitle")}>
            <div dir="ltr" className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={variogram} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="dist" tick={{ fontSize: 10 }} label={{ value: t("spatial.variogram.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="semivar" stroke="#0f766e" strokeWidth={2} dot={{ r: 3 }} name={t("spatial.variogram.seriesName")} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title={t("spatial.scatter.title")} subtitle={t("spatial.scatter.subtitle", { indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })}>
            <div dir="ltr" className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" dataKey="score" domain={[0, 1]} tick={{ fontSize: 10 }} />
                  <YAxis type="number" dataKey="ind" tick={{ fontSize: 10 }} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ fontSize: 11 }} />
                  <Scatter data={fieldMeans} fill={MODELS.find(m => m.id === model)?.color} fillOpacity={0.55} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>

        <Panel title={t("spatial.trend.title")} subtitle={t("spatial.trend.subtitle")} className="col-span-12">
          <div dir="ltr" className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={moranTrend} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={tickInterval(DATES.length, 10)} />
                <YAxis domain={[-0.5, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="moran" stroke="#7c3aed" strokeWidth={2} dot={false} name={t("spatial.trend.seriesName")} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            <Badge color="#7c3aed">{t("spatial.trend.legendPositive")}</Badge>
            <Badge>{t("spatial.trend.legendZero")}</Badge>
            <Badge>{t("spatial.trend.legendNegative")}</Badge>
          </div>
        </Panel>
      </div>
    </div>
  );
}
