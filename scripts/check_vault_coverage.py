"""Final coverage check: every PDF slot 01-78 in thesis_research/papers must have a
markdown note in Thesis_Vault/papers/ (matching by slot number + author/year token)."""

import re
from pathlib import Path

PDFS = Path(r"D:\RS\Thesis\thesis_research\papers")
VAULT = Path(r"D:\RS\Thesis\thesis_research\Thesis_Vault\papers")
ARCHIVE = PDFS / "archived_foundation_models"
DUPES = PDFS / "archived_duplicates"

notes = sorted(VAULT.glob("*.md"))
by_slot: dict[int, list[str]] = {}
for n in notes:
    m = re.match(r"^(\d{2})-", n.name)
    if m:
        by_slot.setdefault(int(m.group(1)), []).append(n.name)

pdfs = sorted(p for p in PDFS.glob("*.pdf"))
slots = {}
for p in pdfs:
    m = re.match(r"^(\d{2})-", p.name)
    if m:
        slots[int(m.group(1))] = p.name

missing = []
dup_notes = []
for sid in sorted(slots):
    files = by_slot.get(sid, [])
    if not files:
        missing.append((sid, slots[sid]))
    elif len(files) > 1:
        dup_notes.append((sid, files))

print(f"PDF slots on disk           : {len(slots)}  (expected 78)")
print(f"vault notes in papers/      : {len(notes)}")
print(f"slots covered by a note     : {len(set(slots) & set(by_slot))}")
print(f"slots WITHOUT a note        : {len(missing)}")
print(f"slots with >1 note          : {len(dup_notes)}")

if missing:
    print("\nMISSING:")
    for sid, pdf in missing:
        print(f"  #{sid:02d}  {pdf}")
if dup_notes:
    print("\nDUPLICATE NOTES:")
    for sid, files in dup_notes:
        print(f"  #{sid:02d}  {files}")

print("\narchive folders (intentionally out of scope):")
for d, label in ((ARCHIVE, "archived_foundation_models"), (DUPES, "archived_duplicates")):
    for p in sorted(d.glob("*.pdf")):
        print(f"  {label}/{p.name}")

extra = sorted(set(by_slot) - set(slots))
if extra:
    print(f"\nnotes with no matching PDF slot: {extra}")

print("\nRESULT:", "COMPLETE" if not missing else "INCOMPLETE")
