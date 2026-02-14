# UnitAI — Technical Specification v0.1

> The open-source testing framework for AI agents.
> "Write tests for your agents like you write tests for your code."

---

## 1. Overview

### 1.1 What UnitAI Is

UnitAI is a Python testing framework that lets developers write deterministic assertions about AI agent behavior. It provides mock infrastructure for agent tools, captures the full trajectory of agent actions during a test run, and supports statistical pass/fail thresholds to handle LLM non-determinism.

### 1.2 Core Principle

The agent runs locally in the developer's test process. Real tools are replaced with mocks. The LLM is real (it makes actual API calls). The test asserts on what the agent *did* — which tools it called, in what order, with what arguments — not just what it *said*.

### 1.3 What a Test Looks Like

```python
from unitai import AgentTestCase, MockToolkit, assert_trajectory

def test_refund_requires_order_lookup():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"order_id": "123", "status": "delivered", "amount": 49.99})
    toolkit.mock("process_refund", return_value={"success": True, "refund_id": "R-456"})

    result = toolkit.run(
        agent=my_refund_agent,
        input="I want a refund for order #123"
    )

    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")
    assert result.tool_called_with("lookup_order", order_id="123")
    assert result.tool_not_called("delete_order")
    assert result.total_cost < 0.10
```

### 1.4 Design Constraints

- Python 3.10+. No other language support in v0.1.
- MIT license.
- Zero required dependencies beyond the Python standard library for the core. Framework adapters (LangGraph, CrewAI, etc.) are optional extras.
- Must work as a pytest plugin. Tests are discovered and run by pytest natively. `unitai` commands are thin wrappers around pytest.
- Must not require any hosted service, account, or API key (beyond the user's own LLM key).
- Must produce JUnit XML output for CI integration.

---

## 2. Package Structure

```
unitai/
├── __init__.py              # Public API surface
├── core/
│   ├── __init__.py
│   ├── trajectory.py        # Trajectory data model + collector
│   ├── assertions.py        # Assertion library
│   └── result.py            # AgentRunResult container
├── mock/
│   ├── __init__.py
│   ├── toolkit.py           # MockToolkit — the primary user-facing mock API
│   ├── tool.py              # MockTool — individual mock tool
│   └── strategies.py        # Response strategies (static, sequence, conditional, error)
├── runner/
│   ├── __init__.py
│   ├── statistical.py       # StatisticalRunner — runs test N times, computes pass rate
│   └── replay.py            # Record/replay cache for LLM responses
├── adapters/
│   ├── __init__.py
│   ├── base.py              # BaseAdapter abstract class
│   ├── langraph.py          # LangGraph adapter
│   ├── crewai.py            # CrewAI adapter
│   ├── openai_agents.py     # OpenAI Agents SDK adapter
│   └── semantic_kernel.py   # Microsoft Semantic Kernel adapter
├── pytest_plugin/
│   ├── __init__.py
│   ├── plugin.py            # pytest plugin registration
│   └── fixtures.py          # pytest fixtures (mock_toolkit, etc.)
├── cli/
│   ├── __init__.py
│   └── main.py              # CLI entrypoint
├── ci/
│   └── github_action/       # GitHub Action definition
│       ├── action.yml
│       └── entrypoint.sh
└── config.py                # Configuration loading (unitai.toml / pyproject.toml)
```

Install targets:

```
pip install unitai                    # Core only
pip install unitai[langraph]          # + LangGraph adapter
pip install unitai[crewai]            # + CrewAI adapter
pip install unitai[openai]            # + OpenAI Agents SDK adapter
pip install unitai[semantic-kernel]   # + Semantic Kernel adapter
pip install unitai[all]               # Everything
```

---

## 3. Core Data Model

### 3.1 Trajectory

A Trajectory is the recorded sequence of everything the agent did during a single test run. It is the fundamental data structure that assertions operate on.

```
Trajectory:
  run_id: str (uuid)
  input: str (the user message that started the run)
  steps: list[TrajectoryStep]
  final_output: str | None (agent's final text response)
  total_tokens: int
  total_cost: float
  duration_seconds: float
  llm_calls: int
  error: Exception | None (if the agent raised)
```

### 3.2 TrajectoryStep

Each step represents one action the agent took — a tool call, an LLM call, or an internal state change.

```
TrajectoryStep:
  step_index: int
  step_type: "tool_call" | "llm_call" | "state_change"
  timestamp: float

  # For tool_call steps:
  tool_name: str
  tool_args: dict
  tool_result: Any
  tool_error: Exception | None

  # For llm_call steps:
  model: str
  prompt_tokens: int
  completion_tokens: int
  cost: float

  # For state_change steps:
  key: str
  old_value: Any
  new_value: Any
```

### 3.3 AgentRunResult

Returned by `toolkit.run()`. Wraps a Trajectory and exposes the assertion methods.

```
AgentRunResult:
  trajectory: Trajectory
  output: str (alias for trajectory.final_output)
  total_cost: float
  duration: float
  error: Exception | None

  # Assertion methods (see Section 5)
  tool_was_called(name) -> bool
  tool_not_called(name) -> bool
  tool_called_before(first, second) -> bool
  tool_called_with(name, **kwargs) -> bool
  tool_call_count(name) -> int
  call_order() -> list[str]
  # ... full list in Section 5
```

---

## 4. Mock Layer

### 4.1 MockToolkit

The primary user-facing API. Developers create a MockToolkit, register mock tools, then run their agent against it.

**Responsibilities:**
- Register mock tools with configurable response strategies
- Inject mocks into the agent (via the appropriate framework adapter)
- Collect the full trajectory during the run
- Return a AgentRunResult

**Key methods:**

```
MockToolkit:
  mock(tool_name, return_value=None, side_effect=None, sequence=None, conditional=None)
    # Registers a mock tool. Exactly one response strategy must be provided.

  run(agent, input, adapter=None, model_override=None, timeout=60)
    # Executes the agent with mocked tools. Auto-detects adapter if not specified.
    # Returns AgentRunResult.

  reset()
    # Clears all recorded calls and resets mock state. Mocks stay registered.
```

### 4.2 MockTool

Represents a single mocked tool. Tracks every invocation.

```
MockTool:
  name: str
  calls: list[MockToolCall]  # Every invocation recorded here
  strategy: ResponseStrategy

  invoke(args: dict) -> Any
    # Called when the agent invokes this tool.
    # Records the call, returns result from strategy.
```

```
MockToolCall:
  args: dict
  result: Any
  error: Exception | None
  timestamp: float
```

### 4.3 Response Strategies

Four built-in strategies for how mock tools respond:

**Static:** Always returns the same value.
```python
toolkit.mock("lookup_order", return_value={"order_id": "123", "status": "delivered"})
```

**Sequence:** Returns values in order. Raises if exhausted.
```python
toolkit.mock("get_next_page", sequence=[
    {"items": ["a", "b"], "has_more": True},
    {"items": ["c"], "has_more": False}
])
```

**Conditional:** Returns different values based on input arguments.
```python
toolkit.mock("lookup_order", conditional={
    lambda args: args["order_id"] == "123": {"status": "delivered"},
    lambda args: args["order_id"] == "456": {"status": "cancelled"},
    "__default__": {"error": "not found"}
})
```

**Error:** Raises an exception when called.
```python
toolkit.mock("payment_api", side_effect=TimeoutError("payment service unavailable"))
```

**Custom callable:** Any function.
```python
def smart_lookup(args):
    if args["order_id"].startswith("R"):
        return {"type": "return", "status": "pending"}
    return {"type": "order", "status": "shipped"}

toolkit.mock("lookup_order", side_effect=smart_lookup)
```

### 4.4 Auto-Detection of Framework

When `toolkit.run()` is called without an explicit adapter, UnitAI inspects the agent object to determine which framework it belongs to:

- If it's a `StateGraph` or `CompiledGraph` → LangGraph adapter
- If it's a `Crew` or `Agent` from `crewai` → CrewAI adapter
- If it inherits from `openai.agents.Agent` → OpenAI Agents adapter
- If it's a `Kernel` or has `semantic_kernel` in module path → Semantic Kernel adapter
- Otherwise → raise `AdapterNotFoundError` with instructions

### 4.5 Tool That Was Not Mocked

If the agent tries to call a tool that hasn't been mocked, the behavior depends on configuration:

- `strict=True` (default): raises `UnmockedToolError` immediately. Test fails clearly.
- `strict=False`: logs a warning, returns `None`, records the call in the trajectory.

---

## 5. Assertion Library

All assertions are methods on `AgentRunResult`. They return booleans so they work with Python's `assert` keyword natively. Each assertion also has a descriptive `__repr__` for clear pytest failure messages.

### 5.1 Tool Call Assertions

| Assertion | Description |
|-----------|-------------|
| `result.tool_was_called("name")` | Tool was called at least once |
| `result.tool_not_called("name")` | Tool was never called |
| `result.tool_call_count("name") == N` | Tool was called exactly N times |
| `result.tool_called_with("name", **kwargs)` | Tool was called with these exact keyword arguments (at least once) |
| `result.tool_called_with_partial("name", **kwargs)` | Tool was called with args that include these key-value pairs (partial match) |
| `result.tool_called_before("first", "second")` | First tool was called before second tool (first occurrence of each) |
| `result.tool_called_immediately_before("first", "second")` | First tool was called directly before second with no other tool calls between them |
| `result.call_order() == ["tool_a", "tool_b", "tool_c"]` | Exact ordered sequence of all tool calls |
| `result.call_order_contains(["tool_a", "tool_b"])` | This subsequence appears in order (other calls may appear between them) |

### 5.2 Output Assertions

| Assertion | Description |
|-----------|-------------|
| `result.output_contains("text")` | Final agent output contains this substring |
| `result.output_not_contains("text")` | Final agent output does not contain this substring |
| `result.output_matches(regex)` | Final output matches regex pattern |

### 5.3 Cost & Performance Assertions

| Assertion | Description |
|-----------|-------------|
| `result.total_cost < 0.10` | Total LLM API cost under threshold |
| `result.llm_calls <= 3` | Number of LLM round-trips under threshold |
| `result.duration < 10.0` | Wall-clock seconds under threshold |
| `result.total_tokens < 5000` | Total token usage under threshold |

### 5.4 Error Assertions

| Assertion | Description |
|-----------|-------------|
| `result.succeeded` | Agent completed without raising |
| `result.failed` | Agent raised an exception |
| `result.error_is(ExceptionType)` | Agent raised this specific exception type |

### 5.5 Trajectory Query API

For advanced assertions, expose raw trajectory queries:

```python
# Get all calls to a specific tool
calls = result.get_calls("lookup_order")  # -> list[MockToolCall]

# Get the Nth call to a tool
call = result.get_call("lookup_order", n=0)  # first call
assert call.args["order_id"] == "123"

# Get the full step-by-step trajectory
for step in result.trajectory.steps:
    if step.step_type == "tool_call":
        print(f"{step.tool_name}({step.tool_args}) -> {step.tool_result}")
```

### 5.6 Custom Assertions

Users can write arbitrary Python assertions over the trajectory. UnitAI doesn't restrict them to built-in assertion methods — the trajectory data model is fully public.

---

## 6. Framework Adapters

### 6.1 Base Adapter Interface

Every adapter implements this interface:

```
BaseAdapter:
  can_handle(agent) -> bool
    # Returns True if this adapter knows how to handle this agent type.

  inject_mocks(agent, toolkit: MockToolkit) -> WrappedAgent
    # Returns a copy/wrapper of the agent where real tools are replaced with mocks.
    # Must not mutate the original agent.

  execute(wrapped_agent, input: str, timeout: float) -> Trajectory
    # Runs the agent with the given input, collects and returns the trajectory.

  extract_tools(agent) -> list[str]
    # Returns the names of tools registered on this agent. Used for validation.
```

### 6.2 LangGraph Adapter

LangGraph agents are `CompiledGraph` instances with tool nodes.

**Tool injection:** LangGraph tools are Python functions decorated with `@tool`. The adapter replaces the tool functions in the graph's tool node with mock implementations. It does this by creating a new `ToolNode` with the mock functions and swapping it into the graph.

**Trajectory collection:** LangGraph has built-in streaming support. The adapter uses the `stream()` method and intercepts `on_tool_start`, `on_tool_end`, `on_llm_start`, `on_llm_end` events via LangChain callbacks to build the trajectory.

**State handling:** LangGraph uses a state dict (typically `TypedDict`). The adapter snapshots state before and after each node execution to capture state_change steps.

### 6.3 CrewAI Adapter

CrewAI agents use `@tool` decorated functions assigned to `Agent` instances within a `Crew`.

**Tool injection:** The adapter replaces the `tools` list on each Agent in the Crew with mock tool wrappers. CrewAI tools are callable objects with a `name` attribute — mocks implement the same interface.

**Trajectory collection:** CrewAI emits verbose logs. The adapter uses CrewAI's callback mechanism (if available) or patches the internal execution loop to intercept tool calls.

### 6.4 OpenAI Agents SDK Adapter

OpenAI Agents SDK defines agents with `function` tools.

**Tool injection:** Tools are defined as Python functions with type annotations. The adapter replaces the function references in the agent's tool registry with mock callables that match the same signature.

**Trajectory collection:** The SDK provides a `Runner` with streaming events. The adapter listens to `tool_call` and `tool_output` events.

### 6.5 Semantic Kernel Adapter

Semantic Kernel uses `KernelFunction` plugins.

**Tool injection:** The adapter creates mock `KernelFunction` instances that return mock values and registers them under the same plugin/function names, replacing the originals in the Kernel.

**Trajectory collection:** Semantic Kernel has a filter/hook system. The adapter registers function invocation filters to intercept pre/post tool execution.

### 6.6 Generic Adapter (Fallback)

For agents not built on a supported framework (custom orchestration code), provide a manual wiring option:

```python
toolkit = MockToolkit()
toolkit.mock("search", return_value=[...])

# User manually passes mock tools to their agent
tools = toolkit.as_dict()  # {"search": <callable>, "lookup": <callable>}
my_custom_agent = MyAgent(tools=tools)
result = toolkit.run_generic(lambda: my_custom_agent.execute("find restaurants"))
```

The `run_generic` method accepts a callable that runs the agent. The toolkit records all mock invocations that occur during the callable's execution. The user is responsible for wiring the mocks into their agent — UnitAI just provides the mocks and records the trajectory.

---

## 7. Statistical Runner

### 7.1 Purpose

LLMs are non-deterministic. The same input can produce different tool call sequences across runs. A test that passes 9/10 times shouldn't be marked as failing. The statistical runner handles this.

### 7.2 Usage

Two ways to use it:

**Decorator:**
```python
from unitai import statistical

@statistical(n=10, threshold=0.95)
def test_refund_flow(mock_toolkit):
    # This function body runs 10 times.
    # Test passes if >= 95% of runs satisfy all assertions.
    result = mock_toolkit.run(agent, "refund order #123")
    assert result.tool_called_before("lookup_order", "process_refund")
```

**Explicit:**
```python
from unitai import StatisticalRunner

runner = StatisticalRunner(n=20, threshold=0.90)
stats = runner.run(test_fn, mock_toolkit, agent, "refund order #123")

assert stats.pass_rate >= 0.90
print(stats.summary())
# 18/20 passed (90.0%)
# Failure modes:
#   - 1x: called process_refund before lookup_order
#   - 1x: did not call process_refund at all
```

### 7.3 StatisticalResult

```
StatisticalResult:
  n: int                          # Total runs
  passed: int                     # Runs where all assertions held
  failed: int
  pass_rate: float                # passed / n
  threshold: float                # Required pass rate
  overall_passed: bool            # pass_rate >= threshold
  failure_modes: dict[str, int]   # Grouped assertion failure messages -> count
  trajectories: list[Trajectory]  # All collected trajectories
  total_cost: float               # Sum across all runs
  mean_duration: float
  mean_tokens: int
```

### 7.4 Parallelism

Statistical runs are embarrassingly parallel. The runner uses `concurrent.futures.ThreadPoolExecutor` to run N invocations concurrently (default: `min(n, 5)` threads). Configurable via `max_workers` parameter.

### 7.5 Cost Safety

Before executing, the runner estimates total cost: `estimated_cost = n * estimated_per_run_cost`. If this exceeds a configurable budget (default: $5.00), it raises `CostLimitExceeded` and does not execute. Per-run cost is estimated from the model and average prompt size if available, or from the first run's actual cost.

---

## 8. Record/Replay Cache

### 8.1 Purpose

For deterministic re-runs and cost savings, UnitAI can cache LLM responses. First run hits the real API. Subsequent runs replay cached responses.

### 8.2 How It Works

When enabled, the adapter intercepts LLM calls (not tool calls — those are already mocked) and:

1. **Record mode (first run):** Forwards the request to the real LLM API. Saves the response to a cache file, keyed by a hash of the model + full message history + tool definitions.
2. **Replay mode (subsequent runs):** Checks the cache. If a matching entry exists, returns the cached response without calling the API. If not, falls back to the real API and records.

### 8.3 Cache Storage

Cache files live in `.unitai/cache/` in the project root. Each entry is a JSON file named by the request hash. The cache directory should be gitignored by default.

### 8.4 Cache Invalidation

The cache key includes:
- Model name and version
- System prompt (hashed)
- User input
- Tool definitions (names + schemas)
- Conversation history up to that point

If any of these change, the cache misses and a fresh API call is made.

### 8.5 Configuration

```toml
# unitai.toml or pyproject.toml [tool.unitai]
[cache]
enabled = false          # Off by default
directory = ".unitai/cache"
ttl_hours = 168          # Cache entries expire after 7 days
```

### 8.6 CLI Control

```bash
unitai test --record          # Force fresh API calls, save to cache
unitai test --replay          # Use cache only, fail if cache misses
unitai test --no-cache        # Ignore cache entirely (default)
unitai cache clear             # Delete all cached responses
unitai cache stats             # Show cache size, hit rate, estimated savings
```

---

## 9. Configuration

### 9.1 Config File

UnitAI reads from `pyproject.toml` under `[tool.unitai]` or from a standalone `unitai.toml` file.

```toml
[tool.unitai]
# Default adapter (auto-detected if not set)
adapter = "langraph"

# Statistical runner defaults
default_n = 10
default_threshold = 0.95
max_workers = 5

# Cost controls
cost_budget_per_test = 1.00        # Max cost per single test function (in USD)
cost_budget_per_suite = 10.00      # Max cost per full test suite run
model_override = ""                 # Override model for all tests (e.g., "gpt-4o-mini")

# Mock behavior
strict_mocks = true                # Fail on unmocked tool calls

# Cache
cache_enabled = false
cache_directory = ".unitai/cache"
cache_ttl_hours = 168

# Output
junit_xml = "test-results/unitai.xml"
verbose = false
```

### 9.2 Environment Variables

All config values can be overridden by environment variables prefixed with `UNITAI_`:

- `UNITAI_DEFAULT_N=20`
- `UNITAI_COST_BUDGET_PER_SUITE=5.00`
- `UNITAI_MODEL_OVERRIDE=gpt-4o-mini`

### 9.3 Per-Test Overrides

Configuration can be overridden at the test level via decorators or arguments:

```python
@statistical(n=50, threshold=0.99)   # Override for this test
def test_critical_payment_flow(mock_toolkit):
    ...
```

---

## 10. CLI

### 10.1 Commands

```bash
# Run all tests
unitai test

# Run specific test file or function
unitai test tests/test_refund.py
unitai test tests/test_refund.py::test_refund_requires_lookup

# Run with statistical override
unitai test --n=20 --threshold=0.90

# Run with model override (use cheap model in dev)
unitai test --model=gpt-4o-mini

# Run with cost cap
unitai test --budget=2.00

# Run with cache
unitai test --record
unitai test --replay

# Cache management
unitai cache clear
unitai cache stats

# Show last run results
unitai results

# Init config file
unitai init
```

### 10.2 Implementation

The CLI is a thin wrapper around pytest. `unitai test` translates to `pytest --unitai` with the appropriate flags. The UnitAI pytest plugin handles discovery, execution, and reporting.

Under the hood:
- `unitai test` → `pytest -x --tb=short -q --unitai` (plus any extra flags)
- `unitai test --n=20` → sets `UNITAI_DEFAULT_N=20` env var, then runs pytest
- JUnit XML output is always generated for CI consumption

---

## 11. pytest Plugin

### 11.1 Registration

UnitAI registers as a pytest plugin via the `pytest11` entry point in `pyproject.toml`. Tests are discovered normally by pytest — any file matching `test_*.py` that imports from `unitai` is a UnitAI test.

### 11.2 Fixtures

The plugin provides these fixtures:

```python
@pytest.fixture
def mock_toolkit():
    """Fresh MockToolkit for each test."""
    toolkit = MockToolkit()
    yield toolkit
    toolkit.reset()
```

### 11.3 Markers

```python
@pytest.mark.unitai_statistical(n=10, threshold=0.95)
def test_something(mock_toolkit):
    ...

@pytest.mark.unitai_budget(max_cost=0.50)
def test_cheap(mock_toolkit):
    ...

@pytest.mark.unitai_skip_if_no_api_key
def test_needs_openai(mock_toolkit):
    ...
```

### 11.4 Failure Reporting

When an assertion fails, UnitAI provides rich output:

```
FAILED test_refund.py::test_refund_requires_lookup

  Assertion: tool_called_before("lookup_order", "process_refund")

  Actual trajectory:
    1. [tool_call] process_refund(order_id="123", amount=49.99)
    2. [tool_call] lookup_order(order_id="123")
    3. [tool_call] send_confirmation(email="user@example.com")

  Expected: lookup_order before process_refund
  Actual:   process_refund was called at step 1, lookup_order at step 2

  Agent output: "Your refund of $49.99 has been processed."
  Cost: $0.003 | Tokens: 847 | Duration: 1.2s
```

For statistical failures:

```
FAILED test_refund.py::test_refund_requires_lookup (statistical)

  Pass rate: 7/10 (70.0%) — required: 95.0%

  Failure modes:
    2x — process_refund called before lookup_order
    1x — lookup_order was never called

  Cost: $0.031 total across 10 runs
```

---

## 12. CI Integration

### 12.1 GitHub Action

```yaml
# .github/workflows/agent-tests.yml
name: Agent Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install unitai[all]
      - run: unitai test --budget=5.00
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/unitai.xml
```

### 12.2 PR Gating

UnitAI produces JUnit XML natively. Any CI system that reads JUnit XML (GitHub Actions, GitLab CI, Jenkins, CircleCI) can gate PRs on UnitAI results with zero additional configuration.

### 12.3 Cost Reporting in CI

The CLI outputs a cost summary at the end of each run:

```
======================== UnitAI Results ========================
12 passed, 1 failed, 2 skipped in 34.2s
Total cost: $0.47 | Total tokens: 52,340 | LLM calls: 38
Budget remaining: $4.53 / $5.00
================================================================
```

---

## 13. Framework Adapter Implementation Details

### 13.1 LangGraph

**Detection:** Check if agent is instance of `langgraph.graph.state.CompiledStateGraph`.

**Tool injection approach:**
LangGraph tools are typically defined as functions with `@tool` decorator and passed to a `ToolNode`. The adapter:
1. Calls `extract_tools(agent)` to get the list of tool names from the graph's tool node.
2. Creates mock callables that match each tool's signature/schema.
3. Builds a new `ToolNode` with the mock callables.
4. Creates a copy of the compiled graph with the tool node replaced.

**Trajectory extraction:**
Use LangChain's `BaseCallbackHandler` interface. Register a custom handler on the run that captures:
- `on_tool_start(tool_name, tool_input)` → record tool call start
- `on_tool_end(output)` → record tool call result
- `on_llm_start(serialized, prompts)` → record LLM call start
- `on_llm_end(response)` → record LLM response with token counts

**State tracking:**
Subscribe to the graph's state channel. Diff state before/after each node to capture state_change steps.

### 13.2 CrewAI

**Detection:** Check if agent is instance of `crewai.Crew` or `crewai.Agent`.

**Tool injection approach:**
CrewAI tools implement `BaseTool` with a `_run` method. The adapter:
1. Iterates over agents in the Crew and their `tools` lists.
2. Creates `MockCrewAITool` instances that subclass `BaseTool` and route calls through UnitAI's mock layer.
3. Replaces each agent's tools list with the mocked versions.

**Trajectory extraction:**
CrewAI supports verbose output and callbacks. The adapter uses the task execution callbacks or patches `Agent._execute_task` to intercept tool usage.

### 13.3 OpenAI Agents SDK

**Detection:** Check if agent module path includes `openai.agents` or `agents`.

**Tool injection approach:**
OpenAI Agents define tools as `FunctionTool` objects with a callable. The adapter:
1. Iterates the agent's tools list.
2. Creates replacement `FunctionTool` instances where the callable is routed through UnitAI's mock layer.
3. Preserves the tool's name, description, and parameter schema.

**Trajectory extraction:**
Use the `Runner` with `run_sync()` or `Runner.run()`. The SDK emits `RunItem` events including `ToolCallItem` and `ToolCallOutputItem`. Iterate the run result's `new_items` to build the trajectory.

### 13.4 Semantic Kernel

**Detection:** Check if agent is instance of `semantic_kernel.Kernel`.

**Tool injection approach:**
SK uses plugins containing `KernelFunction` instances. The adapter:
1. Lists all registered plugins and their functions.
2. Creates mock `KernelFunction` instances that route through UnitAI's mock layer.
3. Registers mock functions under the same plugin/function names, overwriting originals.

**Trajectory extraction:**
SK supports function invocation filters (`FunctionInvocationFilter`). The adapter registers a filter that captures pre/post function invocation events including arguments and return values.

---

## 14. Error Handling & Edge Cases

### 14.1 Agent Timeout

If the agent exceeds the timeout (default 60s), UnitAI:
1. Cancels the execution (via thread interrupt or asyncio cancellation).
2. Records a partial trajectory up to the timeout point.
3. Sets `result.error` to `AgentTimeoutError`.
4. The test can assert on `result.failed` or inspect the partial trajectory.

### 14.2 Agent Infinite Loop

If the agent calls the same tool repeatedly (e.g., retrying endlessly), UnitAI detects this when a single tool is called more than `max_tool_calls` times (default: 50). Terminates the run with `AgentLoopDetectedError`.

### 14.3 LLM API Errors

If the LLM API returns an error (rate limit, auth failure, server error), UnitAI:
1. Does NOT retry (that's the agent's responsibility if it has retry logic).
2. Records the error in the trajectory.
3. Sets `result.error` to the original exception.

### 14.4 Async Agents

Many frameworks support async execution. UnitAI's `toolkit.run()` detects if the agent's execution method is async and uses `asyncio.run()` or integrates with the existing event loop. The public API remains synchronous — tests are always sync functions that block until the agent completes.

---

## 15. Roadmap (Out of Scope for v0.1, But Architecturally Considered)

These features are NOT in v0.1 but the architecture must not preclude them:

### 15.1 Multi-Agent Testing
Testing agent-to-agent interactions. The Trajectory model supports this by adding an `agent_id` field to TrajectoryStep. MockToolkit can manage mocks for multiple agents.

### 15.2 Snapshot Testing
Record a "golden" trajectory and assert that future runs match it (with configurable tolerance). Useful for regression testing. Trajectories are already serializable — snapshot files would be JSON.

### 15.3 UnitAI Cloud
Hosted service for: CI/CD integration without self-hosting, historical test results + regression dashboards, team collaboration, hosted LLM judge for semantic assertions ("assert output is helpful and polite"). The core framework MUST remain fully functional without the cloud service.

### 15.4 LLM-as-Judge Assertions
Instead of deterministic assertions, use an LLM to judge agent output quality. Example: `assert result.llm_judge("Was the refund handled professionally?", threshold=0.8)`. This is intentionally excluded from v0.1 — it adds cost, non-determinism, and complexity. The statistical runner + deterministic assertions cover the most important use cases first.

### 15.5 Scenario Generation
Generate test cases automatically from agent tool schemas. "Given these tools, generate 100 diverse user inputs and expected tool call patterns." Deferred to v0.2 — requires careful design to be useful and not just noisy.

---

## 16. v0.1 Scope & Priorities

### Must Have (v0.1 Launch)
1. MockToolkit with all four response strategies
2. Trajectory collector
3. Full assertion library (Sections 5.1-5.5)
4. Statistical runner with decorator and explicit API
5. LangGraph adapter (most popular framework, best trajectory extraction support)
6. Generic adapter (fallback for unsupported frameworks)
7. pytest plugin with fixtures and rich failure reporting
8. CLI (`unitai test`, `unitai init`)
9. Configuration via pyproject.toml
10. JUnit XML output
11. Cost tracking and budget limits
12. GitHub Action definition
13. README with 5-minute quickstart
14. 3 example test suites (LangGraph refund agent, generic chatbot, multi-tool research agent)

### Should Have (v0.1 If Time Permits)
1. OpenAI Agents SDK adapter
2. CrewAI adapter
3. Record/replay cache
4. `unitai results` command

### Deferred to v0.2
1. Semantic Kernel adapter
2. Multi-agent testing
3. Snapshot testing
4. LLM-as-judge assertions
5. Scenario generation
6. UnitAI Cloud

---

## 17. Naming & Branding

- **Package name:** `unitai`
- **PyPI:** `unitai`
- **GitHub:** `unitai-dev/unitai` (or `saalik/unitai` initially)
- **CLI command:** `unitai`
- **Import:** `from unitai import MockToolkit, statistical`
- **pytest plugin name:** `unitai`
- **Config section:** `[tool.unitai]`
- **Tagline:** "Write tests for your agents like you write tests for your code."
- **Positioning line:** "Salus catches bad actions at runtime. UnitAI prevents them from ever reaching runtime."

---

## 18. Success Criteria for v0.1 Launch

The framework is ready to launch when:

1. A developer can `pip install unitai`, write a test file for a LangGraph agent, and run it with `unitai test` in under 5 minutes.
2. The README includes a copy-pasteable example that works out of the box (with a simple agent included in the repo as a test fixture).
3. All 17 assertion methods in Section 5 work correctly.
4. Statistical runner correctly handles non-determinism and reports pass rates.
5. Cost tracking accurately reports token usage and estimated cost.
6. pytest integration works — tests are discovered, run, and reported with rich failure messages.
7. JUnit XML output is valid and parseable by GitHub Actions.
8. The GitHub Action definition works for a simple workflow.
9. At least 50 unit tests cover the framework itself.
10. Zero runtime dependencies beyond the Python standard library for the core package.

---

## 19. Development Plan

### 19.1 Guiding Principles

Build bottom-up. Each phase produces a working, testable artifact. No phase depends on unbuilt code from a later phase. The framework must be usable (in progressively more complete ways) at the end of every phase.

The dependency chain is: **Data Model → Mocks → Trajectory Collection → Assertions → Runner → Adapters → pytest Plugin → CLI → CI → Docs/Launch**.

Every phase includes its own tests. UnitAI tests itself — the framework's own test suite is written with pytest and validates each component in isolation before integration.

---

### Phase 1: Core Data Model & Mock Primitives

**Goal:** Build the foundational types and the mock tool system. At the end of this phase, a developer can create mock tools, invoke them manually, and inspect recorded calls. No agent execution yet — just the building blocks.

**Build order:**

1. **Project scaffolding**
   - Repository init with `pyproject.toml` (package metadata, build config, extras for adapters)
   - Directory structure per Section 2
   - Dev dependencies: pytest, ruff, mypy, pre-commit
   - CI: GitHub Actions workflow running linting + type checking + tests on every push

2. **`core/trajectory.py`** — Trajectory and TrajectoryStep dataclasses
   - Implement as frozen dataclasses or Pydantic models (decide: Pydantic adds a dependency, dataclasses keep it stdlib-only — prefer dataclasses for v0.1)
   - Trajectory must be serializable to JSON (for future snapshot testing and cache)
   - Implement `Trajectory.add_step()`, `Trajectory.to_dict()`, `Trajectory.from_dict()`

3. **`core/result.py`** — AgentRunResult container
   - Wraps a Trajectory
   - Exposes property accessors: `output`, `total_cost`, `duration`, `error`, `succeeded`, `failed`
   - Stub out assertion methods (raise `NotImplementedError`) — implemented in Phase 3

4. **`mock/strategies.py`** — Response strategy implementations
   - `StaticStrategy(value)` — always returns value
   - `SequenceStrategy(values)` — returns next value each call, raises `MockExhaustedError` when depleted
   - `ConditionalStrategy(conditions, default)` — evaluates lambdas against args
   - `ErrorStrategy(exception)` — raises exception
   - `CallableStrategy(fn)` — delegates to user function

5. **`mock/tool.py`** — MockTool
   - Holds a name, strategy, and call history
   - `invoke(args) -> Any` — executes strategy, records `MockToolCall`, returns result
   - `reset()` — clears call history

6. **`mock/toolkit.py`** — MockToolkit (partial)
   - `mock(name, return_value=None, side_effect=None, sequence=None, conditional=None)` — creates and registers a MockTool with the appropriate strategy
   - `get_tool(name) -> MockTool`
   - `as_dict() -> dict[str, Callable]` — returns dict of name→callable for generic adapter wiring
   - `reset()` — resets all tools
   - `run()` NOT implemented yet — stubbed to raise `NotImplementedError`

**Tests for this phase:**
- Unit tests for each response strategy (static returns value, sequence iterates, conditional matches, error raises, callable delegates)
- Sequence strategy raises on exhaustion
- MockTool records calls with correct args and timestamps
- MockToolkit registers tools, prevents duplicate names, retrieves by name
- Trajectory serializes to JSON and round-trips
- AgentRunResult exposes correct properties from a manually constructed Trajectory

**Success criteria:**
- [ ] All dataclasses type-check cleanly with mypy (strict mode)
- [ ] `MockToolkit` can register 5+ tools with different strategies and invoke them correctly
- [ ] `MockTool.calls` accurately records every invocation with args, result, and timestamp
- [ ] `Trajectory` serializes to JSON and deserializes back to an identical object
- [ ] 15+ unit tests pass
- [ ] CI pipeline (lint + type check + test) is green

**Estimated effort:** 2-3 days

---

### Phase 2: Generic Adapter & Agent Execution

**Goal:** Wire MockToolkit to actually run an agent. Use the generic adapter first — no framework-specific code yet. At the end of this phase, a developer can run a simple agent with mocked tools and get back a AgentRunResult with a real trajectory.

**Build order:**

1. **`adapters/base.py`** — BaseAdapter abstract class
   - Define the interface: `can_handle()`, `inject_mocks()`, `execute()`, `extract_tools()`
   - Document the contract each method must satisfy

2. **`adapters/generic.py`** — GenericAdapter
   - `inject_mocks()` is a no-op (user wires mocks manually via `toolkit.as_dict()`)
   - `execute()` takes a callable (the user's agent runner function), wraps it in trajectory collection context, returns completed Trajectory
   - Trajectory collection works by: the mock tools record their own calls during execution. After the callable returns, the adapter collects all calls from all MockTools and assembles them into a Trajectory in chronological order.

3. **`mock/toolkit.py`** — Complete `run()` and `run_generic()`
   - `run_generic(callable, timeout=60)` — executes the callable, collects trajectory from mock tools, returns AgentRunResult
   - `run(agent, input, adapter=None, ...)` — stubbed for now, will delegate to framework adapters in Phase 5. If no adapter found, raise with instructions to use `run_generic()`.
   - Implement timeout via `threading.Timer` that interrupts execution
   - Implement `strict` mode: if a tool name is invoked that wasn't mocked, raise `UnmockedToolError`

4. **Build a test fixture agent** — A simple agent that doesn't use any framework. Just a Python function that:
   - Takes a user message and a dict of tools
   - Calls OpenAI's API with tool definitions
   - Executes tool calls against the provided dict
   - Returns a final response
   - This agent lives in `tests/fixtures/simple_agent.py` and is used throughout UnitAI's own test suite

5. **Token/cost tracking**
   - During execution, intercept or parse LLM responses for `usage.prompt_tokens`, `usage.completion_tokens`
   - For the generic adapter: the user must pass token info manually, or UnitAI estimates from the mock tool call count (rough heuristic). Full tracking comes with framework adapters.
   - Store in Trajectory's `total_tokens` and `total_cost` fields
   - Cost estimation: maintain a simple model→price lookup table (e.g., gpt-4o = $2.50/1M input, $10/1M output)

**Tests for this phase:**
- Generic adapter runs a simple callable and collects trajectory
- Trajectory step ordering matches chronological tool call order
- Timeout kills a long-running agent and returns partial trajectory
- `strict=True` raises `UnmockedToolError` on unmocked tool
- `strict=False` logs warning and returns None for unmocked tool
- End-to-end: simple fixture agent with mocked tools produces correct trajectory

**Success criteria:**
- [ ] `toolkit.run_generic(my_fn)` executes and returns a `AgentRunResult` with populated trajectory
- [ ] Trajectory contains correct tool call steps in chronological order with accurate args/results
- [ ] Timeout works: agent running >60s is killed and `result.error` is `AgentTimeoutError`
- [ ] Strict mode works: unmocked tool call raises immediately
- [ ] At least one end-to-end test with the fixture agent making a real LLM API call (marked as integration test, requires API key)
- [ ] 12+ new unit tests pass (cumulative: 27+)

**Estimated effort:** 3-4 days

---

### Phase 3: Assertion Library

**Goal:** Implement all assertion methods on AgentRunResult. At the end of this phase, a developer can run an agent, then write expressive assertions about what the agent did. The assertions produce clear, human-readable failure messages.

**Build order:**

1. **`core/assertions.py`** — Standalone assertion functions
   - Each assertion is a pure function that takes a Trajectory and returns a boolean + failure message
   - This separation allows assertions to be reused outside of AgentRunResult (e.g., by the statistical runner for failure mode grouping)

2. **Tool call assertions (Section 5.1)**
   - `tool_was_called(trajectory, name)` — scan steps for any tool_call with matching name
   - `tool_not_called(trajectory, name)` — inverse
   - `tool_call_count(trajectory, name)` — count matching steps
   - `tool_called_with(trajectory, name, **kwargs)` — find a call with exact arg match
   - `tool_called_with_partial(trajectory, name, **kwargs)` — find a call where args are a superset of kwargs
   - `tool_called_before(trajectory, first, second)` — compare step_index of first occurrence of each
   - `tool_called_immediately_before(trajectory, first, second)` — first occurrence of second has step_index == first occurrence of first + 1 (counting only tool_call steps)
   - `call_order(trajectory)` — return list of tool names in order
   - `call_order_contains(trajectory, subsequence)` — subsequence matching

3. **Output assertions (Section 5.2)**
   - `output_contains(trajectory, text)` — substring check on final_output
   - `output_not_contains(trajectory, text)` — inverse
   - `output_matches(trajectory, pattern)` — regex match on final_output

4. **Cost & performance assertions (Section 5.3)**
   - These are just property comparisons on the trajectory/result — no special logic needed. But document them explicitly for discoverability.

5. **Error assertions (Section 5.4)**
   - `succeeded` / `failed` — check if trajectory.error is None
   - `error_is(type)` — isinstance check on trajectory.error

6. **Trajectory query API (Section 5.5)**
   - `get_calls(name)` → filter steps by tool name, return list of MockToolCall
   - `get_call(name, n=0)` → return Nth call to a specific tool

7. **Wire assertions into AgentRunResult**
   - Each method on AgentRunResult delegates to the corresponding function in assertions.py, passing `self.trajectory`
   - Override `__repr__` or use custom assertion introspection to produce rich failure messages when used with `assert`

8. **Failure message formatting**
   - When an assertion fails, produce a structured message showing: the assertion that failed, the actual trajectory (formatted as a numbered step list), the expected vs actual values, and agent output + cost + duration as context
   - Implement a `TrajectoryFormatter` that pretty-prints a trajectory for error output

**Tests for this phase:**
- Each assertion function tested with hand-crafted Trajectory objects (no LLM calls needed)
- `tool_called_before` with correct order → True, wrong order → False, tool not present → False
- `tool_called_with` exact match → True, partial mismatch → False
- `tool_called_with_partial` matches subset → True
- `call_order_contains` with interleaved calls → correctly identifies subsequence
- `output_contains` and `output_matches` with various patterns
- Failure messages are human-readable and include the trajectory
- Edge cases: empty trajectory, single step, tool called multiple times

**Success criteria:**
- [ ] All 17 assertion methods from Section 5 are implemented and tested
- [ ] Each assertion produces a clear, multi-line failure message showing expected vs actual
- [ ] `TrajectoryFormatter` produces readable output for trajectories of 1, 5, and 20+ steps
- [ ] Assertions work correctly on edge cases: empty trajectory, repeated tools, tools never called
- [ ] 25+ new unit tests (cumulative: 52+)

**Estimated effort:** 2-3 days

---

### Phase 4: Statistical Runner

**Goal:** Implement the statistical test execution layer. At the end of this phase, a developer can run a test N times and get aggregate pass/fail results with failure mode grouping.

**Build order:**

1. **`runner/statistical.py`** — StatisticalRunner class
   - Constructor: `StatisticalRunner(n=10, threshold=0.95, max_workers=5, budget=5.00)`
   - `run(test_fn, *args, **kwargs) -> StatisticalResult`
     - Execute `test_fn` N times
     - Each execution is wrapped in try/except to catch assertion errors
     - Collect all trajectories
     - Compute pass rate
     - Group failures by assertion error message

2. **Parallel execution**
   - Use `concurrent.futures.ThreadPoolExecutor` for parallel runs
   - `max_workers` defaults to `min(n, 5)` to avoid overwhelming LLM APIs
   - Each thread gets its own MockToolkit instance (deep copy) to avoid state contamination

3. **Cost safety**
   - Before the full run, execute once to measure actual cost
   - Extrapolate: `estimated_total = actual_first_run_cost * n`
   - If `estimated_total > budget`, raise `CostLimitExceeded` with the estimate and ask user to increase budget
   - Track cumulative cost across all runs, abort if budget exceeded mid-run

4. **StatisticalResult dataclass**
   - Fields per Section 7.3
   - `summary() -> str` — formatted summary string
   - `failure_modes` — group assertion error messages, count occurrences

5. **`@statistical` decorator**
   - Transforms a test function into one that uses StatisticalRunner internally
   - Detects if the function takes `mock_toolkit` argument and creates fresh instances per run
   - Final assertion: `assert stats.overall_passed` — fails the test if pass rate < threshold
   - Attach `StatisticalResult` to the test for reporting

6. **pytest marker `@pytest.mark.unitai_statistical`**
   - Alternative to the decorator, works via the pytest plugin (implemented in Phase 6 but marker registration happens here)

**Tests for this phase:**
- Runner with a deterministic always-pass function → 100% pass rate
- Runner with a deterministic always-fail function → 0% pass rate
- Runner with a function that fails 30% of the time (use random seed) → pass rate ≈ 70%
- Cost safety: mock a test that costs $1/run with budget $3 and n=10 → raises CostLimitExceeded after first run
- Failure mode grouping: function that fails with 2 different assertion messages → both appear in failure_modes with correct counts
- Parallel execution: n=10, max_workers=5 → runs complete faster than serial (timing assertion with tolerance)
- Each parallel run gets independent state (no cross-contamination between mock toolkits)

**Success criteria:**
- [ ] `StatisticalRunner.run()` executes N times and returns accurate `StatisticalResult`
- [ ] Pass rate computation is correct across deterministic and stochastic test functions
- [ ] Failure modes are grouped correctly by assertion message
- [ ] Cost safety aborts before exceeding budget
- [ ] Parallel execution works without state contamination
- [ ] `@statistical` decorator transforms a test function and integrates with `assert`
- [ ] `StatisticalResult.summary()` produces clean, readable output
- [ ] 15+ new unit tests (cumulative: 67+)

**Estimated effort:** 3-4 days

---

### Phase 5: LangGraph Adapter

**Goal:** Implement the first framework-specific adapter. At the end of this phase, a developer can write tests for LangGraph agents using `toolkit.run()` with automatic tool injection and trajectory collection. This is the highest-leverage adapter — LangGraph is the most popular agent framework.

**Build order:**

1. **Study LangGraph internals**
   - Understand how `CompiledStateGraph` stores tool nodes
   - Understand how `ToolNode` wraps tool functions
   - Understand the callback system (`BaseCallbackHandler`)
   - Understand how to copy/modify a compiled graph without mutating the original
   - Document findings in a comment block at the top of the adapter file

2. **`adapters/langgraph.py`** — LangGraphAdapter

3. **`can_handle(agent)`**
   - Check if agent is instance of `langgraph.graph.state.CompiledStateGraph`
   - Also accept `StateGraph` (not yet compiled) — compile it automatically

4. **`extract_tools(agent)`**
   - Walk the graph's nodes, find `ToolNode` instances
   - Extract tool names from the ToolNode's tool list
   - Return list of tool name strings

5. **`inject_mocks(agent, toolkit)`**
   - For each tool in the graph's ToolNode, create a mock callable that:
     - Has the same name and schema as the original tool
     - Routes invocations through `toolkit.get_tool(name).invoke(args)`
   - Build a new ToolNode with the mock callables
   - Create a modified copy of the compiled graph with the swapped ToolNode
   - Return the modified graph (never mutate the original)

6. **`execute(wrapped_agent, input, timeout)`**
   - Create a custom `BaseCallbackHandler` subclass that captures:
     - `on_tool_start` → create TrajectoryStep(step_type="tool_call", tool_name, tool_args)
     - `on_tool_end` → attach tool_result to the step
     - `on_llm_start` → create TrajectoryStep(step_type="llm_call", model)
     - `on_llm_end` → attach token counts and cost
   - Invoke the graph with `.invoke()` or `.ainvoke()`, passing the callback handler
   - Handle timeout via `asyncio.wait_for` or thread-based timeout
   - Assemble collected steps into a Trajectory
   - Extract final output from the graph's output state

7. **Complete `toolkit.run()` with adapter auto-detection**
   - `toolkit.run(agent, input)` now:
     - Iterates registered adapters (LangGraph first, then generic)
     - Calls `adapter.can_handle(agent)` on each
     - Uses the first matching adapter
     - Calls `inject_mocks` then `execute`
     - Returns AgentRunResult

8. **Build a LangGraph test fixture agent**
   - Simple LangGraph agent in `tests/fixtures/langgraph_agent.py`
   - Uses 2-3 tools (e.g., lookup_order, process_refund, send_email)
   - Has a clear happy path and a clear failure path
   - Used for integration tests

**Tests for this phase:**
- `can_handle` returns True for CompiledStateGraph, False for other types
- `extract_tools` correctly lists all tools from a LangGraph agent
- `inject_mocks` produces a graph that calls mock tools instead of real ones
- Original graph is not mutated after `inject_mocks`
- End-to-end: LangGraph fixture agent with mocked tools produces correct trajectory
- Trajectory includes both tool_call and llm_call steps in correct order
- Token counts and cost are populated from LLM response metadata
- `toolkit.run()` auto-detects LangGraph adapter
- Timeout works for LangGraph agent

**Success criteria:**
- [ ] `toolkit.run(langgraph_agent, "refund order 123")` works end-to-end with mocked tools
- [ ] Trajectory contains accurate tool call steps with correct names, args, and results
- [ ] LLM call steps include token counts and cost estimates
- [ ] Auto-detection correctly selects LangGraph adapter
- [ ] Original agent is never mutated
- [ ] Integration test with real LLM call passes (requires API key, marked accordingly)
- [ ] 12+ new tests (cumulative: 79+)

**Estimated effort:** 4-5 days (most complex phase — LangGraph internals require careful study)

---

### Phase 6: pytest Plugin & Failure Reporting

**Goal:** Make UnitAI a first-class pytest citizen. At the end of this phase, tests written with UnitAI are discovered, run, and reported by pytest with rich failure output. The statistical marker works. Fixtures are available.

**Build order:**

1. **`pytest_plugin/plugin.py`** — Plugin registration
   - Register via `pytest11` entry point in `pyproject.toml`
   - Register markers: `unitai_statistical`, `unitai_budget`, `unitai_skip_if_no_api_key`
   - Hook into `pytest_collection_modifyitems` to detect UnitAI tests
   - Hook into `pytest_runtest_protocol` to wrap statistical tests

2. **`pytest_plugin/fixtures.py`** — Fixtures
   - `mock_toolkit` fixture: creates fresh MockToolkit, yields it, calls reset after test
   - `unitai_config` fixture: loads config from pyproject.toml / unitai.toml

3. **Statistical marker integration**
   - When a test has `@pytest.mark.unitai_statistical(n=10, threshold=0.95)`:
     - The plugin wraps the test function in a StatisticalRunner
     - Runs it N times
     - Reports the StatisticalResult
     - Fails/passes based on threshold

4. **Budget marker integration**
   - `@pytest.mark.unitai_budget(max_cost=0.50)` → aborts test if cost exceeds limit

5. **API key skip marker**
   - `@pytest.mark.unitai_skip_if_no_api_key` → skips test if `OPENAI_API_KEY` (or relevant key) not set. Prevents CI failures when API keys aren't configured.

6. **Rich failure output**
   - Hook into `pytest_assertion_rewrite` or `pytest_runtest_makereport`
   - When a UnitAI assertion fails, inject the formatted trajectory, expected/actual values, and cost/duration into the failure report
   - For statistical failures, inject the summary (pass rate, failure modes)

7. **JUnit XML enrichment**
   - Attach UnitAI metadata (cost, tokens, duration, pass_rate) as properties on the JUnit XML test case elements
   - Ensures CI dashboards can display agent-specific metrics

**Tests for this phase:**
- pytest discovers and runs a UnitAI test file correctly
- `mock_toolkit` fixture provides a fresh toolkit and resets after test
- `unitai_statistical` marker runs test N times and reports pass rate
- `unitai_budget` marker aborts on cost overrun
- `unitai_skip_if_no_api_key` skips when key is absent
- Failure output includes trajectory, expected/actual, and cost
- JUnit XML output is valid XML and contains UnitAI properties
- Test these by running pytest programmatically via `pytest.main()` in the test suite and inspecting output

**Success criteria:**
- [ ] `pytest --co` discovers UnitAI test files and lists test functions
- [ ] `pytest test_refund.py` runs UnitAI tests and reports results normally
- [ ] Statistical marker runs test N times and reports pass rate in output
- [ ] Failure output shows the full trajectory, assertion details, and cost
- [ ] JUnit XML contains valid test results parseable by CI tools
- [ ] `mock_toolkit` fixture works correctly (fresh per test, resets after)
- [ ] 10+ new tests (cumulative: 89+)

**Estimated effort:** 3-4 days

---

### Phase 7: CLI

**Goal:** Implement the `unitai` command-line interface. At the end of this phase, developers run `unitai test` from their terminal and get formatted results with cost summaries.

**Build order:**

1. **`cli/main.py`** — CLI entrypoint using `argparse` (no click/typer dependency)
   - Subcommands: `test`, `init`, `cache`, `results`

2. **`unitai test`**
   - Translates to `pytest` invocation with UnitAI plugin flags
   - Pass-through flags: `--n`, `--threshold`, `--model`, `--budget`, `--record`, `--replay`, `--no-cache`
   - Sets corresponding env vars (`UNITAI_DEFAULT_N`, etc.) before invoking pytest
   - Appends UnitAI summary block after pytest output:
     ```
     ======================== UnitAI Results ========================
     12 passed, 1 failed, 2 skipped in 34.2s
     Total cost: $0.47 | Total tokens: 52,340 | LLM calls: 38
     Budget remaining: $4.53 / $5.00
     ================================================================
     ```

3. **`unitai init`**
   - Creates `unitai.toml` with default config values (commented, documented)
   - Creates `tests/test_agent_example.py` with a starter test template
   - Adds `.unitai/` to `.gitignore` if it exists

4. **`unitai cache`**
   - `unitai cache clear` — deletes `.unitai/cache/`
   - `unitai cache stats` — reports cache size, entry count, estimated savings
   - (Cache functionality itself is implemented in Phase 8; CLI commands are wired here, just report "cache not enabled" if Phase 8 isn't complete)

5. **`unitai results`**
   - Reads the last JUnit XML output file
   - Pretty-prints results: pass/fail per test, cost per test, total cost, failure summaries

6. **Entry point registration**
   - `[project.scripts]` in `pyproject.toml`: `unitai = "unitai.cli.main:main"`

**Tests for this phase:**
- `unitai test` invokes pytest and returns correct exit code
- `unitai init` creates config file and example test
- `unitai results` parses JUnit XML and displays formatted output
- CLI passes flags through to pytest correctly (verify via env var inspection)
- Help text (`unitai --help`, `unitai test --help`) is accurate

**Success criteria:**
- [ ] `unitai test` runs the test suite and prints UnitAI summary
- [ ] `unitai init` scaffolds a working config and example test in a fresh directory
- [ ] `unitai results` displays last run in readable format
- [ ] All CLI flags (`--n`, `--threshold`, `--model`, `--budget`) work correctly
- [ ] Exit codes are correct: 0 for all pass, 1 for any failure
- [ ] 8+ new tests (cumulative: 97+)

**Estimated effort:** 2-3 days

---

### Phase 8: Record/Replay Cache

**Goal:** Implement LLM response caching for deterministic re-runs and cost savings. At the end of this phase, a developer can run tests once with `--record` to cache LLM responses, then re-run with `--replay` for free, instant, deterministic execution.

**Build order:**

1. **`runner/replay.py`** — Cache manager
   - `ReplayCache(directory, ttl_hours)`
   - `get(cache_key) -> CachedResponse | None`
   - `put(cache_key, response)`
   - `clear()`
   - `stats() -> CacheStats` (entry count, size, hit rate)

2. **Cache key computation**
   - Hash of: model name, system prompt, user input (full message history), tool definitions (names + schemas), temperature setting
   - Use SHA-256. Key = hex digest. File = `.unitai/cache/{key}.json`

3. **CachedResponse format**
   - JSON file containing: the full LLM response object, token counts, model, timestamp, original cache key inputs (for debugging)

4. **Integration with adapters**
   - Add a `cache` parameter to the adapter's `execute()` method
   - Before making an LLM call, check the cache. On hit, return cached response. On miss, call the API and store the response.
   - For the generic adapter: this requires the user to integrate with a supported LLM client, or caching is unavailable (document this)
   - For the LangGraph adapter: intercept at the callback level — wrap the LLM's `generate` method with cache logic

5. **TTL and invalidation**
   - Each cache entry has a timestamp. Entries older than `ttl_hours` are ignored (treated as miss).
   - `unitai cache clear` deletes all entries.

6. **CLI integration**
   - `--record`: force fresh API calls, save all responses to cache
   - `--replay`: use cache only, raise `CacheMissError` if any request isn't cached
   - `--no-cache`: ignore cache entirely (default behavior)

**Tests for this phase:**
- Cache stores and retrieves responses correctly
- Cache key changes when model, prompt, or tools change
- Cache key is stable (same inputs → same key)
- TTL: expired entries are treated as misses
- `--record` populates cache
- `--replay` uses cache and fails on miss
- `clear` removes all entries
- `stats` reports accurate counts

**Success criteria:**
- [ ] First run with `--record` makes real API calls and populates cache
- [ ] Second run with `--replay` makes zero API calls, returns identical trajectory
- [ ] Cache key correctly changes when prompt, model, or tools change
- [ ] TTL expiration works
- [ ] `unitai cache stats` reports accurate cache size and hit count
- [ ] 10+ new tests (cumulative: 107+)

**Estimated effort:** 2-3 days

---

### Phase 9: Configuration System

**Goal:** Implement full configuration loading from `pyproject.toml` and `unitai.toml`, with environment variable overrides.

**Build order:**

1. **`config.py`** — Configuration loader
   - Load from `pyproject.toml` `[tool.unitai]` section (using `tomllib` from stdlib, Python 3.11+, or `tomli` for 3.10)
   - Fall back to `unitai.toml` if `pyproject.toml` doesn't have the section
   - Apply environment variable overrides (`UNITAI_*` prefix)
   - Return a typed `UnitAIConfig` dataclass

2. **Config schema** — all fields from Section 9.1
   - Validate types and ranges at load time
   - Provide sensible defaults for all fields

3. **Integration**
   - Wire config into MockToolkit (strict mode), StatisticalRunner (defaults), CLI (flags override config), cache (enabled/directory/ttl)
   - pytest plugin loads config once at session start

**Tests for this phase:**
- Config loads from pyproject.toml correctly
- Config loads from unitai.toml correctly
- Environment variables override file config
- Missing config file → all defaults
- Invalid values → clear error messages
- Per-test overrides take precedence over config

**Success criteria:**
- [ ] Config loads correctly from both file formats
- [ ] Environment variables override file values
- [ ] All components respect loaded config
- [ ] Invalid configuration produces clear error messages
- [ ] 8+ new tests (cumulative: 115+)

**Estimated effort:** 1-2 days

---

### Phase 10: CI Integration & GitHub Action

**Goal:** Ship a ready-to-use GitHub Action and CI documentation. At the end of this phase, a team can add UnitAI to their CI pipeline with a copy-paste YAML block.

**Build order:**

1. **`ci/github_action/action.yml`** — GitHub Action definition
   - Composite action that: installs Python, installs unitai, runs `unitai test`
   - Inputs: python-version, budget, model-override, extra-args
   - Outputs: pass-count, fail-count, total-cost
   - Uploads JUnit XML as artifact

2. **`ci/github_action/entrypoint.sh`** — Action runner script

3. **Documentation: CI setup guide**
   - GitHub Actions (primary)
   - GitLab CI (YAML example)
   - CircleCI (YAML example)
   - Generic: "any CI that runs pytest and reads JUnit XML"

4. **Cost reporting in CI**
   - The pytest plugin writes a cost summary as a GitHub Actions job summary (using `$GITHUB_STEP_SUMMARY`)
   - Cost per test + total cost visible in the PR check

**Tests for this phase:**
- GitHub Action YAML is valid (lint with actionlint)
- JUnit XML output is parseable by standard tools
- Cost summary format is correct

**Success criteria:**
- [ ] A test repo using the GitHub Action runs UnitAI tests and reports results
- [ ] JUnit XML artifact is uploaded and visible in GitHub Actions UI
- [ ] Cost summary appears in the GitHub Actions job summary
- [ ] CI docs cover GitHub Actions, GitLab CI, and CircleCI
- [ ] 3+ new tests (cumulative: 118+)

**Estimated effort:** 1-2 days

---

### Phase 11: Additional Adapters (Stretch)

**Goal:** Add OpenAI Agents SDK and CrewAI adapters. These follow the same pattern as the LangGraph adapter. Each is an independent work unit.

**Build order (per adapter):**

1. Study framework internals (tool definition, execution model, callback/tracing system)
2. Implement `can_handle()`, `extract_tools()`, `inject_mocks()`, `execute()`
3. Build a fixture agent for the framework
4. Write integration tests

**11a. OpenAI Agents SDK Adapter**
- Detection: check for `agents.Agent` class
- Tool injection: replace `FunctionTool` callables
- Trajectory extraction: iterate `RunResult.new_items` for `ToolCallItem` / `ToolCallOutputItem`
- **Estimated effort:** 2-3 days

**11b. CrewAI Adapter**
- Detection: check for `crewai.Crew` or `crewai.Agent`
- Tool injection: replace `BaseTool` instances in agent tool lists
- Trajectory extraction: use CrewAI callbacks or patch execution loop
- **Estimated effort:** 2-3 days

**Success criteria (per adapter):**
- [ ] `can_handle()` correctly identifies the framework
- [ ] `toolkit.run(framework_agent, input)` works end-to-end
- [ ] Trajectory is accurate (tool names, args, results, order)
- [ ] Original agent is not mutated
- [ ] Integration test with real LLM call passes
- [ ] 8+ new tests per adapter

---

### Phase 12: Documentation & Examples

**Goal:** Write all documentation needed for launch. At the end of this phase, a developer encountering UnitAI for the first time can go from zero to running tests in 5 minutes.

**Build order:**

1. **README.md**
   - Hero section: one-sentence description + tagline
   - 30-second install + run example (copy-pasteable, works out of the box)
   - Why UnitAI exists (the problem, positioned against Salus/Sentrial)
   - Core concepts: MockToolkit, Trajectory, Assertions, Statistical Runner
   - Quick links to full docs
   - Badges: PyPI version, tests passing, license

2. **docs/quickstart.md** — 5-minute getting started
   - Install
   - Write first test (step by step with a provided fixture agent)
   - Run it
   - Understand the output
   - Add to CI

3. **docs/assertions.md** — Full assertion reference
   - Every assertion method with example, expected output on success, and expected output on failure

4. **docs/adapters.md** — Framework adapter guide
   - LangGraph, OpenAI Agents, CrewAI, Generic
   - Setup, examples, known limitations per framework

5. **docs/statistical-testing.md** — Guide to statistical testing
   - Why agents need it, how to configure, how to interpret results

6. **docs/ci.md** — CI integration guide (from Phase 10)

7. **docs/configuration.md** — Full config reference

8. **Example test suites** (in `examples/` directory)
   - `examples/langgraph_refund/` — Refund agent with 5 tests
   - `examples/generic_chatbot/` — Simple chatbot with 3 tests
   - `examples/multi_tool_research/` — Research agent with 5+ tools, statistical tests
   - Each example is self-contained with its own README, agent code, and test file

**Success criteria:**
- [ ] A developer unfamiliar with UnitAI can follow the README and run a test in under 5 minutes (validated by having 2-3 people try it)
- [ ] All assertion methods are documented with examples
- [ ] All three example suites run successfully
- [ ] Docs are free of broken links and outdated API references
- [ ] README includes install instructions, quick example, and positioning

**Estimated effort:** 3-4 days

---

### Phase 13: Launch Preparation

**Goal:** Package, publish, and prepare all launch materials. At the end of this phase, UnitAI is live on PyPI and ready for public announcement.

**Build order:**

1. **Package publishing**
   - Finalize `pyproject.toml` metadata (description, classifiers, URLs, license)
   - Test build: `python -m build` → verify wheel and sdist
   - Publish to TestPyPI first, verify install works: `pip install -i https://test.pypi.org/simple/ unitai`
   - Publish to PyPI: `pip install unitai`

2. **GitHub repo polish**
   - License file (MIT)
   - Contributing guide (CONTRIBUTING.md)
   - Issue templates (bug report, feature request)
   - PR template
   - Code of conduct
   - GitHub topics/tags: `ai-agents`, `testing`, `pytest`, `llm`, `langchain`, `crewai`

3. **Launch content**
   - Show HN post draft (title + body, per HN guidelines)
   - Twitter/X thread draft (problem → solution → example → link)
   - Blog post: "How 5 Teams Test Their AI Agents (And Why It's Broken)"
   - LangChain Discord tutorial post draft
   - r/LangChain post draft
   - Product Hunt listing draft

4. **Pre-launch testing**
   - Fresh machine install test: clone repo, `pip install unitai`, run example — must work first try
   - Test on Python 3.10, 3.11, 3.12, 3.13
   - Test on macOS, Linux, Windows (via CI matrix)
   - Have 2-3 design partners run the release candidate

**Success criteria:**
- [ ] `pip install unitai` works from PyPI
- [ ] `pip install unitai[langraph]` installs with LangGraph adapter
- [ ] Fresh install on clean machine → example runs in under 5 minutes
- [ ] All tests pass on Python 3.10-3.13 on Linux, macOS, Windows
- [ ] GitHub repo has license, contributing guide, issue templates
- [ ] All launch content drafts are written and reviewed
- [ ] At least 2 design partners have validated the release candidate

**Estimated effort:** 2-3 days

---

### 19.2 Phase Summary

| Phase | What | Depends On | Effort | Cumulative Tests |
|-------|------|------------|--------|-----------------|
| 1 | Data model + mock primitives | — | 2-3 days | 15+ |
| 2 | Generic adapter + agent execution | Phase 1 | 3-4 days | 27+ |
| 3 | Assertion library | Phase 1 | 2-3 days | 52+ |
| 4 | Statistical runner | Phases 2, 3 | 3-4 days | 67+ |
| 5 | LangGraph adapter | Phase 2 | 4-5 days | 79+ |
| 6 | pytest plugin + failure reporting | Phases 3, 4 | 3-4 days | 89+ |
| 7 | CLI | Phase 6 | 2-3 days | 97+ |
| 8 | Record/replay cache | Phase 5 | 2-3 days | 107+ |
| 9 | Configuration system | Phase 7 | 1-2 days | 115+ |
| 10 | CI integration + GitHub Action | Phases 6, 7 | 1-2 days | 118+ |
| 11 | Additional adapters (stretch) | Phase 5 | 4-6 days | 134+ |
| 12 | Documentation + examples | All above | 3-4 days | — |
| 13 | Launch preparation | All above | 2-3 days | — |
| **Total** | | | **33-46 days** | **118-134** |

### 19.3 Critical Path

The minimum path to a launchable product:

**Phases 1 → 2 → 3 → 4 → 5 → 6 → 7 → 12 → 13**

This is ~28-37 days and gives you: core framework, LangGraph + generic adapters, full assertion library, statistical runner, pytest integration, CLI, docs, and launch. Cache (Phase 8), config system (Phase 9), CI action (Phase 10), and additional adapters (Phase 11) can ship as fast follow-ups in the first 2 weeks after launch.

### 19.4 Parallel Tracks

Some phases can run concurrently if you have help or want to interleave:

- **Phase 3 (assertions)** can run in parallel with **Phase 2 (generic adapter)** since assertions operate on hand-crafted Trajectory objects and don't need agent execution
- **Phase 8 (cache)** can run in parallel with **Phase 6 (pytest plugin)** since they're independent subsystems
- **Phase 9 (config)** can run in parallel with **Phase 10 (CI integration)**
- **Phase 12 (docs)** can start incrementally from Phase 5 onward — write docs for each component as it's completed

### 19.5 Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| LangGraph internals change between versions | Adapter breaks | Pin to LangGraph >= 0.2, test against multiple versions in CI |
| LLM API costs during test suite development | Budget overrun | Use gpt-4o-mini for all dev/test work, cache aggressively, mock LLM in unit tests (only integration tests hit real API) |
| pytest plugin conflicts with other plugins | Discovery/execution issues | Test alongside popular plugins (pytest-xdist, pytest-cov, pytest-asyncio) |
| Framework auto-detection misidentifies agent type | Wrong adapter used, confusing errors | Make detection checks specific (exact class checks, not duck typing), allow manual override |
| Non-determinism makes framework tests flaky | CI instability | Use record/replay cache in CI, pin random seeds where possible, use statistical runner for integration tests |
| Scope creep into LLM-as-judge / semantic assertions | Delays v0.1 launch | Hard boundary: v0.1 is deterministic assertions only. LLM-as-judge is explicitly v0.2. |
