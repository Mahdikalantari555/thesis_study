"""Extract first pages of all New_papers PDFs for literature intake."""
import json
import os
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(r"D:\RS\Thesis\New_papers")
OUT = Path(r"D:\RS\Thesis\thesis_research\deep_researches\new_papers_2026-09-10_extract")
OUT.mkdir(parents=True, exist_ok=True)

PAGES = 4  # title + abstract + intro start


def extract_one(path: Path) -> dict:
    reader = PdfReader(str(path))
    n = len(reader.pages)
    parts = []
    for i in range(min(PAGES, n)):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception as e:
            t = f"[extract error page {i}: {e}]"
        parts.append(f"\n===== PAGE {i+1} =====\n{t}")
    meta = {}
    if reader.metadata:
        for k, v in reader.metadata.items():
            try:
                meta[str(k)] = str(v)[:300]
            except Exception:
                pass
    return {
        "file": path.name,
        "category": path.parent.name,
        "relpath": str(path),
        "page_count": n,
        "metadata": meta,
        "text": "".join(parts)[:12000],
    }


def main():
    pdfs = sorted(ROOT.rglob("*.pdf"))
    results = []
    index_lines = []
    for p in pdfs:
        print(f"Extracting: {p.parent.name}/{p.name} ...", flush=True)
        try:
            item = extract_one(p)
        except Exception as e:
            item = {"file": p.name, "category": p.parent.name, "error": str(e), "text": ""}
        results.append(item)
        out_md = OUT / f"{item['category']}__{p.stem}.md"
        md = f"# {p.name}\n\n- Category: {item.get('category')}\n- Pages: {item.get('page_count')}\n- Path: {p}\n\n## Metadata\n\n```json\n{json.dumps(item.get('metadata', {}), indent=2, ensure_ascii=False)}\n```\n\n## First pages\n\n{item.get('text','')}\n"
        out_md.write_text(md, encoding="utf-8")
        # first non-empty line heuristic for title
        first = ""
        for line in item.get("text", "").splitlines():
            s = line.strip()
            if len(s) > 15 and not s.startswith("http"):
                first = s
                break
        index_lines.append(f"| {item.get('category')} | {p.name} | {item.get('page_count')} | {first[:120]} |")

    (OUT / "_index.md").write_text(
        "# New_papers extraction index\n\n| Category | File | Pages | First text line |\n|---|---|---|---|\n"
        + "\n".join(index_lines) + "\n",
        encoding="utf-8",
    )
    print(f"Done. {len(results)} papers -> {OUT}")


if __name__ == "__main__":
    main()
