import { useState } from "react";
import { Panel, Badge, EmptyState, PipelineDataBadge } from "../components/ui";
import { useAnalysis } from "../context/AnalysisContext";
import { DATES, getSeries, getPairs, pearson, spearman, downloadCSV, modelById, indicatorById } from "../data/data";
import { useLocale, useT } from "../i18n";
import { Download, Trash2, FileText, Plus, Image as ImageIcon } from "lucide-react";

export default function Reports() {
  const { experiments, addExperiment, removeExperiment, model, indicator, selectedFields, range, selectedField, setView } = useAnalysis();
  const t = useT();
  const { fmt } = useLocale();
  const [name, setName] = useState("");
  const [note, setNote] = useState("");

  const create = () => {
    const p = getPairs(model, indicator, selectedFields, range);
    addExperiment({
      id: `exp-${Date.now()}`,
      // Experiment names are stored localized at save time — they are user data,
      // not UI chrome, so they are intentionally not re-translated on locale change.
      name: name || t("reports.experiment.defaultSuffix", { model: t(`model.${model}.name`), indicator: indicatorById(indicator).name, n: fmt.integer(selectedFields.length) }),
      created: new Date().toISOString().slice(0, 10),
      model,
      indicator,
      fields: selectedFields,
      range,
      note: note || t("reports.experiment.manualNote"),
      stats: `r=${fmt.number(pearson(p.xs, p.ys), 3)} ρ=${fmt.number(spearman(p.xs, p.ys), 3)} n=${fmt.integer(p.xs.length)}`,
    });
    setName("");
    setNote("");
  };

  const exportSeries = () => {
    const s = getSeries(selectedField);
    // Absent channels export as *empty cells*, never 0.0000 — a fabricated
    // zero in a research CSV is worse than a gap (wire-platform-to-real-data).
    const cell = (v: number | null, d = 4) => (v == null || !Number.isFinite(v) ? "" : v.toFixed(d));
    const score = (v: number | null) => (v == null || !Number.isFinite(v) ? "" : v.toFixed(4));
    downloadCSV(`series_${selectedField}_${model}.csv`, [
      ["date", "missing", model, "ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "precip", "temp", "provenance"],
      ...s.map(o => [o.date, o.missing ? 1 : 0, score(o.scores[model]), cell(o.ndvi), cell(o.evi), cell(o.savi), cell(o.ndmi), cell(o.tvdi), cell(o.cwsi), cell(o.eta), cell(o.precip, 2), cell(o.temp, 2), o.provenance ? JSON.stringify(o.provenance) : ""]),
    ]);
  };

  const exportPairs = () => {
    const p = getPairs(model, indicator, selectedFields, range);
    downloadCSV(`pairs_${model}_${indicator}.csv`, [["field", "date", "score", indicator], ...p.meta.map((m, i) => [m.field, m.date, p.xs[i].toFixed(4), p.ys[i].toFixed(4)])]);
  };

  const exportExperiments = () => {
    downloadCSV("experiments.csv", [
      ["id", "name", "created", "model", "indicator", "fields", "range", "stats", "note"],
      ...experiments.map(e => [e.id, e.name, e.created, e.model, e.indicator, e.fields.join(";"), `${DATES[e.range[0]]?.slice(0, 7) ?? "—"}→${DATES[e.range[1]]?.slice(0, 7) ?? "—"}`, e.stats, e.note]),
    ]);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-12 gap-4">
        <Panel title={t("reports.create.title")} subtitle={t("reports.create.subtitle")} className="col-span-12 lg:col-span-4">
          <div className="space-y-3">
            <div className="text-[12px] space-y-1">
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">{t("reports.create.model")}</span>
                <Badge color={modelById(model).color}>{t(`model.${model}.name`)}</Badge>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">{t("reports.create.indicator")}</span>
                <Badge color={indicatorById(indicator).color}>{indicatorById(indicator).name}</Badge>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">{t("reports.create.fields")}</span>
                <span>{t("reports.create.fieldsSelected", { n: fmt.integer(selectedFields.length) })}</span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">{t("reports.create.range")}</span>
                <span>
                  {DATES[range[0]]?.slice(0, 7) ?? "—"} → {DATES[range[1]]?.slice(0, 7) ?? "—"}
                </span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-slate-500">{t("reports.create.focusField")}</span>
                <span className="font-mono">{selectedField || "—"}</span>
              </div>
            </div>
            <input value={name} onChange={e => setName(e.target.value)} placeholder={t("reports.create.namePlaceholder")} className="w-full h-8 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-[12px] outline-none" />
            <textarea value={note} onChange={e => setNote(e.target.value)} placeholder={t("reports.create.notePlaceholder")} rows={3} className="w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 py-1.5 text-[12px] outline-none" />
            <button onClick={create} className="w-full h-8 bg-teal-700 text-white text-[12px] flex items-center justify-center gap-2">
              <Plus size={13} /> {t("reports.create.save")}
            </button>
            <div className="text-[11px] text-slate-500">{t("reports.create.tip")}</div>
          </div>
        </Panel>

        <Panel title={t("reports.export.title")} subtitle={t("reports.export.subtitle")} className="col-span-12 lg:col-span-4">
          <div className="space-y-2">
            <button onClick={exportSeries} className="w-full flex items-center gap-2 h-9 border border-slate-300 dark:border-slate-700 px-3 text-[12px] hover:bg-slate-50 dark:hover:bg-slate-800">
              <Download size={13} /> {t("reports.export.series", { field: selectedField || "—", model: t(`model.${model}.name`) })}
            </button>
            <button onClick={exportPairs} className="w-full flex items-center gap-2 h-9 border border-slate-300 dark:border-slate-700 px-3 text-[12px] hover:bg-slate-50 dark:hover:bg-slate-800">
              <Download size={13} /> {t("reports.export.pairs", { model: t(`model.${model}.name`), indicator: indicatorById(indicator).name })}
            </button>
            <button onClick={exportExperiments} className="w-full flex items-center gap-2 h-9 border border-slate-300 dark:border-slate-700 px-3 text-[12px] hover:bg-slate-50 dark:hover:bg-slate-800">
              <Download size={13} /> {t("reports.export.experiments")}
            </button>
            <button onClick={() => window.print()} className="w-full flex items-center gap-2 h-9 border border-slate-300 dark:border-slate-700 px-3 text-[12px] hover:bg-slate-50 dark:hover:bg-slate-800">
              <ImageIcon size={13} /> {t("reports.export.print")}
            </button>
            <div className="border border-slate-200 dark:border-slate-800 p-2 text-[11px] text-slate-500 leading-relaxed">
              {t("reports.export.note")}
              <div className="mt-2">
                <PipelineDataBadge />
              </div>
            </div>
          </div>
        </Panel>

        <Panel title={t("reports.checklist.title")} className="col-span-12 lg:col-span-4">
          <ul className="text-[12px] text-slate-600 dark:text-slate-400 space-y-2 list-disc ps-4 leading-relaxed">
            <li>{t("reports.checklist.a")}</li>
            <li>{t("reports.checklist.b")}</li>
            <li>{t("reports.checklist.c")}</li>
            <li>{t("reports.checklist.d")}</li>
            <li>{t("reports.checklist.e")}</li>
          </ul>
        </Panel>
      </div>

      <Panel title={t("reports.saved.title")} subtitle={t("reports.saved.subtitle", { n: fmt.integer(experiments.length) })} pad={false}>
        {experiments.length === 0 ? (
          <div className="p-4">
            <EmptyState title={t("reports.saved.emptyTitle")} desc={t("reports.saved.emptyDesc")} />
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="w-full text-[12px]">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="text-start px-4 py-2 font-medium">{t("reports.saved.name")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.created")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.modelIndicator")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.fields")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.range")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.stats")}</th>
                  <th className="text-start px-2 py-2 font-medium">{t("reports.saved.note")}</th>
                  <th className="px-2 py-2" />
                </tr>
              </thead>
              <tbody>
                {experiments.map(e => (
                  <tr key={e.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-4 py-2.5 font-medium">
                      <span className="inline-flex items-center gap-1.5">
                        <FileText size={12} className="text-slate-400" />
                        {e.name}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-slate-500">{e.created}</td>
                    <td className="px-2 py-2.5">
                      <Badge color={modelById(e.model).color}>{modelById(e.model).short}</Badge> <Badge color={indicatorById(e.indicator).color}>{indicatorById(e.indicator).name}</Badge>
                    </td>
                    <td className="px-2 py-2.5"><bdi>{fmt.integer(e.fields.length)}</bdi></td>
                    <td className="px-2 py-2.5">
                      {DATES[e.range[0]]?.slice(0, 7) ?? "—"}→{DATES[e.range[1]]?.slice(0, 7) ?? "—"}
                    </td>
                    <td className="px-2 py-2.5 font-mono text-[11px]">{e.stats}</td>
                    <td className="px-2 py-2.5 text-slate-500 max-w-48 truncate">{e.note}</td>
                    <td className="px-2 py-2.5">
                      <button onClick={() => removeExperiment(e.id)} aria-label={t("reports.saved.remove")} className="text-slate-400 hover:text-red-600">
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <div className="flex flex-wrap gap-2">
        <button onClick={() => setView("validation")} className="h-8 px-3 border border-slate-300 dark:border-slate-700 text-[12px]">
          {t("reports.gotoValidation")}
        </button>
        <button onClick={() => setView("comparison")} className="h-8 px-3 border border-slate-300 dark:border-slate-700 text-[12px]">
          {t("reports.gotoComparison")}
        </button>
      </div>
    </div>
  );
}
