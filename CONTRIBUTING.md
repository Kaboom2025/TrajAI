# Contributing to UnitAI

Thanks for your interest in contributing to UnitAI! This guide covers how to set up development, run tests, and submit changes.

---

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/saalik/unitai.git
cd unitai
```

2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

3. Install in editable mode with all extras:

```bash
pip install -e ".[all]"
pip install ruff mypy pytest
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_trajectory.py

# Run a single test
pytest tests/test_trajectory.py::test_trajectory_serialization

# Verbose output
pytest -v
```

---

## Code Quality

All code must pass linting and type checking before merge.

```bash
# Lint
ruff check .

# Auto-fix lint issues
ruff check --fix .

# Format
ruff format .

# Type check
mypy .
```

---

## Code Style

- **Formatter/linter:** ruff (line length 88, Python 3.12 target)
- **Type checking:** mypy strict mode
- **Dataclasses over Pydantic** for core types (zero runtime dependencies)
- **Frozen dataclasses** for `Trajectory`, `TrajectoryStep`, `AgentRunResult`, `MockToolCall`
- **Pure functions** for assertions (in `core/assertions.py`), not methods on result objects
- **Never mutate agents:** adapters create copies/wrappers

---

## Adding a New Assertion

1. Add a pure function to `unitai/core/assertions.py`:

```python
def my_assertion(trajectory: Trajectory, ...) -> tuple[bool, str]:
    # Return (passed, message)
    ...
```

2. Add a boolean method to `AgentRunResult` in `unitai/core/result.py`:

```python
def my_assertion(self, ...) -> bool:
    return assertions.my_assertion(self.trajectory, ...)[0]
```

3. Optionally add an assert method:

```python
def assert_my_assertion(self, ...) -> None:
    self._check(assertions.my_assertion(self.trajectory, ...))
```

4. Add tests in `tests/` using hand-crafted trajectories.

5. Document the new assertion in `docs/assertions.md`.

---

## Adding a New Adapter

1. Create a new file in `unitai/adapters/` (e.g., `my_framework.py`).
2. Subclass `BaseAdapter` and implement `can_handle()`, `inject_mocks()`, `execute()`, and `extract_tools()`.
3. Add a conditional import in `unitai/adapters/__init__.py`.
4. Add the framework as an optional dependency in `pyproject.toml`.
5. Add tests in `tests/` and a fixture agent in `tests/fixtures/`.
6. Document the adapter in `docs/adapters.md`.

---

## Pull Request Process

1. Fork the repo and create a branch from `main`.
2. Make your changes. Add tests for new functionality.
3. Ensure all tests pass: `pytest`
4. Ensure code quality: `ruff check .` and `mypy .`
5. Write a clear PR description explaining what and why.
6. Submit the PR. A maintainer will review it.

---

## Reporting Bugs

Use the [bug report template](https://github.com/saalik/unitai/issues/new?template=bug_report.md) on GitHub. Include:

- Python version and OS
- UnitAI version (`pip show unitai`)
- Minimal reproduction steps
- Expected vs actual behavior

---

## Requesting Features

Use the [feature request template](https://github.com/saalik/unitai/issues/new?template=feature_request.md) on GitHub.
