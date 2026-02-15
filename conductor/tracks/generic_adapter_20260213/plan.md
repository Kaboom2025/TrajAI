# Implementation Plan: Phase 2 - Generic Adapter & Agent Execution

This plan covers the implementation of the `BaseAdapter` interface, the `GenericAdapter` for framework-less agent code, and the `run_generic` / `run_callable` entry points in `MockToolkit`.

## Phase 1: Adapter Infrastructure [checkpoint: 7d69471]
- [x] **Task: Define BaseAdapter Interface** 74c7f84
    - [ ] Create `unitai/adapters/base.py`.
    - [ ] Define `BaseAdapter` abstract base class with `can_handle`, `inject_mocks`, `execute`, and `extract_tools` methods.
- [x] **Task: Implement GenericAdapter** 1ca7a78
    - [ ] Create `unitai/adapters/generic.py`.
    - [ ] Implement `GenericAdapter.execute` to run a callable, aggregate `MockTool.calls` and toolkit LLM calls, and return a `Trajectory`.
- [x] **Task: Conductor - User Manual Verification 'Adapter Infrastructure' (Protocol in workflow.md)**

## Phase 2: MockToolkit Integration & Execution Logic
- [x] **Task: Implement MockToolDict & record_llm_call** 84a1002
    - [ ] Implement `MockToolDict` in `unitai/mock/toolkit.py` with `strict` mode logic.
    - [ ] Add `_recorded_llm_calls` and `record_llm_call` to `MockToolkit`.
- [x] **Task: Implement run_generic & run_callable** f8e863d
    - [ ] Implement `run_generic` using `asyncio.wait_for` and `asyncio.to_thread` for timeout handling.
    - [ ] Implement `run_callable` as a wrapper around `run_generic`.
    - [ ] Ensure `AgentTimeoutError` returns partial trajectories.
- [ ] **Task: Conductor - User Manual Verification 'Execution Logic' (Protocol in workflow.md)**

## Phase 3: Simple Agent Fixture & Final Verification
- [ ] **Task: Create Simple Agent Fixture**
    - [ ] Create `tests/fixtures/simple_agent.py` containing a basic tool-calling agent.
- [ ] **Task: Verify Generic Adapter End-to-End**
    - [ ] Write tests verifying `run_generic` and `run_callable` with the simple agent.
    - [ ] Verify `strict` mode and `UnmockedToolError`.
    - [ ] Verify timeout handling and partial trajectory capture.
    - [ ] Verify `record_llm_call` correctly populates LLM metadata in the trajectory.
    - [ ] Run `mypy --strict` and `ruff check`.
- [ ] **Task: Conductor - User Manual Verification 'Final Verification' (Protocol in workflow.md)**
