# -*- coding: utf-8 -*-
"""
Finish the thesis corpus import via the Zotero 7+ LOCAL API (desktop app).
The web API kept rate-limiting; the local API (localhost:23119) has no limits,
shows items immediately, and syncs in the background.
Requires the Zotero desktop app to be running. Idempotent.
Run:  /d/Dev/Miniforge3/envs/geo/python.exe scripts/zotero_local_finish_2026-10-04.py
"""
import json
import re
import sys
import time
import importlib.util
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("zbase", HERE / "zotero_import_2026-10-04.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)  # brings P, COLLS, TAGS, PDF_FILES, crossref, batch_arxiv, manual, UA

LOCAL = "http://localhost:23119/api/users/0"
SERVER_ID = None


def req(method, path, payload=None):
    """Local-API request; keeps the Zotero-Server-ID fresh from responses."""
    global SERVER_ID
    url = LOCAL + path
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={"Content-Type": "application/json", **base.UA})
    try:
        resp = urllib.request.urlopen(r, timeout=60)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {body}")
    sid = resp.headers.get("Zotero-Server-ID")
    if sid:
        SERVER_ID = sid
    return json.load(resp)


def write(method, path, payload=None):
    global SERVER_ID
    if SERVER_ID is None:
        # pull the server id from any GET
        req("GET", "/collections")
    r = urllib.request.Request(LOCAL + path, method=method,
                               data=json.dumps(payload).encode() if payload is not None else None,
                               headers={"Content-Type": "application/json", "Zotero-Server-ID": SERVER_ID, **base.UA})
    try:
        resp = urllib.request.urlopen(r, timeout=60)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:300]}")
    sid = resp.headers.get("Zotero-Server-ID")
    if sid:
        SERVER_ID = sid
    raw = resp.read().decode()
    return json.loads(raw) if raw.strip() else {}


def main():
    # 0. server id + reachability
    req("GET", "/collections")
    print("local API OK, server id:", SERVER_ID)

    # 1. collections (create missing under Thesis)
    cols = req("GET", "/collections")
    names = {c["data"]["name"]: c["key"] for c in cols}
    if "Thesis" not in names:
        k = write("POST", "/collections", [{"name": "Thesis"}])["successful"]["0"]["key"]
        names["Thesis"] = k
    for cname in base.COLLS:
        if cname not in names:
            k = write("POST", "/collections", [{"name": cname, "parentCollection": names["Thesis"]}])
            names[cname] = k["successful"]["0"]["key"]
    colls = {n: names[n] for n in base.COLLS}
    print("collections ready:", len(colls) + 1)

    # 2. present items
    items = req("GET", "/items?limit=500&itemType=-attachment")
    have = set()
    for it in items:
        m = re.search(r"Matrix #(\d+)", it["data"].get("extra") or "")
        if m:
            have.add(int(m.group(1)))
            continue
        key = it["data"].get("archiveID") or it["data"].get("DOI") or ""
        for i, (ident, _fb) in base.P.items():
            if ident and key and key.lower().endswith(str(ident).lower()):
                have.add(i)
    todo = [i for i in sorted(base.P) if i not in have]
    print(f"present={len(have)} todo={len(todo)}", flush=True)
    if not todo:
        print("nothing to do")
        return

    # 3. metadata (batched arXiv + crossref; manual fallback flagged)
    axmeta = base.batch_arxiv([str(base.P[i][0]) for i in todo
                               if base.P[i][0] and not str(base.P[i][0]).startswith("10.")])
    print(f"arXiv batch: {len(axmeta)} records", flush=True)
    report, ok = [], 0
    for i in todo:
        ident, fb = base.P[i]
        try:
            if ident is None:
                meta = base.manual(i, fb)
            elif str(ident).startswith("10."):
                try:
                    meta = base.crossref(ident)
                except Exception:
                    if not fb:
                        raise
                    meta = base.manual(i, fb)
                time.sleep(0.5)
            else:
                meta = axmeta.get(str(ident))
                if meta is None:
                    meta = base.manual(i, fb or f"arXiv:{ident} — metadata fetch failed; refresh from arXiv")
                    meta.update({"itemType": "preprint", "repository": "arXiv", "archiveID": f"arXiv:{ident}",
                                 "url": f"https://arxiv.org/abs/{ident}"})
            src = "manual" if ident is None else ("Crossref" if str(ident).startswith("10.") else ("arXiv" if meta.get("archiveID") else "manual-fallback"))
        except Exception as e:
            report.append({"id": i, "status": "META-FAIL", "error": str(e)[:150]})
            print(f"META-FAIL #{i}: {e}", flush=True)
            continue
        meta.setdefault("extra", f"Matrix #{i:02d} | local PDF: papers/{base.PDF_FILES[i]}")
        if "Matrix #" not in meta["extra"]:
            meta["extra"] += f" | Matrix #{i:02d} | local PDF: papers/{base.PDF_FILES[i]}"
        meta["tags"] = [{"tag": t} for t in base.TAGS.get(i, [])]
        meta["collections"] = [colls[n] for n, ids in base.COLLS.items() if i in ids]
        try:
            try:
                res = write("POST", "/items", [meta])
                item = res["successful"]["0"]
                route = "local"
            except RuntimeError as e:
                if "401" not in str(e) and "403" not in str(e):
                    raise
                # local API refused (needs /api/local/authorize) → web API fallback
                r = base.z.create_items([meta])
                item = r["successful"]["0"]
                route = "web"
        except Exception as e:
            report.append({"id": i, "status": "CREATE-FAIL", "error": str(e)[:250]})
            print(f"CREATE-FAIL #{i}: {str(e)[:150]}", flush=True)
            continue
        pdf = base.PAPERS / base.PDF_FILES[i]
        if pdf.exists():
            att = {"itemType": "attachment", "linkMode": "linked_file", "parentItem": item["key"],
                   "title": base.PDF_FILES[i], "path": str(pdf), "tags": [], "collections": []}
            try:
                if route == "local":
                    write("POST", "/items", [att])
                else:
                    base.z.create_items([att])
                    time.sleep(1.0)
            except Exception as e:
                report.append({"id": i, "status": "ATTACH-FAIL", "error": str(e)[:200]})
        ok += 1
        report.append({"id": i, "status": "created", "key": item["key"],
                       "title": (meta.get("title") or "")[:80], "source": src, "route": route})
        time.sleep(0.3 if route == "local" else 1.2)
    (base.REPORT.parent).mkdir(exist_ok=True)
    (base.REPORT.parent / "zotero_local_finish_report_2026-10-04.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"created={ok} failed={len([r for r in report if 'FAIL' in r['status']])}")
    for r in report:
        if "FAIL" in r["status"]:
            print("FAIL:", r)
    import random
    made = [r for r in report if r["status"] == "created"]
    for r in random.sample(made, min(10, len(made))):
        print("VERIFY:", r["id"], "|", r["source"], "|", r["title"])


if __name__ == "__main__":
    main()
