"""Extract full text of vault-missing PDFs to .txt for cheap agent reading.

Usage: python extract_vault_text.py
Output: C:\\Users\\ASUS\\AppData\\Local\\Temp\\opencode\\pdf_text\\<NN>-<stem>.txt
"""

from pathlib import Path

from pypdf import PdfReader

PAPERS = Path(r"D:\RS\Thesis\thesis_research\papers")
OUT = Path(r"C:\Users\ASUS\AppData\Local\Temp\opencode\pdf_text")
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "39-Maes-2012-CWSI-ground-thermal.pdf",
    "40-Feller-2014-drought-heat-physiology.pdf",
    "41-Tardieu-2018-drought-probabilistic.pdf",
    "42-Gerhards-2019-TIR-water-stress.pdf",
    "43-Wang-2021-S2-Salinity-Arid-ML.pdf",
    "45-Shen-2025-broadacre-resilience.pdf",
    "46-Smanov-2026-salt-tolerance-salinity-RS.pdf",
    "47-RS-Agent-2024-TaskPlanning-DualRAG.pdf",
    "48-ThinkGeo-2025-ToolAgent-Benchmark.pdf",
    "49-Talemi-2026-Agentic-RS-Survey.pdf",
    "50-AgriWorld-2026-Verifiable-Agri-Agents.pdf",
    "51-Xiao-2026-GeoMMBench-GeoMMAgent.pdf",
    "52-BSCTR-2026-Tool-Retrieval.pdf",
    "53-RSMeM-2026-Memory-Evolution.pdf",
    "54-Earth-Agent-Pro-2026-FullChain-EO.pdf",
    "55-Feng-2025-Spatial-Intelligence-Survey.pdf",
    "56-Munir-2026-Agentic-AI-RS-Position.pdf",
    "57-ExpertsRS-2026-MultiAgent-RS.pdf",
    "58-GeoArbiter-2026-Verifiability-Grounding.pdf",
    "59-REMSA-2026-FM-Selection-Agent.pdf",
    "61-Zhang-2026-Pixel-IWU.pdf",
    "62-Khamseh-2026-IWU-Uncertainty.pdf",
    "63-Sun-2026-SelfEvolution-RS-Agents.pdf",
    "64-GeoAgentic-RAG-2026.pdf",
    "65-Tariq-2025-Edge-Agentic-Agriculture.pdf",
    "66-Musazade-2026-LLM-VLM-Plant-Stress.pdf",
    "67-CottonBot-2025-LLM-RAG-Irrigation.pdf",
    "68-Ahmad-2021-CropWaterStress-Review.pdf",
    "73-Gokul-2026-UAV-CropWaterStress-Review.pdf",
    "74-GraciaRojas-2026-ML-DL-AgriForestry-SLR.pdf",
    "75-Olawoyin-2026-Volta-ET-CWSI.pdf",
    "78-Virnodkar-2020-WaterStress-ML-Review.pdf",
]

for name in TARGETS:
    src = PAPERS / name
    dst = OUT / (src.stem + ".txt")
    if not src.exists():
        print(f"MISSING PDF: {name}")
        continue
    try:
        reader = PdfReader(str(src))
        chunks = []
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
            except Exception as e:  # noqa: BLE001
                txt = f"[extract error page {i}: {e}]"
            chunks.append(f"\n===== PAGE {i + 1} =====\n{txt}")
        body = "".join(chunks)
        dst.write_text(body, encoding="utf-8", errors="replace")
        print(f"OK {name} -> {dst.name} ({len(reader.pages)}p, {len(body)} chars)")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name}: {e}")
