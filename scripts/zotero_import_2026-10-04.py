# -*- coding: utf-8 -*-
"""
Zotero corpus import — thesis_research papers 01-78 (2026-10-04).

Idempotent: skips items already present (matched by `Matrix #NN` in extra, or
by arXiv DOI/archiveID). Metadata: Crossref (DOI), arXiv API in ONE batched
request for all arXiv-only items, manual fallback (flagged) otherwise.
PDFs attached as linked files (paths, not uploads). Credentials from
ZOTERO_API_KEY / ZOTERO_USER_ID env vars only.
Run:  /d/Dev/Miniforge3/envs/geo/python.exe scripts/zotero_import_2026-10-04.py
"""
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from pyzotero import zotero

REPO = Path(__file__).resolve().parent.parent
PAPERS = REPO / "papers"
REPORT = REPO / "outputs" / "zotero_import_report_2026-10-04.json"
UA = {"User-Agent": "thesis-corpus-import/1.0 (mailto:research@example.org)"}

z = zotero.Zotero(os.environ["ZOTERO_USER_ID"], "user", os.environ["ZOTERO_API_KEY"])
assert z.key_info()["access"]["user"]["write"], "API key has no write access"

# ---------------------------------------------------------------- identifiers
# id: (doi | arXiv id | None, manual_fallback_title)
P = {
    1:  ("2409.09673", None), 2: ("2404.03936", None), 3: ("2304.12210", None),
    4:  ("2402.13791", None), 5: ("10.1016/j.isprsjprs.2020.06.006", None),
    6:  (None, "Ahmed et al. (2025). XAI for Spectroscopic Agriculture (review). Computers and Electronics in Agriculture."),
    7:  ("10.3390/plants11212884", None), 8: ("10.1007/s11119-025-10279-5", None),
    9:  ("10.1016/j.atech.2026.102391", None),
    10: (None, "Zoratipour et al. (2026). Hourly vs daily CWSI in sugarcane (proximal/satellite), Khuzestan."),
    11: (None, "Hajeb et al. (2023). Multivariate sugarcane trait retrieval from Sentinel-2. ISPRS Journal."),
    12: (None, "Malee et al. (2026). Sugarcane crop coefficients (local Ky). Agricultural Water Management."),
    13: ("10.1016/j.scienta.2025.113860", "Sapkota et al. (2025). Comparative analysis of ET, CWSI, and NDVI for irrigation scheduling in almond orchards. Scientia Horticulturae 339:113860 (DOI 404 on Crossref 2026-10-04 — verify)."), 14: ("2607.18791", None),
    15: ("2506.03394", None), 16: ("2507.13514", None), 17: ("2407.08298", None),
    18: ("2501.00502", None), 19: ("2510.23124", None), 20: ("2509.02265", None),
    21: ("2506.01714", None), 22: ("2412.15075", None),
    23: ("10.3389/fagro.2025.1681294", None), 24: ("10.1016/j.agwat.2025.109862", None),
    25: (None, "Zoratipour et al. (2025). Sentinel-2 MSI vs Landsat thermal CWSI. Iranian Journal of Soil and Water Research."),
    26: ("2108.05484", None), 27: ("2204.02029", None), 28: ("1602.06335", None),
    29: ("2603.23779", None), 30: ("2609.10156", None), 31: ("2106.07770", None),
    32: ("2509.10804", None), 33: ("2609.07915", None), 34: ("2508.13379", None),
    35: (None, "Hornero et al. (2026). CWSI for oak trees using high-resolution thermal imaging. Remote Sensing of Environment 344:115549."),
    36: (None, "Sanchez-Virosta et al. (2025). UAV-based CWSI in almond orchards. International Journal of Applied Earth Observation 142:104737."),
    37: (None, "Bai et al. (2017). TVDI vs CWSI for drought monitoring. Journal of Integrative Agriculture."),
    38: ("10.3390/rs12091449", None), 39: ("10.1093/jxb/ers165", None),
    40: ("10.3389/fenvs.2014.00039", None), 41: ("10.1146/annurev-arplant-042817-040218", None),
    42: ("10.3390/rs11101240", None), 43: ("10.3390/rs13020305", None),
    44: ("10.1016/j.rse.2022.113198", None), 45: ("10.3390/rs17233886", None),
    46: ("10.3390/rs18091420", None),
    47: ("2406.07089", None), 48: ("2505.23752", None), 49: ("2601.01891", None),
    50: ("2602.15325", None), 51: ("2604.08896", None), 52: ("2606.07538", None),
    53: ("2607.24772", None), 54: ("2609.12533", None), 55: ("2504.09848", None),
    56: ("2604.24919", None), 57: ("10.1080/20964471.2025.2600178", None),
    58: ("2608.00877", None), 59: (None, "Chen, B., et al. (2025-26). REMSA: Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent (arXiv:2511.17442 — ID returned 404 on 2026-10-04, verify)."),
    60: ("10.1016/j.compag.2024.109734", None), 61: ("10.1016/j.agwat.2025.110077", None),
    62: ("10.1016/j.agwat.2026.110444", None), 63: ("10.1016/j.eij.2026.101025", None),
    64: ("10.1016/j.jag.2026.105195", None), 65: ("10.1016/j.rineng.2025.107342", None),
    66: ("10.1016/j.plaphe.2025.100161", None), 67: ("10.1016/j.atech.2025.101640", None),
    68: ("10.3390/rs13204155", None), 69: ("10.3390/rs13010006", None),
    70: ("10.5194/hess-26-4537-2022", None), 71: ("10.1016/j.jag.2023.103438", None),
    72: ("10.1016/j.atech.2025.101583", None), 73: ("10.14719/pst.13057", None),
    74: ("10.1016/j.rsase.2026.102279", None), 75: ("10.1016/j.htopen.2026.100024", None),
    76: ("10.1016/j.agwat.2026.110260", None),
    77: (None, "Waters et al. (2024). Sugarcane crop health monitoring review (arXiv:2404.16844 — ID 404 at import time, verify)."),
    78: ("10.1007/s11119-020-09711-9", None),
}

COLLS = {
    "Core-Method (architecture-SSL-XAI)": [1, 2, 3, 4, 5, 6, 14, 15, 16, 17, 18, 26, 30, 31, 32, 33, 34, 38, 60, 74],
    "Concurrent-Stress": [7, 21, 40, 41, 44, 45, 69, 70, 71, 72],
    "Salinity": [8, 19, 20, 27, 43, 46],
    "CWSI-Thermal": [10, 13, 24, 25, 28, 35, 36, 37, 39, 42, 61, 62, 68, 73, 75, 78],
    "Khuzestan-Local": [9, 11, 12, 23, 29, 76, 77],
    "Agentic-Optional": [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 63, 64, 65, 66, 67],
    "Datasets-Benchmarks": [22],
}
TAGS = {
    70: ["verified-full-read-2026-10-04"], 8: ["verified-full-read-2026-10-04"],
    **{i: ["agentic-frozen-2026-10-04"] for i in COLLS["Agentic-Optional"]},
}
PDF_FILES = {
    1: "01-Qin-2024-SITSMamba.pdf", 2: "02-Miller-2024-DL-SITS-Review.pdf",
    3: "03-Balestriero-2023-SSL-Cookbook.pdf", 4: "04-Hohl-2024-XAI-RS-Review.pdf",
    5: "05-Russwurm-2020-SelfAttention-SITS.pdf", 6: "06-Ahmed-2025-XAI-Spectroscopy-Review.pdf",
    7: "07-Angon-2022-combined-stress.pdf", 8: "08-Paciolla-2025-Salinity-LAI-DA.pdf",
    9: "09-Motlagh-2026-Sugarcane-Yield-Variability.pdf", 10: "10-Zoratipour-2026-Hourly-Daily-CWSI-Proximal.pdf",
    11: "11-Hajeb-2023-S2-Sugarcane-Retrieval.pdf", 12: "12-Malee-2026-Sugarcane-Crop-Coefficients.pdf",
    13: "13-Sapkota-2025-ET-CWSI-NDVI-Almond.pdf", 14: "14-Dalal-2026-STSPORT-SelfSupervised-Stress.pdf",
    15: "15-Ahmad-2025-EigenCL-Unsupervised-Contrastive.pdf", 16: "16-Sadbhave-2025-SugarBeet-SITS-3DAE.pdf",
    17: "17-Najjar-2024-XAI-Guided-Vegetation-Indices.pdf", 18: "18-Miranda-2024-PINN-YieldLoss.pdf",
    19: "19-Dey-2025-DeepSalt-DomainAdaptation.pdf", 20: "20-Gupta-2025-Spectroscopic-Salinity-Review.pdf",
    21: "21-Li-2025-Plant-Stress-Physiology.pdf", 22: "22-Tan-2024-DroughtSet-SpatialTemporal.pdf",
    23: "23-Vinayaka-2025-AI-RS-Sugarcane-Review.pdf", 24: "24-Zoratipour-2025-ML-BiasCorrection-CWSI.pdf",
    25: "25-Zoratipour-2025-Sentinel2-vs-Landsat-CWSI.pdf", 26: "26-Agastya-2021-SSL-Irrigation-Detection.pdf",
    27: "27-Shi-2022-Salinity-Irrigation-Bayesian.pdf", 28: "28-Nay-2016-VegHealth-ML-Forecasting.pdf",
    29: "29-Narimani-2026-S2-Yield-Estimation-Review.pdf", 30: "30-Fan-2026-ScopeMamba-YOLO-RS.pdf",
    31: "31-Butler-2021-Potato-Stress-Aerial-DL.pdf", 32: "32-Narimani-2025-Tomato-Weed-SITS.pdf",
    33: "33-Bhaumik-2026-JEDI-Foundation-Model.pdf", 34: "34-Bukhari-2025-LowCost-Stress-Sensing.pdf",
    35: "35-Hornero-2026-CWSI-Oak-Thermal-Imaging.pdf", 36: "36-Sanchez-Virosta-2025-CWSI-UAV-Almond.pdf",
    37: "37-Bai-2017-TVDI-vs-CWSI-Drought.pdf", 38: "38-Akbari-2020-RF-PSO-Crop-Mapping.pdf",
    39: "39-Maes-2012-CWSI-ground-thermal.pdf", 40: "40-Feller-2014-drought-heat-physiology.pdf",
    41: "41-Tardieu-2018-drought-probabilistic.pdf", 42: "42-Gerhards-2019-TIR-water-stress.pdf",
    43: "43-Wang-2021-S2-Salinity-Arid-ML.pdf", 44: "44-Berger-2022-optical-stress-synergies.pdf",
    45: "45-Shen-2025-broadacre-resilience.pdf", 46: "46-Smanov-2026-salt-tolerance-salinity-RS.pdf",
    47: "47-RS-Agent-2024-TaskPlanning-DualRAG.pdf", 48: "48-ThinkGeo-2025-ToolAgent-Benchmark.pdf",
    49: "49-Talemi-2026-Agentic-RS-Survey.pdf", 50: "50-AgriWorld-2026-Verifiable-Agri-Agents.pdf",
    51: "51-Xiao-2026-GeoMMBench-GeoMMAgent.pdf", 52: "52-BSCTR-2026-Tool-Retrieval.pdf",
    53: "53-RSMeM-2026-Memory-Evolution.pdf", 54: "54-Earth-Agent-Pro-2026-FullChain-EO.pdf",
    55: "55-Feng-2025-Spatial-Intelligence-Survey.pdf", 56: "56-Munir-2026-Agentic-AI-RS-Position.pdf",
    57: "57-ExpertsRS-2026-MultiAgent-RS.pdf", 58: "58-GeoArbiter-2026-Verifiability-Grounding.pdf",
    59: "59-REMSA-2026-FM-Selection-Agent.pdf", 60: "60-Paul-2025-DL-Plant-Stress-Review.pdf",
    61: "61-Zhang-2026-Pixel-IWU.pdf", 62: "62-Khamseh-2026-IWU-Uncertainty.pdf",
    63: "63-Sun-2026-SelfEvolution-RS-Agents.pdf", 64: "64-GeoAgentic-RAG-2026.pdf",
    65: "65-Tariq-2025-Edge-Agentic-Agriculture.pdf", 66: "66-Musazade-2026-LLM-VLM-Plant-Stress.pdf",
    67: "67-CottonBot-2025-LLM-RAG-Irrigation.pdf", 68: "68-Ahmad-2021-CropWaterStress-Review.pdf",
    69: "69-Wen-2021-Salinity-Drought-RS-Challenges.pdf", 70: "70-Wen-2022-Drought-Salinity-Combined-NL.pdf",
    71: "71-Wen-2023-Crop-Salinity-Drought-US.pdf", 72: "72-Haq-2025-MultiDim-Optical-Stress.pdf",
    73: "73-Gokul-2026-UAV-CropWaterStress-Review.pdf", 74: "74-GraciaRojas-2026-ML-DL-AgriForestry-SLR.pdf",
    75: "75-Olawoyin-2026-Volta-ET-CWSI.pdf", 76: "76-Motlagh-2026-Ky-Derivation.pdf",
    77: "77-Waters-2024-Sugarcane-Health-Review.pdf", 78: "78-Virnodkar-2020-WaterStress-ML-Review.pdf",
}

# ------------------------------------------------------------ metadata fetch
def clean_abs(s):
    if not s:
        return None
    return re.sub(r"<[^>]+>", "", s).strip()[:1500] or None

def crossref(doi):
    req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        m = json.load(r)["message"]
    year = None
    for k in ("published-print", "published-online", "issued"):
        if m.get(k) and m[k].get("date-parts"):
            year = m[k]["date-parts"][0][0]
            if year:
                break
    return {
        "itemType": "journalArticle",
        "title": m["title"][0] if m.get("title") else None,
        "creators": [{"creatorType": "author", "firstName": a.get("given", ""), "lastName": a.get("family", "")}
                     for a in m.get("author", []) if a.get("family")],
        "publicationTitle": (m.get("container-title") or [None])[0],
        "volume": m.get("volume"), "pages": m.get("page"),
        "date": str(year) if year else None, "DOI": m.get("DOI"),
        "abstractNote": clean_abs(m.get("abstract")), "url": m.get("URL"),
    }

def batch_arxiv(aids):
    """Fetch many arXiv records with ONE id_list call; returns {aid: meta}."""
    out = {}
    if not aids:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for chunk in [aids[i:i + 50] for i in range(0, len(aids), 50)]:
        for attempt in range(4):
            try:
                req = urllib.request.Request(
                    f"https://export.arxiv.org/api/query?id_list={','.join(chunk)}&max_results=100", headers=UA)
                with urllib.request.urlopen(req, timeout=60) as r:
                    root = ET.parse(r).getroot()
                for e in root.findall("a:entry", ns):
                    eid = (e.find("a:id", ns).text or "").rsplit("/", 1)[-1]  # e.g. http://arxiv.org/abs/2409.09673v2
                    eid = re.sub(r"v\d+$", "", eid)
                    out[eid] = {
                        "itemType": "preprint", "repository": "arXiv", "archiveID": f"arXiv:{eid}",
                        "title": " ".join((e.find("a:title", ns).text or "").split()),
                        "creators": [{"creatorType": "author",
                                      "firstName": (p.find("a:name", ns).text or "").rsplit(" ", 1)[0],
                                      "lastName": (p.find("a:name", ns).text or "").rsplit(" ", 1)[-1]}
                                     for p in e.findall("a:author", ns) if p.find("a:name", ns) is not None],
                        "date": (e.find("a:published", ns).text or "")[:4],
                        "url": f"https://arxiv.org/abs/{eid}",
                        "abstractNote": " ".join((e.find("a:summary", ns).text or "").split())[:1500],
                    }
                break
            except Exception as e:
                print(f"batch arXiv retry {attempt + 1}: {type(e).__name__}", flush=True)
                time.sleep(10 * (attempt + 1))
        time.sleep(3)
    return out

def manual(i, title):
    return {"itemType": "journalArticle", "title": title, "date": None, "creators": [],
            "extra": f"MANUAL metadata — verify. Matrix #{i:02d} | local PDF: papers/{PDF_FILES[i]}"}

# ------------------------------------------------------------------- helpers
def find_coll(name):
    for c in z.collections():
        if c["data"]["name"] == name:
            return c["key"]
    return None

def created_key(result):
    if isinstance(result, list) and result:
        return result[0]["data"]["key"]
    return result["successful"]["0"]["key"]

def ensure_colls():
    keys = {}
    root = find_coll("Thesis")
    if not root:
        root = created_key(z.create_collections([{"name": "Thesis"}]))
    for name in COLLS:
        k = find_coll(name)
        if not k:
            k = created_key(z.create_collections([{"name": name, "parentCollection": root}]))
        keys[name] = k
    return keys

def present_ids():
    have = set()
    for it in z.everything(z.top()):
        d = it["data"]
        m = re.search(r"Matrix #(\d+)", d.get("extra") or "")
        if m:
            have.add(int(m.group(1)))
            continue
        key = d.get("archiveID") or d.get("DOI") or ""
        for i, (ident, _fb) in P.items():
            if ident and key and key.lower().endswith(str(ident).lower()):
                have.add(i)
    return have

def main():
    colls = ensure_colls()
    have = present_ids()
    todo = [i for i in sorted(P) if i not in have]
    print(f"present={len(have)} todo={len(todo)}: {todo}", flush=True)
    axmeta = batch_arxiv([str(P[i][0]) for i in todo if P[i][0] and "." not in str(P[i][0])])
    report, ok = [], 0
    for i in todo:
        ident, fb = P[i]
        if ident is None:
            meta = manual(i, fb)
        elif "." in ident:
            meta = None
            for attempt in range(3):
                try:
                    meta = crossref(ident)
                    break
                except Exception as e:
                    print(f"crossref retry {attempt + 1} #{i}: {type(e).__name__}", flush=True)
                    time.sleep(6 * (attempt + 1))
            if meta is None:
                report.append({"id": i, "status": "META-FAIL", "error": f"crossref {ident}"})
                continue
        else:
            meta = axmeta.get(str(ident))
            if meta is None:
                meta = manual(i, fb or f"arXiv:{ident} — metadata fetch failed; refresh from arXiv")
                meta.update({"itemType": "preprint", "repository": "arXiv", "archiveID": f"arXiv:{ident}",
                             "url": f"https://arxiv.org/abs/{ident}"})
                meta["extra"] = meta["extra"].replace("MANUAL metadata — verify. ", "MANUAL metadata (arXiv fetch failed) — verify. ")
        src = "manual" if ident is None else ("Crossref" if "." in ident else ("arXiv" if meta.get("archiveID") else "manual-fallback"))
        meta.setdefault("extra", f"Matrix #{i:02d} | local PDF: papers/{PDF_FILES[i]}")
        if not re.search(r"Matrix #\d+", meta["extra"]):
            meta["extra"] += f" | Matrix #{i:02d} | local PDF: papers/{PDF_FILES[i]}"
        meta["tags"] = [{"tag": t} for t in TAGS.get(i, [])]
        meta["collections"] = [colls[n] for n, ids in COLLS.items() if i in ids]
        item = None
        failinfo = ""
        for attempt in range(5):
            try:
                r = z.create_items([meta])
            except Exception as e:
                r = {"exc": f"{type(e).__name__}: {e}"[:200]}
            succ = (r.get("successful") or {}).get("0")
            if succ:
                item = succ
                break
            failinfo = json.dumps((r.get("failed") or r), default=str)[:200]
            time.sleep(3 * (attempt + 1))
        if item is None:
            report.append({"id": i, "status": "CREATE-FAIL", "error": failinfo})
            print(f"CREATE-FAIL #{i}: {failinfo}", flush=True)
            continue
        pdf = PAPERS / PDF_FILES[i]
        if pdf.exists():
            att = {"itemType": "attachment", "linkMode": "linked_file", "parentItem": item["key"],
                   "title": PDF_FILES[i], "path": str(pdf), "tags": [], "collections": []}
            try:
                z.create_items([att])
            except Exception as e:
                report.append({"id": i, "status": "ATTACH-FAIL", "error": str(e)[:200]})
        ok += 1
        report.append({"id": i, "status": "created", "key": item["key"],
                       "title": (meta.get("title") or "")[:80], "source": src})
        time.sleep(1.2)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"created={ok} failed={len([r for r in report if 'FAIL' in r['status']])}", flush=True)
    import random
    made = [r for r in report if r["status"] == "created"]
    for r in random.sample(made, min(10, len(made))):
        print("VERIFY:", r["id"], "|", r["source"], "|", r["title"])
    still = sorted(set(range(1, 79)) - have - {r["id"] for r in made})
    if still:
        print("STILL MISSING:", still)

if __name__ == "__main__":
    main()
