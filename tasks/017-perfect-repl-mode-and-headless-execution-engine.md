---
id: "017"
title: "Perfect REPL Mode and Headless Execution Engine"
type: "feature"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Feature] Perfect REPL Mode and Headless Execution Engine

## Description
Elevate Hexanna IIVX REPL and Headless CLI modes to production-grade perfection with dynamic model resolution, pipe/stdin support, structured JSON emission, correct semantic exit codes, multi-line SQL, session exporting, and full SQLite persistence.

## Acceptance Criteria
- [x] Upgrade headless execution in `src/hexanna/__main__.py`:
  - [x] Add stdin support (`-`) for `hexanna run -` and `hexanna query - <out.parquet>`.
  - [x] Add `--json` and `--quiet` flags for machine-readable pipeline consumption.
  - [x] Implement deterministic semantic exit codes (0 for success, 1 for incomplete, 2 for client error, 3 for circuit breaker).
  - [x] Enable full SQLite history persistence for headless execution sessions and generated artifacts.
  - [x] Implement hierarchical model and configuration resolution (CLI -> Env -> SQLite -> Local Config -> Fallback).
- [x] Upgrade REPL mode in `src/hexanna/tui/repl.py`:
  - [x] Add `/models` and `/model <name>` (`/switch <name>`) commands for real-time model discovery and hot-swapping.
  - [x] Add `/export [markdown|json] [path]` command to serialize active session traces.
  - [x] Add `/tables` command to discover Parquet and CSV datasets in current directory.
  - [x] Support multi-line SQL statement input terminated by semicolon `;`.
  - [x] Add tab-completion entries for new slash commands in `HexannaCompleter`.
- [x] Add unit and integration tests for headless and REPL upgrades (`tests/unit/test_cli_headless.py` and `tests/unit/test_repl_enhanced.py`).
- [x] Verify test suite passes 100% green inside Docker container.

## Context / Notes
- Target files: `src/hexanna/__main__.py`, `src/hexanna/tui/repl.py`, `tests/unit/test_cli_headless.py`, `tests/unit/test_repl_enhanced.py`
- Anti-AI-slop: zero emojis, zero em dashes, pure neutral aesthetics.
