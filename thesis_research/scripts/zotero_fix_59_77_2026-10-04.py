# -*- coding: utf-8 -*-
"""Fix Zotero manual items #59 (REMSA) and #77 (Waters) with metadata verified
via the arXiv API on 2026-10-04. Raw web-API PATCH."""
import json, os, urllib.request

KEY = os.environ["ZOTERO_API_KEY"]; UID = os.environ["ZOTERO_USER_ID"]
BASE = f"https://api.zotero.org/users/{UID}"
H = {"Zotero-API-Key": KEY, "Content-Type": "application/json", "User-Agent": "thesis-corpus-fix/1.0"}

FIX = {
    # find by extra tag first — keys may differ
}
def find_item(matrix_id):
    import re as _re
    start = 0
    while True:
        url = f"{BASE}/items/top?format=json&start={start}&limit=100"
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r:
            batch = json.load(r)
        if not batch:
            return None
        for it in batch:
            extra = it["data"].get("extra", "") or ""
            if _re.search(rf"Matrix #{matrix_id}\b", extra):
                return it
        start += 100

PATCHES = {
    59: {  # REMSA — arXiv 2511.17442 (was 404 at import)
        "itemType": "preprint",
        "title": "REMSA: Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent",
        "creators": [
            {"creatorType": "author", "firstName": "Binger", "lastName": "Chen"},
            {"creatorType": "author", "firstName": "Tacettin Emre", "lastName": "Bök"},
            {"creatorType": "author", "firstName": "Behnood", "lastName": "Rasti"},
            {"creatorType": "author", "firstName": "Volker", "lastName": "Markl"},
            {"creatorType": "author", "firstName": "Begüm", "lastName": "Demir"},
        ],
        "date": "2025-11-21",
        "repository": "arXiv",
        "archiveID": "arXiv:2511.17442",
        "url": "https://arxiv.org/abs/2511.17442",
        "extra": "Matrix #59 | verified via arXiv API 2026-10-04 (import-time ID 404 was a transient failure)",
    },
    77: {  # Waters — now PUBLISHED: CEA 229:109686
        "itemType": "journalArticle",
        "title": "Sugarcane Health Monitoring With Satellite Spectroscopy and Machine Learning: A Review",
        "creators": [
            {"creatorType": "author", "firstName": "Ethan Kane", "lastName": "Waters"},
            {"creatorType": "author", "firstName": "Carla Chia-Ming", "lastName": "Chen"},
            {"creatorType": "author", "firstName": "Mostafa Rahimi", "lastName": "Azghadi"},
        ],
        "publicationTitle": "Computers and Electronics in Agriculture",
        "volume": "229", "pages": "109686", "date": "2025",
        "DOI": "10.1016/j.compag.2024.109686",
        "url": "https://doi.org/10.1016/j.compag.2024.109686",
        "extra": "Matrix #77 | verified via arXiv API 2026-10-04 (arXiv:2404.16844; published version exists — cite CEA 229:109686, 2025)",
    },
}

out = {}
for mid, patch in PATCHES.items():
    it = find_item(mid)
    if not it:
        out[mid] = "ITEM NOT FOUND"
        continue
    key = it["key"]; version = it["version"]
    req = urllib.request.Request(f"{BASE}/items/{key}", method="PATCH",
                                 data=json.dumps(patch).encode(),
                                 headers={**H, "If-Unmodified-Since-Version": str(version)})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out[mid] = f"{key} HTTP {r.status}"
    except urllib.error.HTTPError as e:
        out[mid] = f"FAILED HTTP {e.code}: {e.read().decode()[:200]}"
print(json.dumps(out, indent=1))
