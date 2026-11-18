# AGENTS.md — thesis_research

Multi-subject MSc thesis research notebook (Shahid Beheshti University, Remote Sensing & Geoinformatics). Subjects are self-contained top-level packages; shared literature/data/memory live at root.

## Subjects (top-level packages)

- `proposal/` — original proposal skeleton (Persian).
- `new proposal/` — crop-stress in sugarcane SITS package (Persian/English); see its `README.md`.
- `SSL_Proposal/` — new subject, scaffolded (README only); populate like `new proposal/`.
- Root `lit_review/`, `papers/`, `Thesis_Vault/`, `memory/` are shared across subjects.

## Shared layout

- `lit_review/` — literature review (English): `00_thesis_literature_review.md` (main), `phase1_stress_detection_methods.md`, `00_paper_links.md`, `papers_not_downloaded.md`.
- `papers/` — downloaded PDFs, LOCAL ONLY, gitignored (`*.pdf`). Never commit.
- `Thesis_Vault/` — Obsidian vault: 78 paper notes, `Literature-Matrix.md`, thesis design. Don't edit `.obsidian/` config.
- `deep_researches/` — extracts, advisor analysis, search logs.
- `memory/` — dated findings `YYYY-MM-DD-slug.md`. Read latest before a task; append after.
- `scripts/` — Python/GEE utilities; deps in `requirements.txt`.
- `data/`, `notebooks/`, `outputs/` — large artifacts (mostly gitignored).

## Rules

- Branch `main`; conventional commits; push after meaningful change; no force-push; no new branches without request.
- Never commit PDFs/binaries; share papers via `lit_review/00_paper_links.md`.
- Citations must be real and verifiable; prefer 2021-2026 Q1 journals; APA 7th; mark unverifiable `[UNVERIFIED]` and don't use in formal proposals. Never invent.
- Memory is shared state: read before acting, write after.
- Language: formal proposal docs Persian (Farsi) with English terms; lit review English; memory English. Agent responses: match the user's language — reply in Persian when the user writes in Persian, otherwise English; use only English or Persian, never any other language.
- Justify methodological decisions with literature; table captions + sources; describe figures; be quantitative.
- Don't modify outside repo; don't delete/overwrite without backup; no credentials.

## Gotchas

- Paths with spaces (`new proposal/`) must be quoted in PowerShell.
- `.kilo/worktrees/` are agent sandboxes; edit root unless explicitly working in a worktree.
- `download_results.json` is ignored.
- Frozen content: vault rows 47-59 and 63-67 (agentic cluster) = future work only; foundation-model PDFs are archived with no notes. Don't expand.
- Zotero scripts need env `ZOTERO_API_KEY` / `ZOTERO_USER_ID` (user `mahdi555`) in the `geo` env.
- No test suite configured; verification is doc review + script runs.

## Pre-commit checklist

- [ ] citations real/verifiable
- [ ] no PDFs staged
- [ ] memory log updated
- [ ] conventional commit message
- [ ] pushed to `main`
