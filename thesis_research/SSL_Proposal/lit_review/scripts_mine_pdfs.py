import json, re, sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(r"D:/RS/Thesis/thesis_research")
OUT = ROOT / "SSL_Proposal/lit_review/_pdf_mining.json"

TARGETS = [
    ROOT / "SSL_Proposal/papers/2304.14065.pdf",
    ROOT / "SSL_Proposal/papers/2306.10125.pdf",
    ROOT / "SSL_Proposal/papers/2404.08931.pdf",
    ROOT / "SSL_Proposal/papers/2507.04366.pdf",
    ROOT / "SSL_Proposal/papers/2512.23986.pdf",
    ROOT / "SSL_Proposal/papers/2605.19462.pdf",
    ROOT / "SSL_Proposal/papers/2607.18791.pdf",
    ROOT / "SSL_Proposal/papers/2608.02322.pdf",
    ROOT / "SSL_Proposal/papers/2608.25888.pdf",
    ROOT / "SSL_Proposal/papers/A_Unifying_Review_of_Deep_and_Shallow_Anomaly_Detection.pdf",
    ROOT / "SSL_Proposal/papers/fpls-16-1576756.pdf",
    ROOT / "papers/03-Balestriero-2023-SSL-Cookbook.pdf",
    ROOT / "papers/01-Qin-2024-SITSMamba.pdf",
    ROOT / "papers/02-Miller-2024-DL-SITS-Review.pdf",
    ROOT / "papers/05-Russwurm-2020-SelfAttention-SITS.pdf",
    ROOT / "papers/14-Dalal-2026-STSPORT-SelfSupervised-Stress.pdf",
    ROOT / "papers/15-Ahmad-2025-EigenCL-Unsupervised-Contrastive.pdf",
    ROOT / "papers/16-Sadbhave-2025-SugarBeet-SITS-3DAE.pdf",
    ROOT / "papers/22-Tan-2024-DroughtSet-SpatialTemporal.pdf",
    ROOT / "papers/26-Agastya-2021-SSL-Irrigation-Detection.pdf",
    ROOT / "papers/60-Paul-2025-DL-Plant-Stress-Review.pdf",
    ROOT / "papers/79-Elbeltagi-2026-Vegetation-Water-Stress-EVI-FeatureOptimized-ML.pdf",
]

ARXIV = re.compile(r"arXiv[:\s]*(\d{4}\.\d{4,5})", re.I)
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)")

results = []
for p in TARGETS:
    rec = {"file": p.name, "exists": p.exists()}
    if not p.exists():
        results.append(rec); continue
    try:
        r = PdfReader(str(p))
        t1 = (r.pages[0].extract_text() or "")[:2600]
        if len(r.pages) > 1:
            t2 = (r.pages[1].extract_text() or "")[:1200]
        else:
            t2 = ""
        rec["n_pages"] = len(r.pages)
        rec["page1"] = t1
        rec["page2"] = t2
        m = ARXIV.search(t1)
        rec["arxiv_id"] = m.group(1) if m else None
        d = DOI.search(t1)
        rec["doi"] = d.group(1).rstrip(".,;") if d else None
    except Exception as e:
        rec["error"] = repr(e)
    results.append(rec)

OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT, len(results), "records")
