import React from "react";
import { FlaskConical } from "lucide-react";
import { cn } from "../utils/cn";
import { useT } from "../i18n";

export function Panel({ title, subtitle, right, children, className, pad = true }: { title?: string; subtitle?: string; right?: React.ReactNode; children: React.ReactNode; className?: string; pad?: boolean }) {
  return (
    <section className={cn("border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900", className)}>
      {(title || right) && (
        <header className="flex items-start justify-between gap-3 border-b border-slate-200 dark:border-slate-800 px-4 py-3">
          <div className="min-w-0">
            {title && <h3 className="text-[13px] font-semibold tracking-tight text-slate-900 dark:text-slate-100">{title}</h3>}
            {subtitle && <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">{subtitle}</p>}
          </div>
          {right && <div className="shrink-0">{right}</div>}
        </header>
      )}
      <div className={pad ? "p-4" : ""}>{children}</div>
    </section>
  );
}

export function Stat({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: string }) {
  return (
    <div className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3">
      <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400 font-medium">{label}</div>
      {/* <bdi> isolates the value so Persian prose around it cannot reverse a
          leading minus sign into "0.547-" under dir="rtl". */}
      <div className={cn("text-xl font-semibold tracking-tight mt-1 text-slate-900 dark:text-slate-100", tone)}>
        <bdi>{value}</bdi>
      </div>
      {sub && <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

export function Badge({ children, color, title }: { children: React.ReactNode; color?: string; title?: string }) {
  return <span title={title} className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 border" style={{ color: color || "#475569", borderColor: color ? color + "55" : "#cbd5e1", background: color ? color + "12" : "#f8fafc" }}>{children}</span>;
}

/**
 * Data-provenance badge. Every view rendering the pipeline payload carries an
 * explicit marker of where its values come from and their validation status
 * (wire-platform-to-real-data: the old "Demonstration data" wording
 * misrepresented real pipeline output as demo data).
 */
export function PipelineDataBadge({ className }: { className?: string }) {
  const t = useT();
  return (
    <span
      title={t("ui.pipelineBadgeTitle")}
      className={cn(
        "inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 border border-teal-600/40 text-teal-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40",
        className
      )}
    >
      <FlaskConical size={10} aria-hidden="true" />
      {t("ui.pipelineBadge")}
    </span>
  );
}

export function Select({ value, onChange, children, className, ariaLabel }: { value: string; onChange: (v: string) => void; children: React.ReactNode; className?: string; ariaLabel?: string }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      aria-label={ariaLabel}
      className={cn("h-8 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12px] px-2 text-slate-800 dark:text-slate-200 outline-none focus:border-teal-600", className)}
    >
      {children}
    </select>
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-[10px] uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400 font-medium mb-1">{children}</label>;
}

export function EmptyState({ title, desc }: { title?: string; desc?: string }) {
  const t = useT();
  return (
    <div className="border border-dashed border-slate-300 dark:border-slate-700 p-8 text-center">
      <div className="text-[13px] font-medium text-slate-700 dark:text-slate-300">{title ?? t("ui.noData")}</div>
      <div className="text-[12px] text-slate-500 mt-1">{desc ?? t("ui.noDataDesc")}</div>
    </div>
  );
}

export function SigBadge({ p }: { p: number }) {
  const t = useT();
  if (isNaN(p)) return <Badge>—</Badge>;
  const label = p < 0.001 ? t("ui.pStrong") : p < 0.01 ? t("ui.pMid") : p < 0.05 ? t("ui.pWeak") : t("ui.pNs");
  const color = p < 0.05 ? "#0f766e" : "#64748b";
  return <Badge color={color}>{label}</Badge>;
}

export const fmt = (v: number | null | undefined, d = 3) => (v == null || isNaN(v) ? "—" : v.toFixed(d));
export const fmt2 = (v: number | null | undefined) => (v == null || isNaN(v) ? "—" : v.toFixed(2));

export function anomalyColor(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "#94a3b8";
  if (v >= 0.75) return "#be123c";
  if (v >= 0.65) return "#ea580c";
  if (v >= 0.5) return "#d97706";
  if (v >= 0.35) return "#65a30d";
  return "#0f766e";
}

export type ProvenanceChipState = 'observed' | 'modelled' | 'proxy' | 'absent' | 'legacy' | 'model';

export function ProvenanceChip({ state, title }: { state: ProvenanceChipState; title?: string }): React.ReactElement {
  const t = useT();
  const labels: Record<ProvenanceChipState, string> = {
    observed: t("prov.observed"),
    modelled: t("prov.modelled"),
    model: t("prov.model"),
    proxy: t("prov.proxy"),
    absent: t("prov.absent"),
    legacy: t("prov.legacy"),
  };
  const colors: Record<ProvenanceChipState, string> = {
    observed: "#0f766e",
    modelled: "#0284c7",
    model: "#7c3aed",
    proxy: "#d97706",
    absent: "#94a3b8",
    legacy: "#be123c",
  };
  const color = colors[state];
  return (
    <span
      title={title ?? labels[state]}
      className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 border"
      style={{ color: color, borderColor: color + "55", background: color + "12" }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} aria-hidden="true" />
      {labels[state]}
    </span>
  );
}

export const fmtObs = (v: number | null, d = 3): string => {
  const n = v == null ? NaN : v;
  return isNaN(n) ? "—" : n.toFixed(d);
};

/**
 * Compact provenance summary for one observation. The previous UI rendered
 * ten separate chips (one per channel) that dominated the inspector; the same
 * information is grouped by provenance state into at most three short lines.
 * Hovering a line titles the exact channel: state pairs, so the per-channel
 * labelling contract is preserved (platform-real-data spec).
 */
const PROV_CHANNEL_ORDER: { key: string; label: string }[] = [
  { key: "ndvi", label: "NDVI" },
  { key: "evi", label: "EVI" },
  { key: "savi", label: "SAVI" },
  { key: "ndmi", label: "NDMI" },
  { key: "tvdi", label: "TVDI" },
  { key: "cwsi", label: "CWSI" },
  { key: "eta", label: "ETa" },
  { key: "lst", label: "LST" },
  { key: "precip", label: "Precip" },
  { key: "temp", label: "Temp" },
];

const PROV_STATE_COLORS: Record<string, string> = {
  observed: "#0f766e",
  modelled: "#0284c7",
  model: "#7c3aed",
  proxy: "#d97706",
  absent: "#94a3b8",
  legacy: "#be123c",
};

export function ProvenanceSummary({ provenance }: { provenance: Record<string, string> }): React.ReactElement {
  const t = useT();
  const byState = new Map<string, string[]>();
  PROV_CHANNEL_ORDER.forEach(({ key, label }) => {
    const st = provenance[key];
    if (!st) return;
    const list = byState.get(st) ?? [];
    list.push(label);
    byState.set(st, list);
  });
  if (!byState.size) return <></>;
  return (
    <div className="mt-2 space-y-1">
      {[...byState.entries()].map(([state, channels]) => {
        const color = PROV_STATE_COLORS[state] ?? "#94a3b8";
        return (
          <div
            key={state}
            className="flex items-center gap-1.5 text-[10px] leading-tight"
            title={channels.map(ch => `${ch}: ${state}`).join(" · ")}
          >
            <span className="w-1.5 h-1.5 shrink-0 rounded-full" style={{ background: color }} aria-hidden="true" />
            <span className="shrink-0 font-medium" style={{ color }}>
              {t(`prov.${state}`)}
            </span>
            <span className="font-mono text-slate-500 truncate">{channels.join(" · ")}</span>
          </div>
        );
      })}
    </div>
  );
}

export function LegacyPayloadNotice(): React.ReactElement {
  const t = useT();
  return (
    <div className="mt-2 p-2 border border-amber-400 bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-200 text-[11px] rounded">
      <bdi>{t("legacy.notice.title") || "Legacy payload"}</bdi>: {t("legacy.notice.body") || "This payload was written by an older data contract. Some channels are labelled legacy/absent and may not match the current UI."}
    </div>
  );
}

/**
 * Causal stress-flag chip (contract v5). `flag === undefined` (v4 payload) and
 * `flag === null` (v5 without a main checkpoint) both render "unavailable" —
 * the flag is never fabricated as "normal" when no model backs it. The positive
 * state is "suspected stress (anomaly)" until L4 validation (honest naming).
 */
export type StressFlagChipValue = 'normal' | 'suspected_stress' | 'no_data' | null | undefined;

export function StressFlagChip({ flag, title }: { flag: StressFlagChipValue; title?: string }): React.ReactElement {
  const t = useT();
  const state: 'normal' | 'suspected_stress' | 'no_data' | 'unavailable' =
    flag === 'normal' || flag === 'suspected_stress' || flag === 'no_data' ? flag : 'unavailable';
  const labels: Record<typeof state, string> = {
    normal: t("stressFlag.normal"),
    suspected_stress: t("stressFlag.suspected"),
    no_data: t("stressFlag.noData"),
    unavailable: t("stressFlag.unavailable"),
  };
  const colors: Record<typeof state, string> = {
    normal: "#15803d",
    suspected_stress: "#be123c",
    no_data: "#94a3b8",
    unavailable: "#64748b",
  };
  const color = colors[state];
  return (
    <span
      title={title ?? `${t("stressFlag.label")}: ${labels[state]}`}
      className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 border"
      style={{ color: color, borderColor: color + "55", background: color + "12" }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} aria-hidden="true" />
      {labels[state]}
    </span>
  );
}

/** Subtle split-membership suffix for an observation (train = in-sample). */
export const SPLIT_TAG_COLORS: Record<string, string> = {
  train: "#b45309",
  dev: "#0284c7",
  test: "#7c3aed",
  monitoring: "#64748b",
};

export function SplitTagChip({ split }: { split: string | null | undefined }): React.ReactElement | null {
  const t = useT();
  if (split !== 'train' && split !== 'dev' && split !== 'test' && split !== 'monitoring') return null;
  const label = {
    train: t("split.train"),
    dev: t("split.dev"),
    test: t("split.test"),
    monitoring: t("split.monitoring"),
  }[split];
  const color = SPLIT_TAG_COLORS[split];
  return (
    <span
      title={`split: ${split}`}
      className="inline-flex items-center text-[9px] font-medium px-1 py-0.5 border"
      style={{ color: color, borderColor: color + "55", background: color + "12" }}
    >
      {label}
    </span>
  );
}