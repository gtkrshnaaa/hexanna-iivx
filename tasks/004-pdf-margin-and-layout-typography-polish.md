---
id: "004"
title: "PDF Margin and Layout Typography Polish"
type: "style"
status: "done"
created_at: "2026-10-31"
updated_at: "2026-10-31"
---

# [Style] PDF Margin and Layout Typography Polish

## Description
Polish PDF margins, page geometry, typography, and float layouts in paper/main.tex and sections to produce a clean, balanced, and aesthetically beautiful camera-ready manuscript.

## Acceptance Criteria
- [x] Subtask 1: Refactor paper/main.tex with modern geometry, typography packages (microtype, lmodern), float controls, clean fancyhdr headers/footers, and caption formatting
- [x] Subtask 2: Optimize float placements across sections and tables (table instead of table*, [htbp], scaled TikZ architecture diagram)
- [x] Subtask 3: Refine section titles and listing aesthetics in paper/main.tex and section files
- [x] Subtask 4: Compile camera-ready manuscript with tectonic and verify page flow, float balance, and zero warnings
- [x] Subtask 5: Verify test suite ./tests/scripts/sh/test.sh passes 100% green
- [x] Subtask 6: Mark task done, commit with in-stride micro-commits, and sync git remotes (devv and main)

## Context / Notes
- Target files: paper/main.tex, paper/sections/*.tex, paper/tables/*.tex
- Engine: Tectonic 0.17.0
