---
id: "013"
title: "Configure Air-Gapped Local Benchmark Environments"
type: "chore"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Chore] Configure Air-Gapped Local Benchmark Environments

## Description
Configure local air-gapped environment profiles for running real empirical benchmarks against DeepSeek V4.1 Flash and Gemini 3.8 Flash without publishing keys or local endpoints to Git.

## Acceptance Criteria
- [x] Subtask 1: Harden .gitignore to exclude .env, .env.*, *.local, and benchmarks/local/
- [x] Subtask 2: Provide an unversioned air-gapped local environment setup and benchmark invocation helper
- [x] Subtask 3: Verify git status confirms zero tracked credentials or secrets
- [x] Subtask 4: Complete task 013, commit in-stride, and sync remotes (devv and main)

## Context / Notes
- Strict rule: NEVER stage or commit any API keys, tokens, or private base URLs to git.
