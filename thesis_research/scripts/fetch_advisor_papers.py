"""Fetch metadata for 8 advisor-specified papers (2020-2025)."""
import subprocess, json, time, sys, re

papers = [
    # From arxiv
    ("SITSMamba", "2409.09673"),
    ("DL_for_SITS_review", "2404.03936"),
    ("SSL_Cookbook", "2304.12210"),
    ("XAI_RV_RS", "2402.13791"),
    # Non-arxiv — search by title
    ("SelfAttention_raw_optical_SITS", "Self-attention for raw optical Satellite Time Series"),
    ("XAI_agriculture_review", "systematic review explainable artificial intelligence agriculture"),
    ("combined_drought_salinity_plants", "How Do Plants Respond to Combined Drought and Salinity Stress"),
    ("salinity_water_satellite_leaf", "Salinity stress water availability inferred from satellite leaf"),
]

results = []

# First batch: arxiv papers
for name, pid in papers[:4]:
    print(f"Fetching arxiv {pid}...", file=sys.stderr)
    cmd = f'curl -s "https://export.arxiv.org/api/query?id_list={pid}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    entry = r.stdout
    # Parse XML
    import xml.etree.ElementTree as ET
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(entry)
    e = root.find('a:entry', ns)
    if e is None:
        results.append({"name": name, "error": "not found in arxiv"})
        continue
    arxiv_id = e.find('a:id', ns).text.strip().split('/abs/')[-1]
    title = e.find('a:title', ns).text.strip().replace('\n', ' ')
    authors = ', '.join(a.find('a:name', ns).text for a in e.findall('a:author', ns))
    published = e.find('a:published', ns).text[:10]
    summary = e.find('a:summary', ns).text.strip()
    results.append({
        "name": name,
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "year": published[:4],
        "abstract": summary,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "source": "arxiv"
    })
    time.sleep(1)

# Search for non-arxiv papers via Semantic Scholar with backoff
non_arxiv = papers[4:]
for name, query in non_arxiv:
    print(f"Searching SSS: {name}...", file=sys.stderr)
    for attempt in range(3):
        try:
            cmd = f'curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query={query.replace(" ", "+")}&limit=3&fields=title,authors,year,abstract,url,externalIds"'
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            data = json.loads(r.stdout)
            if data.get('data'):
                paper = data['data'][0]
                results.append({
                    "name": name,
                    "title": paper.get('title', ''),
                    "authors": ", ".join(a.get('name','') for a in paper.get('authors',[])),
                    "year": paper.get('year', ''),
                    "abstract": paper.get('abstract', '') or '',
                    "url": paper.get('url', ''),
                    "source": "semanticscholar"
                })
                break
            else:
                time.sleep(2 ** attempt)
        except Exception as e:
            time.sleep(2 ** attempt)

with open(r'D:\RS\Thesis\thesis_research\deep_researches\advisor_papers_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("Done. Metadata saved.")
for r in results:
    print(f"[{r.get('source','?')}] {r.get('name','')} | {r.get('title','NO TITLE')[:80]}")
