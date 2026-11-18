// SeasonRing — ported from the Halqeh desk (ring.tsx) for the platform anomaly
// desk (add-halqeh-anomaly-desk task 2.2): props-driven, no zustand, envelopes
// + naive cut read from the desk payload (platform/src/data/desk.ts), platform
// fonts only. Angle = progress through the cycle; radius = NDVI.
import { DESK, DESK_NAIVE_CUT, DESK_STAGES, type DeskCase, type DeskMode, type DeskStageId } from "../data/desk";
import { useT } from "../i18n";

const NDVI_MAX = 0.85;

function polar(cx: number, cy: number, p: number, r: number) {
  const a = -Math.PI / 2 + p * Math.PI * 2;
  return [cx + Math.cos(a) * r, cy + Math.sin(a) * r] as const;
}

function rOf(ndvi: number, r0: number, r1: number) {
  const t = Math.max(0, Math.min(1, ndvi / NDVI_MAX));
  return r0 + t * (r1 - r0);
}

function sector(cx: number, cy: number, p0: number, p1: number, rIn: number, rOut: number) {
  const n = 28;
  let d = "";
  for (let i = 0; i <= n; i++) {
    const p = p0 + ((p1 - p0) * i) / n;
    const [x, y] = polar(cx, cy, p, rOut);
    d += `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
  }
  for (let i = n; i >= 0; i--) {
    const p = p0 + ((p1 - p0) * i) / n;
    const [x, y] = polar(cx, cy, p, rIn);
    d += `L${x.toFixed(2)},${y.toFixed(2)}`;
  }
  return `${d}Z`;
}

function called(v: number, flagged: boolean, mode: DeskMode) {
  return mode === "envelope" ? flagged : v < DESK_NAIVE_CUT;
}

export function SeasonRing({
  item,
  mode,
  active,
  onPick,
}: {
  item: DeskCase;
  mode: DeskMode;
  active: number | null;
  onPick: (index: number) => void;
}) {
  const t = useT();
  const cx = 160;
  const cy = 160;
  const r0 = 46;
  const r1 = 132;
  const bins = item.bins;
  const trace = bins
    .map((b, i) => {
      const [x, y] = polar(cx, cy, b.p, rOf(b.v, r0, r1));
      return `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join("");

  const median = bins
    .map((b, i) => {
      const [x, y] = polar(cx, cy, b.p, rOf(b.med, r0, r1));
      return `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join("");

  return (
    <svg viewBox="-16 -12 352 344" className="mx-auto h-auto w-full max-w-xs" role="img">
      <title>{t("desk.ring.a11y", { code: item.code ?? item.fieldId, cycle: String(item.cycle) })}</title>
      <circle cx={cx} cy={cy} r={r1 + 8} fill="none" stroke="var(--desk-line)" strokeWidth="1" />
      <circle cx={cx} cy={cy} r={r0} fill="var(--desk-card)" stroke="var(--desk-line)" />
      {mode === "naive" ? (
        <circle
          cx={cx}
          cy={cy}
          r={rOf(DESK_NAIVE_CUT, r0, r1)}
          fill="none"
          stroke="var(--desk-slip)"
          strokeDasharray="3 3"
          strokeWidth="1.25"
        />
      ) : (
        DESK_STAGES.map((stage) => {
          const env = DESK.envelopes[stage.id as DeskStageId];
          const inner = rOf(Math.max(0, env.lo), r0, r1);
          const outer = rOf(Math.min(NDVI_MAX, env.hi), r0, r1);
          return (
            <path
              key={stage.id}
              d={sector(cx, cy, stage.from, stage.to, inner, outer)}
              fill="var(--desk-cane)"
              opacity={stage.id === "S2" ? 0.28 : 0.14}
            />
          );
        })
      )}
      {DESK_STAGES.map((stage) => {
        const [x, y] = polar(cx, cy, (stage.from + stage.to) / 2, r1 + 16);
        return (
          <text
            key={stage.id}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="var(--desk-muted)"
            fontSize="11"
          >
            {stage.id}
          </text>
        );
      })}
      <path d={median} fill="none" stroke="var(--desk-cane)" strokeWidth="1.25" strokeDasharray="2 3" />
      <path d={trace} fill="none" stroke="var(--desk-ink)" strokeWidth="2" />
      {bins.map((b, i) => {
        const hit = called(b.v, b.f, mode);
        const [x, y] = polar(cx, cy, b.p, rOf(b.v, r0, r1));
        const on = active === i;
        return (
          <circle
            key={`${b.d}-${b.i}`}
            cx={x}
            cy={y}
            r={on ? 6 : hit ? 4.2 : 2.2}
            fill={hit ? "var(--desk-slip)" : "var(--desk-card)"}
            stroke="var(--desk-ink)"
            strokeWidth={on ? 1.6 : 1}
            className="cursor-pointer"
            onClick={() => onPick(i)}
          />
        );
      })}
      <text x={cx} y={cy - 6} textAnchor="middle" fill="var(--desk-ink)" fontSize="15">
        {item.code ?? item.fieldId}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="var(--desk-muted)" fontSize="11">
        {mode === "envelope" ? t("desk.chip.slips", { n: item.flags }) : t("desk.ring.naiveCount", { n: item.naive })}
      </text>
    </svg>
  );
}
