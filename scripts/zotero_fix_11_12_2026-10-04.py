# -*- coding: utf-8 -*-
"""Fix Zotero items #11 (Hajeb) and #12 (Malee) with verified Crossref metadata.
#12 was a mis-filed placeholder: its PDF was actually the Motlagh Ky paper (#76).
Local API first, pyzotero web fallback. Run with Zotero desktop open:
/d/Dev/Miniforge3/envs/geo/python.exe scripts/zotero_fix_11_12_2026-10-04.py
"""
import json, os, urllib.request

LOCAL = "http://localhost:23119/api/users/0"
UA = {"User-Agent": "thesis-corpus-fix/1.0"}
SERVER_ID = None

FIX = {
    "EQI2E6UV": {
        "title": "Simultaneous retrieval of sugarcane variables from Sentinel-2 data using Bayesian regularized neural network",
        "creators": [
            {"creatorType": "author", "firstName": "Mohammad", "lastName": "Hajeb"},
            {"creatorType": "author", "firstName": "Saeid", "lastName": "Hamzeh"},
            {"creatorType": "author", "firstName": "Seyed Kazem", "lastName": "Alavipanah"},
            {"creatorType": "author", "firstName": "Lamya", "lastName": "Neissi"},
            {"creatorType": "author", "firstName": "Jochem", "lastName": "Verrelst"},
        ],
        "publicationTitle": "International Journal of Applied Earth Observation and Geoinformation",
        "volume": "116", "pages": "103168", "date": "2023",
        "DOI": "10.1016/j.jag.2022.103168", "url": "https://doi.org/10.1016/j.jag.2022.103168",
        "ISSN": "1569-8432",
        "extra": "Matrix #11 | verified via Crossref 2026-10-04 | local PDF: papers/11-Hajeb-2023-S2-Sugarcane-Retrieval.pdf",
    },
    "FRBZ964I": {
        "title": "Enhancing water productivity in sugarcane cultivation by integrating basal crop coefficient with deficit irrigation",
        "creators": [
            {"creatorType": "author", "firstName": "Chawanan", "lastName": "Malee"},
            {"creatorType": "author", "firstName": "Jessada", "lastName": "Phattaralerphong"},
            {"creatorType": "author", "firstName": "Ekasit", "lastName": "Kositsakulchai"},
            {"creatorType": "author", "firstName": "Siriporn", "lastName": "Rattanasakphakdee"},
            {"creatorType": "author", "firstName": "Ekawan", "lastName": "Luepromchai"},
            {"creatorType": "author", "firstName": "Boonlue", "lastName": "Kachenchart"},
        ],
        "publicationTitle": "Agricultural Water Management",
        "volume": "333", "pages": "110529", "date": "2026",
        "DOI": "10.1016/j.agwat.2026.110529", "url": "https://doi.org/10.1016/j.agwat.2026.110529",
        "ISSN": "0378-3774",
        "extra": "Matrix #12 | verified via Crossref 2026-10-04 | PDF pending browser fetch (Elsevier blocks curl)",
    },
}


def capture_sid():
    global SERVER_ID
    if SERVER_ID is None:
        with urllib.request.urlopen(urllib.request.Request(f"{LOCAL}/collections", headers=UA), timeout=30) as r:
            r.read()
            SERVER_ID = r.headers.get("Zotero-Server-ID")


def try_local(key, meta):
    global SERVER_ID
    capture_sid()
    with urllib.request.urlopen(urllib.request.Request(f"{LOCAL}/items/{key}", headers=UA), timeout=30) as r:
        item = json.load(r)
    data = item["data"]
    version = data["version"]
    for k, v in meta.items():
        data[k] = v
    body = {k: v for k, v in data.items() if k not in ("key", "library", "links", "meta")}
    req = urllib.request.Request(f"{LOCAL}/items/{key}", method="PUT",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Zotero-Server-ID": SERVER_ID,
                                          "If-Unmodified-Since-Version": str(version), **UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
        sid = r.headers.get("Zotero-Server-ID")
        if sid:
            SERVER_ID = sid
        return f"local HTTP {r.status}"


def try_web(key, meta):
    from pyzotero import zotero
    z = zotero.Zotero(os.environ["ZOTERO_USER_ID"], "user", os.environ["ZOTERO_API_KEY"])
    item = z.item(key)
    data = item["data"]
    for k, v in meta.items():
        data[k] = v
    z.update_item(key, data)
    return "web-ok"


results = {}
for key, meta in FIX.items():
    try:
        results[key] = try_local(key, meta)
    except Exception as e:
        print(f"local failed for {key}: {str(e)[:200]}")
        try:
            results[key] = try_web(key, meta)
        except Exception as e2:
            results[key] = f"FAILED: {str(e2)[:200]}"
print(json.dumps(results, indent=1))
