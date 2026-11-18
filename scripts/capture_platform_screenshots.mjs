#!/usr/bin/env node
/**
 * Capture platform screenshots of all eight views AND audit the runtime:
 * per-view console errors, page exceptions and failed network requests, plus
 * a Map Explorer tile scenario against scripts/serve_tiles.py.
 *
 * Originally the PR-evidence capture for `make-platform-bilingual-and-audit-page-bugs`
 * (task 9.2/9.3); extended by `wire-platform-to-real-data` (tasks 5.1/5.2) into
 * the runtime verification gate: every view must render with zero console
 * errors / zero page exceptions, and the raster overlay must demonstrably
 * render RGB and NDVI tiles with the tile server alive.
 *
 * Dependency-free apart from Node's built-ins: headless Chrome/Edge over the
 * raw DevTools protocol, the caller supplies the binary —
 *
 *   node scripts/capture_platform_screenshots.mjs \
 *     --executable /path/to/chrome \
 *     [--out reports/screenshots/en] [--locale en] [--width 1680] [--height 1500]
 *     [--no-tile-server]   # server-down run: skip the tile scenario and treat
 *                          # 127.0.0.1:8765 console noise as expected degradation
 *
 * The build is a single self-contained HTML file (`platform/dist/index.html`),
 * but its inlined bundle is an ES module, and `file://` module loading is
 * blocked by browsers ("cross-origin requests are only supported for http(s)").
 * The script therefore starts a throwaway static server on 127.0.0.1 for the
 * duration of the capture — still fully offline (fonts are self-hosted, no CDN).
 *
 * Exit codes: 0 gate passed, 1 gate failed (see audit.json), 2 no browser.
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DIST = path.join(ROOT, "platform", "dist", "index.html");
const TILE_BASE = "http://127.0.0.1:8765";

// ── CLI ──────────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { out: path.join(ROOT, "reports", "screenshots", "fa"), locale: "fa", width: 1680, height: 1500, port: 0, noTileServer: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === "--executable") out.executable = next();
    else if (a === "--out") out.out = path.resolve(next());
    else if (a === "--locale") out.locale = next();
    else if (a === "--width") out.width = Number(next());
    else if (a === "--height") out.height = Number(next());
    else if (a === "--port") out.port = Number(next());
    else if (a === "--no-tile-server") out.noTileServer = true;
    else if (a === "--help" || a === "-h") {
      console.log(fs.readFileSync(fileURLToPath(import.meta.url), "utf8").split("*/")[0]);
      process.exit(0);
    }
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));

const PAGES = [
  { id: "overview", file: "01_overview.png" },
  { id: "map", file: "02_geospatial-explorer.png" },
  { id: "temporal", file: "03_temporal-analysis.png" },
  { id: "spectral", file: "04_spectral-temporal.png" },
  { id: "validation", file: "05_validation-lab.png" },
  { id: "comparison", file: "06_model-comparison.png" },
  { id: "spatial", file: "07_spatial-analysis.png" },
  { id: "reports", file: "08_reports-experiments.png" },
  { id: "desk", file: "09_anomaly-desk.png" },
];

// ── Browser discovery ────────────────────────────────────────────────────────
function findExecutable() {
  if (args.executable) return args.executable;
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  ].filter(Boolean);
  for (const c of candidates) {
    try {
      if (c && fs.existsSync(c)) return c;
    } catch {
      /* ignore */
    }
  }
  return null;
}

// ── Minimal DevTools-protocol client (no puppeteer, no websocket package) ─────
async function connect(webSocketDebuggerUrl) {
  const { WebSocket } = globalThis; // Node ≥ 22 ships a built-in WebSocket client
  const ws = new WebSocket(webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = () => reject(new Error("failed to open DevTools websocket"));
  });
  let id = 0;
  const pending = new Map();
  const events = new Map();
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(`${msg.error.message} (${msg.error.code})`)) : resolve(msg.result);
    } else if (msg.method) {
      const list = events.get(msg.method) ?? [];
      list.forEach(fn => fn(msg.params));
    }
  };
  const send = (method, params = {}, timeoutMs = 60000) =>
    new Promise((resolve, reject) => {
      const msgId = ++id;
      const timer = setTimeout(() => {
        pending.delete(msgId);
        reject(new Error(`CDP timeout after ${timeoutMs} ms: ${method}`));
      }, timeoutMs);
      pending.set(msgId, {
        resolve: v => {
          clearTimeout(timer);
          resolve(v);
        },
        reject: e => {
          clearTimeout(timer);
          reject(e);
        },
      });
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  const once = method =>
    new Promise(resolve => {
      const list = events.get(method) ?? [];
      list.push(resolve);
      events.set(method, list);
    });
  return { send, once, close: () => ws.close() };
}

function rpcHttp(port, method, pathname) {
  return new Promise((resolve, reject) => {
    const req = http.request({ port, method, path: pathname }, res => {
      let body = "";
      res.on("data", d => (body += d));
      res.on("end", () => {
        try {
          resolve(JSON.parse(body));
        } catch (err) {
          reject(new Error(`bad response for ${pathname}: ${body.slice(0, 200)}`));
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

async function waitForDevTools(port, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const list = await rpcHttp(port, "GET", "/json/list");
      if (Array.isArray(list) && list.length) return list;
    } catch {
      /* not up yet */
    }
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error(`Chrome DevTools endpoint on port ${port} did not respond within ${timeoutMs} ms`);
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

/** Throwaway static file server for platform/dist (127.0.0.1 only). */
function serveDist() {
  const dir = path.dirname(DIST);
  const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2", ".json": "application/json", ".png": "image/png" };
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent((req.url || "/").split("?")[0]);
    const file = path.join(dir, rel === "/" ? "index.html" : rel);
    if (!file.startsWith(dir)) {
      res.writeHead(403).end();
      return;
    }
    fs.readFile(file, (err, buf) => {
      if (err) {
        res.writeHead(404).end("not found");
        return;
      }
      res.writeHead(200, { "content-type": mime[path.extname(file)] ?? "application/octet-stream" });
      res.end(buf);
    });
  });
  return new Promise(resolve => server.listen(0, "127.0.0.1", () => resolve({ server, port: server.address().port })));
}

// ── Runtime audit (wire-platform-to-real-data task 5.1) ─────────────────────
const audit = {
  startedAt: new Date().toISOString(),
  locale: args.locale,
  tileServerExpectedUp: !args.noTileServer,
  views: {},
  tileScenario: null,
  deskScenario: null,
};
let currentView = null;

function isTileServerNoise(text) {
  return typeof text === "string" && text.includes("127.0.0.1:8765");
}

function recordConsole(type, text) {
  if (!currentView) return;
  const v = audit.views[currentView] ?? (audit.views[currentView] = { console: [], pageErrors: [], failedRequests: [], screenshot: null });
  if (type === "error" || type === "assert") v.console.push(text);
}

function recordPageError(text) {
  if (!currentView) return;
  const v = audit.views[currentView] ?? (audit.views[currentView] = { console: [], pageErrors: [], failedRequests: [], screenshot: null });
  v.pageErrors.push(text);
}

function recordFailedRequest(url, errorText) {
  if (!currentView) return;
  const v = audit.views[currentView] ?? (audit.views[currentView] = { console: [], pageErrors: [], failedRequests: [], screenshot: null });
  v.failedRequests.push({ url, errorText });
}

// Tile responses seen on the Network domain (status codes for the scenario).
const tileResponses = [];
const tileFailures = [];

async function attachAuditListeners(session) {
  const { send, once } = session;
  // connect() exposes no on(); piggyback via Runtime.consoleAPICalled etc. by
  // registering raw handlers through a tiny event tap: connect() dispatches
  // method events to `once()`-style lists, so use a long-lived once() that
  // re-arms itself.
  const tap = async (method, handler) => {
    (async () => {
      for (;;) {
        try {
          const params = await once(method);
          handler(params);
        } catch {
          return; // websocket closed
        }
      }
    })();
  };

  await send("Runtime.enable");
  await send("Log.enable");
  await send("Network.enable");
  await tap("Runtime.consoleAPICalled", p => {
    const text = (p.args || []).map(a => a.value ?? a.description ?? "").join(" ").slice(0, 500);
    recordConsole(p.type, text);
  });
  await tap("Runtime.exceptionThrown", p => {
    const d = p.exceptionDetails;
    const text = d?.exception?.description || d?.text || "unknown exception";
    recordPageError(text.slice(0, 500));
  });
  await tap("Log.entryAdded", p => {
    const e = p.entry;
    if (e?.level === "error") recordConsole("error", `[${e.source}] ${e.text}`.slice(0, 500));
  });
  await tap("Network.responseReceived", p => {
    const url = p.response?.url ?? "";
    if (/:8765\/tiles\//.test(url)) tileResponses.push({ url, status: p.response.status });
  });
  await tap("Network.loadingFailed", p => {
    // loadingFailed carries only an requestId; CanceledRequestText is not mapped
    // back to URLs without bookkeeping, so match via the requestWillBeSent map.
    const url = requestUrls.get(p.requestId) ?? "(unknown)";
    if (/:8765\/tiles\//.test(url)) tileFailures.push({ url, errorText: p.errorText });
    recordFailedRequest(url, p.errorText);
  });
  await tap("Network.requestWillBeSent", p => {
    requestUrls.set(p.requestId, p.request.url);
  });
}

const requestUrls = new Map();

async function evaluateJson(send, expression) {
  const r = await send("Runtime.evaluate", { expression, returnByValue: true });
  const v = r?.result?.value;
  if (typeof v === "string") {
    try {
      return JSON.parse(v);
    } catch {
      return v; // raw string (returnByValue passes it through unwrapped)
    }
  }
  return v ?? null;
}

async function activateView(send, locale, id) {
  const labels = navLabels(locale);
  const clicked = await send("Runtime.evaluate", {
    expression: `(() => {
      const buttons = [...document.querySelectorAll('aside nav button')];
      const target = buttons.find(b => (b.textContent || '').includes(${JSON.stringify(labels[id])}));
      if (!target) return false;
      target.click();
      return true;
    })()`,
    returnByValue: true,
  });
  if (!clicked.result.value) throw new Error(`could not activate nav item "${id}"`);
  for (let i = 0; i < 40; i++) {
    const active = await send("Runtime.evaluate", {
      expression: `(() => { const b = [...document.querySelectorAll('aside nav button')].find(x => x.getAttribute('aria-current') === 'page'); return b ? b.textContent : ''; })()`,
      returnByValue: true,
    });
    if ((active.result.value || "").includes(labels[id])) break;
    await sleep(150);
  }
}

/** Set a React-controlled <select> to the option matching `predicate` source. */
async function setSelect(send, findExpr, value) {
  const ok = await send("Runtime.evaluate", {
    expression: `(() => {
      const sel = (${findExpr});
      if (!sel) return false;
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
      setter.call(sel, ${JSON.stringify(value)});
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    })()`,
    returnByValue: true,
  });
  return !!ok.result.value;
}

const LAYER_SELECT_EXPR = `(() => {
  const selects = [...document.querySelectorAll('select')];
  return selects.find(s => [...s.options].some(o => o.value === 'rgb') && [...s.options].some(o => o.value === 'ndvi')) ?? null;
})()`;

/**
 * The observation-date slider: the only range input whose max is the shared
 * date-axis length (opacity sliders are 0–1). One slider now drives both the
 * field series and the raster overlay (wire-platform-to-real-data task 6.3).
 */
const DATE_SLIDER_EXPR = `(() => {
  const sliders = [...document.querySelectorAll('input[type=range]')];
  return sliders.find(el => Number(el.max) > 5) ?? null;
})()`;

async function setRangeSlider(send, findExpr, value) {
  const ok = await send("Runtime.evaluate", {
    expression: `(() => {
      const el = (${findExpr});
      if (!el) return false;
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(el, String(${JSON.stringify(value)}));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    })()`,
    returnByValue: true,
  });
  return !!ok.result.value;
}

/** Poll until at least `min` loaded raster tiles (src on :8765) are present. */
async function waitForRasterTiles(send, urlPart, min = 1, timeoutMs = 25000) {
  const started = Date.now();
  let last = { total: 0, ok: 0 };
  while (Date.now() - started < timeoutMs) {
    last = (await evaluateJson(
      send,
      `(() => {
        const imgs = [...document.querySelectorAll('img.leaflet-tile-loaded')].filter(i => i.src.includes('${urlPart}'));
        const ok = imgs.filter(i => i.complete && i.naturalWidth > 0);
        return JSON.stringify({ total: imgs.length, ok: ok.length });
      })()`
    )) ?? last;
    if (last.ok >= min) return last;
    await sleep(300);
  }
  return last;
}

/** Effective opacity of a raster tile = product of computed opacity up the tree. */
async function rasterOpacity(send) {
  return evaluateJson(
    send,
    `(() => {
      const img = [...document.querySelectorAll('img.leaflet-tile')].find(i => i.src.includes(':8765/tiles/'));
      if (!img) return null;
      let el = img, op = 1;
      while (el && el !== document.documentElement) {
        const o = parseFloat(getComputedStyle(el).opacity);
        if (Number.isFinite(o)) op *= o;
        el = el.parentElement;
      }
      return Math.round(op * 1000) / 1000;
    })()`
  );
}

/** Drag-pan the Leaflet map via real input events (fires live tile requests). */
async function dragPan(send, dx, dy) {
  const rect = await evaluateJson(
    send,
    `JSON.stringify((() => {
      const r = document.querySelector('.leaflet-container').getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    })())`
  );
  if (!rect) throw new Error("no .leaflet-container found");
  const steps = 8;
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: rect.x, y: rect.y, button: "left", clickCount: 1 });
  for (let i = 1; i <= steps; i++) {
    await send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x: rect.x + (dx * i) / steps,
      y: rect.y + (dy * i) / steps,
      button: "left",
      buttons: 1,
    });
    await sleep(30);
  }
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: rect.x + dx, y: rect.y + dy, button: "left", clickCount: 1 });
}

/** Map Explorer tile scenario: RGB + NDVI render, pan, opacity persistence. */
async function runTileScenario(send, outDir) {
  const scenario = { rgbTiles: 0, ndviTiles: 0, tileResponses: null, tileFailures: null, opacityAfterRgb: null, opacityAfterNdvi: null, pans: 0, ok: false, drivenByDateSlider: false };
  currentView = "map";
  await activateView(send, args.locale, "map");
  await sleep(2000);

  const hasLayerSel = await evaluateJson(send, `!!(${LAYER_SELECT_EXPR})`);
  if (!hasLayerSel) throw new Error("raster layer select not found (no scene for the default observation date?)");

  // Drive the observation-date slider (task 6.3): move to idx 6 so the raster
  // demonstrably follows the single date control.
  tileResponses.length = 0;
  tileFailures.length = 0;
  scenario.drivenByDateSlider = await setRangeSlider(send, DATE_SLIDER_EXPR, 6);
  await sleep(800);

  // RGB
  const rgb = await waitForRasterTiles(send, "/tiles/");
  scenario.rgbTiles = rgb.ok;
  scenario.opacityAfterRgb = await rasterOpacity(send);
  await dragPan(send, -260, 120);
  await dragPan(send, 200, -140);
  scenario.pans = 2;
  await sleep(1200);
  const rgbAfterPan = await waitForRasterTiles(send, "/tiles/");
  fs.writeFileSync(path.join(outDir, "tile_rgb.png"), await screenshot(send));
  scenario.opacityAfterPan = await rasterOpacity(send);

  // NDVI — same observation date, switch layer
  await setSelect(send, LAYER_SELECT_EXPR, "ndvi");
  await sleep(300);
  const ndvi = await waitForRasterTiles(send, "/ndvi/");
  scenario.ndviTiles = ndvi.ok;
  scenario.opacityAfterNdvi = await rasterOpacity(send);
  await sleep(1000);
  fs.writeFileSync(path.join(outDir, "tile_ndvi.png"), await screenshot(send));

  // Task 6.1 evidence: "Hide" removes only the field-polygon layer — the
  // raster overlay AND basemap tiles stay on the map.
  const hideLabel = args.locale === "fa" ? "پنهان" : "Hide";
  const clickedHide = await evaluateJson(
    send,
    `(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.textContent || '').trim() === ${JSON.stringify(hideLabel)});
      if (!b) return false;
      b.click();
      return true;
    })()`
  );
  await sleep(900);
  scenario.hideFields = await evaluateJson(
    send,
    `JSON.stringify({
      clicked: ${clickedHide ? "true" : "false"},
      polygonPaths: document.querySelectorAll('.leaflet-overlay-pane path').length,
      rasterTiles: [...document.querySelectorAll('img.leaflet-tile-loaded')].filter(i => i.src.includes(':8765')).length,
      basemapTiles: [...document.querySelectorAll('img.leaflet-tile-loaded')].filter(i => !i.src.includes(':8765')).length,
    })`
  );
  fs.writeFileSync(path.join(outDir, "tile_nofields.png"), await screenshot(send));
  // restore the polygons for the remaining audit steps
  const showLabel = args.locale === "fa" ? "نمایش" : "Show";
  await evaluateJson(
    send,
    `(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.textContent || '').trim() === ${JSON.stringify(showLabel)});
      if (!b) return false;
      b.click();
      return true;
    })()`
  );

  // Everything observed on the Network domain during the whole scenario
  // (RGB, pans, NDVI) must be a 200 PNG with zero transport failures.
  scenario.tileResponses = tileResponses.slice();
  scenario.tileFailures = tileFailures.slice();
  scenario.tileResponsesOk = tileResponses.length > 0 && tileResponses.every(r => r.status === 200);
  const hideOk = !!scenario.hideFields && scenario.hideFields.clicked && scenario.hideFields.polygonPaths === 0 && scenario.hideFields.rasterTiles > 0 && scenario.hideFields.basemapTiles > 0;
  scenario.hideFieldsOk = hideOk;
  scenario.ok =
    scenario.drivenByDateSlider && rgb.ok > 0 && ndvi.ok > 0 && rgbAfterPan.ok > 0 && scenario.tileResponsesOk && tileFailures.length === 0 && hideOk;
  return scenario;
}

/**
 * Anomaly Desk scenario (add-halqeh-anomaly-desk task 5.1): select a slip case,
 * verify the review surface renders from the desk payload, capture envelope +
 * naive modes, and (server-up only) the desk raster overlay. With
 * --no-tile-server the scenario instead captures the explicit "scene absent"
 * degradation state (task 4.2).
 */
async function runDeskScenario(send, outDir) {
  const scenario = {
    slipFilterClicked: false,
    slipChipClicked: false,
    chips: 0,
    naiveClicked: false,
    sceneLabelOk: false,
    deskRasterTiles: 0,
    absentStateOk: false,
    ok: false,
  };
  currentView = "desk";
  await activateView(send, args.locale, "desk");
  await sleep(1500);

  const deskRoot = await evaluateJson(send, `!!document.querySelector('.desk-root')`);
  if (!deskRoot) throw new Error("desk view did not mount (.desk-root missing)");
  const slipLabel = args.locale === "fa" ? "لغزش" : "Slips";
  scenario.slipFilterClicked = await evaluateJson(
    send,
    `(() => {
      const b = [...document.querySelectorAll('main button')].find(x => (x.textContent || '').trim().startsWith(${JSON.stringify(slipLabel)}));
      if (!b) return false;
      b.click();
      return true;
    })()`
  );
  await sleep(400);
  scenario.chips = (await evaluateJson(send, `document.querySelectorAll('main aside button').length`)) ?? 0;
  scenario.slipChipClicked = await evaluateJson(
    send,
    `(() => {
      const chip = document.querySelector('main aside button');
      if (!chip) return false;
      chip.click();
      return true;
    })()`
  );
  await sleep(1200);

  if (args.noTileServer) {
    // Degradation evidence (task 4.2): explicit absent copy, no broken tiles.
    const absentText = args.locale === "fa" ? "کارساز کاشی روشن نیست" : "Tile server not running";
    for (let i = 0; i < 20; i++) {
      scenario.absentStateOk = (await evaluateJson(
        send,
        `document.body.innerText.includes(${JSON.stringify(absentText)})`
      )) ?? false;
      if (scenario.absentStateOk) break;
      await sleep(300);
    }
    fs.writeFileSync(path.join(outDir, "desk_absent.png"), await screenshot(send));
    scenario.ok = scenario.slipFilterClicked && scenario.slipChipClicked && scenario.absentStateOk;
    return scenario;
  }

  // Server-up: the opened slip case should resolve a nearby scene and render
  // raster tiles inside the desk map.
  await waitForRasterTiles(send, "/tiles/");
  scenario.deskRasterTiles = (await evaluateJson(
    send,
    `[...document.querySelectorAll('img.leaflet-tile-loaded')].filter(i => i.src.includes(':8765/tiles/')).length`
  )) ?? 0;
  const sceneWord = args.locale === "fa" ? "دورنگار" : "Scene";
  scenario.sceneLabelOk = (await evaluateJson(
    send,
    `document.body.innerText.includes(${JSON.stringify(sceneWord)})`
  )) ?? false;
  fs.writeFileSync(path.join(outDir, "desk_tile_rgb.png"), await screenshot(send));

  // Naive (blunt NDVI cut) mode capture.
  const naiveLabel = args.locale === "fa" ? "برش خام NDVI" : "Blunt NDVI cut";
  scenario.naiveClicked = await evaluateJson(
    send,
    `(() => {
      const b = [...document.querySelectorAll('main button')].find(x => (x.textContent || '').trim() === ${JSON.stringify(naiveLabel)});
      if (!b) return false;
      b.click();
      return true;
    })()`
  );
  await sleep(800);
  fs.writeFileSync(path.join(outDir, "desk_naive.png"), await screenshot(send));

  scenario.ok =
    scenario.slipFilterClicked && scenario.slipChipClicked && scenario.chips > 0 &&
    scenario.deskRasterTiles > 0 && scenario.sceneLabelOk && scenario.naiveClicked;
  return scenario;
}

async function screenshot(send) {
  const { data } = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  return Buffer.from(data, "base64");
}

async function main() {
  // Hard ceiling: a wedged CDP command now rejects (see send timeout), but the
  // watchdog guarantees the run can never hang silently forever.
  const watchdog = setTimeout(
    () => {
      console.error("[capture] watchdog: run exceeded 12 min — aborting");
      process.exit(1);
    },
    12 * 60 * 1000,
  );
  if (!fs.existsSync(DIST)) {
    console.error(`[capture] missing build: ${DIST}\n          run:  cd platform && npm run build`);
    process.exit(1);
  }
  const executable = findExecutable();
  if (!executable) {
    console.error(
      "[capture] no Chrome/Chromium binary found.\n" +
        "          pass --executable /path/to/chrome (or set CHROME_PATH).\n" +
        "          Manual fallback: open platform/dist/index.html, switch to FA and screenshot each page."
    );
    process.exit(2);
  }

  fs.mkdirSync(args.out, { recursive: true });
  const { server, port: httpPort } = await serveDist();
  console.log(`[capture] serving ${path.relative(ROOT, path.dirname(DIST))} on 127.0.0.1:${httpPort}`);
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "agri-shots-"));
  const port = args.port || 9200 + Math.floor(Math.random() * 400);

  const child = spawn(
    executable,
    [
      "--headless=new",
      "--no-sandbox",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-dev-shm-usage",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${userDataDir}`,
      `--window-size=${args.width},${args.height}`,
      "about:blank",
    ],
    { stdio: ["ignore", "pipe", "pipe"] }
  );
  const chromeLog = [];
  child.stderr.on("data", d => chromeLog.push(String(d)));
  child.stdout.on("data", d => chromeLog.push(String(d)));

  let session;
  try {
    await waitForDevTools(port);
    const targets = await rpcHttp(port, "GET", "/json/new?about:blank", undefined);
    void targets;
  } catch {
    /* /json/new is blocked on some builds; reuse the initial page target below */
  }

  try {
    const list = await waitForDevTools(port);
    const pageTarget = list.find(t => t.type === "page") ?? list[0];
    session = await connect(pageTarget.webSocketDebuggerUrl);
    const { send, once } = session;

    await attachAuditListeners(session);

    await send("Page.enable");
    await send("Emulation.setDeviceMetricsOverride", {
      width: args.width,
      height: args.height,
      deviceScaleFactor: 2,
      mobile: false,
    });

    // Persist the locale *before* the app's first script runs, exactly like a
    // returning visitor — this exercises the localStorage-restore path of the
    // `Persistent language preference` requirement rather than a UI click.
    await send("Page.addScriptToEvaluateOnNewDocument", {
      source: `try { localStorage.setItem("agrianomaly.locale", ${JSON.stringify(args.locale)}); } catch (e) {}`,
    });

    const url = `http://127.0.0.1:${httpPort}/index.html`;
    await send("Page.navigate", { url });

    // Poll instead of trusting load events: the inlined bundle is ~9 MB and
    // React mounts asynchronously after `load`.
    const probe = () =>
      send("Runtime.evaluate", {
        expression: `JSON.stringify({
          ready: document.readyState,
          dir: document.documentElement.dir,
          lang: document.documentElement.lang,
          nav: document.querySelectorAll('aside nav button').length,
          localized: document.body.innerText.includes(${JSON.stringify(navLabels(args.locale).overview)}),
          font: getComputedStyle(document.body).fontFamily,
        })`,
        returnByValue: true,
      }).then(r => {
        // The first probe can race the navigation and come back undefined.
        try {
          return JSON.parse(r?.result?.value ?? "{}");
        } catch {
          return {};
        }
      });

    let state = await probe();
    for (let i = 0; i < 480 && !(state.nav >= PAGES.length && state.dir === (args.locale === "fa" ? "rtl" : "ltr")); i++) {
      await sleep(250);
      state = await probe();
    }
    if (state.nav < PAGES.length) throw new Error(`app did not mount: ${JSON.stringify(state)}`);
    if (state.dir !== (args.locale === "fa" ? "rtl" : "ltr") || state.lang !== args.locale) {
      throw new Error(`locale not applied: ${JSON.stringify(state)}`);
    }
    if (!state.localized) throw new Error(`copy not translated to ${args.locale}: ${JSON.stringify(state)}`);
    console.log(`[capture] mounted · dir=${state.dir} · lang=${state.lang} · nav=${state.nav} buttons · font=${state.font.split(",")[0]}`);

    // Wait for the webfont to be ready so Persian text is not captured in a
    // fallback face (font-display: swap would otherwise show Inter/system).
    await send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => true)", awaitPromise: true });
    await sleep(600);
    // Mount-phase console noise lands on the first view the loop activates.
    currentView = "overview";

    for (const page of PAGES) {
      currentView = page.id;
      await activateView(send, args.locale, page.id);
      // Wait until the clicked nav entry is marked active, then let charts
      // animate in and Leaflet lay out its tiles.
      await sleep(1500); // chart animations + Leaflet tile layout

      // Size the viewport to the *full* page, wait for Recharts'
      // ResponsiveContainer to re-measure, and only then capture. Using
      // `captureBeyondViewport` instead produces mid-reflow frames where
      // charts are briefly 14×14 px (Recharts' minimum surface).
      const height = await send("Runtime.evaluate", { expression: "document.documentElement.scrollHeight", returnByValue: true });
      const fullHeight = Math.max(args.height, Math.ceil(height.result.value ?? args.height));
      await send("Emulation.setDeviceMetricsOverride", { width: args.width, height: fullHeight, deviceScaleFactor: 2, mobile: false });
      await sleep(1200);
      const target = path.join(args.out, page.file);
      fs.writeFileSync(target, await screenshot(send));
      (audit.views[page.id] ??= { console: [], pageErrors: [], failedRequests: [], screenshot: null }).screenshot = path.basename(target);
      console.log(`[capture] ${path.relative(ROOT, target)}  (${args.width}×${fullHeight} css)`);
      // Reset for the next page so its layout is measured at the base viewport.
      await send("Emulation.setDeviceMetricsOverride", { width: args.width, height: args.height, deviceScaleFactor: 2, mobile: false });
      await sleep(300);
      const { result } = await send("Runtime.evaluate", { expression: "document.documentElement.scrollHeight", returnByValue: true });
    }

    // Map Explorer tile scenario (server must be up) — RGB + NDVI evidence.
    if (!args.noTileServer) {
      console.log("[capture] running Map Explorer tile scenario…");
      audit.tileScenario = await runTileScenario(send, args.out);
      console.log(
        `[capture] tile scenario · rgb=${audit.tileScenario.rgbTiles} ndvi=${audit.tileScenario.ndviTiles} ` +
          `responses=${audit.tileScenario.tileResponses.length} failures=${audit.tileScenario.tileFailures.length} ` +
          `opacity rgb→ndvi: ${audit.tileScenario.opacityAfterRgb}→${audit.tileScenario.opacityAfterNdvi} (pan: ${audit.tileScenario.opacityAfterPan})`
      );
    }

    // Anomaly Desk scenario — slip case, envelope + naive modes, raster
    // evidence (server-up) or the explicit absent state (--no-tile-server).
    console.log("[capture] running Anomaly Desk scenario…");
    audit.deskScenario = await runDeskScenario(send, args.out);
    console.log(
      `[capture] desk scenario · chips=${audit.deskScenario.chips} slip=${audit.deskScenario.slipChipClicked} ` +
        `rasterTiles=${audit.deskScenario.deskRasterTiles} sceneLabel=${audit.deskScenario.sceneLabelOk} ` +
        `naive=${audit.deskScenario.naiveClicked} absentState=${audit.deskScenario.absentStateOk}`
    );

    // ── Gate evaluation ──────────────────────────────────────────────────────
    // In the server-down run (--no-tile-server) the <img> requests to
    // 127.0.0.1:8765 fail with ERR_CONNECTION_REFUSED: that noise is the
    // *expected* graceful-degradation signal (basemap + polygons stay intact),
    // so both the console lines and the :8765 failed requests are excluded.
    const tileNoise = text =>
      args.noTileServer && (/127\.0\.0\.1:8765/.test(text) || /net::ERR_CONNECTION_REFUSED/.test(text));
    let pass = true;
    for (const page of PAGES) {
      const v = audit.views[page.id] ?? {};
      const consoleErrors = (v.console ?? []).filter(t => !tileNoise(t) && !(args.noTileServer && isTileServerNoise(t)));
      const pageErrors = v.pageErrors ?? [];
      const badTiles = (v.failedRequests ?? []).filter(f => /:8765\/tiles\//.test(f.url) && !args.noTileServer);
      const ok = consoleErrors.length === 0 && pageErrors.length === 0 && badTiles.length === 0 && !!v.screenshot;
      if (!ok) pass = false;
      console.log(
        `[gate] ${page.id}: ${ok ? "OK" : "FAIL"} (console=${consoleErrors.length} page=${pageErrors.length} tileFails=${badTiles.length} shot=${v.screenshot ? "yes" : "no"})`
      );
      for (const c of consoleErrors.slice(0, 5)) console.log(`   console: ${c}`);
      for (const e of pageErrors.slice(0, 5)) console.log(`   page: ${e}`);
      for (const f of badTiles.slice(0, 5)) console.log(`   tile: ${f.url} ${f.errorText}`);
    }
    if (!args.noTileServer) {
      const s = audit.tileScenario;
      const ok = s && s.ok && s.rgbTiles > 0 && s.ndviTiles > 0;
      if (!ok) pass = false;
      console.log(`[gate] tile-scenario: ${ok ? "OK" : "FAIL"}`);
    }
    const ds = audit.deskScenario;
    const deskOk = ds && ds.ok;
    if (!deskOk) pass = false;
    console.log(`[gate] desk-scenario: ${deskOk ? "OK" : "FAIL"}`);
    audit.pass = pass;
    audit.finishedAt = new Date().toISOString();
    fs.writeFileSync(path.join(args.out, "audit.json"), JSON.stringify(audit, null, 2));
    fs.writeFileSync(path.join(args.out, "README.md"), README_TEXT(args));
    console.log(`[capture] ${pass ? "GATE PASSED" : "GATE FAILED"} → ${path.relative(ROOT, args.out)}`);
    if (!pass) process.exitCode = 1;
  } finally {
    try {
      server.close();
    } catch {
      /* ignore */
    }
    try {
      session?.close();
    } catch {
      /* ignore */
    }
    child.kill("SIGTERM");
    await new Promise(r => setTimeout(r, 400));
    try {
      fs.rmSync(userDataDir, { recursive: true, force: true });
    } catch {
      /* ignore */
    }
    if (chromeLog.length && process.env.DEBUG_CHROME) console.error(chromeLog.join(""));
  }
}

/** Nav labels per locale, used to locate each page's sidebar button. */
const NAV_LABELS_EN = {
  overview: "Overview",
  map: "Geospatial Explorer",
  temporal: "Temporal Analysis",
  spectral: "Spectral",
  validation: "Validation Lab",
  comparison: "Model Comparison",
  spatial: "Spatial Analysis",
  reports: "Reports & Experiments",
  desk: "Anomaly Desk",
};

const NAV_LABELS_FA = {
  overview: "نمای کلی",
  map: "کاوشگر جغرافیایی",
  temporal: "تحلیل زمانی",
  spectral: "طیفی–زمانی",
  validation: "آزمایشگاه اعتبارسنجی",
  comparison: "مقایسه مدل‌ها",
  spatial: "تحلیل فضایی",
  reports: "گزارش‌ها و آزمایش‌ها",
  desk: "میز ناهنجاری",
};

const navLabels = locale => (locale === "fa" ? NAV_LABELS_FA : NAV_LABELS_EN);

const README_TEXT = a => `# Platform screenshots + runtime audit (${a.locale})

Generated by \`node scripts/capture_platform_screenshots.mjs --locale ${a.locale}\`${
  a.noTileServer ? " **with --no-tile-server (server-down degradation run)**" : " with the tile server running (tile scenario included)"
}.

- \`01…09_*.png\` — the nine views, viewport ${a.width}×${a.height} CSS px at deviceScaleFactor 2.
- \`tile_rgb.png\` / \`tile_ndvi.png\` — Map Explorer raster-overlay evidence (only in server-up runs).
- \`desk_tile_rgb.png\` / \`desk_naive.png\` — Anomaly Desk slip-case review, envelope + naive modes (server-up); \`desk_absent.png\` — the explicit scene-absent degradation state (--no-tile-server runs).
- \`audit.json\` — per-view console errors / page exceptions / failed requests and the tile- + desk-scenario results.
- Gate: zero console errors, zero page errors, tiles render with the server up (wire-platform-to-real-data + add-halqeh-anomaly-desk).
`;

main().catch(err => {
  console.error(`[capture] ${err.stack || err.message}`);
  process.exit(1);
});
