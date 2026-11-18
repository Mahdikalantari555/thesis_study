import { useMemo, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Line, ComposedChart, ReferenceLine } from "recharts";
import { Panel, Label, Select, Stat, EmptyState } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { MODELS, INDICATORS, FIELDS, getPairs, pearson, spearman, linReg, laggedCorr, DATES, LAST_IDX, FIELDS_WITH_SERIES, downsampleForDisplay } from "../data/data";
import { useLocale, useT } from "../i18n";

export default function Spectral() {
  const { model, setModel, indicator, setIndicator, selectedFields, range, setRange } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();
  const [season, setSeason] = useState<"all" | "wet" | "dry">("all");
  const [scope, setScope] = useState<"selection" | "all">("selection");

  const fieldIds = useMemo(() => (scope === "all" ? FIELDS.map(f => f.id) : selectedFields), [scope, selectedFields]);
  const { xs, ys, meta } = useMemo(() => {
    const p = getPairs(model, indicator, fieldIds, range);
    if (season === "all") return p;
    const keep: number[] = [];
    p.meta.forEach((m, i) => {
      const mo = parseInt(m.date.slice(5, 7));
      const ok = season === "wet" ? mo >= 10 || mo <= 3 : mo >= 4 && mo <= 9;
      if (ok) keep.push(i);
    });
    return { xs: keep.map(i => p.xs[i]), ys: keep.map(i => p.ys[i]), meta: keep.map(i => p.meta[i]) };
  }, [model, indicator, fieldIds, range, season]);

  const r = pearson(xs, ys), rho = spearman(xs, ys), reg = linReg(xs, ys);
  // Display layer only: stride sample of the full pair set (stats use all pairs).
  const scatterAll = xs.map((x, i) => ({ x: +x.toFixed(3), y: +ys[i].toFixed(3), field: meta[i].field, date: meta[i].date.slice(0, 7) }));
  const scatter = downsampleForDisplay(scatterAll, 5000);
  const lineData = Array.from({ length: 20 }, (_, i) => {
    const x = i / 19;
    return { x: +x.toFixed(3), y: +(reg.intercept + reg.slope * x).toFixed(3) };
  });
  const lags = laggedCorr(xs, ys, 6);
  const lagData = lags.map(l => ({ lag: l.lag, r: +l.r.toFixed(3) }));
  const bestLag = lags.reduce((a, b) => (Math.abs(b.r) > Math.abs(a.r) ? b : a), lags[0]);

  // Correlation matrix: models × indicators (weather indicators excluded — no
  // causal reading, and their units are not comparable with spectral indices).
  const matrix = useMemo(
    () =>
      MODELS.map(m => {
        const row: Record<string, string | number> = { model: t(`model.${m.id}.name`), color: m.color };
        INDICATORS.filter(i => i.kind !== "weather").forEach(ind => {
          const p = getPairs(m.id, ind.id, fieldIds, range);
          row[ind.name] = +pearson(p.xs, p.ys).toFixed(2);
        });
        return row;
      }),
    // `t` changes identity with the locale, which is exactly when the matrix labels must refresh.
    [fieldIds, range, t]
  );

  const indCols = INDICATORS.filter(i => i.kind !== "weather");

  const pearsonLabel = !Number.isFinite(r) ? "—" : r > 0.5 ? t("spectral.stat.pearsonStrong") : r > 0.3 ? t("spectral.stat.pearsonModeratePlus") : r < -0.3 ? t("spectral.stat.pearsonModerateMinus") : t("spectral.stat.pearsonWeak");

  const quantileRows = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(q => {
    const sortedXs = [...xs].sort((a, b) => a - b);
    const sortedYs = [...ys].sort((a, b) => a - b);
    const pick = (arr: number[]) => (arr.length ? +arr[Math.floor((q / 9) * (arr.length - 1))].toFixed(3) : 0);
    return { q: `P${q * 10}`, score: pick(sortedXs), ind: pick(sortedYs) };
  });

  const hasPairs = xs.length > 2 && Number.isFinite(r);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-end border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
        <div>
          <Label>{t("spectral.controls.model")}</Label>
          <Select value={model} onChange={v => setModel(v as typeof model)}>
            {MODELS.map(m => (
              <option key={m.id} value={m.id}>
                {t(`model.${m.id}.name`)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("spectral.controls.indicator")}</Label>
          <Select value={indicator} onChange={v => setIndicator(v as typeof indicator)}>
            {INDICATORS.map(i => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("spectral.controls.scope")}</Label>
          <Select value={scope} onChange={v => setScope(v as typeof scope)}>
            <option value="selection">{t("spectral.controls.scopeSelection", { n: fmt.integer(selectedFields.length) })}</option>
            <option value="all">{t("spectral.controls.scopeAll", { n: fmt.integer(FIELDS_WITH_SERIES.length) })}</option>
          </Select>
        </div>
        <div>
          <Label>{t("spectral.controls.season")}</Label>
          <Select value={season} onChange={v => setSeason(v as typeof season)}>
            <option value="all">{t("spectral.controls.seasonAll")}</option>
            <option value="wet">{t("spectral.controls.seasonWet")}</option>
            <option value="dry">{t("spectral.controls.seasonDry")}</option>
          </Select>
        </div>
        <div className="flex-1 min-w-48">
          <Label>{t("spectral.controls.dateRange", { from: DATES[range[0]]?.slice(0, 7) ?? "—", to: DATES[range[1]]?.slice(0, 7) ?? "—" })}</Label>
          <div className="flex gap-2">
            <input type="range" min={0} max={LAST_IDX} value={range[0]} onChange={e => setRange([Math.min(+e.target.value, range[1]), range[1]])} aria-label={t("map.layer.rangeStart")} className="flex-1 accent-teal-700" />
            <input type="range" min={0} max={LAST_IDX} value={range[1]} onChange={e => setRange([range[0], Math.max(+e.target.value, range[0])])} aria-label={t("map.layer.rangeEnd")} className="flex-1 accent-teal-700" />
          </div>
        </div>
        <div className="text-[11px] text-slate-500">{t("spectral.controls.pairedObs", { n: fmt.integer(xs.length) })}</div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
        <Stat label={t("spectral.stat.pearson")} value={fmt.number(r, 3)} sub={pearsonLabel} />
        <Stat label={t("spectral.stat.spearman")} value={fmt.number(rho, 3)} sub={t("spectral.stat.spearmanSub")} />
        <Stat label={t("spectral.stat.slope")} value={fmt.number(reg.slope, 3)} sub={t("spectral.stat.slopeSub", { r2: fmt.number(reg.r2, 3) })} />
        <Stat label={t("spectral.stat.bestLag")} value={t("spectral.stat.bestLagValue", { lag: fmt.integer(bestLag?.lag ?? 0) })} sub={t("spectral.stat.bestLagSub")} />
      </div>

      {!hasPairs && <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />}

      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("spectral.scatter.title", { model: t(`model.${model}.name`), indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })} subtitle={t("spectral.scatter.subtitle")} className="col-span-12 xl:col-span-7">
          <div dir="ltr" className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" dataKey="x" name={t("spectral.scatter.xAxis")} domain={[0, 1]} tick={{ fontSize: 10 }} label={{ value: t("spectral.scatter.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis type="number" dataKey="y" name={INDICATORS.find(i => i.id === indicator)?.name} tick={{ fontSize: 10 }} label={{ value: INDICATORS.find(i => i.id === indicator)?.name, angle: -90, position: "insideLeft", fontSize: 10 }} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ fontSize: 11 }} />
                <Scatter data={scatter.points} fill={MODELS.find(m => m.id === model)?.color} fillOpacity={0.55} />
                <Line type="monotone" dataKey="y" data={lineData} stroke="#be123c" strokeWidth={2} dot={false} name={t("spectral.scatter.ols")} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("spectral.lagged.title")} subtitle={t("spectral.lagged.subtitle")} className="col-span-12 xl:col-span-5">
          <div dir="ltr" className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={lagData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="lag" tick={{ fontSize: 10 }} label={{ value: t("spectral.lagged.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <ReferenceLine y={0} stroke="#94a3b8" />
                <Line type="monotone" dataKey="r" stroke="#0f766e" strokeWidth={2} dot={{ r: 3 }} name={t("spectral.lagged.seriesName")} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">{t("spectral.lagged.note")}</div>
        </Panel>

        <Panel title={t("spectral.matrix.title")} subtitle={t("spectral.matrix.subtitle")} className="col-span-12" pad={false}>
          <div className="overflow-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800">
                  <th className="text-start px-3 py-2 font-medium">{t("spectral.matrix.model")}</th>
                  {indCols.map(i => (
                    <th key={i.id} className="px-2 py-2 font-medium text-center">
                      {i.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.map(row => (
                  <tr key={row.model as string} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="px-3 py-1.5 font-medium">
                      <span className="inline-block w-2 h-2 me-1.5" style={{ background: row.color as string }} />
                      {row.model as string}
                    </td>
                    {indCols.map(i => {
                      const v = row[i.name] as number;
                      const bg = v > 0.3 ? `rgba(15,118,110,${Math.min(0.85, v)})` : v < -0.3 ? `rgba(190,18,60,${Math.min(0.85, -v)})` : "#f1f5f9";
                      const fg = Math.abs(v) > 0.3 ? "#fff" : "#334155";
                      return (
                        <td key={i.id} className="px-1 py-1 text-center">
                          <span className="inline-block min-w-12 px-1 py-0.5 font-mono" style={{ background: bg, color: fg }}>
                            {Number.isFinite(v) ? fmt.number(v, 2) : "—"}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title={t("spectral.dist.title")} subtitle={t("spectral.dist.subtitle")} className="col-span-12 xl:col-span-6">
          <div dir="ltr" className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={quantileRows} margin={{ top: 5, right: 30, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="q" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="l" domain={[0, 1]} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Line yAxisId="l" type="monotone" dataKey="score" stroke={MODELS.find(m => m.id === model)?.color} strokeWidth={2} dot={false} name={t("spectral.dist.scoreQuantile")} />
                <Line yAxisId="r" type="monotone" dataKey="ind" stroke={INDICATORS.find(i => i.id === indicator)?.color} strokeWidth={2} dot={false} name={t("spectral.dist.indicatorQuantile")} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("spectral.notes.title")} className="col-span-12 xl:col-span-6">
          <ul className="text-[12px] text-slate-600 dark:text-slate-400 space-y-2 list-disc ps-4 leading-relaxed">
            <li>{t("spectral.notes.a")}</li>
            <li>{t("spectral.notes.b")}</li>
            <li>{t("spectral.notes.c")}</li>
            <li>{t("spectral.notes.d")}</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
