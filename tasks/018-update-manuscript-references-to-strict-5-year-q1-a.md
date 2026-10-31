---
id: "018"
title: "Update Manuscript References to Strict 5-Year Q1 Archival Window (2021-2026)"
type: "docs"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Docs] Update Manuscript References to Strict 5-Year Q1 Archival Window (2021-2026)

## Description
Audit and replace all bibliographic citations older than 5 years (prior to 2021) with top-tier peer-reviewed publications from 2021-2026 to satisfy strict Q1 archival journal standards (Elsevier JSS).

## Acceptance Criteria
- [x] Audit all 34 entries in `paper/references.bib` and replace all pre-2021 entries with high-impact 2021-2026 peer-reviewed citations.
- [x] Update corresponding `\cite{...}` keys across `paper/sections/01_introduction.tex`, `paper/sections/02_related_work.tex`, and `paper/sections/04_experimental_setup.tex`.
- [x] Verify 100% of bibliographic references have publication years between 2021 and 2026 ($2021 \le \text{year} \le 2026$).
- [x] Recompile `paper/main.pdf` using Tectonic with zero BibTeX or typesetting warnings.
- [x] Verify test suite `./tests/scripts/sh/test.sh` passes 100% green inside Docker container.

## Context / Notes
- Target files: `paper/references.bib`, `paper/sections/*.tex`, `paper/main.pdf`
- Standard: Maximum 5-year reference window (2021-2026) for Q1 journals.
