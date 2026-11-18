// DeskMap — raster context for the reviewed case (add-halqeh-anomaly-desk,
// design D4). Given a case (polygon + centroid from the farms payload) and the
// selected bin date, it fetches the tile server's /scenes index once, resolves
// the nearest scene within ±bin_days of the bin date (preferring the selected
// layer), overlays its NDVI/RGB tiles, and labels the scene date actually used
// — which may differ from the bin date. With the tile server off, it degrades
// to basemap + polygon with an explicit "scene absent" state (never a blank
// stretch, never a broken-tile widget). scripts/serve_tiles.py is reused
// unchanged; its contract (transparent-PNG 404s, zoom clamp 8–14) already
// covers the degradation paths.
import { useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { DESK, nearestScene, type DeskCase } from "../data/desk";
import { useAnalysis } from "../context/AnalysisContext";
import { useT } from "../i18n";

interface SceneEntry {
  date: string;
  has_rgb: boolean;
  has_ndvi: boolean;
}

type ScenesState =
  | { status: "loading" }
  | { status: "ok"; scenes: SceneEntry[] }
  | { status: "unavailable" };

const TILE_DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_LIGHT = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION = "© OpenStreetMap © CARTO";
const TILE_SERVER_BASE = "http://127.0.0.1:8765";
const KHUZESTAN_CENTER: [number, number] = [31.0217, 48.2794];

export default function DeskMap({
  item,
  polygon,
  centroid,
  binDate,
  height = "320px",
}: {
  item: DeskCase;
  /** Field polygon [lat, lng][] from the farms payload (farms_khuzestan.json). */
  polygon: [number, number][];
  centroid: [number, number] | null;
  /** The reviewed bin's date (ISO) — scenes are resolved against it. */
  binDate: string | null;
  height?: string;
}) {
  const { dark } = useAnalysis();
  const t = useT();
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const polyLayerRef = useRef<L.LayerGroup | null>(null);
  const baseRef = useRef<L.TileLayer | null>(null);
  const rasterRef = useRef<L.TileLayer | null>(null);
  const [scenes, setScenes] = useState<ScenesState>({ status: "loading" });
  const [layer, setLayer] = useState<"ndvi" | "rgb">("ndvi");
  const [opacity, setOpacity] = useState(0.7);

  // Map lifecycle — mount once (BUG-04 pattern: never recreate on theme change).
  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = L.map(ref.current, { zoomControl: true, attributionControl: true }).setView(KHUZESTAN_CENTER, 11);
    mapRef.current = map;
    polyLayerRef.current = L.layerGroup().addTo(map);
    return () => {
      map.remove();
      mapRef.current = null;
      polyLayerRef.current = null;
      baseRef.current = null;
      rasterRef.current = null;
    };
  }, []);

  // Theme → tile layer only.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (baseRef.current) {
      map.removeLayer(baseRef.current);
      baseRef.current = null;
    }
    baseRef.current = L.tileLayer(dark ? TILE_DARK : TILE_LIGHT, { attribution: ATTRIBUTION }).addTo(map);
  }, [dark]);

  // /scenes fetch — once per mount. Failure IS the degradation state (tile
  // server not running): explicit "absent" copy, basemap + polygon stay.
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    fetch(`${TILE_SERVER_BASE}/scenes`, { signal: controller.signal })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`scenes ${r.status}`))))
      .then((json: { scenes?: SceneEntry[] }) => {
        if (cancelled) return;
        const list = Array.isArray(json?.scenes) ? json.scenes.filter(s => typeof s?.date === "string") : [];
        setScenes({ status: "ok", scenes: list });
      })
      .catch(() => {
        if (cancelled) return;
        setScenes({ status: "unavailable" });
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  // Field polygon + centroid — redrawn per case; fit so the field fills the map.
  useEffect(() => {
    const layer = polyLayerRef.current;
    const map = mapRef.current;
    if (!layer || !map) return;
    layer.clearLayers();
    if (polygon.length) {
      L.polygon(polygon, {
        color: "#1c1915",
        weight: 2,
        fillColor: "#2f6b45",
        fillOpacity: 0.25,
      }).addTo(layer);
      if (centroid) {
        L.circleMarker(centroid, { radius: 5, color: "#1c1915", fillColor: "#ffffff", fillOpacity: 1, weight: 2 }).addTo(layer);
      }
      map.fitBounds(L.latLngBounds(polygon.map(([lat, lng]) => L.latLng(lat, lng))), { padding: [24, 24], maxZoom: 14 });
    }
  }, [polygon, centroid, item.id]);

  // Raster resolution: nearest scene within ±bin_days, preferring the selected
  // layer; fall back to the other layer only when the requested one is absent
  // for every candidate scene (never silently relabels the bin date).
  const windowDays = DESK.provenance.binDays;
  const resolution = useMemo<{ scene: SceneEntry; layer: "ndvi" | "rgb" } | null>(() => {
    if (scenes.status !== "ok" || !binDate) return null;
    const preferred = nearestScene(scenes.scenes, binDate, layer, windowDays);
    if (preferred) return { scene: preferred, layer };
    const other = layer === "ndvi" ? "rgb" : "ndvi";
    const fallback = nearestScene(scenes.scenes, binDate, other, windowDays);
    return fallback ? { scene: fallback, layer: other } : null;
  }, [scenes, binDate, layer, windowDays]);

  // Raster overlay — swapped when scene/layer changes, opacity updated in place.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (rasterRef.current) {
      map.removeLayer(rasterRef.current);
      rasterRef.current = null;
    }
    if (!resolution) return;
    rasterRef.current = L.tileLayer(
      `${TILE_SERVER_BASE}/tiles/${resolution.scene.date}/${resolution.layer}/{z}/{x}/{y}.png`,
      {
        minNativeZoom: 8,
        maxNativeZoom: 14,
        maxZoom: 18,
        opacity,
        errorTileUrl: "",
        attribution: "Landsat Collection-2 Level-2",
      },
    ).addTo(map);
    // opacity intentionally excluded: slider drags go through setOpacity below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolution?.scene.date, resolution?.layer]);

  useEffect(() => {
    rasterRef.current?.setOpacity(opacity);
  }, [opacity]);

  const statusText = (() => {
    if (scenes.status === "loading") return t("desk.map.loading");
    if (scenes.status === "unavailable") return t("desk.map.serverAbsent");
    // Bin dates are shown at full ISO precision — never month-truncated —
    // because the label's job is to expose scene-vs-bin day drift.
    if (!binDate) return t("desk.map.sceneAbsent", { bin: "—" });
    if (!resolution) return t("desk.map.sceneAbsent", { bin: binDate });
    return t("desk.map.sceneDate", { scene: resolution.scene.date, bin: binDate });
  })();

  return (
    <figure className="rounded-2xl border border-[var(--desk-line)] bg-[var(--desk-card)] p-3" data-desk-map>
      <figcaption className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--desk-muted)]">
        <span>{t("desk.map.title")}</span>
        <span className="flex items-center gap-2">
          <select
            value={layer}
            onChange={e => setLayer(e.target.value as "ndvi" | "rgb")}
            aria-label={t("map.layer.rasterLayer")}
            className="border border-[var(--desk-line)] bg-[var(--desk-card)] px-1.5 py-1 text-[11px] text-[var(--desk-ink)]"
          >
            <option value="ndvi">{t("map.layer.rasterNdvi")}</option>
            <option value="rgb">{t("map.layer.rasterRgb")}</option>
          </select>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={opacity}
            onChange={e => setOpacity(+e.target.value)}
            aria-label={t("map.layer.rasterOpacity", { value: String(Math.round(opacity * 100) / 100) })}
            className="accent-[#2f6b45]"
          />
        </span>
      </figcaption>
      <div ref={ref} dir="ltr" style={{ height, width: "100%", zIndex: 0 }} className="bg-[#e7e0d4]" />
      <p className="mt-2 text-xs text-[var(--desk-muted)]" dir="auto">
        {statusText}
      </p>
      <p className="mt-1 text-[10px] text-[var(--desk-muted)]" dir="auto">
        {t("desk.map.locatorNote")}
      </p>
    </figure>
  );
}
