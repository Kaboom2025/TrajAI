# Implementation Plan: Phase 3 - Assertion Library

This plan covers the implementation of the assertion engine, the trajectory formatter, and the integration of both boolean and raising assertion APIs on `AgentRunResult`.

## Phase 1: Pure Assertion Functions (`unitai.core.assertions`)
- [x] **Task: Implement Tool Call Assertions** b648280
    - [ ] Create `unitai/core/assertions.py`.
    - [ ] Implement `tool_was_called`, `tool_not_called`, `tool_call_count`.
    - [ ] Implement `tool_called_with` (exact) and `tool_called_with_partial` (subset).
    - [ ] Implement `tool_called_before` and `tool_called_immediately_before` (ignoring non-tool steps).
    - [ ] Implement `call_order` and `call_order_contains`.
- [x] **Task: Implement Output & Metadata Assertions** 7a4c8ad
    - [ ] Implement `output_equals`, `output_contains`, `output_not_contains`, `output_matches`.
    - [ ] Implement `cost_under`, `tokens_under`, `duration_under`, `llm_calls_under`.
    - [ ] Implement `succeeded`, `failed`, `error_is`.
- [x] **Task: Conductor - User Manual Verification 'Pure Assertion Functions' (Protocol in workflow.md)**

## Phase 2: Trajectory Formatter & Rich Messages
- [x] **Task: Implement TrajectoryFormatter** 2a0d175
    - [ ] Create `unitai/core/formatter.py`.
    - [ ] Implement basic formatting: numbered steps, typed markers, truncated values.
    - [ ] Implement diagnostic highlighting with arrows (`←`) and annotations.
    - [ ] Implement smart truncation logic for trajectories >20 steps.
- [x] **Task: Conductor - User Manual Verification 'Trajectory Formatter' (Protocol in workflow.md)**

## Phase 3: AgentRunResult Integration & Final Verification
- [~] **Task: Wire APIs to AgentRunResult**
    - [ ] Update `unitai/core/result.py`.
    - [ ] Implement the Boolean API (delegating to `assertions.py`).
    - [ ] Implement the Assert API (`assert_*` methods raising `UnitAIAssertionError`).
    - [ ] Implement `get_calls` and `get_call` (with descriptive `IndexError`).
- [ ] **Task: Final Verification & Test Suite**
    - [ ] Write 25+ unit tests in `tests/test_assertions.py` covering happy paths and all edge cases (missing tools, None output, etc.).
    - [ ] Run `mypy --strict` and `ruff check`.
- [ ] **Task: Conductor - User Manual Verification 'Final Verification' (Protocol in workflow.md)**
