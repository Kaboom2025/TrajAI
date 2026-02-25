# Quick Start Guide

Get from zero to running AI agent tests in 5 minutes.

---

## 1. Install UnitAI

```bash
pip install unitai
```

For framework-specific adapters:

```bash
pip install unitai[langgraph]     # LangGraph support
pip install unitai[crewai]        # CrewAI support
pip install unitai[openai-agents] # OpenAI Agents SDK support
```

## 2. Write Your Agent

Create a simple agent function. This is a callable that takes an input string and a tools dictionary, uses tools to accomplish a task, and returns a response.

```python
# agent.py

def customer_service_agent(input: str, tools: dict) -> str:
    """A simple agent that looks up orders and processes refunds."""
    if "refund" in input.lower():
        order = tools["lookup_order"]({"order_id": "123"})
        if order["status"] == "delivered":
            result = tools["process_refund"]({"order_id": "123", "amount": 29.99})
            return f"Refund {result['confirmation']} processed successfully."
        return f"Cannot refund — order status is {order['status']}."
    return "How can I help you today?"
```

## 3. Write Your First Test

Create a test file using `MockToolkit` to mock the tools and assert on agent behavior.

```python
# test_agent.py
from unitai.mock import MockToolkit

from agent import customer_service_agent

def test_refund_calls_lookup_first():
    """Agent must look up the order before processing a refund."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered", "id": "123"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-789", "success": True})

    result = toolkit.run_callable(customer_service_agent, "I want a refund for order 123")

    # Verify the agent called the right tools in the right order
    assert result.tool_was_called("lookup_order")
    assert result.tool_was_called("process_refund")
    assert result.tool_called_before("lookup_order", "process_refund")

    # Verify the output mentions the confirmation number
    assert result.output_contains("RF-789")

def test_no_refund_for_undelivered_order():
    """Agent should not process refund if order isn't delivered."""
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "shipped", "id": "123"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-000", "success": True})

    result = toolkit.run_callable(customer_service_agent, "I want a refund for order 123")

    assert result.tool_was_called("lookup_order")
    assert result.tool_not_called("process_refund")
    assert result.output_contains("shipped")
```

## 4. Run Your Tests

```bash
pytest test_agent.py -v
```

Expected output:

```
test_agent.py::test_refund_calls_lookup_first PASSED
test_agent.py::test_no_refund_for_undelivered_order PASSED

========== 2 passed in 0.03s ==========
```

## 5. Understanding the Output

When a test fails, UnitAI prints the full trajectory so you can see exactly what happened:

```python
def test_wrong_order():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    # Forgot to mock process_refund!

    result = toolkit.run_callable(customer_service_agent, "Refund order 123")
    result.assert_tool_was_called("process_refund")  # Will fail with trajectory
```

The failure message includes a formatted trajectory showing every step the agent took — tool calls with arguments and results, timestamps, and where the assertion failed.

## 6. Inspecting Results

The `AgentRunResult` object gives you full access to what happened:

```python
result = toolkit.run_callable(agent, "Refund order 123")

# Final agent output
print(result.output)

# All tool calls in order
print(result.call_order())  # ["lookup_order", "process_refund"]

# Specific call details
call = result.get_call("lookup_order", 0)  # First call to lookup_order
print(call.args)      # {"order_id": "123"}
print(call.result)    # {"status": "delivered"}
print(call.timestamp) # 1708900000.123

# Metadata
print(result.total_tokens)  # Sum of prompt + completion tokens
print(result.total_cost)    # Total LLM cost
print(result.duration)      # Execution time in seconds
print(result.llm_calls)     # Number of LLM API calls
```

## 7. Add to CI

UnitAI tests are standard pytest tests. Add them to your CI pipeline like any other test:

```yaml
# .github/workflows/test.yml
- name: Run agent tests
  run: pytest tests/ -v
```

For advanced CI setup with cost budgets, statistical runners, and JUnit XML reports, see the [CI Integration Guide](ci.md).

---

## Next Steps

- [Assertion Reference](assertions.md) — Every assertion method with examples
- [Framework Adapters](adapters.md) — LangGraph, CrewAI, OpenAI Agents setup
- [Statistical Testing](statistical-testing.md) — Handle LLM non-determinism
- [Configuration](configuration.md) — Customize defaults via `pyproject.toml` or env vars
