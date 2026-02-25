# UnitAI

**The open-source testing framework for AI agents.**

[![PyPI version](https://img.shields.io/pypi/v/unitai.svg)](https://pypi.org/project/unitai/)
[![CI](https://github.com/saalik/unitai/actions/workflows/ci.yml/badge.svg)](https://github.com/saalik/unitai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

UnitAI lets you write deterministic tests for non-deterministic AI agents. Mock tools, capture execution trajectories, and assert on what your agent *did* — not just what it said.

---

## Quick Start

```bash
pip install unitai
```

```python
# test_agent.py
from unitai.mock import MockToolkit

def my_agent(input: str, tools: dict):
    order = tools["lookup_order"]({"order_id": "123"})
    if order["status"] == "delivered":
        refund = tools["process_refund"]({"order_id": "123", "amount": 50.0})
        return f"Refund processed: {refund['confirmation']}"
    return "Order not yet delivered"

def test_refund_flow():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-456", "success": True})

    result = toolkit.run_callable(my_agent, "Refund order 123")

    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")
    assert result.output_contains("RF-456")
```

```bash
pytest test_agent.py -v
```

---

## Why UnitAI?

Testing AI agents is hard. LLMs are non-deterministic, tool calls have side effects, and there's no standard way to assert on agent behavior. Teams end up with fragile integration tests that hit real APIs, cost money, and break randomly.

UnitAI fixes this:

- **Mock tools, not LLMs.** Your agent runs with real LLM calls but mocked tools. No side effects, deterministic tool responses.
- **Assert on behavior.** Test *what* the agent did (which tools it called, in what order, with what arguments) — not just its final text output.
- **Handle non-determinism.** Run tests N times and assert on pass rates. "This agent calls the right tools 95% of the time" is a valid, useful test.
- **Framework support.** Works with LangGraph, CrewAI, OpenAI Agents SDK, or any Python callable.

---

## Core Concepts

### MockToolkit

The central API. Register mock tools, run your agent, get results.

```python
toolkit = MockToolkit()
toolkit.mock("search", return_value={"results": [...]})
toolkit.mock("send_email", return_value={"sent": True})
```

### Assertions

Both boolean and assert-style APIs for testing agent behavior:

```python
result = toolkit.run_callable(agent, "Find and email the report")

# Boolean API — use with assert
assert result.tool_was_called("search")
assert result.tool_called_before("search", "send_email")
assert result.tool_call_count("search", 1)

# Assert API — raises UnitAIAssertionError with formatted trajectory on failure
result.assert_tool_was_called("search")
result.assert_output_contains("report")
```

### Trajectory

Every agent run produces a `Trajectory` — a chronological record of all tool calls, LLM calls, and state changes. When assertions fail, the full trajectory is pretty-printed in the error message.

### Statistical Testing

Handle LLM non-determinism by running tests multiple times:

```python
from unitai.runner import statistical

@statistical(n=10, threshold=0.9)
def test_agent_uses_correct_tools():
    toolkit = MockToolkit()
    toolkit.mock("lookup", return_value={"id": "123"})
    result = toolkit.run_callable(agent, "Look up order 123")
    assert result.tool_was_called("lookup")
```

---

## Framework Support

| Framework | Install | Status |
|-----------|---------|--------|
| Any Python callable | `pip install unitai` | Stable |
| LangGraph | `pip install unitai[langgraph]` | Stable |
| CrewAI | `pip install unitai[crewai]` | Stable |
| OpenAI Agents SDK | `pip install unitai[openai-agents]` | Stable |

Framework-specific adapters handle tool injection and trajectory collection automatically:

```python
# LangGraph — auto-detects and injects mocks
result = toolkit.run(my_langgraph_agent, "Refund order 123")

# Generic callable — you wire the tools
result = toolkit.run_callable(my_function, "Refund order 123")
```

---

## Mock Strategies

```python
# Static return value
toolkit.mock("get_weather", return_value={"temp": 72, "unit": "F"})

# Sequence — different value on each call
toolkit.mock("check_status", sequence=[
    {"status": "pending"},
    {"status": "shipped"},
    {"status": "delivered"},
])

# Side effect — custom function
toolkit.mock("calculate", side_effect=lambda args: args["a"] + args["b"])

# Error — simulate failures
toolkit.mock("flaky_api", side_effect=ConnectionError("timeout"))

# Conditional — return based on arguments
toolkit.mock("lookup", conditional={
    lambda args: args.get("id") == "1": {"name": "Alice"},
    lambda args: args.get("id") == "2": {"name": "Bob"},
})
```

---

## Documentation

- [Quick Start Guide](docs/quickstart.md) — Get running in 5 minutes
- [Assertion Reference](docs/assertions.md) — Every assertion method with examples
- [Framework Adapters](docs/adapters.md) — LangGraph, CrewAI, OpenAI Agents setup
- [Statistical Testing](docs/statistical-testing.md) — Handle non-determinism
- [Configuration](docs/configuration.md) — Full config reference
- [CI Integration](docs/ci.md) — GitHub Actions, GitLab CI, CircleCI

---

## Examples

Self-contained example projects in the [`examples/`](examples/) directory:

- [`generic_chatbot/`](examples/generic_chatbot/) — Simple chatbot with basic assertions
- [`refund_agent/`](examples/refund_agent/) — Multi-step refund workflow with ordering constraints
- [`research_agent/`](examples/research_agent/) — Research agent with statistical testing

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and how to submit changes.

---

## License

MIT License. See [LICENSE](LICENSE).
