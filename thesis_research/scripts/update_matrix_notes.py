"""Update Thesis_Vault/Literature-Matrix.md with links to the newly written vault notes.

Updates, for each matrix row that now has a vault note:
  - Status column  -> "✅ Full read (2026-10-20)"  (or the frozen-cluster wording)
  - Notes column   -> append the vault-note path (repo convention: `papers/<file>.md`)
Also refreshes the coverage paragraph at the top of the file.

Idempotent: re-running does not duplicate the note path.
"""

import re
from pathlib import Path

MATRIX = Path(r"D:\RS\Thesis\thesis_research\Thesis_Vault\Literature-Matrix.md")
VAULT = Path(r"D:\RS\Thesis\thesis_research\Thesis_Vault\papers")

# matrix row id -> vault note filename
NOTES = {
    39: "39-Maes-2012-CWSI-Ground-Thermal.md",
    40: "40-Feller-2014-Drought-Heat-Physiology.md",
    41: "41-Tardieu-2018-Drought-Tolerance-Scenarios.md",
    42: "42-Gerhards-2019-TIR-WaterStress.md",
    43: "43-Wang-2021-S2-Salinity-Arid-ML.md",
    45: "45-Shen-2025-Broadacre-Resilience.md",
    46: "46-Smanov-2026-SaltTolerance-Salinity-RS.md",
    47: "47-RS-Agent-2024-TaskPlanning-DualRAG.md",
    48: "48-ThinkGeo-2025-ToolAgent-Benchmark.md",
    49: "49-Talemi-2026-Agentic-RS-Survey.md",
    50: "50-AgriWorld-2026-Verifiable-Agri-Agents.md",
    51: "51-Xiao-2026-GeoMMBench-GeoMMAgent.md",
    52: "52-BSCTR-2026-Tool-Retrieval.md",
    53: "53-RSMeM-2026-Memory-Evolution.md",
    54: "54-Earth-Agent-Pro-2026-FullChain-EO.md",
    55: "55-Feng-2025-Spatial-Intelligence-Survey.md",
    56: "56-Munir-2026-Agentic-AI-RS-Position.md",
    57: "57-ExpertsRS-2026-MultiAgent-RS.md",
    58: "58-GeoArbiter-2026-Verifiability-Grounding.md",
    59: "59-REMSA-2026-FM-Selection-Agent.md",
    61: "61-Zhang-2026-Pixel-IWU.md",
    62: "62-Khamseh-2026-IWU-Uncertainty.md",
    63: "63-Sun-2026-SelfEvolution-RS-Agents.md",
    64: "64-GeoAgentic-RAG-2026.md",
    65: "65-Tariq-2025-Edge-Agentic-Agriculture.md",
    66: "66-Musazade-2026-LLM-VLM-Plant-Stress.md",
    67: "67-CottonBot-2025-LLM-RAG-Irrigation.md",
    68: "68-Ahmad-2021-CropWaterStress-Review.md",
    73: "73-Gokul-2026-UAV-CropWaterStress-Review.md",
    74: "74-GraciaRojas-2026-ML-DL-AgriForestry-SLR.md",
    75: "75-Olawoyin-2026-Volta-ET-CWSI.md",
    78: "78-Virnodkar-2020-WaterStress-ML-Review.md",
}

# rows in the frozen agentic cluster keep their "background/frozen" wording
FROZEN = {47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 63, 64, 65, 66, 67}

missing = [f for f in NOTES.values() if not (VAULT / f).exists()]
if missing:
    raise SystemExit("ERROR - vault notes not found:\n  " + "\n  ".join(missing))

text = MATRIX.read_text(encoding="utf-8")
lines = text.split("\n")
changed = 0

for i, line in enumerate(lines):
    m = re.match(r"^\|\s*(\d{2})\s*\|", line)
    if not m:
        continue
    rid = int(m.group(1))
    if rid not in NOTES:
        continue
    cells = line.split("|")
    # cells: ['', ' 39 ', ' citation ', ' year ', ... , ' status ', ' notes ', '']
    status_i = len(cells) - 3
    notes_i = len(cells) - 2
    if status_i < 2 or notes_i < 2:
        continue
    note_ref = f"`papers/{NOTES[rid]}`"
    if note_ref not in cells[notes_i]:
        cells[notes_i] = cells[notes_i].rstrip() + "; " + note_ref
    new_status = (
        "✅ Full read (2026-10-20) — frozen-cluster background"
        if rid in FROZEN
        else "✅ Full read (2026-10-20)"
    )
    if cells[status_i].strip() != new_status:
        cells[status_i] = f" {new_status} "
    lines[i] = "|".join(cells)
    changed += 1

text = "\n".join(lines)

OLD_COV = (
    "**Second-pass full reads (2026-10-04): 60, 69, 71, 44, 11, 72, 77, 76, 12** — the entire "
    "second-tier queue is now verified; the only remaining extract-level rows are background/frozen "
    "material."
)
NEW_COV = (
    "**Second-pass full reads (2026-10-04): 60, 69, 71, 44, 11, 72, 77, 76, 12.** "
    "**Third pass (2026-10-20): the corpus is now fully noted** — the 32 rows that previously had "
    "no vault note (39–43, 45–59, 61–68, 73–75, 78) were read against the full PDF text and now have "
    "a note under `papers/`. Every row 01–78 has a vault note; the frozen agentic cluster (47–59, "
    "63–67) was also read in full but remains background/future-work only. "
    "The 7 archived foundation-model papers (Prithvi-EO-2.0, Prithvi-1.0, TerraMind, AlphaEarth, "
    "Clay v1.5, SatMAE, FARM) have notes under `papers/FM-*.md` — ablation/background only."
)
if OLD_COV in text:
    text = text.replace(OLD_COV, NEW_COV)
    print("coverage note updated")
else:
    print("WARN: coverage paragraph not matched verbatim - left unchanged")

MATRIX.write_text(text, encoding="utf-8")
print(f"rows updated: {changed}/{len(NOTES)}")
