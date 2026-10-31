---
id: "015"
title: "Configure Live API Integration Tests With Real Credentials"
type: "test"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Test] Configure Live API Integration Tests With Real Credentials

## Description
Ensure the test suite incorporates and validates live inference calls using real API keys and base URLs for both DeepSeek Flash and Gemini 3.8 Flash without leaking credentials to git.

## Acceptance Criteria
- [x] Configure `tests/scripts/sh/test.sh` with `--network host` to allow containerized test execution to access local port 60000 and external endpoints.
- [x] Implement `tests/integration/test_live_api_execution.py` dynamically loading credentials from `benchmarks/local/models.json` and environment variables.
- [x] Test live completion and tool-calling with DeepSeek Flash (`https://api.deepseek.com`).
- [x] Test live completion and tool-calling with Gemini 3.8 Flash (`http://localhost:60000/v1`).
- [x] Verify full test suite passes green in isolated Docker container.

## Context / Notes
- Target files: `tests/scripts/sh/test.sh`, `tests/integration/test_live_api_execution.py`
- Credentials source: `benchmarks/local/models.json` (gitignored), zero plaintext secrets in tracked files.
