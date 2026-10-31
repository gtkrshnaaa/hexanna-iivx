---
id: "007"
title: "Refine Manuscript Title to Professional Q1 Archival Standard"
type: "style"
status: "done"
created_at: "2026-10-31"
updated_at: "2026-10-31"
---

# [Style] Refine Manuscript Title to Professional Q1 Archival Standard

## Description
Refine manuscript title to top-tier Q1 archival standard by omitting the software project codename from the paper title ("A Deterministic, Metadata-Driven Agent Harness for Out-of-Core Local Data Engineering") and introducing Hexanna IIVX as the concrete system implementation within the abstract and text.

## Acceptance Criteria
- [x] Subtask 1: Remove project codename from paper title in paper/main.tex (A Deterministic, Metadata-Driven Agent Harness for Out-of-Core Local Data Engineering), update pdftitle and running header
- [x] Subtask 2: Update publication citation title in README.md
- [x] Subtask 3: Recompile camera-ready manuscript with tectonic to generate paper/main.pdf
- [x] Subtask 4: Verify test suite ./tests/scripts/sh/test.sh passes 100% green
- [x] Subtask 5: Complete task 007, commit in-stride, and sync git remotes (devv and main)

## Context / Notes
- Target files: paper/main.tex, README.md
- Engine: Tectonic 0.17.0
