import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, LineChart, Line, CartesianGrid, Legend } from "recharts";
import { FIELDS, MODELS, INDICATORS, getSeries, DATES, mean, quantile, ANOMALY_THRESHOLD, COVERAGE, N, DATA_PROVENANCE, FIELDS_WITH_SERIES, isLegacyPayload, tickInterval } from "../data/data";
import { Panel, Stat, Badge, PipelineDataBadge, EmptyState, anomalyColor, fmtObs, LegacyPayloadNotice } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { useLocale, useT } from "../i18n";
import { AlertTriangle, CalendarDays, Database, Layers, MapPin } from "lucide-react";

export default function Overview() {
  const { setView, setSelectedField, model, setModel, range } = useAnalysis();
  const t = useT();
  const { fmt, locale } = useLocale();

  const stats = useMemo(() => {
    let totalObs = 0, missing = 0;
    const allScores: number[] = [];
    const perModel: Record<string, number[]> = {};
    MODELS.forEach(m => (perModel[m.id] = []));
    FIELDS.forEach(f =>
      getSeries(f.id).forEach(o => {
        totalObs++;
        if (o.missing) missing++;
        MODELS.forEach(m => {
          const sv = o.scores[m.id];
          // Absent scores stay out of every statistic — substituting a
          // constant (the old 0.5 fallback) fabricated data.
          if (typeof sv === "number" && Number.isFinite(sv)) {
            perModel[m.id].push(sv);
            if (m.id === model) allScores.push(sv);
          }
        });
      })
    );
    const hist = Array.from({ length: 10 }, (_, i) => ({ bin: `${(i / 10).toFixed(1)}–${((i + 1) / 10).toFixed(1)}`, count: allScores.filter(v => v >= i / 10 && v < (i + 1) / 10).length }));
    const monthly = DATES.map((d, i) => {
      const vals = FIELDS.flatMap(f => {
        const o = getSeries(f.id)[i];
        const sv = o && !o.missing ? o.scores[model] : null;
        return typeof sv === "number" && Number.isFinite(sv) ? [sv] : [];
      });
      return { date: d.slice(0, 7), mean: +(Number.isFinite(mean(vals)) ? mean(vals) : 0).toFixed(3), p90: +(Number.isFinite(quantile(vals, 0.9)) ? quantile(vals, 0.9) : 0).toFixed(3) };
    });
    const completeness = totalObs ? 100 * (1 - missing / totalObs) : 0;
    const anomalies = FIELDS.flatMap(f => getSeries(f.id).map(o => ({ field: f, obs: o })))
      .filter(x => {
        const sv = x.obs.scores[model];
        return !x.obs.missing && typeof sv === "number" && sv >= ANOMALY_THRESHOLD;
      })
      .sort((a, b) => (b.obs.scores[model] as number) - (a.obs.scores[model] as number))
      .slice(0, 8);

    // Year columns are derived from the date axis instead of a hard-coded
    // 2021–2024 list, so the table cannot describe years the data lacks.
    const years = Array.from(new Set(DATES.map(d => d.slice(0, 4))));
    const fieldYear = FIELDS.slice(0, 24).map(f => {
      const s = getSeries(f.id);
      const row: Record<string, string | number> = { field: f.code };
      years.forEach(y => {
        const vals = s
          .filter(o => o.date.startsWith(y))
          .map(o => o.scores[model])
          .filter((v): v is number => typeof v === "number");
        row[y] = vals.length ? +mean(vals).toFixed(2) : NaN;
      });
      return row;
    });

    return { totalObs, missing, completeness, hist, monthly, anomalies, fieldYear, perModel, years };
  }, [model]);

  const totalArea = FIELDS.reduce((s, f) => s + (f.areaHa ?? 0), 0);

  if (!FIELDS.length || !N) {
    return <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />;
  }

  return (
    <div className="space-y-4">
      {isLegacyPayload && <LegacyPayloadNotice />}
      {/* Dataset strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
        <Stat label={t("overview.stat.fields")} value={fmt.integer(FIELDS.length)} sub={t("overview.stat.fieldsSub", { area: fmt.integer(totalArea) })} />
        <Stat label={t("overview.stat.observations")} value={fmt.integer(stats.totalObs)} sub={t("overview.stat.observationsSub")} />
        <Stat label={t("overview.stat.coverage")} value={`${COVERAGE.yearStart}–${COVERAGE.yearEnd}`} sub={t("overview.stat.coverageSub", { n: fmt.integer(N) })} />
        <Stat label={t("overview.stat.completeness")} value={`${fmt.number(stats.completeness, 1)}%`} sub={t("overview.stat.completenessSub", { n: fmt.integer(stats.missing) })} />
        <Stat label={t("overview.stat.models")} value={fmt.integer(MODELS.length)} sub={t("overview.stat.modelsSub")} />
        <Stat label={t("overview.stat.indicators")} value={fmt.integer(INDICATORS.length)} sub={t("overview.stat.indicatorsSub")} />
      </div>

      <div className="grid grid-cols-12 gap-4">
        <Panel
          title={t("overview.dist.title")}
          subtitle={t("overview.dist.subtitle", { model: t(`model.${model}.name`), threshold: fmt.number(ANOMALY_THRESHOLD, 2) })}
          className="col-span-12 xl:col-span-5"
          right={
            <select value={model} onChange={e => setModel(e.target.value as typeof model)} className="h-7 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-[11px] px-1.5">
              {MODELS.map(m => (
                <option key={m.id} value={m.id}>
                  {t(`model.${m.id}.name`)}
                </option>
              ))}
            </select>
          }
        >
          <div dir="ltr" className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.hist} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="bin" tick={{ fontSize: 10 }} interval={1} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="count" name={t("overview.dist.observations")}>
                  {stats.hist.map((_, i) => (
                    <Cell key={i} fill={anomalyColor((i + 0.5) / 10)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-4 mt-2 text-[11px] text-slate-500">
            <span>{t("overview.dist.legendNominal")}</span>
            <span>{t("overview.dist.legendElevated")}</span>
            <span>{t("overview.dist.legendAnomalous")}</span>
          </div>
        </Panel>

        <Panel title={t("overview.completeness.title")} subtitle={t("overview.completeness.subtitle")} className="col-span-12 md:col-span-6 xl:col-span-3">
          <div dir="ltr" className="h-44 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    { name: t("overview.completeness.valid"), value: stats.completeness },
                    { name: t("overview.completeness.missing"), value: 100 - stats.completeness },
                  ]}
                  dataKey="value"
                  innerRadius={52}
                  outerRadius={72}
                  paddingAngle={2}
                >
                  <Cell fill="#0f766e" />
                  <Cell fill="#cbd5e1" />
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-[12px] text-slate-600 dark:text-slate-400">
            <b className="text-slate-900 dark:text-slate-100">{fmt.number(stats.completeness, 1)}%</b> {t("overview.completeness.caption")}
          </div>
        </Panel>

        <Panel title={t("overview.monthly.title")} subtitle={t("overview.monthly.subtitle")} className="col-span-12 md:col-span-6 xl:col-span-4">
          <div dir="ltr" className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.monthly} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={tickInterval(DATES.length, 12)} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="mean" stroke="#0f766e" strokeWidth={2} dot={false} name={t("overview.monthly.mean")} />
                <Line type="monotone" dataKey="p90" stroke="#ea580c" strokeWidth={1.5} dot={false} name={t("overview.monthly.p90")} strokeDasharray="4 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("overview.fieldYear.title")} subtitle={t("overview.fieldYear.subtitle")} className="col-span-12 xl:col-span-7" pad={false}>
          <div className="overflow-auto max-h-72">
            <table className="w-full text-[11px]">
              <thead className="sticky top-0 bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="text-start px-3 py-2 font-medium">{t("overview.fieldYear.field")}</th>
                  {stats.years.map(y => (
                    <th key={y} className="px-2 py-2 font-medium text-end">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stats.fieldYear.map(r => (
                  <tr
                    key={r.field}
                    className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer"
                    onClick={() => {
                      const target = FIELDS.find(f => f.code === r.field);
                      if (!target) return;
                      setSelectedField(target.id);
                      setView("map");
                    }}
                  >
                    <td className="px-3 py-1.5 font-mono">{r.field}</td>
                    {stats.years.map(y => {
                      const v = r[y] as number;
                      return (
                        <td key={y} className="px-2 py-1.5 text-end">
                          {Number.isFinite(v) ? (
                            <span className="inline-block min-w-10 px-1.5 py-0.5 text-center text-white text-[10px]" style={{ background: anomalyColor(v) }}>
                              {fmt.number(v, 2)}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title={t("overview.notable.title")} subtitle={t("overview.notable.subtitle", { threshold: fmt.number(ANOMALY_THRESHOLD, 2), model: t(`model.${model}.name`) })} className="col-span-12 xl:col-span-5" pad={false}>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {stats.anomalies.map((a, i) => (
              <button
                key={i}
                onClick={() => {
                  setSelectedField(a.field.id);
                  setView("temporal");
                }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-start hover:bg-slate-50 dark:hover:bg-slate-800/60"
              >
                <AlertTriangle size={14} className="text-orange-600 shrink-0" />
                <span className="flex-1 min-w-0">
                  <span className="block text-[12px] font-medium truncate">
                    {a.field.code} — {a.field.name || a.field.code} · {a.field.municipality || "—"}
                  </span>
                  <span className="block text-[11px] text-slate-500">
                    {a.obs.date.slice(0, 7)} · NDVI {fmtObs(a.obs.ndvi, 2)} · CWSI {fmtObs(a.obs.cwsi, 2)}
                  </span>
                </span>
                <Badge color={anomalyColor(a.obs.scores[model])}>{fmt.number(a.obs.scores[model] ?? NaN, 3)}</Badge>
              </button>
            ))}
            {stats.anomalies.length === 0 && <div className="p-6 text-[12px] text-slate-500">{t("overview.notable.empty")}</div>}
          </div>
        </Panel>

        <Panel title={t("overview.models.title")} subtitle={t("overview.models.subtitle")} className="col-span-12 xl:col-span-6" pad={false}>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {MODELS.map(m => {
              const vals = stats.perModel[m.id];
              const anom = vals.length ? vals.filter(v => v >= ANOMALY_THRESHOLD).length / vals.length : NaN;
              return (
                <button key={m.id} onClick={() => setModel(m.id)} className="w-full flex items-center gap-3 px-4 py-3 text-start hover:bg-slate-50 dark:hover:bg-slate-800/60">
                  <span className="w-2.5 h-2.5 shrink-0" style={{ background: m.color }} />
                  <span className="flex-1">
                    <span className="block text-[12px] font-medium">
                      {t(`model.${m.id}.name`)} <span className="text-slate-400 font-normal">· {t(m.typeKey)}</span>
                    </span>
                    <span className="block text-[11px] text-slate-500">{t(m.descKey)}</span>
                  </span>
                  <span className="text-end text-[11px] text-slate-500">
                    {t("overview.models.mean", { value: fmt.number(mean(vals), 3) })}
                    <br />
                    {t("overview.models.anomalous", { value: fmt.number(anom * 100, 1) })}
                  </span>
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel title={t("overview.indicators.title")} subtitle={t("overview.indicators.subtitle")} className="col-span-12 xl:col-span-6" pad={false}>
          <div className="grid grid-cols-2 sm:grid-cols-3">
            {INDICATORS.map(ind => (
              <div key={ind.id} className="border-b border-e border-slate-100 dark:border-slate-800 p-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2" style={{ background: ind.color }} />
                  <span className="text-[12px] font-semibold">{ind.name}</span>
                  <span className="text-[10px] text-slate-400">{ind.unit}</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-1 leading-snug">{t(ind.descKey)}</div>
                <Badge color={ind.color}>{t(ind.kindKey)}</Badge>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-slate-500 items-center">
        <span className="inline-flex items-center gap-1">
          <CalendarDays size={13} />
          {t("overview.footer.cadence")}
        </span>
        <span className="inline-flex items-center gap-1">
          <Database size={13} />
          {t("overview.footer.data")}
        </span>
        <span className="inline-flex items-center gap-1">
          <Layers size={13} />
          {t("overview.footer.region")}
        </span>
        <span className="inline-flex items-center gap-1">
          <MapPin size={13} />
          {t("overview.footer.range", { from: DATES[range[0]]?.slice(0, 7) ?? "—", to: DATES[range[1]]?.slice(0, 7) ?? "—" })}
        </span>
        <PipelineDataBadge />
        <Badge color="#64748b">
          {DATA_PROVENANCE.source} · {fmt.integer(FIELDS_WITH_SERIES.length)} / {fmt.integer(FIELDS.length)} {locale === "fa" ? "قطعه با سری" : "fields with series"}
        </Badge>
      </div>
    </div>
  );
}
