---
id: "008"
title: "Update Author Academic Email in Manuscript"
type: "fix"
status: "done"
created_at: "2026-10-31"
updated_at: "2026-10-31"
---

# [Fix] Update Author Academic Email in Manuscript

## Description
Update the first author's institutional student email address in the camera-ready research manuscript `paper/main.tex` to `student.gilangtejakrishna26@mti.utdi.ac.id` for official academic and university affiliation tracking, without altering GitHub profile credentials.

## Acceptance Criteria
- [x] Subtask 1: Update author email in paper/main.tex to student.gilangtejakrishna26@mti.utdi.ac.id
- [x] Subtask 2: Recompile camera-ready manuscript with tectonic to generate paper/main.pdf
- [x] Subtask 3: Verify text extraction from paper/main.pdf shows academic student email
- [x] Subtask 4: Verify test suite ./tests/scripts/sh/test.sh passes 100% green
- [x] Subtask 5: Complete task 008, commit in-stride, and sync git remotes (devv and main)

## Context / Notes
- Target file: paper/main.tex, paper/main.pdf
- Academic email: student.gilangtejakrishna26@mti.utdi.ac.id
- Do not modify git config or GitHub credentials
