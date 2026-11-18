# -*- coding: utf-8 -*-
"""Raw web-API PATCH for Zotero items #11 (Hajeb) and #12 (Malee).
Credentials from Windows env vars ZOTERO_API_KEY / ZOTERO_USER_ID."""
import json, os, urllib.request

KEY = os.environ["ZOTERO_API_KEY"]
UID = os.environ["ZOTERO_USER_ID"]
BASE = f"https://api.zotero.org/users/{UID}"

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

out = {}
for key, patch in FIX.items():
    req = urllib.request.Request(f"{BASE}/items/{key}", headers={"Zotero-API-Key": KEY, **{"User-Agent": "thesis-corpus-fix/1.0"}})
    with urllib.request.urlopen(req, timeout=30) as r:
        version = json.load(r)["version"]
    req = urllib.request.Request(f"{BASE}/items/{key}", method="PATCH",
                                 data=json.dumps(patch).encode(),
                                 headers={"Zotero-API-Key": KEY, "Content-Type": "application/json",
                                          "If-Unmodified-Since-Version": str(version),
                                          "User-Agent": "thesis-corpus-fix/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out[key] = f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        out[key] = f"FAILED HTTP {e.code}: {e.read().decode()[:200]}"
print(json.dumps(out, indent=1))
