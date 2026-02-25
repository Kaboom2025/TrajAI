# UnitAI - Project Context

## Project Overview
UnitAI is a Python-based testing framework for AI agents. It allows developers to write deterministic assertions about agent behavior by mocking tools, capturing the full trajectory of agent actions, and supporting statistical pass/fail thresholds to handle LLM non-determinism.

### Key Technologies
- **Language:** Python 3.10+
- **Testing Framework:** pytest (UnitAI acts as a pytest plugin)
- **Supported Agent Frameworks (Planned):** LangGraph, CrewAI, OpenAI Agents SDK, Semantic Kernel.
- **Architecture:**
  - `core/`: Trajectory data models and assertion logic.
  - `mock/`: Tool mocking infrastructure (`MockToolkit`).
  - `runner/`: Statistical runner for non-deterministic tests and record/replay caching.
  - `adapters/`: Framework-specific logic for injecting mocks and extracting trajectories.
  - `pytest_plugin/`: Integration with pytest via fixtures and markers.
  - `cli/`: Command-line interface (`unitai` command).

## Building and Running

### Installation
```bash
# Core only
pip install trajai

# With specific adapters
pip install trajai[langraph]
pip install trajai[crewai]
pip install trajai[all]
```

### Running Tests
UnitAI tests are typically run via the `unitai` CLI, which wraps `pytest`.
```bash
# Run all tests
trajai test

# Run with statistical override
trajai test --n=20 --threshold=0.90

# Run with specific model or budget
trajai test --model=gpt-4o-mini --budget=2.00
```

### Development Commands
- **Linting:** `ruff check .`
- **Type Checking:** `mypy .`
- **Unit Testing:** `pytest` (standard pytest commands also work)

## Development Conventions

### Coding Style
- Follow standard Python idioms and PEP 8.
- Use type hints extensively (verified via `mypy`).
- Maintain zero required dependencies for the core package beyond the Python standard library.

### Testing Practices
- **Trajectory Assertions:** Assert on *what* the agent did (tool calls, order, arguments) rather than just its output.
- **Statistical Testing:** Use the `@statistical` decorator for tests that may exhibit non-deterministic behavior.
- **Mocking:** Use `MockToolkit` to replace real tools with deterministic mocks.
- **Cost Awareness:** Tests should be mindful of LLM API costs. Use budget limits and the record/replay cache during development.

### Contribution Guidelines
- Add tests for any new features or bug fixes.
- Ensure the pytest plugin and CLI commands are updated if core APIs change.
- Adhere to the MIT license.
