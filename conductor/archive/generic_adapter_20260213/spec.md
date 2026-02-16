# Track Specification: Phase 2 - Generic Adapter & Agent Execution

## Overview
This track implements the bridge between the UnitAI mock layer and actual agent code. It establishes the `BaseAdapter` interface and the `GenericAdapter`, allowing for the testing of framework-less agent code. Key features include automatic trajectory recording through tool-call aggregation, robust timeout handling via `asyncio`, and a strict mode to catch unmocked tool calls.

## Functional Requirements

### 1. Adapter Infrastructure
- **`BaseAdapter` Interface:** Define the abstract base class in `unitai.adapters.base` with methods: `can_handle`, `inject_mocks`, `execute`, and `extract_tools`.
- **`GenericAdapter` Implementation:** Implement the fallback adapter that handles arbitrary callables.

### 2. Trajectory Collection Mechanism
- **Aggregation Logic:** Trajectory collection in the `GenericAdapter` works by aggregating `MockTool.calls` from all registered tools after execution completes, sorted chronologically by timestamp.
- **LLM Step Collection:** The `MockToolkit` will maintain a separate list of recorded LLM calls (via `record_llm_call`) which are also aggregated into the final trajectory.
- **Reset-Before-Run:** Ensure `toolkit.reset()` is called at the start of every execution to prevent trajectory leakage between runs.

### 3. Execution & Timeout Handling
- **`run_generic(callable, timeout=60)`:** Executes an arbitrary callable.
- **`run_callable(fn, input, timeout=60)`:** Executes `fn(input)`. This separates input from the function to facilitate cleaner re-runs in the statistical runner.
- **Async Timeout:** Use `asyncio.wait_for` combined with `asyncio.to_thread` for synchronous agent execution.
- **Timeout Behavior:** If the timeout expires, stop waiting, raise `AgentTimeoutError`, and return an `AgentRunResult` containing the partial trajectory recorded up to that point.
- **Cleanup:** Provide a `_cleanup_callback` parameter for user-defined resource cleanup on timeout.

### 4. Strict Mode & Safety
- **`MockToolDict`:** Implement a `dict` subclass returned by `toolkit.as_dict()`.
- **`UnmockedToolError`:** If `strict=True` (default), the dict wrapper must raise this error when the agent attempts to access a tool name that has no registered mock.
- **Immutability:** Ensure the `AgentRunResult` and its underlying `Trajectory` are immutable once constructed.

### 5. Manual Metadata Hooks
- **`toolkit.record_llm_call(model, prompt_tokens, completion_tokens, cost)`:** Appends an `llm_call` TrajectoryStep to the current recording session. This allows users to capture LLM metadata during agent execution.

## Non-Functional Requirements
- **Honest Reporting:** Cost and tokens must remain at zero unless explicitly provided by the user; no heuristic estimates.
- **Zero Dependencies:** Maintain the core design constraint of using only the Python standard library.

## Acceptance Criteria
- `BaseAdapter` interface is defined and documented.
- `GenericAdapter` successfully executes a "simple agent" fixture.
- `MockToolCall` steps are automatically captured and sorted in the trajectory.
- `UnmockedToolError` is raised when calling a missing tool in strict mode.
- `AgentTimeoutError` is raised after the timeout period, returning a partial `AgentRunResult`.
- `run_callable` correctly separates input from logic and produces a valid result.
- `toolkit.record_llm_call` correctly injects LLM metadata into the final trajectory.

## Out of Scope
- Framework-specific adapters (LangGraph, CrewAI, etc.) - scheduled for Phase 5.
- Record/Replay cache (Phase 8).
