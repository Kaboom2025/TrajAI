# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UnitAI is an open-source testing framework for AI agents. It enables developers to write deterministic assertions about agent behavior by mocking tools, capturing execution trajectories, and supporting statistical pass/fail thresholds for handling LLM non-determinism.

**Core principle:** Agents run locally with real LLM calls but mocked tools. Tests assert on what the agent *did* (tool calls, order, arguments) not just what it *said*.

## Development Commands

### Running Tests
```bash
# Run all tests with pytest
pytest

# Run specific test file
pytest tests/test_trajectory.py

# Run single test
pytest tests/test_trajectory.py::test_trajectory_serialization

# Run with verbose output
pytest -v

# Skip slow integration tests (if marked)
pytest -m "not integration"
```

### Code Quality
```bash
# Linting (ruff)
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type checking (mypy)
mypy .

# Format code
ruff format .
```

### Package Development
```bash
# Install in editable mode for development
pip install -e .

# Build package
python -m build

# Install with specific extras
pip install -e ".[langraph]"
pip install -e ".[all]"
```

## Architecture Overview

### Core Data Flow
1. **MockToolkit** registers mock tools with response strategies
2. **Adapters** inject mocks into agents and collect execution data
3. **Trajectory** captures the sequence of all agent actions (tool calls, LLM calls)
4. **AgentRunResult** wraps trajectory and exposes assertion methods
5. **Assertions** validate agent behavior (tool call order, arguments, output)

### Key Components

#### `unitai/core/`
- **`trajectory.py`**: Core data model. `Trajectory` contains ordered `TrajectoryStep` objects representing agent actions. Fully serializable to JSON.
- **`result.py`**: `AgentRunResult` wraps a trajectory and provides both boolean API (`tool_was_called()`) and assert API (`assert_tool_was_called()`) for testing.
- **`assertions.py`**: Pure functions that take a `Trajectory` and return `(bool, str)` tuples. All assertion logic lives here.
- **`formatter.py`**: `TrajectoryFormatter` pretty-prints trajectories for failure messages.

#### `unitai/mock/`
- **`toolkit.py`**: `MockToolkit` is the primary user-facing API. Registers mocks, executes agents, collects trajectories.
  - `mock(name, return_value=..., side_effect=..., sequence=..., conditional=...)` registers a tool
  - `run_generic(callable)` executes a generic agent (Phase 2)
  - `run_callable(fn, input, tools)` executes callable agents with tool dict
  - `run(agent, input)` will auto-detect framework adapters (Phase 5+)
- **`strategies.py`**: Response strategy implementations (`StaticStrategy`, `SequenceStrategy`, `ConditionalStrategy`, `ErrorStrategy`, `CallableStrategy`)

#### `unitai/adapters/`
- **`base.py`**: `BaseAdapter` abstract interface defining `can_handle()`, `inject_mocks()`, `execute()`, `extract_tools()`
- **`generic.py`**: `GenericAdapter` for framework-agnostic agents. User manually wires mock tools.
- Framework-specific adapters (LangGraph, CrewAI, OpenAI Agents, Semantic Kernel) planned for future phases.

#### `tests/`
- Tests use pytest. No special test runner needed.
- `tests/fixtures/` contains reusable test agents
- All tests are synchronous (async execution handled internally)

### Design Principles

1. **Dataclasses over Pydantic**: Core uses stdlib dataclasses to avoid dependencies
2. **Immutability**: `Trajectory`, `TrajectoryStep`, `AgentRunResult`, and `MockToolCall` are frozen dataclasses
3. **Separation of concerns**: Assertions are pure functions in `assertions.py`, not methods mixed into result objects
4. **Never mutate agents**: Adapters must create copies/wrappers, never modify original agent objects
5. **Type safety**: Strict mypy checking enabled. All public APIs fully typed.

## Current Development Status

**Completed Phases** (tracked in `conductor/tracks.md`):
- ✅ Phase 1: Core Data Model & Mock Primitives
- ✅ Phase 2: Generic Adapter & Agent Execution
- ✅ Phase 3: Assertion Library

**Next Phases** (see `unitai-spec.md` Section 19 for full plan):
- Phase 4: Statistical Runner (handle non-determinism with N runs + pass rate threshold)
- Phase 5: LangGraph Adapter (framework-specific tool injection + trajectory collection)
- Phase 6: pytest Plugin (fixtures, markers, rich failure reporting)
- Phase 7: CLI (`unitai test` command)
- Phase 8: Record/Replay Cache (cache LLM responses for deterministic re-runs)

## Important Implementation Notes

### Adding New Assertions
1. Add pure function to `core/assertions.py` with signature: `(Trajectory, ...) -> tuple[bool, str]`
2. Add boolean method to `AgentRunResult` that calls the assertion function
3. Optionally add assert method that raises `UnitAIAssertionError` via `_check()`
4. Write tests in `tests/test_assertions_*.py` using hand-crafted trajectories

### Mock Tool Response Strategies
When calling `toolkit.mock()`, exactly one response strategy must be provided:
- `return_value`: Static value (default strategy)
- `side_effect`: Callable or Exception
- `sequence`: List of values to return in order
- `conditional`: Dict mapping condition lambdas to return values

### Trajectory Collection
All trajectory collection happens through adapters:
1. Mock tools record their invocations automatically (timestamp, args, result, error)
2. Adapters are responsible for recording LLM calls via `toolkit.record_llm_call()`
3. Adapters aggregate all steps chronologically and create final `Trajectory` object

### Exception Handling
- All UnitAI-specific exceptions inherit from `UnitAIMockError` (in `mock/toolkit.py`)
- Assertion failures use `UnitAIAssertionError` (in `core/assertions.py`)
- Original agent exceptions are preserved in `Trajectory.error` field
- Timeout handling uses `asyncio.wait_for()` and returns partial trajectories

### Testing Patterns
```python
# Standard test pattern
def test_agent_behavior():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"id": "123", "status": "delivered"})
    toolkit.mock("process_refund", return_value={"success": True})

    result = toolkit.run_callable(my_agent, "refund order 123")

    # Boolean API
    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")

    # Assert API (raises with formatted trajectory on failure)
    result.assert_tool_was_called("lookup_order")
    result.assert_output_contains("refund")
```

## Development Workflow

The project follows a **bottom-up, phase-by-phase** development approach. Each phase produces working, testable code before moving to the next. See `unitai-spec.md` Section 19 for the complete 13-phase development plan.

### Conductor System
The `conductor/` directory contains project planning and tracking:
- `product.md`, `product-guidelines.md`: Product strategy and positioning
- `tech-stack.md`: Technology decisions
- `workflow.md`: Development workflow guidelines
- `tracks.md`: Tracks completed and in-progress phases
- `archive/`: Completed phase documentation

### Git Workflow
- Main development branch: `main`
- Current branch: `master` (should be synced with `main`)
- Follow conventional commits when possible
- Test suite must pass before commits to main branches

## Technical Constraints

- **Python 3.12+** required (uses `tomllib`, modern type hints)
- **Zero runtime dependencies** for core package (stdlib only)
- **Framework adapters as extras**: `pip install unitai[langraph]`, etc.
- **pytest integration**: UnitAI registers as a pytest plugin
- **MIT License**
- **No hosted service required**: Fully local, only needs user's own LLM API keys

## Key Files to Reference

- `unitai-spec.md`: Complete technical specification (70+ pages)
- `GEMINI.md`: Project context for Gemini (legacy, less comprehensive than this file)
- `pyproject.toml`: Package metadata, build config, tool configuration
- `conductor/workflow.md`: Detailed development workflow guidelines
