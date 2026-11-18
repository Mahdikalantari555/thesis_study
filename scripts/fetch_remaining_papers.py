"""Fetch the 4 non-arxiv advisor papers via various APIs."""
import subprocess, json, time, sys

papers = [
    # (name, search_query, api)
    ("SelfAttention_raw_SITS_Russwurm", "Self-attention+raw+optical+Satellite+Time+Series+Russwurm", "crossref"),
    ("XAI_agriculture_Ahmed", "systematic+review+explainable+artificial+intelligence+agriculture+Ahmed", "crossref"),
    ("Combined_drought_salinity_Angon", "combined+drought+salinity+stress+plants+response+Angon", "crossref"),
    ("Salinity_water_satellite_Paciolla", "salinity+stress+water+availability+satellite+leaf+Paciolla", "crossref"),
]

results = []
for name, query, api in papers:
    print(f"Searching: {name}...", file=sys.stderr)
    if api == "crossref":
        url = f"https://api.crossref.org/works?query.title={query}&rows=3&mailto=test@example.com"
    else:
        continue
    try:
        r = subprocess.run(f'curl -s "{url}"', shell=True, capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout)
        items = data.get("message", {}).get("items", [])
        if items:
            item = items[0]
            title = item.get("title", [""])[0]
            authors = ", ".join(a.get("family","") + " " + a.get("given","") for a in item.get("author",[])[:3])
            year = item.get("published-print", item.get("published", {})).get("date-parts", [[]])[0][0]
            results.append({"name": name, "title": title, "authors": authors, "year": year})
            print(f"  FOUND: {title[:80]}", file=sys.stderr)
        else:
            results.append({"name": name, "error": "no results from crossref"})
            print(f"  NOT FOUND", file=sys.stderr)
    except Exception as e:
        results.append({"name": name, "error": str(e)})
    time.sleep(1)

with open(r"D:\RS\Thesis\thesis_research\deep_researches\advisor_papers_search.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("Done.")
for r in results:
    print(r)
