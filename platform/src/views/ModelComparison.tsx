import { useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, ScatterChart, Scatter, Legend } from "recharts";
import { Panel, Label, Badge, EmptyState } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { MODELS, INDICATORS, FIELDS, getSeries, getPairs, pearson, mean, quantile, ANOMALY_THRESHOLD, DATES, tickInterval, downsampleForDisplay, type ModelId } from "../data/data";
import { useLocale, useT } from "../i18n";

export default function ModelComparison() {
  const { compareModels, setCompareModels, indicator, setIndicator, range, selectedField } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();
  const [normalize, setNormalize] = useState<"raw" | "percentile">("raw");

  const toggle = (m: ModelId) => setCompareModels(compareModels.includes(m) ? compareModels.filter(x => x !== m) : [...compareModels, m]);

  // Distributions
  const distData = useMemo(() => {
    const bins = Array.from({ length: 10 }, (_, i) => ({ bin: `${(i / 10).toFixed(1)}` }) as Record<string, string | number>);
    compareModels.forEach(m => {
      // Absent scores are excluded, not folded in as a constant.
      const vals = FIELDS.flatMap(f => getSeries(f.id).map(o => o.scores[m])).filter((v): v is number => typeof v === "number");
      if (!vals.length) return;
      const sorted = [...vals].sort((a, b) => a - b);
      bins.forEach((b, i) => {
        let v = vals.filter(x => x >= i / 10 && x < (i + 1) / 10).length / vals.length;
        if (normalize === "percentile") v = quantile(sorted, (i + 0.5) / 10);
        b[m] = +v.toFixed(3);
      });
    });
    return bins;
  }, [compareModels, normalize]);

  // Pairwise correlations between models
  const pairMatrix = useMemo(
    () =>
      compareModels.map(a => {
        const row: Record<string, string | number> = { model: t(`model.${a}.name`), color: MODELS.find(m => m.id === a)?.color ?? "#64748b" };
        compareModels.forEach(b => {
          const xs: number[] = [], ys: number[] = [];
          FIELDS.forEach(f =>
            getSeries(f.id).forEach(o => {
              const va = o.scores[a], vb = o.scores[b];
              if (typeof va === "number" && typeof vb === "number") {
                xs.push(va);
                ys.push(vb);
              }
            })
          );
          row[MODELS.find(m => m.id === b)?.short || b] = +pearson(xs, ys).toFixed(2);
        });
        return row;
      }),
    [compareModels, t]
  );

  // Correlation with indicator per model
  const indCorr = useMemo(
    () =>
      compareModels.map(m => {
        const p = getPairs(m, indicator, FIELDS.map(f => f.id), range);
        return {
          model: t(`model.${m}.name`),
          color: MODELS.find(x => x.id === m)?.color ?? "#64748b",
          r: +pearson(p.xs, p.ys).toFixed(3),
          mean: +mean(p.xs).toFixed(3),
          anomRate: p.xs.length ? +(p.xs.filter(v => v >= ANOMALY_THRESHOLD).length / p.xs.length).toFixed(3) : NaN,
        };
      }),
    [compareModels, indicator, range, t]
  );

  // Event agreement (Jaccard)
  const agreement = useMemo(
    () =>
      compareModels.map(a => {
        const row: Record<string, string | number> = { model: MODELS.find(m => m.id === a)?.short ?? a };
        compareModels.forEach(b => {
          let inter = 0, union = 0;
          FIELDS.forEach(f =>
            getSeries(f.id).forEach(o => {
              const va = o.scores[a], vb = o.scores[b];
              // A pair member with no score cannot join the event sets.
              const ea = typeof va === "number" && va >= ANOMALY_THRESHOLD;
              const eb = typeof vb === "number" && vb >= ANOMALY_THRESHOLD;
              if (ea && eb) inter++;
              if (ea || eb) union++;
            })
          );
          row[MODELS.find(m => m.id === b)?.short || b] = union ? +(inter / union).toFixed(2) : 0;
        });
        return row;
      }),
    [compareModels]
  );

  // Temporal sync for selected field
  const temporal = useMemo(
    () =>
      getSeries(selectedField).map(o => {
        const row: Record<string, string | number> = { date: o.date.slice(0, 7) };
        compareModels.forEach(m => {
          const sv = o.scores[m];
          row[m] = typeof sv === "number" ? +sv.toFixed(3) : "";
        });
        return row;
      }),
    [compareModels, selectedField]
  );

  // Boxplot-like summary per model
  const box = useMemo(
    () =>
      compareModels.map(m => {
        const vals = FIELDS.flatMap(f => getSeries(f.id).map(o => o.scores[m])).filter((v): v is number => typeof v === "number").sort((a, b) => a - b);
        if (!vals.length) return { model: t(`model.${m}.name`), color: "#64748b", min: NaN, p25: NaN, median: NaN, p75: NaN, max: NaN };
        return {
          model: t(`model.${m}.name`),
          color: MODELS.find(x => x.id === m)?.color ?? "#64748b",
          min: +vals[0].toFixed(2),
          p25: +quantile(vals, 0.25).toFixed(2),
          median: +quantile(vals, 0.5).toFixed(2),
          p75: +quantile(vals, 0.75).toFixed(2),
          max: +vals[vals.length - 1].toFixed(2),
        };
      }),
    [compareModels, t]
  );

  // Pairwise scatter first two models
  const pairScatter = useMemo(() => {
    if (compareModels.length < 2) return { points: [] as { x: number; y: number }[], total: 0 };
    const [a, b] = compareModels;
    const all = FIELDS.flatMap(f =>
      getSeries(f.id)
        .map(o => ({ va: o.scores[a], vb: o.scores[b] }))
        .filter((p): p is { va: number; vb: number } => typeof p.va === "number" && typeof p.vb === "number")
        .map(p => ({ x: +p.va.toFixed(3), y: +p.vb.toFixed(3) }))
    );
    // Statistics above use every pair; the SVG layer shows a stride sample.
    return downsampleForDisplay(all, 5000);
  }, [compareModels]);

  // Field-level means, memoized once per model selection (the inline version
  // recomputed 490 series on every render).
  const fieldLevel = useMemo(
    () =>
      FIELDS.map(f => {
        const means = compareModels.map(m =>
          mean(
            getSeries(f.id)
              .map(o => o.scores[m])
              .filter((v): v is number => typeof v === "number")
          )
        );
        const spread = means.length ? Math.max(...means) - Math.min(...means) : 0;
        return { f, means, spread };
      })
        .sort((a, b) => b.spread - a.spread)
        .slice(0, 20),
    [compareModels]
  );

  if (!FIELDS.length) {
    return <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 items-start border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
        <div>
          <Label>{t("comparison.controls.models")}</Label>
          <div className="flex flex-wrap gap-2">
            {MODELS.map(m => (
              <button
                key={m.id}
                onClick={() => toggle(m.id)}
                className="flex items-center gap-1.5 h-8 px-2 border text-[12px]"
                style={{
                  borderColor: compareModels.includes(m.id) ? m.color : "#cbd5e1",
                  background: compareModels.includes(m.id) ? m.color + "18" : "transparent",
                  color: compareModels.includes(m.id) ? m.color : "#64748b",
                }}
              >
                <span className="w-2 h-2" style={{ background: m.color }} />
                {t(`model.${m.id}.name`)}
              </button>
            ))}
          </div>
        </div>
        <div>
          <Label>{t("comparison.controls.indicator")}</Label>
          <select value={indicator} onChange={e => setIndicator(e.target.value as typeof indicator)} className="h-8 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12px] px-2">
            {INDICATORS.map(i => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label>{t("comparison.controls.scale")}</Label>
          <select value={normalize} onChange={e => setNormalize(e.target.value as typeof normalize)} className="h-8 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12px] px-2">
            <option value="raw">{t("comparison.controls.scaleRaw")}</option>
            <option value="percentile">{t("comparison.controls.scalePercentile")}</option>
          </select>
        </div>
        <div className="text-[11px] text-slate-500 self-end pb-1">
          {t("comparison.controls.fieldTemporal", { field: selectedField || "—", from: DATES[range[0]]?.slice(0, 7) ?? "—", to: DATES[range[1]]?.slice(0, 7) ?? "—" })}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("comparison.dist.title")} subtitle={normalize === "raw" ? t("comparison.dist.subtitleRaw") : t("comparison.dist.subtitlePercentile")} className="col-span-12 xl:col-span-7">
          <div dir="ltr" className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distData} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="bin" tick={{ fontSize: 10 }} label={{ value: t("comparison.dist.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {compareModels.map(m => (
                  <Bar key={m} dataKey={m} name={t(`model.${m}.name`)} fill={MODELS.find(x => x.id === m)?.color} fillOpacity={0.75} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("comparison.box.title")} subtitle={t("comparison.box.subtitle")} className="col-span-12 xl:col-span-5" pad={false}>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800">
                <th className="text-start px-3 py-2 font-medium">{t("comparison.box.model")}</th>
                {["Min", "P25", "Med", "P75", "Max"].map(h => (
                  <th key={h} className="px-2 py-2 font-medium text-end">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {box.map(b => (
                <tr key={b.model} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-medium">
                    <span className="inline-block w-2 h-2 me-1.5" style={{ background: b.color }} />
                    {b.model}
                  </td>
                  {[b.min, b.p25, b.median, b.p75, b.max].map((v, i) => (
                    <td key={i} className="px-2 py-2 text-end font-mono">
                      {Number.isFinite(v) ? fmt.number(v, 2) : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-3">
            {box.map(b =>
              Number.isFinite(b.min) ? (
                <div key={b.model} className="flex items-center gap-2 mb-1.5 text-[10px]">
                  <span className="w-24 text-end truncate">{b.model}</span>
                  <div className="flex-1 relative h-4 bg-slate-100 dark:bg-slate-800">
                    <div
                      className="absolute top-0 h-full"
                      style={{
                        left: `${b.min * 100}%`,
                        width: `${(b.max - b.min) * 100}%`,
                        background: b.color + "33",
                        borderLeft: `2px solid ${b.color}`,
                        borderRight: `2px solid ${b.color}`,
                      }}
                    />
                    <div className="absolute top-0 h-full w-0.5 bg-slate-900 dark:bg-white" style={{ left: `${b.median * 100}%` }} />
                  </div>
                </div>
              ) : null
            )}
            <div className="text-[10px] text-slate-400">{t("comparison.box.note")}</div>
          </div>
        </Panel>

        <Panel title={t("comparison.pairCorr.title")} subtitle={t("comparison.pairCorr.subtitle")} className="col-span-12 md:col-span-6" pad={false}>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800">
                <th className="px-3 py-2" />
                <th className="px-2 py-2 font-medium text-center">{t("comparison.pairCorr.mean")}</th>
                <th className="px-2 py-2 font-medium text-center">{t("comparison.pairCorr.anomalyRate")}</th>
                <th className="px-2 py-2 font-medium text-center">{t("comparison.pairCorr.vsIndicator", { indicator: INDICATORS.find(i => i.id === indicator)?.name ?? "" })}</th>
              </tr>
            </thead>
            <tbody>
              {indCorr.map(c => (
                <tr key={c.model} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-medium">
                    <span className="inline-block w-2 h-2 me-1.5" style={{ background: c.color }} />
                    {c.model}
                  </td>
                  <td className="px-2 py-2 text-center font-mono"><bdi>{fmt.number(c.mean, 3)}</bdi></td>
                  <td className="px-2 py-2 text-center font-mono">{fmt.number(c.anomRate * 100, 1)}%</td>
                  <td className="px-2 py-2 text-center font-mono"><bdi>{fmt.number(c.r, 3)}</bdi></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-3 overflow-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr>
                  <th className="px-2 py-1" />
                  {compareModels.map(m => (
                    <th key={m} className="px-2 py-1 font-medium text-center">
                      {MODELS.find(x => x.id === m)?.short}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pairMatrix.map(r => (
                  <tr key={r.model as string}>
                    <td className="px-2 py-1 font-medium">{r.model as string}</td>
                    {compareModels.map(m => {
                      const v = r[MODELS.find(x => x.id === m)?.short || m] as number;
                      return (
                        <td key={m} className="px-1 py-1 text-center">
                          <span className="inline-block min-w-10 px-1 py-0.5 font-mono text-white" style={{ background: `rgba(15,118,110,${Math.max(0.15, v)})` }}>
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

        <Panel title={t("comparison.jaccard.title")} subtitle={t("comparison.jaccard.subtitle", { threshold: fmt.number(ANOMALY_THRESHOLD, 2) })} className="col-span-12 md:col-span-6" pad={false}>
          <div className="p-3 overflow-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr>
                  <th className="px-2 py-1" />
                  {compareModels.map(m => (
                    <th key={m} className="px-2 py-1 font-medium text-center">
                      {MODELS.find(x => x.id === m)?.short}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {agreement.map(r => (
                  <tr key={r.model as string}>
                    <td className="px-2 py-1 font-medium">{r.model as string}</td>
                    {compareModels.map(m => {
                      const v = r[MODELS.find(x => x.id === m)?.short || m] as number;
                      return (
                        <td key={m} className="px-1 py-1 text-center">
                          <span className="inline-block min-w-10 px-1 py-0.5 font-mono text-white" style={{ background: `rgba(37,99,235,${Math.max(0.12, v)})` }}>
                            {fmt.number(v, 2)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-3 pb-3 text-[11px] text-slate-500">{t("comparison.jaccard.note")}</div>
        </Panel>

        <Panel title={t("comparison.temporal.title", { field: selectedField || "—" })} subtitle={t("comparison.temporal.subtitle")} className="col-span-12 xl:col-span-7">
          <div dir="ltr" className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={temporal} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={tickInterval(DATES.length, 10)} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {compareModels.map(m => (
                  <Line key={m} type="monotone" dataKey={m} name={t(`model.${m}.name`)} stroke={MODELS.find(x => x.id === m)?.color} strokeWidth={1.8} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title={t("comparison.scatter.title")}
          subtitle={
            compareModels.length >= 2
              ? t("comparison.scatter.subtitle", { left: t(`model.${compareModels[0]}.name`), right: t(`model.${compareModels[1]}.name`) })
              : t("comparison.scatter.subtitleEmpty")
          }
          className="col-span-12 xl:col-span-5"
        >
          <div dir="ltr" className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" dataKey="x" domain={[0, 1]} tick={{ fontSize: 10 }} />
                <YAxis type="number" dataKey="y" domain={[0, 1]} tick={{ fontSize: 10 }} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ fontSize: 11 }} />
                <Scatter data={pairScatter.points} fill="#0f766e" fillOpacity={0.4} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-slate-500">{t("comparison.scatter.note")} {t("comparison.scatter.sampled", { shown: fmt.integer(pairScatter.points.length), total: fmt.integer(pairScatter.total) })}</div>
        </Panel>

        <Panel title={t("comparison.fieldLevel.title")} subtitle={t("comparison.fieldLevel.subtitle")} className="col-span-12" pad={false}>
          <div className="overflow-auto max-h-72">
            <table className="w-full text-[11px]">
              <thead className="sticky top-0 bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="text-start px-3 py-2 font-medium">{t("comparison.fieldLevel.field")}</th>
                  {compareModels.map(m => (
                    <th key={m} className="px-2 py-2 font-medium text-end">
                      {MODELS.find(x => x.id === m)?.short}
                    </th>
                  ))}
                  <th className="px-2 py-2 font-medium text-end">{t("comparison.fieldLevel.spread")}</th>
                </tr>
              </thead>
              <tbody>
                {fieldLevel.map(({ f, means, spread }) => (
                  <tr key={f.id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="px-3 py-1.5 font-mono">{f.code}</td>
                    {means.map((v, i) => (
                      <td key={i} className="px-2 py-1.5 text-end font-mono">
                        {fmt.number(v, 3)}
                      </td>
                    ))}
                    <td className="px-2 py-1.5 text-end">
                      <Badge color={spread > 0.15 ? "#be123c" : "#64748b"}>{fmt.number(spread, 3)}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
