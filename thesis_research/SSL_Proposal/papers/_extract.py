import glob, os, sys, warnings
import logging
logging.getLogger("pypdf").setLevel(logging.CRITICAL)
from pypdf import PdfReader

src = r"D:/RS/Thesis/thesis_research/SSL_Proposal/papers"
out = os.path.join(src, "_txt")
pdfs = sorted(glob.glob(os.path.join(src, "*.pdf")))
batch = pdfs[27:54]
print(f"Total PDFs: {len(pdfs)}, my batch: {len(batch)}", file=sys.stderr)
for p in batch:
    base = os.path.splitext(os.path.basename(p))[0]
    outp = os.path.join(out, base + ".txt")
    try:
        r = PdfReader(p)
        txt = []
        for pg in r.pages:
            try:
                txt.append(pg.extract_text() or "")
            except Exception as e:
                txt.append(f"\n[PAGE ERROR: {e}]\n")
        t = "\n\n=== PAGE BREAK ===\n\n".join(txt)
        with open(outp, "w", encoding="utf-8") as f:
            f.write(t)
        print(f"OK {len(t):>8} chars  {base}", file=sys.stderr)
    except Exception as e:
        print(f"FAIL {base}: {e}", file=sys.stderr)
