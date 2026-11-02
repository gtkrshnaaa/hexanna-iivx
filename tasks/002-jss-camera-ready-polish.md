---
id: "002"
title: "JSS Camera-Ready Polish"
type: "fix"
status: "in-progress"
created_at: "2026-10-31"
updated_at: "2026-11-02"
---

# [Fix] JSS Camera-Ready Polish

## Description
Execute camera-ready editorial polish for Journal of Systems and Software (Elsevier, Manuscript ID: JSS-2026-8841.R1): resolve BibTeX citations for Apache Arrow and Apache Parquet, correct minor typographical errors in tables, adjust secondary Y-axis labelpad for Figure 4 token invariance plot, polish mathematical notation in Section 3.1, and verify clean compilation.

## Acceptance Criteria
- [x] Subtask 1: Resolve BibTeX citations for Apache Arrow (arrow2024) and Apache Parquet (parquet2024) in paper/references.bib, 02_related_work.tex, and 04_experimental_setup.tex
- [x] Subtask 2: Audit and fix typographical errors in paper/tables/table1_performance_matrix.tex and paper/tables/table2_query_profiles.tex
- [x] Subtask 3: Adjust matplotlib secondary Y-axis labelpad in benchmarks/analysis/generate_latex_plots.py and re-render paper/figures/token_invariance_plot.pdf
- [x] Subtask 4: Polish mathematical formatting of M(D) in paper/sections/03_system_architecture.tex
- [x] Subtask 5: Clean recompile manuscript with tectonic to generate camera-ready paper/main.pdf with zero missing citations or warnings
- [x] Subtask 6: Execute test suite ./tests/scripts/sh/test.sh to confirm 100% green status
- [x] Subtask 7: Complete task, commit, and sync devv with main

## Context / Notes
- Target files: paper/references.bib, paper/sections/*.tex, paper/tables/*.tex, benchmarks/analysis/generate_latex_plots.py
- Engine: Tectonic 0.17.0
