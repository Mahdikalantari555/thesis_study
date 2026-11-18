"""QA check for Thesis_Vault/papers notes: structure, footer, placeholder leakage."""

import re
import sys
from pathlib import Path

VAULT = Path(r"D:\RS\Thesis\thesis_research\Thesis_Vault\papers")

REQUIRED_ANY = [
    ("full-citation", r"\*\*Full Citation:\*\*"),
    ("status", r"\*\*Status:\*\*"),
    ("what-it-does", r"##\s*What It Does"),
    ("relevance", r"##\s*Relevance to Thesis"),
    ("takeaway", r"##\s*Key Takeaway"),
    ("footer", r"\*Linked from: \[\[Literature-Matrix\]\]\*"),
]
VERDICT_RE = re.compile(
    r"\*\*Optional\*\*|\*\*Critical\*\*|\*\*High\*\*|\*\*Medium-High\*\*|\*\*Medium\*\*|"
    r"\*\*Low-Medium\*\*|\*\*Low\*\*"
)
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\bTBD\b|XXX|\bLorem\b|\[INSERT|<placeholder", re.I)

# Notes written in the 2026-10-20 completion pass (must match the new house style).
# Everything else predates the pass and uses a looser legacy heading style.
NEW_PASS_IDS = {
    39, 40, 41, 42, 43, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
    61, 62, 63, 64, 65, 66, 67, 68, 73, 74, 75, 78,
}


def is_new_pass(path: Path) -> bool:
    if path.name.startswith("FM-"):
        return True
    m = re.match(r"^(\d{2})-", path.name)
    return bool(m) and int(m.group(1)) in NEW_PASS_IDS


problems = []
rows = []
legacy_count = 0
for f in sorted(VAULT.glob("*.md")):
    text = f.read_text(encoding="utf-8", errors="replace")
    issues = []
    for name, pat in REQUIRED_ANY:
        if not re.search(pat, text):
            issues.append(f"missing {name}")
    if not VERDICT_RE.search(text):
        issues.append("no relevance verdict")
    ph = PLACEHOLDER_RE.findall(text)
    if ph:
        issues.append(f"placeholder tokens: {set(ph)}")
    if not text.lstrip().startswith("#"):
        issues.append("no H1 title")
    if is_new_pass(f):
        if issues:
            problems.append((f.name, issues))
        rows.append((f.name, f.stat().st_size, issues))
    else:
        legacy_count += 1

print("2026-10-20 completion pass — structural QA")
print(f"{'file':<52} {'bytes':>7}  status")
print("-" * 80)
for name, size, issues in rows:
    status = "OK" if not issues else "; ".join(issues)
    print(f"{name:<52} {size:>7}  {status}")

print("-" * 80)
print(f"new-pass notes checked: {len(rows)}   failing: {len(problems)}")
print(f"pre-existing (legacy style) notes skipped: {legacy_count}")
if problems:
    print("\nPROBLEMS:")
    for name, issues in problems:
        print(f"  {name}: {issues}")
    sys.exit(1)
print("\nAll new-pass notes pass structural QA.")
