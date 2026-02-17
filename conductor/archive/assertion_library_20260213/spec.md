# Track Specification: Phase 3 - Assertion Library

## Overview
This track implements the comprehensive assertion engine for UnitAI. It provides developers with an expressive, deterministic API to verify agent trajectories. The library uses a dual-API design: boolean methods for logic/composition and `assert_*` methods for rich, descriptive failure reporting. All assertion logic is decoupled into pure functions for reuse and testability.

## Functional Requirements

### 1. Pure Assertion Logic (`unitai.core.assertions`)
- Implement all assertion logic as pure functions that take a `Trajectory` and return a `tuple[bool, str]`, where the string is a descriptive failure message.
- **Tool Call Assertions:**
    - `tool_was_called(name)`
    - `tool_not_called(name)`
    - `tool_call_count(name, expected_count)`
    - `tool_called_with(name, **kwargs)` (Exact argument match)
    - `tool_called_with_partial(name, **kwargs)` (Subset argument match)
    - `tool_called_before(first, second)` (Ordering check)
    - `tool_called_immediately_before(first, second)` (Sequential ordering - ignores non-tool steps)
    - `call_order()` (Returns full tool sequence)
    - `call_order_contains(subsequence)` (Subsequence match)
- **Output Assertions:**
    - `output_equals(text)` (Strict `==` comparison, no whitespace trimming)
    - `output_contains(text)`
    - `output_not_contains(text)`
    - `output_matches(pattern)` (Regex)
- **Metadata Assertions:**
    - `cost_under(limit)`, `tokens_under(limit)`, `duration_under(limit)`, `llm_calls_under(limit)`.
- **Error Assertions:**
    - `succeeded()`, `failed()`, `error_is(exception_type)`.

### 2. Dual-API on `AgentRunResult`
- **Boolean API:** Methods like `result.tool_was_called("search")` return `True/False`.
- **Assert API:** Methods like `result.assert_tool_was_called("search")` raise `UnitAIAssertionError(rich_message)` on failure.
- Ensure the `assert_*` methods utilize the same underlying pure functions to avoid logic duplication.

### 3. Trajectory Formatter & Rich Failure Messages
- Create a `TrajectoryFormatter` to generate human-readable trajectory summaries for inclusion in failure messages.
- **Visual Style:**
    - Numbered steps (1, 2, 3...).
    - Text markers for step types: `[tool]`, `[llm]`, `[state]`.
    - Truncated values: Cap tool arguments and results at ~100 characters with `...`.
- **Diagnostic Features:**
    - **Highlighting:** Use arrows (`←`) and annotations to point directly to the steps that caused the failure (e.g., "← called second").
    - **Smart Truncation:** For trajectories >20 steps, truncate irrelevant segments while preserving the failing steps and their immediate context.

### 4. Trajectory Query API
- Implement `result.get_calls(name)` and `result.get_call(name, n)` to allow users to manually inspect specific steps for custom assertions.

## Non-Functional Requirements
- **Determinism:** All assertions must be 100% deterministic based on the provided trajectory.
- **Zero Dependencies:** Use only Python standard library (regex, etc.).
- **Terminal Friendly:** Use plain text markers for visual distinction to ensure compatibility with all CI environments.

## Acceptance Criteria
- All 17+ assertion methods are implemented and return correct booleans.
- Corresponding `assert_*` methods raise `UnitAIAssertionError` with rich messages.
- Failure messages include a numbered, typed, and annotated trajectory summary.
- Smart truncation correctly collapses long trajectories while keeping relevant context.
- `tool_called_with` correctly distinguishes between exact and partial matches.
- `output_equals` performs a strict `==` check (no trimming or case-insensitivity).
- **Edge Case Robustness:**
    - Ordering checks return `False` (not error) if one or both tools are missing.
    - `tool_called_immediately_before` ignores `llm_call` and `state_change` steps.
    - Subsequence matching handles repeated tool names correctly.
    - Output checks return `False` safely if `final_output` is `None`.
    - `get_call` raises a descriptive `IndexError` on out-of-bounds requests.
- All code passes `ruff` linting and `mypy --strict`.
- 25+ new unit tests cover all assertion logic and edge cases.

## Out of Scope
- Statistical runner logic (Phase 4).
- LLM-as-judge or fuzzy string matching (v0.2).
