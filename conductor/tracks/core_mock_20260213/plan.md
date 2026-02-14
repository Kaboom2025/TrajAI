# Implementation Plan: Phase 1 - Core Data Model & Mock Primitives

This plan covers the initial scaffolding of the UnitAI project and the implementation of its core data structures and mocking layer.

## Phase 1: Project Scaffolding [checkpoint: fa617b2]
- [x] **Task: Initialize Directory Structure** ecd84df
    - [ ] Create all package directories: `unitai`, `unitai/core`, `unitai/mock`, `unitai/runner`, `unitai/adapters`, `unitai/pytest_plugin`, `unitai/cli`, `unitai/ci`, `unitai/config`.
    - [ ] Create `__init__.py` files in each directory.
- [x] **Task: Project Configuration** 89ecf78
    - [ ] Create `pyproject.toml` with build system (Hatch), project metadata, and dependencies (core: none, dev: pytest, ruff, mypy, pre-commit).
    - [ ] Set up `.gitignore` and `.github/workflows/ci.yml`.
- [x] **Task: Conductor - User Manual Verification 'Project Scaffolding' (Protocol in workflow.md)**

## Phase 2: Core Data Models (`unitai.core`) [checkpoint: 641181f]
- [x] **Task: Implement Trajectory & TrajectoryStep Dataclasses** e9be248
    - [ ] Define `TrajectoryStep` with `step_type` validation in `__post_init__`.
    - [ ] Define `Trajectory` to hold steps and metadata.
    - [ ] Implement robust `to_dict` and `from_dict` methods for JSON serialization, handling Exception types.
- [x] **Task: Implement MockToolCall & AgentRunResult** ee8476c
    - [ ] Define `MockToolCall` dataclass with JSON serialization support.
    - [ ] Define `AgentRunResult` as a wrapper for `Trajectory` with property accessors and stubbed assertion methods.
- [x] **Task: Verify Data Models** 2f1b779
    - [ ] Write unit tests for JSON round-tripping of all models, including complex cases like nested exceptions.
    - [ ] Run `mypy --strict` and `ruff check`.
- [x] **Task: Conductor - User Manual Verification 'Core Data Models' (Protocol in workflow.md)**

## Phase 3: Mock Layer Implementation (`unitai.mock`)
- [x] **Task: Implement Response Strategies** 7f41652
    - [ ] Create `strategies.py` with `StaticStrategy`, `SequenceStrategy`, `ConditionalStrategy`, `ErrorStrategy`, and `CallableStrategy`.
    - [ ] Implement custom error types: `MockExhaustedError`, `NoMatchingConditionError`.
- [ ] **Task: Implement MockTool & MockToolkit**
    - [ ] Implement `MockTool` with `invoke` and `reset` logic.
    - [ ] Implement `MockToolkit` with `mock` registration, `as_dict` wiring, and `reset`.
- [ ] **Task: Verify Mock Layer**
    - [ ] Write unit tests for each strategy, ensuring correct error raising and exception capturing in `CallableStrategy`.
    - [ ] Verify `MockToolkit` correctly manages multiple tools and state resets.
    - [ ] Run `mypy --strict` and `ruff check`.
- [ ] **Task: Conductor - User Manual Verification 'Mock Layer Implementation' (Protocol in workflow.md)**
