"""Get full metadata for all 8 advisor papers."""
import subprocess, json, time

papers = [
    ("SITSMamba", "https://doi.org/10.48550/arXiv.2409.09673"),
    ("DL_SITS_review", "https://doi.org/10.48550/arXiv.2404.03936"),
    ("SSL_Cookbook", "https://doi.org/10.48550/arXiv.2304.12210"),
    ("XAI_RS_review", "https://doi.org/10.48550/arXiv.2402.13791"),
    ("SelfAttention_SITS", "https://doi.org/10.5194/isprs-annals-X-1-W1-2020-301-2020"),
    ("XAI_agriculture", "https://doi.org/10.1016/j.compag.2025.108835"),
    ("Combined_drought_salinity", "https://doi.org/10.3390/plants11212884"),
    ("Salinity_water_satellite", "https://doi.org/10.1007/s11119-025-10279-5"),
]

results = []
for name, doi in papers:
    print(f"Fetching {name}...", end=" ", flush=True)
    # Try Crossref first
    r = subprocess.run(
        f'curl -s "https://api.crossref.org/works/{doi}"',
        shell=True, capture_output=True, text=True, timeout=15
    )
    try:
        data = json.loads(r.stdout)
        msg = data.get("message", {})
        title = msg.get("title", [""])[0] if msg.get("title") else ""
        authors = msg.get("author", [])
        author_str = ", ".join(a.get("family","") + ", " + a.get("given","") for a in authors[:5])
        year = msg.get("published-print", msg.get("published", {})).get("date-parts", [[]])[0][0]
        journal = msg.get("container-title", [""])[0] if msg.get("container-title") else ""
        abstract = msg.get("abstract", "")
        results.append({
            "name": name, "doi": doi, "title": title,
            "authors": author_str, "year": year,
            "journal": journal, "abstract": abstract[:500]
        })
        print(f"OK ({year})")
    except Exception as e:
        results.append({"name": name, "doi": doi, "error": str(e)})
        print(f"FAILED: {e}")
    time.sleep(0.5)

with open(r"D:\RS\Thesis\thesis_research\deep_researches\advisor_papers_full_metadata.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\nDone. All metadata saved.")
for r in results:
    status = f"{r.get('year','?')} | {r.get('journal','')[:40]}" if 'title' in r else f"ERROR: {r.get('error','')}"
    print(f"  [{r['name']}] {status}")
