# UnitAI Examples

This folder contains practical scenarios demonstrating how to use UnitAI to test agent behavior. Each scenario is a self-contained example that you can run, study, and adapt to your own use cases.

## Scenarios

### 1. `scenario_1_single_tool_call.py`
**What it simulates:** A simple order lookup agent that calls a single tool.

**Use case:** Testing basic agent behavior where an agent is expected to call exactly one tool to answer a question.

**Key assertions demonstrated:**
- `tool_was_called()` — verify a tool was invoked
- `tool_not_called()` — verify a tool was NOT invoked
- `output` — access the agent's final response
- `llm_calls` — inspect LLM API calls made
- `total_tokens` — check token usage
- Iterating `trajectory.steps` — see the sequence of agent actions

**Real-world example:** Customer service chatbot checking order status.

---

### 2. `scenario_2_two_tool_calls_sequence.py`
**What it simulates:** An agent that performs multiple actions in sequence (lookup order, then process refund).

**Use case:** Testing multi-step workflows where tool call order matters and you need to assert dependencies between actions.

**Key assertions demonstrated:**
- `tool_called_before()` — enforce ordering constraints between tools
- `call_order()` — get a list of tools called in sequence
- `output_contains()` — verify agent output mentions expected content
- `get_call()` — retrieve specific tool call details (args, result)

**Real-world example:** Refund processing that must look up the order first before approving the refund.

---

### 3. `scenario_3_no_tool_call.py`
**What it simulates:** An agent that responds with pure conversation, not calling any tools.

**Use case:** Verifying that an agent correctly recognizes when a question doesn't require tool use (e.g., general knowledge).

**Key assertions demonstrated:**
- `tool_not_called()` — assert multiple tools were not used
- Handling pure LLM responses without tool invocation

**Real-world example:** Chatbot responding to casual conversation without needing external data.

---

### 4. `scenario_4_sequence_mock.py`
**What it simulates:** An agent that calls the same tool multiple times, with different return values each time.

**Use case:** Testing agents that iterate or batch-process items, where each call should get a different response.

**Key assertions demonstrated:**
- `sequence` mock parameter — return different values on repeated calls
- `tool_call_count()` — verify a tool was called exactly N times
- `get_call(tool_name, index)` — access nth invocation of a repeated tool
- Handling stateful mock behavior

**Real-world example:** Agent checking multiple order IDs in a loop, getting different statuses for each.

---

### 5. `scenario_5_error_handling.py`
**What it simulates:** Attempting to use UnitAI with an agent framework that isn't supported yet.

**Use case:** Understanding how UnitAI handles unsupported agent types and what the error message looks like.

**Key assertions demonstrated:**
- Exception handling with `try/except`
- `AdapterNotFoundError` — when an agent framework can't be auto-detected

**Real-world example:** Catching configuration errors early.

---

### 6. `scenario_6_openai_agents.py` (Phase 11)
**What it simulates:** Testing agents built with the OpenAI Agents SDK.

**Use case:** Integrating UnitAI with OpenAI's native agent framework for mocking FunctionTool calls.

**Key assertions demonstrated:**
- Auto-detection of `agents.Agent` objects
- FunctionTool replacement without mutating the original agent
- Multi-step workflows with OpenAI Agents
- LLM metadata extraction from `RunResult`

**Real-world example:** Customer support agent using OpenAI Agents SDK.

---

### 7. `scenario_7_crewai.py` (Phase 11)
**What it simulates:** Testing CrewAI agents and crews.

**Use case:** Mocking BaseTool instances in CrewAI agents for deterministic testing.

**Key assertions demonstrated:**
- Auto-detection of `Crew` and `Agent` objects
- BaseTool replacement via `model_copy()`
- Testing multi-agent crews with shared tools
- Crew.kickoff() result extraction

**Real-world example:** Market research crew analyzing competitors.

---

### 8. `scenario_8_statistical_testing.py` (Phase 4)
**What it simulates:** Running tests multiple times to handle LLM non-determinism.

**Use case:** Testing agents where behavior varies across runs, requiring statistical pass rate thresholds.

**Key assertions demonstrated:**
- `StatisticalRunner` for N-run testing
- Pass rate thresholds (e.g., 90% success required)
- Cost budget enforcement
- `@pytest.mark.unitai_statistical` decorator
- CI integration with cost reporting

**Real-world example:** Flaky agent that should succeed 90%+ of the time.

---

## How to Run

Run all examples:
```bash
python -m pytest tests/examples/
```

Run a single example:
```bash
python tests/examples/scenario_1_single_tool_call.py
```

Run with verbose output:
```bash
python -m pytest tests/examples/ -v
```

---

## Learning Path

If you're new to UnitAI, we recommend studying the scenarios in this order:

1. **Scenario 1** — Start here to understand basic mock setup and assertions
2. **Scenario 2** — Learn multi-step workflows and ordering constraints
3. **Scenario 3** — Understand negative assertions (tools NOT called)
4. **Scenario 4** — See advanced mocking with sequences and repeated calls
5. **Scenario 5** — Learn error handling patterns
6. **Scenario 6** — OpenAI Agents SDK integration (if using OpenAI Agents)
7. **Scenario 7** — CrewAI integration (if using CrewAI)
8. **Scenario 8** — Statistical testing for handling LLM non-determinism

---

## Common Patterns

### Pattern: Basic Mock + Assert
```python
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"status": "delivered"})
result = toolkit.run(agent, "What's my order status?")
assert result.tool_was_called("lookup_order")
```

### Pattern: Multiple Mocks + Ordering
```python
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"status": "delivered"})
toolkit.mock("process_refund", return_value={"success": True})
result = toolkit.run(agent, "Refund my order")
assert result.tool_called_before("lookup_order", "process_refund")
```

### Pattern: Sequence Mocks (Repeated Calls)
```python
toolkit = MockToolkit()
toolkit.mock("lookup", sequence=[
    {"id": "1", "status": "shipped"},
    {"id": "2", "status": "delivered"},
])
result = toolkit.run(agent, "Check orders 1 and 2")
assert result.tool_call_count("lookup", 2)
```

---

## Next Steps

After working through these examples:
- See `demo.py` for the full runnable version of all scenarios
- Check `CLAUDE.md` for detailed API documentation
- Read `unitai-spec.md` Section 8 for assertion library reference
- Explore `tests/` for unit tests of individual features

---

## Tips & Tricks

**Inspect the full trajectory:**
```python
for step in result.trajectory.steps:
    print(f"{step.step_type}: {step}")
```

**Debug assertion failures:**
```python
try:
    result.assert_tool_was_called("lookup_order")
except UnitAIAssertionError as e:
    print(e)  # See pretty-printed trajectory on failure
```

**Check token usage (for cost tracking):**
```python
print(result.total_tokens)  # Sum of prompt + completion tokens
```

**Get specific tool call details:**
```python
call = result.get_call("lookup_order", 0)
print(call.args)       # Tool arguments
print(call.result)     # Tool return value
print(call.timestamp)  # When it was called
```

---

## Contributing

Found a pattern that should be documented? Spotted a gap in the examples? Feel free to extend this folder with additional scenarios or improvements to existing ones.
