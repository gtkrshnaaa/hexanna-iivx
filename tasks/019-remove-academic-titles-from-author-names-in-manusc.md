---
id: "019"
title: "Remove Academic Titles From Author Names in Manuscript"
type: "docs"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Docs] Remove Academic Titles From Author Names in Manuscript

## Description
Remove academic titles and degrees (S.Kom., S.Si., M.Kom., Ph.D.) from author names in `paper/main.tex` and related manuscript documents according to international academic journal publication standards (IEEE/Elsevier).

## Acceptance Criteria
- [x] Remove academic degrees from the author block in `paper/main.tex` (`I Putu Gede Gilang Teja Krishna` and `Sri Redjeki`).
- [x] Update `paper/RESPONSE_TO_REVIEWERS.md` author listing to match without academic titles.
- [x] Recompile `paper/main.pdf` using Tectonic with zero errors and verify clean author display.
- [x] Verify test suite `./tests/scripts/sh/test.sh` passes 100% green inside Docker container.

## Context / Notes
- Target files: `paper/main.tex`, `paper/RESPONSE_TO_REVIEWERS.md`, `paper/main.pdf`
- Standards: International academic indexing (IEEE, Elsevier, ACM) requires standard legal names without academic degrees or honorific titles.
