---
id: "005"
title: "Update Hardware Storage Specification and Author Affiliation"
type: "fix"
status: "done"
created_at: "2026-10-31"
updated_at: "2026-10-31"
---

# [Fix] Update Hardware Storage Specification and Author Affiliation

## Description
Correct hardware specification in Section 4.1 from 1 TB to 256 GB PCIe 4.0 NVMe SSD and update formal author credentials and institutional affiliation to I Putu Gede Gilang Teja Krishna, S.Kom. (Universitas Teknologi Digital Indonesia).

## Acceptance Criteria
- [x] Subtask 1: Correct storage specification in paper/sections/04_experimental_setup.tex from 1 TB to 256 GB NVMe SSD
- [x] Subtask 2: Update author block in paper/main.tex and BibTeX citation in README.md to I Putu Gede Gilang Teja Krishna, S.Kom. with Universitas Teknologi Digital Indonesia (UTDI) affiliation
- [x] Subtask 3: Recompile camera-ready manuscript with tectonic to generate paper/main.pdf
- [x] Subtask 4: Verify test suite ./tests/scripts/sh/test.sh passes 100% green
- [x] Subtask 5: Complete task 005, commit in-stride, and sync git remotes (devv and main)

## Context / Notes
- Target files: paper/sections/04_experimental_setup.tex, paper/main.tex, README.md
- Engine: Tectonic 0.17.0
