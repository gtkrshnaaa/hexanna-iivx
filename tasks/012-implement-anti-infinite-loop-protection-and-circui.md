---
id: "012"
title: "Implement Anti-Infinite Loop Protection and Circuit Breakers for API Calls"
type: "feature"
status: "done"
created_at: "2026-11-01"
updated_at: "2026-11-01"
---

# [Feature] Implement Anti-Infinite Loop Protection and Circuit Breakers for API Calls

## Description
Protect the agent runtime, LLM gateway, and REPL against infinite loop API calls and runaway token consumption:
1. Define `InfiniteLoopDetectedException` in domain exceptions.
2. Establish API call ceilings, timeout parameters, and cyclic pattern thresholds in `ResourcePolicy`.
3. Implement loop detection circuit breaker in `HexannaRuntime` tracking total API calls, consecutive identical tool call signatures, and consecutive error thresholds.
4. Add client request timeout and bounded exponential backoff in `OpenAIGateway`.
5. Gracefully catch and display circuit breaker alerts in `HexannaREPL`.
6. Add comprehensive unit tests in `tests/unit/test_loop_protection.py`.

## Acceptance Criteria
- [x] Subtask 1: Add InfiniteLoopDetectedException in src/hexanna/domain/exceptions.py and loop parameters in ResourcePolicy and ExecutionState
- [x] Subtask 2: Implement circuit breaker and loop prevention logic in src/hexanna/harness/runtime.py
- [x] Subtask 3: Add request timeout and backoff safeguards in src/hexanna/adapters/llm/openai_client.py
- [x] Subtask 4: Update src/hexanna/tui/repl.py to handle circuit breaker triggers gracefully
- [x] Subtask 5: Author unit tests in tests/unit/test_loop_protection.py and verify test suite passes 100% green
- [x] Subtask 6: Complete task 012, commit in-stride, and sync remotes (devv and main)

## Context / Notes
- Target files: src/hexanna/domain/exceptions.py, src/hexanna/domain/policies.py, src/hexanna/domain/models.py, src/hexanna/harness/runtime.py, src/hexanna/adapters/llm/openai_client.py, src/hexanna/tui/repl.py, tests/unit/test_loop_protection.py
