import { useEffect, useMemo } from "react";
import { AnalysisProvider, useAnalysis } from "./context/AnalysisContext";
import Overview from "./views/Overview";
import MapExplorer from "./views/MapExplorer";
import Temporal from "./views/Temporal";
import Spectral from "./views/Spectral";
import Validation from "./views/Validation";
import ModelComparison from "./views/ModelComparison";
import Spatial from "./views/Spatial";
import Reports from "./views/Reports";
import AnomalyDesk from "./views/AnomalyDesk";
import { LayoutDashboard, Map as MapIcon, Activity, ScatterChart, ShieldCheck, GitCompareArrows, Globe2, FileText, Sun, Moon, Sprout, X, FlaskConical, CircleDot } from "lucide-react";
import { cn } from "./utils/cn";
import { MODELS, INDICATORS, DATES, FIELDS, COVERAGE, DATA_PROVENANCE } from "./data/data";
import { useLocale, useT, LOCALES, type Locale } from "./i18n";

const NAV = [
  { id: "overview", icon: LayoutDashboard },
  { id: "map", icon: MapIcon },
  { id: "temporal", icon: Activity },
  { id: "spectral", icon: ScatterChart },
  { id: "validation", icon: ShieldCheck },
  { id: "comparison", icon: GitCompareArrows },
  { id: "spatial", icon: Globe2 },
  { id: "reports", icon: FileText },
  { id: "desk", icon: CircleDot },
] as const;

/** Compact, accessible language switcher (spec: labels "EN" and "FA"). */
function LanguageSwitcher() {
  const { locale, setLocale, labels, names } = useLocale();
  const t = useT();
  return (
    <div role="group" aria-label={t("app.language")} className="inline-flex items-center border border-slate-300 dark:border-slate-700 h-8" dir="ltr">
      {LOCALES.map((l: Locale) => (
        <button
          key={l}
          onClick={() => setLocale(l)}
          aria-pressed={locale === l}
          title={l === "fa" ? t("app.languageSwitchToFa") : t("app.languageSwitchToEn")}
          lang={l}
          className={cn(
            "h-full px-2 text-[11px] font-medium transition-colors",
            locale === l ? "bg-teal-700 text-white" : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          )}
        >
          <span aria-hidden="true">{labels[l]}</span>
          <span className="sr-only">{names[l]}</span>
        </button>
      ))}
    </div>
  );
}

function Shell() {
  const { view, setView, dark, setDark, model, setModel, indicator, setIndicator, selectedField, range, showDemoBanner, setShowDemoBanner } = useAnalysis();
  const t = useT();
  const { locale, fmt } = useLocale();
  const active = NAV.find(n => n.id === view) ?? NAV[0];

  // Keep the document title in sync with the locale.
  useEffect(() => {
    document.title = t("app.title");
  }, [t]);

  const navItems = useMemo(
    () => NAV.map(n => ({ ...n, label: t(`nav.${n.id}`), desc: t(`nav.${n.id}Desc`) })),
    // Re-derive the nav labels when the locale changes (`t` identity changes).
    [t]
  );

  const rangeLabel = `${DATES[range[0]]?.slice(0, 7) ?? "—"}→${DATES[range[1]]?.slice(0, 7) ?? "—"}`;

  return (
    <div className={cn("min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100", dark && "dark")}>
      <div className="flex min-h-screen">
        {/* Sidebar — first flex child follows the writing direction, so under
            dir="rtl" it sits on the right without extra CSS. */}
        <aside className="hidden md:flex flex-col w-60 shrink-0 border-e border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 sticky top-0 h-screen">
          <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-teal-700 flex items-center justify-center text-white shrink-0">
                <Sprout size={18} />
              </div>
              <div className="min-w-0">
                <div className="text-[13px] font-bold tracking-tight leading-tight">{t("app.name")}</div>
                <div className="text-[10px] text-slate-500 leading-tight">
                  {t("app.tagline")}
                  <br />
                  {t("app.taglineLine2")}
                </div>
              </div>
            </div>
          </div>
          <nav className="flex-1 overflow-auto py-2">
            {navItems.map(n => (
              <button
                key={n.id}
                onClick={() => setView(n.id)}
                aria-current={view === n.id ? "page" : undefined}
                className={cn(
                  "w-full flex items-center gap-2.5 px-4 py-2.5 text-start text-[12px] border-s-2",
                  view === n.id
                    ? "border-teal-700 bg-teal-50 dark:bg-teal-950/40 font-semibold text-teal-900 dark:text-teal-100"
                    : "border-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60"
                )}
              >
                <n.icon size={15} className="shrink-0" />
                <span>
                  <span className="block leading-tight">{n.label}</span>
                  <span className="block text-[10px] font-normal text-slate-400 leading-tight">{n.desc}</span>
                </span>
              </button>
            ))}
          </nav>
          <div className="p-3 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 leading-relaxed">
            <div className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
              <FlaskConical size={11} /> {t("app.sidebarFooterRole")}
            </div>
            <div className="mt-1">
              {t("app.sidebarFooterData")}
              <br />
              {t("app.sidebarFooterYears")}
            </div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Topbar */}
          <header className="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3 px-4 h-12">
              <div className="md:hidden flex items-center gap-2">
                <div className="w-7 h-7 bg-teal-700 flex items-center justify-center text-white">
                  <Sprout size={15} />
                </div>
                <span className="text-[12px] font-bold">{t("app.name")}</span>
              </div>
              <div className="hidden md:block min-w-0">
                <div className="text-[13px] font-semibold leading-tight truncate">{t(`nav.${active.id}`)}</div>
                <div className="text-[10px] text-slate-500 leading-tight truncate">{t(`nav.${active.id}Desc`)}</div>
              </div>
              <div className="flex-1" />
              {/* Shared state controls */}
              <div className="hidden lg:flex items-center gap-2 text-[11px]">
                <select value={model} onChange={e => setModel(e.target.value as typeof model)} aria-label={t("map.layer.model")} className="h-7 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-1.5 text-[11px]">
                  {MODELS.map(m => (
                    <option key={m.id} value={m.id}>
                      {t(`model.${m.id}.name`)}
                    </option>
                  ))}
                </select>
                <select value={indicator} onChange={e => setIndicator(e.target.value as typeof indicator)} aria-label={t("map.layer.indicatorLabel")} className="h-7 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-1.5 text-[11px]">
                  {INDICATORS.map(i => (
                    <option key={i.id} value={i.id}>
                      {i.name}
                    </option>
                  ))}
                </select>
                <span className="px-2 h-7 flex items-center border border-slate-200 dark:border-slate-700 text-slate-500 font-mono" dir="ltr">
                  {selectedField || "—"} · {rangeLabel}
                </span>
              </div>
              <LanguageSwitcher />
              <button onClick={() => setDark(!dark)} aria-label={t("app.toggleDark")} aria-pressed={dark} className="w-8 h-8 flex items-center justify-center border border-slate-300 dark:border-slate-700">
                {dark ? <Sun size={14} /> : <Moon size={14} />}
              </button>
            </div>
            {/* Mobile nav */}
            <div className="md:hidden flex overflow-x-auto gap-1 px-2 pb-2">
              {navItems.map(n => (
                <button key={n.id} onClick={() => setView(n.id)} className={cn("shrink-0 px-2.5 py-1.5 text-[11px] border", view === n.id ? "bg-teal-700 text-white border-teal-700" : "border-slate-300 dark:border-slate-700")}>
                  {n.label}
                </button>
              ))}
            </div>
          </header>

          {showDemoBanner && (
            <div className="bg-teal-50 dark:bg-teal-950/40 border-b border-teal-200 dark:border-teal-900 px-4 py-2 flex items-start gap-2 text-[11px] text-teal-900 dark:text-teal-200">
              <FlaskConical size={13} className="shrink-0 mt-0.5" />
              <span className="flex-1 leading-relaxed">
                <b>{t("app.demoBannerTitle")}</b> {t("app.demoBannerBody")}
              </span>
              <button onClick={() => setShowDemoBanner(false)} aria-label={t("app.dismissBanner")} className="shrink-0">
                <X size={13} />
              </button>
            </div>
          )}

          <main className="flex-1 p-4 max-w-[1600px] w-full mx-auto">
            {view === "overview" && <Overview />}
            {view === "map" && <MapExplorer />}
            {view === "temporal" && <Temporal />}
            {view === "spectral" && <Spectral />}
            {view === "validation" && <Validation />}
            {view === "comparison" && <ModelComparison />}
            {view === "spatial" && <Spatial />}
            {view === "reports" && <Reports />}
            {view === "desk" && <AnomalyDesk />}
          </main>

          <footer className="border-t border-slate-200 dark:border-slate-800 px-4 py-3 text-[10px] text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
            <span>{t("app.footer.title")}</span>
            <span>
              {t("app.footer.coverage", {
                fields: fmt.integer(FIELDS.length),
                first: COVERAGE.yearStart,
                last: COVERAGE.yearEnd,
              })}
            </span>
            <span>{t("app.footer.models")}</span>
            <span className="font-mono" dir="ltr">
              {DATA_PROVENANCE.source} · {locale}
            </span>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AnalysisProvider>
      <Shell />
    </AnalysisProvider>
  );
}
