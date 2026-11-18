import { useMemo, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Line, ComposedChart, ReferenceLine, BarChart, Bar, Cell } from "recharts";
import { Panel, Label, Select, Stat, SigBadge, PipelineDataBadge, EmptyState } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { MODELS, INDICATORS, FIELDS, getPairs, pearson, spearman, kendall, partialCorr, linReg, fisherCI, pValue, laggedCorr, DATES, LAST_IDX, ANOMALY_THRESHOLD, FIELDS_WITH_SERIES, downsampleForDisplay, type IndicatorId } from "../data/data";
import { useLocale, useT } from "../i18n";
import { ShieldAlert, Info } from "lucide-react";

export default function Validation() {
  const { model, setModel, indicator, setIndicator, selectedFields, range, setRange, addExperiment } = useAnalysis();
  const t = useT();
  const { fmt, locale } = useLocale();
  const [control, setControl] = useState<IndicatorId>("ndmi");
  const [scope, setScope] = useState<"selection" | "all">("selection");
  const [saved, setSaved] = useState(false);

  const fieldIds = useMemo(() => (scope === "all" ? FIELDS.map(f => f.id) : selectedFields), [scope, selectedFields]);
  const { xs, ys } = useMemo(() => getPairs(model, indicator, fieldIds, range), [model, indicator, fieldIds, range]);
  const ctrl = useMemo(() => getPairs(model, control, fieldIds, range), [model, control, fieldIds, range]);

  const n = xs.length;
  const r = pearson(xs, ys), rho = spearman(xs, ys), tau = kendall(xs, ys);
  const pr = ctrl.xs.length === n && n > 2 ? partialCorr(xs, ys, ctrl.ys) : NaN;
  const reg = linReg(xs, ys);
  const [lo, hi] = fisherCI(r, n);
  const p = pValue(r, n);
  const lags = laggedCorr(xs, ys, 6);
  const lagData = lags.map(l => ({ lag: l.lag, r: +l.r.toFixed(3) }));

  // Event-level agreement: score >= thr vs indicator in stress direction
  const events = useMemo(() => {
    let tp = 0, fp = 0, fn = 0, tn = 0;
    const stressHigh = ["tvdi", "cwsi", "lst", "temp"].includes(indicator);
    const thr = indicator === "ndvi" || indicator === "evi" || indicator === "savi" ? 0.45 : indicator === "ndmi" ? 0.2 : indicator === "eta" ? 2.5 : 0.6;
    xs.forEach((x, i) => {
      const pred = x >= ANOMALY_THRESHOLD;
      const actual = stressHigh ? ys[i] >= thr : ys[i] <= thr;
      if (pred && actual) tp++;
      else if (pred && !actual) fp++;
      else if (!pred && actual) fn++;
      else tn++;
    });
    const sens = tp + fn ? tp / (tp + fn) : NaN;
    const spec = tn + fp ? tn / (tn + fp) : NaN;
    const prec = tp + fp ? tp / (tp + fp) : NaN;
    const agreementRate = n ? (tp + tn) / n : NaN;
    return { tp, fp, fn, tn, sens, spec, prec, agreementRate, thr };
  }, [xs, ys, indicator, n]);

  // Robustness by year — derived from the actual date axis (BUG-02: the old
  // version hard-coded four year windows [0,12] … [36,48]).
  const byYear = useMemo(() => {
    const years = Array.from(new Set(DATES.map(d => d.slice(0, 4))));
    return years.map(y => {
      const idx = DATES.map((d, i) => (d.startsWith(y) ? i : -1)).filter(i => i >= 0);
      const lo2 = idx[0] ?? 0;
      const hi2 = idx[idx.length - 1] ?? 0;
      const p2 = getPairs(model, indicator, fieldIds, [lo2, hi2]);
      return { year: y, r: +pearson(p2.xs, p2.ys).toFixed(3), n: p2.xs.length };
    });
  }, [model, indicator, fieldIds]);

  // Temporal consistency: split-half correlation
  const half = Math.floor(n / 2);
  const r1 = pearson(xs.slice(0, half), ys.slice(0, half)), r2 = pearson(xs.slice(half), ys.slice(half));

  // Display layer only: stride sample of the full pair set (stats use all pairs).
  const scatterAll = xs.map((x, i) => ({ x: +x.toFixed(3), y: +ys[i].toFixed(3) }));
  const scatter = downsampleForDisplay(scatterAll, 5000);
  const fit = Array.from({ length: 20 }, (_, i) => {
    const x = i / 19;
    return { x: +x.toFixed(3), y: +(reg.intercept + reg.slope * x).toFixed(3) };
  });

  const save = () => {
    addExperiment({
      id: `exp-${Date.now()}`,
      name: `${t(`model.${model}.name`)} vs ${INDICATORS.find(i => i.id === indicator)?.name} — ${scope === "all" ? t("reports.experiment.allFields") : t("reports.experiment.defaultSuffix", { model: "", indicator: "", n: fmt.integer(selectedFields.length) }).replace(/^ — /, "")}`.replace(/ {2,}/g, " "),
      created: new Date().toISOString().slice(0, 10),
      model,
      indicator,
      fields: fieldIds,
      range,
      note: t("reports.experiment.savedFromValidation"),
      stats: `r=${fmt.number(r, 3)} ρ=${fmt.number(rho, 3)} τ=${fmt.number(tau, 3)} n=${fmt.integer(n)}`,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const summaryRows: [string, string, string][] = [
    [t("validation.summary.pearson"), fmt.number(r, 3), t("validation.summary.pearsonDesc")],
    [t("validation.summary.spearman"), fmt.number(rho, 3), t("validation.summary.spearmanDesc")],
    [t("validation.summary.kendall"), fmt.number(tau, 3), t("validation.summary.kendallDesc")],
    [t("validation.summary.partial"), fmt.number(pr, 3), t("validation.summary.partialDesc", { indicator: INDICATORS.find(i => i.id === control)?.name ?? "" })],
    [t("validation.summary.slope"), fmt.number(reg.slope, 3), t("validation.summary.slopeDesc")],
    [t("validation.summary.r2"), fmt.number(reg.r2, 3), t("validation.summary.r2Desc")],
    [t("validation.summary.ci"), `[${fmt.number(lo, 3)}, ${fmt.number(hi, 3)}]`, t("validation.summary.ciDesc")],
    [t("validation.summary.p"), p < 0.001 ? "<0.001" : fmt.number(p, 4), t("validation.summary.pDesc")],
  ];

  return (
    <div className="space-y-4">
      {/* Disclaimer */}
      <div className="border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800 p-3 flex gap-3">
        <ShieldAlert size={18} className="text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="text-[12px] leading-relaxed text-amber-900 dark:text-amber-200">
          <b>{t("validation.disclaimer.title")}</b> {t("validation.disclaimer.body")}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-end border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
        <div>
          <Label>{t("validation.controls.model")}</Label>
          <Select value={model} onChange={v => setModel(v as typeof model)}>
            {MODELS.map(m => (
              <option key={m.id} value={m.id}>
                {t(`model.${m.id}.name`)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("validation.controls.indicator")}</Label>
          <Select value={indicator} onChange={v => setIndicator(v as typeof indicator)}>
            {INDICATORS.map(i => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("validation.controls.control")}</Label>
          <Select value={control} onChange={v => setControl(v as IndicatorId)}>
            {INDICATORS.map(i => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>{t("validation.controls.scope")}</Label>
          <Select value={scope} onChange={v => setScope(v as typeof scope)}>
            <option value="selection">{t("validation.controls.scopeSelection")}</option>
            <option value="all">{t("validation.controls.scopeAll", { n: fmt.integer(FIELDS_WITH_SERIES.length) })}</option>
          </Select>
        </div>
        <div className="flex-1 min-w-48">
          <Label>{t("validation.controls.range", { from: DATES[range[0]]?.slice(0, 7) ?? "—", to: DATES[range[1]]?.slice(0, 7) ?? "—" })}</Label>
          <div className="flex gap-2">
            <input type="range" min={0} max={LAST_IDX} value={range[0]} onChange={e => setRange([Math.min(+e.target.value, range[1]), range[1]])} aria-label={t("map.layer.rangeStart")} className="flex-1 accent-teal-700" />
            <input type="range" min={0} max={LAST_IDX} value={range[1]} onChange={e => setRange([range[0], Math.max(+e.target.value, range[0])])} aria-label={t("map.layer.rangeEnd")} className="flex-1 accent-teal-700" />
          </div>
        </div>
        <button onClick={save} className="h-8 px-3 bg-teal-700 text-white text-[12px]">
          {saved ? t("validation.controls.saved") : t("validation.controls.save")}
        </button>
        <PipelineDataBadge />
      </div>

      {!n && <EmptyState title={t("ui.noData")} desc={t("ui.noDataDesc")} />}

      {/* Metadata strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
        <Stat label={t("validation.stat.n")} value={fmt.integer(n)} sub={t("validation.stat.nSub", { fields: fmt.integer(fieldIds.length), months: fmt.integer(range[1] - range[0] + 1) })} />
        <Stat label={t("validation.stat.pearsonCi")} value={fmt.number(r, 3)} sub={`[${fmt.number(lo, 3)}, ${fmt.number(hi, 3)}]`} />
        <Stat label={t("validation.stat.spearman")} value={fmt.number(rho, 3)} sub={t("validation.stat.spearmanSub")} />
        <Stat label={t("validation.stat.kendall")} value={fmt.number(tau, 3)} sub={t("validation.stat.kendallSub")} />
        <Stat label={t("validation.stat.partial")} value={fmt.number(pr, 3)} sub={t("validation.stat.partialSub", { indicator: INDICATORS.find(i => i.id === control)?.name ?? "" })} />
      </div>

      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("validation.scatter.title")} subtitle={t("validation.scatter.subtitle", { slope: fmt.number(reg.slope, 3), intercept: fmt.number(reg.intercept, 3), r2: fmt.number(reg.r2, 3) })} className="col-span-12 xl:col-span-7">
          <div dir="ltr" className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" dataKey="x" domain={[0, 1]} tick={{ fontSize: 10 }} label={{ value: t("spectral.scatter.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis type="number" dataKey="y" tick={{ fontSize: 10 }} label={{ value: INDICATORS.find(i => i.id === indicator)?.name, angle: -90, position: "insideLeft", fontSize: 10 }} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ fontSize: 11 }} />
                <Scatter data={scatter.points} fill={MODELS.find(m => m.id === model)?.color} fillOpacity={0.5} />
                <Line type="monotone" dataKey="y" data={fit} stroke="#be123c" strokeWidth={2} dot={false} name="OLS" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <SigBadge p={p} />
            <span className="text-slate-500">{t("validation.scatter.footnote", { n: fmt.integer(n) })}</span>
          </div>
        </Panel>

        <Panel title={t("validation.summary.title")} subtitle={t("validation.summary.subtitle")} className="col-span-12 xl:col-span-5" pad={false}>
          <table className="w-full text-[12px]">
            <tbody>
              {summaryRows.map(([k, v, d]) => (
                <tr key={k} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="px-4 py-2 font-medium">{k}</td>
                  <td className="px-2 py-2 font-mono text-end">{v}</td>
                  <td className="px-4 py-2 text-slate-500 text-[11px]">{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-3 text-[11px] text-slate-500 flex gap-1.5">
            <Info size={13} className="shrink-0 mt-0.5" /> {t("validation.summary.partialNote")}
          </div>
        </Panel>

        <Panel title={t("validation.lagged.title")} subtitle={t("validation.lagged.subtitle")} className="col-span-12 md:col-span-6">
          <div dir="ltr" className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={lagData} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="lag" tick={{ fontSize: 10 }} label={{ value: t("spectral.lagged.xAxis"), position: "insideBottom", offset: -2, fontSize: 10 }} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <ReferenceLine y={0} stroke="#94a3b8" />
                <Line type="monotone" dataKey="r" stroke="#0f766e" strokeWidth={2} dot={{ r: 3 }} name={t("spectral.lagged.seriesName")} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("validation.events.title")} subtitle={t("validation.events.subtitle", { threshold: fmt.number(ANOMALY_THRESHOLD, 2), thr: fmt.number(events.thr, 2) })} className="col-span-12 md:col-span-6" pad={false}>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-px bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 text-center text-[12px]">
              <div className="bg-white dark:bg-slate-900 p-3">
                <div className="text-[10px] uppercase text-slate-400">{t("validation.events.tpFp")}</div>
                <div className="font-mono font-semibold">
                  {fmt.integer(events.tp)} / {fmt.integer(events.fp)}
                </div>
              </div>
              <div className="bg-white dark:bg-slate-900 p-3">
                <div className="text-[10px] uppercase text-slate-400">{t("validation.events.fnTn")}</div>
                <div className="font-mono font-semibold">
                  {fmt.integer(events.fn)} / {fmt.integer(events.tn)}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mt-3 text-center">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">{t("validation.events.sensitivity")}</div>
                <div className="font-semibold">{fmt.number(events.sens, 2)}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">{t("validation.events.specificity")}</div>
                <div className="font-semibold">{fmt.number(events.spec, 2)}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">{t("validation.events.precision")}</div>
                <div className="font-semibold">{fmt.number(events.prec, 2)}</div>
              </div>
            </div>
            <div className="text-[10px] text-slate-400 mt-2">{t("validation.events.note", { rate: fmt.number(events.agreementRate * 100, 1) })}</div>
          </div>
        </Panel>

        <Panel title={t("validation.byYear.title")} subtitle={t("validation.byYear.subtitle")} className="col-span-12 md:col-span-6">
          <div dir="ltr" className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byYear} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <ReferenceLine y={0} stroke="#94a3b8" />
                <Bar dataKey="r" name={t("validation.summary.pearson")}>
                  {byYear.map((d, i) => (
                    <Cell key={i} fill={d.r >= 0 ? "#0f766e" : "#be123c"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={t("validation.splitHalf.title")} subtitle={t("validation.splitHalf.subtitle")} className="col-span-12 md:col-span-6">
          <div className="space-y-3 text-[12px]">
            <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <span>{t("validation.splitHalf.first")}</span>
              <b className="font-mono"><bdi>{fmt.number(r1, 3)}</bdi></b>
            </div>
            <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <span>{t("validation.splitHalf.second")}</span>
              <b className="font-mono"><bdi>{fmt.number(r2, 3)}</bdi></b>
            </div>
            <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <span>{t("validation.splitHalf.full")}</span>
              <b className="font-mono"><bdi>{fmt.number(r, 3)}</bdi></b>
            </div>
            <div className="text-[11px] text-slate-500 leading-relaxed">{t("validation.splitHalf.note")}</div>
            <div className="border border-slate-200 dark:border-slate-800 p-2">
              <div className="text-[10px] uppercase text-slate-400 mb-1">{t("validation.metadata.title")}</div>
              <div className="font-mono text-[10px] leading-relaxed text-slate-600 dark:text-slate-400" dir="ltr">
                model={model} · indicator={indicator} · control={control}
                <br />
                fields=[{fieldIds.slice(0, 4).join(",")}
                {fieldIds.length > 4 ? `, … (${fieldIds.length})` : ""}]<br />
                range={DATES[range[0]]?.slice(0, 7) ?? "—"}→{DATES[range[1]]?.slice(0, 7) ?? "—"} · n={n} · method=pearson/spearman/kendall/partial
                <br />
                locale={locale}
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}
