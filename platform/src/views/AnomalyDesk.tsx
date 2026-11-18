// AnomalyDesk — the Halqeh review desk as the platform's ninth view
// (add-halqeh-anomaly-desk tasks 2.3–2.5, 3.1–3.2).
//
// Ported from the Grok workspace build (D:\RS\Thesis\Halqeh\…, never committed):
// the season-ring case review with stage-envelope vs. blunt-NDVI-cut modes,
// verdict buttons and field notes. Differences from the source, all deliberate:
//  - state is platform-idiomatic useState + localStorage (no zustand, design D3);
//  - language follows the platform switcher (no internal toggle, design D6);
//  - case data comes from the desk payload — a complete replay of the run's
//    parquet, not the source build's 12-case hand-pick (design D1);
//  - the SVG centroid scatter is replaced by DeskMap with real raster context
//    (design D4);
//  - opening a case selects its first flagged bin (the review desk opens on
//    the evidence instead of an empty selection).
//
// Honesty framing (spec platform-anomaly-desk): flags are stage-conditioned
// NDVI anomalies under review; verdicts/notes are device-local annotations,
// never ground truth; censored cycles read as incomplete; L2–L3 evidence
// browsing only — no accuracy claim appears in this view.
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import {
  DESK,
  DESK_CASES,
  DESK_STAGES,
  firstFlaggedIdx,
  type DeskCase,
  type DeskFilter,
  type DeskMode,
  type DeskVerdict,
} from "../data/desk";
import { fieldById } from "../data/data";
import { useLocale, useT } from "../i18n";
import { SeasonRing } from "../components/SeasonRing";
import { SeasonChart } from "../components/SeasonChart";
import DeskMap from "../components/DeskMap";
import {
  loadDeskNotes,
  loadDeskUi,
  loadDeskVerdicts,
  saveDeskNotes,
  saveDeskUi,
  saveDeskVerdicts,
  type DeskNotes,
  type DeskVerdicts,
} from "../utils/deskStorage";

const VERDICTS: DeskVerdict[] = ["stress", "delay", "gap", "clear"];

const FILTERS: { id: DeskFilter; labelKey: string }[] = [
  { id: "all", labelKey: "desk.filter.all" },
  { id: "slip", labelKey: "desk.filter.slips" },
  { id: "spared", labelKey: "desk.filter.spared" },
  { id: "unread", labelKey: "desk.filter.unread" },
];

export default function AnomalyDesk() {
  const { fmt } = useLocale();
  const t = useT();

  const storedUi = useMemo(() => loadDeskUi(), []);
  const [filter, setFilter] = useState<DeskFilter>(storedUi?.filter ?? "all");
  const [mode, setMode] = useState<DeskMode>(storedUi?.mode ?? "envelope");
  const [caseId, setCaseId] = useState<string | null>(storedUi?.caseId ?? null);
  const [binIndex, setBinIndex] = useState<number | null>(null);
  const [verdicts, setVerdicts] = useState<DeskVerdicts>(() => loadDeskVerdicts());
  const [notes, setNotes] = useState<DeskNotes>(() => loadDeskNotes());

  const visible = useMemo(() => {
    return DESK_CASES.filter(c => {
      if (filter === "slip") return c.kind === "slip";
      if (filter === "spared") return c.kind === "spared";
      if (filter === "unread") return !verdicts[c.id];
      return true;
    });
  }, [filter, verdicts]);

  const item: DeskCase | undefined = visible.find(c => c.id === caseId) ?? visible[0] ?? DESK_CASES[0];
  const index = item ? Math.max(0, visible.findIndex(c => c.id === item.id)) : 0;
  const bin = item && binIndex != null ? item.bins[binIndex] : undefined;

  // Opening a case lands on its first flagged bin; a stale bin index (case
  // switch, shorter cycle) resets to the same default. Null-safe on empty sets.
  useEffect(() => {
    if (!item) return;
    setBinIndex(prev => (prev != null && prev < item.bins.length ? prev : firstFlaggedIdx(item)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.id, item?.bins.length]);

  // Persist the resolved UI state + annotations (device-local, D3).
  useEffect(() => {
    saveDeskUi({ caseId: item?.id ?? null, mode, filter });
  }, [item?.id, mode, filter]);
  useEffect(() => saveDeskVerdicts(verdicts), [verdicts]);
  useEffect(() => saveDeskNotes(notes), [notes]);

  const counts = useMemo(
    () => ({
      all: DESK_CASES.length,
      slip: DESK_CASES.filter(c => c.kind === "slip").length,
      spared: DESK_CASES.filter(c => c.kind === "spared").length,
      unread: DESK_CASES.filter(c => !verdicts[c.id]).length,
    }),
    [verdicts],
  );

  function pickCase(id: string) {
    setCaseId(id);
    const c = DESK_CASES.find(x => x.id === id);
    setBinIndex(c ? firstFlaggedIdx(c) : null);
  }

  function step(delta: number) {
    if (!visible.length || !item) return;
    const next = visible[(index + delta + visible.length) % visible.length];
    pickCase(next.id);
  }

  function setVerdict(id: string, verdict: DeskVerdict) {
    setVerdicts(prev => ({ ...prev, [id]: { verdict, updatedAt: new Date().toISOString() } }));
  }

  function setNote(id: string, note: string) {
    setNotes(prev => ({ ...prev, [id]: { note, updatedAt: new Date().toISOString() } }));
  }

  /** Review-session download (design D7): only user-authored state + the
   *  payload provenance. Reviewers archive it under reports/expert_reviews/. */
  function exportReview() {
    const annotations: Record<string, { verdict?: string; note?: string; updated_at: string }> = {};
    for (const [id, e] of Object.entries(verdicts)) {
      annotations[id] = { verdict: e.verdict, updated_at: e.updatedAt };
    }
    for (const [id, e] of Object.entries(notes)) {
      if (!e.note.trim()) continue;
      const merged = annotations[id] ?? {};
      annotations[id] = {
        note: e.note,
        updated_at: (merged.updated_at ?? "") > e.updatedAt ? merged.updated_at : e.updatedAt,
      };
    }
    const clean = Object.fromEntries(
      Object.entries(annotations).filter(([, a]) => a.verdict !== undefined || a.note !== undefined),
    );
    const body = JSON.stringify(
      { exported_at: new Date().toISOString(), payload_provenance: DESK.provenance, annotations: clean },
      null,
      2,
    );
    const url = URL.createObjectURL(new Blob([body], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `halqeh-desk-review-${new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!item) {
    return (
      <div className="desk-root bg-[var(--desk-paper)] p-6 text-[var(--desk-ink)]">
        <p>{t("ui.noData")}</p>
      </div>
    );
  }

  const verdict = verdicts[item.id];
  const note = notes[item.id];
  const farm = fieldById(item.fieldId);

  return (
    <div className="desk-root bg-[var(--desk-paper)] text-[var(--desk-ink)]">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-5 lg:px-8 lg:py-8">
        <header className="flex flex-col gap-4 border-b border-[var(--desk-line)] pb-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="desk-serif text-3xl italic leading-none tracking-tight lg:text-4xl">Halqeh</p>
              <p className="mt-1 text-lg leading-none text-[var(--desk-cane)]">حلقه</p>
              <p className="mt-3 max-w-xl text-sm text-[var(--desk-muted)]">{t("desk.kicker")}</p>
            </div>
            <button
              type="button"
              onClick={exportReview}
              className="flex min-h-11 items-center gap-2 rounded-full border border-[var(--desk-line)] bg-[var(--desk-card)] px-4 text-sm font-medium"
            >
              <Download className="size-4" aria-hidden="true" />
              {t("desk.export")}
            </button>
          </div>
          <p className="max-w-2xl text-base">{t("desk.lede")}</p>
          <p className="max-w-2xl text-sm text-[var(--desk-muted)]">
            {t("desk.compare")} <bdi>{fmt.integer(DESK.totals.naiveOnly)}</bdi> {t("desk.compareMid")}{" "}
            <bdi>{fmt.integer(DESK.totals.envelopeOnly)}</bdi> {t("desk.compareEnd")}
          </p>
        </header>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {FILTERS.map(({ id, labelKey }) => (
            <button
              key={id}
              type="button"
              onClick={() => setFilter(id)}
              aria-pressed={filter === id}
              className={
                filter === id
                  ? "min-h-11 shrink-0 rounded-full bg-[var(--desk-ink)] px-4 text-sm text-[var(--desk-paper)]"
                  : "min-h-11 shrink-0 rounded-full border border-[var(--desk-line)] bg-[var(--desk-card)] px-4 text-sm"
              }
            >
              {t(labelKey)} <bdi>{fmt.integer(counts[id])}</bdi>
            </button>
          ))}
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-[17rem_1fr]">
          <aside className="flex flex-row flex-nowrap gap-2 overflow-x-auto lg:max-h-[38rem] lg:flex-col lg:overflow-y-auto">
            {visible.map(c => (
              <CaseChip
                key={c.id}
                item={c}
                active={c.id === item.id}
                reviewed={!!verdicts[c.id]}
                onPick={() => pickCase(c.id)}
              />
            ))}
          </aside>

          <section className="flex flex-col gap-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm text-[var(--desk-muted)]">
                  {item.fieldId} · {item.farm ?? "—"} · {t("desk.cycle")} <bdi>{fmt.integer(item.cycle)}</bdi>
                </p>
                <h1 className="desk-serif mt-1 text-2xl leading-tight lg:text-3xl">{headline(item)}</h1>
                <p className="mt-2 text-sm text-[var(--desk-muted)]">
                  {item.name ?? item.code ?? item.fieldId} · <bdi>{item.start}</bdi> → <bdi>{item.end}</bdi> ·{" "}
                  <bdi>{fmt.integer(item.lengthDays)}</bdi> {t("desk.days")}
                </p>
              </div>
              <div className="flex shrink-0 gap-2" dir="ltr">
                <button
                  type="button"
                  aria-label={t("desk.prevCase")}
                  onClick={() => step(-1)}
                  className="flex size-11 items-center justify-center rounded-full border border-[var(--desk-line)] bg-[var(--desk-card)]"
                >
                  <ChevronLeft className="size-5" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  aria-label={t("desk.nextCase")}
                  onClick={() => step(1)}
                  className="flex size-11 items-center justify-center rounded-full border border-[var(--desk-line)] bg-[var(--desk-card)]"
                >
                  <ChevronRight className="size-5" aria-hidden="true" />
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              {(
                [
                  ["envelope", t("desk.mode.envelope")],
                  ["naive", t("desk.mode.naive")],
                ] as [DeskMode, string][]
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setMode(id)}
                  aria-pressed={mode === id}
                  className={
                    mode === id
                      ? "min-h-11 rounded-full bg-[var(--desk-cane)] px-4 text-sm font-medium text-[var(--desk-card)]"
                      : "min-h-11 rounded-full border border-[var(--desk-line)] bg-[var(--desk-card)] px-4 text-sm"
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="grid gap-4 rounded-2xl border border-[var(--desk-line)] bg-[var(--desk-card)] p-3 lg:grid-cols-[18rem_1fr] lg:p-4">
              <SeasonRing item={item} mode={mode} active={binIndex} onPick={setBinIndex} />
              <div className="flex flex-col gap-3">
                <p className="desk-serif text-sm text-[var(--desk-muted)]">{t("desk.rule")}</p>
                <ul className="flex flex-col gap-2">
                  {DESK_STAGES.map(stage => {
                    const env = DESK.envelopes[stage.id];
                    const on = bin?.stage === stage.id;
                    return (
                      <li
                        key={stage.id}
                        className={
                          on
                            ? "rounded-xl border border-[var(--desk-cane)] bg-[var(--desk-paper)] px-3 py-2"
                            : "rounded-xl border border-[var(--desk-line)] px-3 py-2"
                        }
                      >
                        <div className="flex items-baseline justify-between gap-3">
                          <span className="text-sm font-medium">
                            {stage.id} · {t(stage.nameKey)}
                          </span>
                          <span className="text-xs text-[var(--desk-muted)]">
                            {t("desk.floor")}{" "}
                            <bdi>{env.lo < 0 ? "—" : fmt.number(env.lo, 2)}</bdi> · {t("desk.median")}{" "}
                            <bdi>{fmt.number(env.median, 2)}</bdi> ·{" "}
                            <bdi>{fmt.integer(env.n)}</bdi> {t("desk.binsPooled")}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-[var(--desk-muted)]">{t(stage.noteKey)}</p>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>

            <div className="rounded-2xl border border-[var(--desk-line)] bg-[var(--desk-card)] p-3 lg:p-4">
              <SeasonChart item={item} mode={mode} active={binIndex} onPick={setBinIndex} />
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--desk-muted)]">
                <span>{t("desk.legend.band")}</span>
                <span>{t("desk.legend.median")}</span>
                <span>{t("desk.legend.ink")}</span>
                <span>{t("desk.legend.called")}</span>
                <span>
                  <bdi>{fmt.integer(item.flags)}</bdi> {t("desk.envelopeOn")}
                </span>
                <span>
                  <bdi>{fmt.integer(item.naive)}</bdi> {t("desk.naiveOn")}
                </span>
                {item.kind === "slip" ? (
                  <span>
                    <bdi>{fmt.number(item.deepest, 3)}</bdi> {t("desk.deepest")}
                  </span>
                ) : null}
              </div>
            </div>

            {bin ? (
              <p className="text-sm">
                <bdi>{bin.d}</bdi> · {bin.stage} · NDVI <bdi>{fmt.number(bin.v, 3)}</bdi> · {t("desk.floor")}{" "}
                <bdi>{fmt.number(bin.lo, 3)}</bdi>
                {bin.f ? ` · ${t("desk.bin.underFloor")}` : ""}
              </p>
            ) : null}

            <div className="rounded-2xl border border-[var(--desk-line)] bg-[var(--desk-card)] p-4">
              <p className="desk-serif text-sm text-[var(--desk-muted)]">{t("desk.read")}</p>
              <p className="mt-2 text-sm">{reading(item)}</p>
              {item.censored ? <p className="mt-2 text-sm text-[var(--desk-muted)]">{t("desk.censored")}</p> : null}
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
                <Fact k={t("desk.place")} v={item.municipality ?? "—"} />
                <Fact k={t("desk.variety")} v={item.variety ?? "—"} />
                <Fact k={t("desk.area")} v={item.areaHa != null ? `${fmt.number(item.areaHa, 1)} ${t("desk.ha")}` : "—"} />
                <Fact
                  k={t("desk.anomaly")}
                  v={verdict ? t(`desk.verdict.${verdict.verdict}`) : "—"}
                />
              </dl>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {VERDICTS.map(v => {
                const on = verdict?.verdict === v;
                return (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setVerdict(item.id, v)}
                    aria-pressed={on}
                    className={
                      on
                        ? v === "clear"
                          ? "min-h-11 rounded-xl bg-[var(--desk-cane)] px-3 text-sm font-medium text-[var(--desk-card)]"
                          : v === "stress"
                            ? "min-h-11 rounded-xl bg-[var(--desk-slip)] px-3 text-sm font-medium text-[var(--desk-card)]"
                            : "min-h-11 rounded-xl bg-[var(--desk-ink)] px-3 text-sm font-medium text-[var(--desk-paper)]"
                        : "min-h-11 rounded-xl border border-[var(--desk-line)] bg-[var(--desk-card)] px-3 text-sm"
                    }
                  >
                    {t(`desk.verdict.${v}`)}
                  </button>
                );
              })}
            </div>
            <textarea
              value={note?.note ?? ""}
              onChange={e => setNote(item.id, e.target.value)}
              placeholder={t("desk.note.placeholder")}
              aria-label={t("desk.note.placeholder")}
              rows={2}
              className="w-full resize-none rounded-xl border border-[var(--desk-line)] bg-[var(--desk-card)] px-3 py-3 text-sm placeholder:text-[var(--desk-muted)]"
            />
            <p className="text-xs text-[var(--desk-muted)]">{t("desk.export.hint")}</p>

            <DeskMap
              item={item}
              polygon={farm.polygon as [number, number][]}
              centroid={farm.centroid as [number, number] | null}
              binDate={bin?.d ?? null}
            />
          </section>
        </div>

        <footer className="border-t border-[var(--desk-line)] pt-4 text-xs leading-relaxed text-[var(--desk-muted)]">
          <p>
            {t("desk.published")}: <bdi>{fmt.integer(DESK.totals.flags)}</bdi> /{" "}
            <bdi>{fmt.integer(DESK.totals.validObsReported)}</bdi> (
            <bdi>{fmt.number(DESK.totals.flagRate * 100, 2)}%</bdi>) ·{" "}
            {t("desk.footer.fields", { n: fmt.integer(DESK.totals.fieldsInRun) })} ·{" "}
            {t("desk.footer.cycles", { n: fmt.integer(DESK.totals.cycles) })} · <bdi>{DESK.generated}</bdi>.{" "}
            {t("desk.replaySentence", { rows: fmt.integer(DESK.totals.rows), flags: fmt.integer(DESK.totals.flags) })}
          </p>
          <p className="mt-2">{t("desk.ladder")}</p>
          <p className="mt-2">{t("desk.source", { date: DESK.generated })}</p>
        </footer>
      </div>
    </div>
  );

  function headline(it: DeskCase): string {
    if (it.kind === "spared") return t("desk.headline.spared");
    if (it.flags >= 6) return t("desk.headline.flags", { n: fmt.integer(it.flags) });
    return t("desk.headline.short", { n: fmt.integer(it.flags) });
  }

  function reading(it: DeskCase): string {
    if (it.kind === "spared") {
      const peak = it.s2max != null ? fmt.number(it.s2max, 2) : "—";
      const low = it.s3min != null ? fmt.number(it.s3min, 2) : "—";
      const drop = it.s2max != null && it.s3min != null ? fmt.number(it.s2max - it.s3min, 2) : "—";
      return t("desk.read.spared", { peak, low, drop, naive: fmt.integer(it.naive) });
    }
    return t("desk.read.slip", { deepest: fmt.number(it.deepest, 3) });
  }
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs text-[var(--desk-muted)]">{k}</dt>
      <dd className="mt-0.5">{v}</dd>
    </div>
  );
}

function CaseChip({
  item,
  active,
  reviewed,
  onPick,
}: {
  item: DeskCase;
  active: boolean;
  reviewed: boolean;
  onPick: () => void;
}) {
  const { fmt } = useLocale();
  const t = useT();
  const w = 64;
  const h = 26;
  const bins = item.bins;
  const d = bins
    .map((b, i) => {
      const x = bins.length === 1 ? 0 : (i / (bins.length - 1)) * w;
      const y = h - (Math.max(0, Math.min(0.85, b.v)) / 0.85) * (h - 2) - 1;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join("");
  return (
    <button
      type="button"
      onClick={onPick}
      aria-pressed={active}
      className={
        active
          ? "flex min-h-16 min-w-52 shrink-0 items-center gap-3 rounded-2xl border border-[var(--desk-ink)] bg-[var(--desk-card)] px-3 py-2 text-start lg:w-full"
          : "flex min-h-16 min-w-52 shrink-0 items-center gap-3 rounded-2xl border border-[var(--desk-line)] bg-[var(--desk-card)] px-3 py-2 text-start lg:w-full"
      }
    >
      <svg viewBox={`0 0 ${w} ${h}`} className="h-7 w-16 shrink-0" aria-hidden="true">
        <path d={d} fill="none" stroke="var(--desk-ink)" strokeWidth="1.4" />
      </svg>
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium">{item.code ?? item.fieldId}</span>
        <span className="block text-xs text-[var(--desk-muted)]">
          {item.kind === "spared"
            ? t("desk.chip.spared")
            : t("desk.chip.slips", { n: fmt.integer(item.flags) })}
          {reviewed ? " · ●" : ""}
        </span>
      </span>
    </button>
  );
}
