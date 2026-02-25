# Statistical Testing

LLMs are non-deterministic. The same agent with the same input might call different tools, in a different order, or produce different output across runs. TrajAI's statistical testing lets you assert on *rates* instead of absolutes: "this agent uses the correct tools at least 90% of the time."

---

## Why Statistical Tests?

A traditional unit test is binary: pass or fail. But with LLM-powered agents:

- An agent might call `search` before `summarize` 95% of the time, but occasionally reverse the order.
- An agent might correctly identify the right tool 9 out of 10 times.
- Temperature, model updates, and prompt sensitivity cause run-to-run variation.

Statistical testing handles this by running the same test N times and checking if the pass rate meets a threshold.

---

## Using the `@statistical` Decorator

The simplest way to run statistical tests:

```python
from trajai.mock import MockToolkit
from trajai.runner import statistical

@statistical(n=10, threshold=0.9)
def test_agent_calls_correct_tool():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    toolkit.mock("search_products", return_value={"results": []})

    result = toolkit.run_callable(agent, "Check order 123")
    assert result.tool_was_called("lookup_order")
    assert result.tool_not_called("search_products")
```

This runs the test 10 times. If at least 9 out of 10 runs pass (90%), the test passes. Otherwise it raises `TrajAIStatisticalError`.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | `int` | Config default (10) | Number of times to run the test |
| `threshold` | `float` | Config default (0.95) | Required pass rate (0.0 to 1.0) |
| `max_workers` | `int` | Config default (5) | Max parallel threads for concurrent runs |
| `budget` | `float` | Config default (1.00) | Cost budget in dollars. Aborts if exceeded. |

---

## Using `StatisticalRunner` Directly

For more control, use the `StatisticalRunner` class:

```python
from trajai.runner.statistical import StatisticalRunner

def my_test():
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": ["doc1"]})
    result = toolkit.run_callable(agent, "Find the report")
    assert result.tool_was_called("search")

runner = StatisticalRunner(n=20, threshold=0.85, budget=5.00)
stat_result = runner.run(my_test)

print(stat_result.summary())
```

### `StatisticalResult`

The runner returns a `StatisticalResult` dataclass:

```python
stat_result.total_runs     # 20
stat_result.passed_runs    # 18
stat_result.failed_runs    # 2
stat_result.pass_rate      # 0.9
stat_result.total_cost     # 0.0456
stat_result.failure_modes  # {"AssertionError: Tool 'search' was never called.": 2}
```

The `failure_modes` dictionary groups failures by error message, so you can see *why* tests failed — not just how many.

### `summary()`

```
Statistical Result: 18/20 passed (90.0%)
Total Cost: $0.0456
Failure Modes:
  2x — AssertionError: Tool 'search' was never called.
```

---

## Cost Budget Protection

Statistical tests run the same test many times, which means many LLM API calls. TrajAI protects against runaway costs:

1. **Calibration run.** The first run executes serially. Its cost is multiplied by N to estimate total cost.
2. **Pre-flight check.** If the estimated total exceeds the budget, the test aborts immediately with `CostLimitExceeded`.
3. **Mid-run check.** Cumulative cost is tracked across parallel runs. If it exceeds the budget, remaining runs are cancelled.

```python
@statistical(n=50, threshold=0.9, budget=2.00)
def test_expensive_agent():
    # If run 1 costs $0.05, estimated total = $2.50 > $2.00 budget
    # Test aborts with CostLimitExceeded before running the other 49 times
    ...
```

---

## Execution Model

1. **Run 1** executes serially (calibration).
2. **Runs 2-N** execute in parallel using a thread pool (controlled by `max_workers`).
3. Each run gets a fresh `MockToolkit` if the test function accepts a `mock_toolkit` parameter.
4. Non-assertion exceptions (e.g., `RuntimeError`) immediately cancel all runs and re-raise.

---

## pytest Integration

Use the `@pytest.mark.trajai` marker to configure statistical testing per-test:

```python
import pytest

@pytest.mark.trajai(n=10, threshold=0.9)
def test_agent_behavior():
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": ["doc1"]})
    result = toolkit.run_callable(agent, "Find the report")
    assert result.tool_was_called("search")
```

The marker parameters override config defaults for that specific test.

---

## Configuration

Set defaults in `pyproject.toml`:

```toml
[tool.trajai]
default_n = 10
default_threshold = 0.95
max_workers = 5
cost_budget_per_test = 1.00
```

Or via environment variables:

```bash
export TRAJAI_DEFAULT_N=10
export TRAJAI_DEFAULT_THRESHOLD=0.95
export TRAJAI_MAX_WORKERS=5
export TRAJAI_COST_BUDGET_PER_TEST=1.00
```

See [Configuration](configuration.md) for the full reference.
