# Track Specification: Phase 1 - Core Data Model & Mock Primitives

## Overview
This track focuses on building the foundational data structures and the mock tool system for UnitAI. It establishes the core objects that represent agent trajectories and the primary API for developer-facing mocks. This phase is critical as it defines the data model that all subsequent features (assertions, adapters, runners) will operate on.

## Functional Requirements

### 1. Project Scaffolding
- Initialize the full directory structure as defined in the project specification.
- Create empty `__init__.py` files for all planned modules (`core`, `mock`, `runner`, `adapters`, `pytest_plugin`, `cli`, `ci`, `config`).
- Configure `pyproject.toml` with package metadata, build configuration (using Hatch), and dev dependencies (`pytest`, `ruff`, `mypy`, `pre-commit`).
- Set up a basic GitHub Actions workflow for linting, type checking, and testing.

### 2. Core Data Models (`unitai.core`)
- **`Trajectory` & `TrajectoryStep`:**
    - Implement as Python `dataclasses` (no external dependencies).
    - `TrajectoryStep` types: `tool_call`, `llm_call`, `state_change`.
    - Support for recording timestamps, tool arguments, results, and LLM metadata (tokens/cost).
    - Implement `to_dict()` and `from_dict()` methods for JSON serialization/deserialization.
    - Handle Exception serialization in `to_dict()` by storing type, message, and module.
    - Use `__post_init__` for basic validation (e.g., valid `step_type`).
- **`MockToolCall`:**
    - Dataclass representing a single invocation of a mock tool.
    - Fields: `args: dict`, `result: Any`, `error: Exception | None`, `timestamp: float`.
    - Implements JSON serialization logic identical to `TrajectoryStep`.
- **`AgentRunResult`:**
    - A container class wrapping a `Trajectory`.
    - Exposes properties: `output`, `total_cost`, `duration`, `error`, `succeeded`, `failed`.
    - Assertion methods will be stubbed (raising `NotImplementedError`) in this phase.

### 3. Mock Layer (`unitai.mock`)
- **Response Strategies:**
    - `StaticStrategy`: Returns a fixed value.
    - `SequenceStrategy`: Returns values in order; raises `MockExhaustedError` with a diagnostic message upon depletion.
    - `ConditionalStrategy`: Evaluates lambdas; raises `NoMatchingConditionError` with provided arguments if no match is found.
    - `ErrorStrategy`: Raises a specified exception.
    - `CallableStrategy`: Delegates to a user-provided function; catches and records exceptions in the trajectory before re-raising.
- **`MockTool`:**
    - Tracks its own name, strategy, and call history (`list[MockToolCall]`).
    - `invoke(args)`: Executes strategy, records the call, and returns the result.
    - `reset()`: Clears the call history for this specific tool.
- **`MockToolkit`:**
    - Primary user-facing API to register and manage `MockTool` instances.
    - `mock()`: Registry for mock tools with various strategies.
    - `as_dict()`: Returns a mapping of tool names to callables for manual wiring.
    - `reset()`: Clears all recorded calls from all registered tools; the mock definitions themselves stay registered.

## Non-Functional Requirements
- **Zero Runtime Dependencies:** The core library must not require any external packages.
- **Strict Typing:** All code must pass `mypy` strict mode.
- **Serialization Stability:** Objects must round-trip through JSON perfectly for future caching and snapshots.

## Acceptance Criteria
- Full package directory structure created with `__init__.py` files.
- `Trajectory`, `TrajectoryStep`, and `MockToolCall` correctly handle JSON serialization including exceptions.
- `MockToolkit` can register 5+ tools with different strategies and record their calls accurately.
- `MockToolkit.reset()` and `MockTool.reset()` correctly clear histories.
- `SequenceStrategy` raises `MockExhaustedError` on depletion.
- `ConditionalStrategy` raises `NoMatchingConditionError` when no criteria are met.
- `CallableStrategy` correctly captures user-function errors in the tool call history.
- All code passes `ruff` linting and `mypy` type checking.
- At least 15 unit tests covering data models and mock strategies pass.

## Out of Scope
- Framework adapters (LangGraph, CrewAI, etc.).
- The assertion library logic (methods will be stubbed).
- The statistical runner and record/replay cache.
- CLI implementation.
