---
id: "001"
title: "JSS Major Revision Manuscript Update"
type: "feature"
status: "in-progress"
created_at: "2026-10-31"
updated_at: "2026-11-02"
---

# [Feature] JSS Major Revision Manuscript Update

## Description
Revise manuscript for Journal of Systems and Software (Elsevier, Manuscript ID: JSS-2026-8841) addressing all six reviewer critiques: out-of-core streaming baselines (Polars, Raw DuckDB), wall-clock latency curves and NVMe spill overhead, three granular TPC-H query profiles (A, B, C), empirical proof of O(1) prompt wire size invariance, ProfileSketcher ablation and self-healing error taxonomy, and bibliography expansion with clean MB/GB rescaled vector plots.

## Acceptance Criteria
- [x] Task 1: Complete and commit paper/references.bib with all 33 peer-reviewed citations
- [x] Task 2: Revise paper/sections/01_introduction.tex with RQ1-RQ4 and updated baseline overview
- [x] Task 3: Revise paper/sections/02_related_work.tex integrating all 33 citations across 4 thematic subsections
- [x] Task 4: Revise paper/sections/03_system_architecture.tex with formal mathematical proof of O(1) wire invariance and self-healing dispatch loop
- [x] Task 5: Revise paper/sections/04_experimental_setup.tex with hardware platform, 3 TPC-H query profiles (A/B/C), and evaluation metrics
- [x] Task 6: Revise paper/sections/05_results_and_discussion.tex with rescaled Fig 1 (MB), Fig 2 (latency), Fig 3 (wire invariance), Table 1, Table 2, Table 3, and discussion of RQ1-RQ4
- [x] Task 7: Revise paper/sections/06_conclusion.tex with synthesis, limitations, and future work
- [x] Task 8: Verify paper/main.tex compiles cleanly with tectonic to produce paper/main.pdf
- [x] Task 9: Verify complete test suite `./tests/scripts/sh/test.sh` passes 100% green
- [x] Task 10: Sync devv branch with main branch and push to remotes

## Context / Notes
- Target files: paper/references.bib, paper/sections/*.tex, paper/main.tex
- Engine: Tectonic 0.17.0
