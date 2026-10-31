---
id: "009"
title: "Address Editorial Audit Compliance for Elsevier Submission"
type: "fix"
status: "done"
created_at: "2026-10-31"
updated_at: "2026-10-31"
---

# [Fix] Address Editorial Audit Compliance for Elsevier Submission

## Description
Resolve critical editorial and metadata compliance issues identified in formal desk review:
1. Delete premature acceptance claim ("Accepted for Publication in Journal of Systems and Software (Elsevier)") from Page 1 of `paper/main.tex`.
2. Remove imitation journal running header ("Journal of Systems and Software") across Pages 2–16, leaving it empty or using short running title.
3. Verify and maintain standardized "SF-10 (10 GB)" notation in Table 2 (`paper/tables/table1_performance_matrix.tex`).
4. Align publication notes in `README.md` to "Preprint under review".
5. Clean auxiliary build files and recompile camera-ready manuscript `paper/main.pdf` using Tectonic.
6. Verify automated test suite passes 100% green.

## Acceptance Criteria
- [x] Subtask 1: Delete premature acceptance claim from Page 1 in paper/main.tex
- [x] Subtask 2: Remove "Journal of Systems and Software" running headers across Pages 2–16 in paper/main.tex
- [x] Subtask 3: Ensure Table 2 (table1_performance_matrix.tex) uses standardized SF-10 (10 GB) notation
- [x] Subtask 4: Update README.md publication status to preprint under review
- [x] Subtask 5: Clean auxiliary files and recompile camera-ready main.pdf via tectonic
- [x] Subtask 6: Verify automated test suite ./tests/scripts/sh/test.sh passes 100% green
- [x] Subtask 7: Complete task 009, commit in-stride, and sync remotes (devv and main)

## Context / Notes
- Target files: paper/main.tex, paper/tables/table1_performance_matrix.tex, README.md, paper/main.pdf
- Engine: Tectonic 0.17.0
