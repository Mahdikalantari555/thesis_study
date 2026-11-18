// SeasonChart — ported from the Halqeh desk (season-chart.tsx) for the
// platform anomaly desk (add-halqeh-anomaly-desk task 2.2): recharts composed
// chart, envelope band vs. blunt-cut reference line, red dots on called bins.
// Data comes from the desk payload; the naive cut from the payload totals.
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DESK_NAIVE_CUT, type DeskBin, type DeskCase, type DeskMode } from "../data/desk";
import { useT } from "../i18n";

interface Row {
  i: number;
  d: string;
  v: number;
  lo: number;
  hi: number;
  med: number;
  f: boolean;
  s: string;
}

function Tip({
  active,
  payload,
  floorLabel,
}: {
  active?: boolean;
  payload?: { payload: Row }[];
  floorLabel: string;
}) {
  if (!active || !payload?.length) return null;
  const b = payload[0].payload;
  return (
    <div className="rounded-xl border border-[var(--desk-line)] bg-[var(--desk-card)] px-3 py-2 text-xs text-[var(--desk-ink)] shadow-none">
      <div className="font-medium">{b.d}</div>
      <div className="mt-1">NDVI {b.v.toFixed(3)}</div>
      <div className="text-[var(--desk-muted)]">
        {b.s} · {floorLabel} {b.lo.toFixed(3)}
      </div>
    </div>
  );
}

export function SeasonChart({
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
  const rows: Row[] = item.bins.map((b: DeskBin) => ({
    i: b.i,
    d: b.d.slice(2),
    v: b.v,
    lo: Math.max(0, b.lo),
    hi: b.hi,
    med: b.med,
    f: b.f,
    s: b.stage,
  }));
  const activeDate = active != null ? rows[active]?.d : undefined;

  return (
    <div className="h-56 w-full lg:h-72">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={rows}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
          onClick={(state) => {
            const idx = state?.activeTooltipIndex;
            if (typeof idx === "number") onPick(idx);
          }}
        >
          <CartesianGrid stroke="var(--desk-line)" vertical={false} />
          <XAxis
            dataKey="d"
            tick={{ fill: "var(--desk-muted)", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            minTickGap={28}
          />
          <YAxis
            domain={[0, 0.9]}
            tick={{ fill: "var(--desk-muted)", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          <Tooltip content={<Tip floorLabel={t("desk.floor")} />} />
          {mode === "envelope" ? (
            <>
              <Area
                type="stepAfter"
                dataKey="hi"
                stroke="none"
                fill="var(--desk-cane)"
                fillOpacity={0.22}
                isAnimationActive={false}
              />
              <Area
                type="stepAfter"
                dataKey="lo"
                stroke="none"
                fill="var(--desk-card)"
                fillOpacity={1}
                isAnimationActive={false}
              />
            </>
          ) : (
            <ReferenceLine
              y={DESK_NAIVE_CUT}
              stroke="var(--desk-slip)"
              strokeDasharray="4 4"
            />
          )}
          <Line
            type="stepAfter"
            dataKey="med"
            stroke="var(--desk-cane)"
            strokeDasharray="3 3"
            dot={false}
            strokeWidth={1.25}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="v"
            stroke="var(--desk-ink)"
            strokeWidth={2}
            isAnimationActive={false}
            dot={(props) => {
              const { cx, cy, payload, index, key } = props as {
                key?: string | number;
                cx?: number;
                cy?: number;
                index?: number;
                payload?: Row;
              };
              if (cx == null || cy == null || !payload || index == null) {
                return <circle key={key ?? index} cx={0} cy={0} r={0} />;
              }
              const hit = mode === "envelope" ? payload.f : payload.v < DESK_NAIVE_CUT;
              const on = active === index;
              return (
                <circle
                  key={key ?? index}
                  cx={cx}
                  cy={cy}
                  r={on ? 5 : hit ? 3.5 : 2}
                  fill={hit ? "var(--desk-slip)" : "var(--desk-card)"}
                  stroke="var(--desk-ink)"
                  strokeWidth={1}
                />
              );
            }}
          />
          {activeDate ? (
            <ReferenceLine x={activeDate} stroke="var(--desk-ink)" strokeOpacity={0.35} />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
