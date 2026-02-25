# Assertion Reference

Complete reference for all assertion methods available on `AgentRunResult`.

Every assertion is available in two forms:

- **Boolean API** — Returns `True`/`False`. Use with Python's `assert`.
- **Assert API** — Raises `TrajAIAssertionError` with a formatted trajectory on failure.

```python
from trajai.mock import MockToolkit

toolkit = MockToolkit()
toolkit.mock("search", return_value={"results": ["doc1"]})
result = toolkit.run_callable(agent, "Find the report")

# Boolean API
assert result.tool_was_called("search")

# Assert API (better failure messages)
result.assert_tool_was_called("search")
```

---

## Tool Call Assertions

### `tool_was_called(name)`

Check if a tool was called at least once.

```python
# Boolean
assert result.tool_was_called("lookup_order")

# Assert
result.assert_tool_was_called("lookup_order")
```

**Passes:** Tool `lookup_order` appears in the trajectory.

**Failure message:** `Tool 'lookup_order' was never called.`

---

### `tool_not_called(name)`

Check if a tool was never called.

```python
assert result.tool_not_called("delete_account")
result.assert_tool_not_called("delete_account")
```

**Passes:** Tool `delete_account` does not appear in the trajectory.

**Failure message:** `Tool 'delete_account' was called but expected not to be.`

---

### `tool_call_count(name, count)`

Check if a tool was called exactly N times.

```python
assert result.tool_call_count("search", 3)
result.assert_tool_call_count("search", 3)
```

**Passes:** Tool `search` was called exactly 3 times.

**Failure message:** `Tool 'search' was called 1 times, expected 3.`

---

### `tool_called_with(name, **kwargs)`

Check if a tool was called with exact arguments at least once.

```python
assert result.tool_called_with("lookup_order", order_id="123")
result.assert_tool_called_with("lookup_order", order_id="123")
```

**Passes:** At least one call to `lookup_order` had `{"order_id": "123"}` as its exact arguments.

**Failure message:** `Tool 'lookup_order' was never called with exact args: {'order_id': '123'}`

---

### `tool_called_with_partial(name, **kwargs)`

Check if a tool was called with arguments containing these key-value pairs (allows additional keys).

```python
assert result.tool_called_with_partial("create_order", customer_id="C-1")
result.assert_tool_called_with_partial("create_order", customer_id="C-1")
```

**Passes:** At least one call to `create_order` had `customer_id="C-1"` in its arguments (other keys may also be present).

**Failure message:** `Tool 'create_order' was never called with partial args matching: {'customer_id': 'C-1'}`

---

### `tool_called_before(first, second)`

Check if the first occurrence of one tool was called before the first occurrence of another.

```python
assert result.tool_called_before("lookup_order", "process_refund")
result.assert_tool_called_before("lookup_order", "process_refund")
```

**Passes:** `lookup_order` first appears at an earlier step index than `process_refund`.

**Failure message:** `Tool 'lookup_order' (step 3) was NOT called before 'process_refund' (step 1).`

---

### `tool_called_immediately_before(first, second)`

Check if one tool was called directly before another with no other tool calls in between.

```python
assert result.tool_called_immediately_before("validate", "submit")
result.assert_tool_called_immediately_before("validate", "submit")
```

**Passes:** In the sequence of tool calls, `validate` appears immediately followed by `submit`.

**Failure message:** `Tool 'validate' was NOT called immediately before 'submit'.`

---

### `call_order_contains(subsequence)`

Check if a specific subsequence of tool calls appears in order (not necessarily consecutively).

```python
assert result.call_order_contains(["search", "summarize", "send_email"])
result.assert_call_order_contains(["search", "summarize", "send_email"])
```

**Passes:** The tools `search`, `summarize`, and `send_email` appear in that order in the trajectory (other tools may appear between them).

**Failure message:** `Trajectory does NOT contain tool call subsequence: ['search', 'summarize', 'send_email']`

---

## Output Assertions

### `output_equals(text)`

Check if the agent's final output matches text exactly.

```python
assert result.output_equals("Order 123 has been refunded.")
result.assert_output_equals("Order 123 has been refunded.")
```

**Failure message:** `Agent output does NOT match. Expected: '...', Actual: '...'`

---

### `output_contains(text)`

Check if the agent's final output contains a substring.

```python
assert result.output_contains("refunded")
result.assert_output_contains("refunded")
```

**Failure message:** `Agent output does NOT contain: 'refunded'`

---

### `output_not_contains(text)`

Check if the agent's final output does NOT contain a substring.

```python
assert result.output_not_contains("error")
result.assert_output_not_contains("error")
```

**Failure message:** `Agent output contains 'error' but expected not to.`

---

### `output_matches(pattern)`

Check if the agent's final output matches a regex pattern.

```python
assert result.output_matches(r"RF-\d+")
result.assert_output_matches(r"RF-\d+")
```

**Failure message:** `Agent output does NOT match pattern: 'RF-\d+'`

---

## Query API

These methods retrieve data from the result rather than asserting.

### `call_order()`

Returns the list of tool names called, in order.

```python
order = result.call_order()
# ["lookup_order", "process_refund"]
```

---

### `get_calls(name)`

Returns all `MockToolCall` objects for a specific tool.

```python
calls = result.get_calls("search")
for call in calls:
    print(call.args)      # Tool arguments dict
    print(call.result)    # Tool return value
    print(call.timestamp) # When the call happened
    print(call.error)     # Exception if the tool raised
```

---

### `get_call(name, n=0)`

Returns the Nth call to a specific tool (0-indexed). Raises `IndexError` if the tool wasn't called that many times.

```python
first_search = result.get_call("search", 0)
print(first_search.args)    # {"query": "quarterly report"}
print(first_search.result)  # {"results": [...]}

second_search = result.get_call("search", 1)
```

---

## Properties

### `output`

The agent's final text output, or `None` if the agent produced no output.

```python
print(result.output)  # "Your refund has been processed."
```

### `total_cost`

Total LLM API cost across all LLM calls in the trajectory.

```python
print(result.total_cost)  # 0.0023
```

### `total_tokens`

Total tokens (prompt + completion) across all LLM calls.

```python
print(result.total_tokens)  # 1547
```

### `duration`

Total execution time in seconds.

```python
print(result.duration)  # 2.34
```

### `llm_calls`

Number of LLM API calls made during execution.

```python
print(result.llm_calls)  # 3
```

### `succeeded`

`True` if the agent completed without raising an exception.

```python
assert result.succeeded
```

### `failed`

`True` if the agent raised an exception during execution.

```python
assert result.failed
```

### `error`

The exception raised by the agent, or `None` if it succeeded.

```python
if result.error:
    print(type(result.error).__name__, result.error)
```

---

## Metadata Assertions (Pure Functions)

These are available as pure functions in `unitai.core.assertions` but are not exposed as methods on `AgentRunResult`. Use them directly with the trajectory:

```python
from trajai.core.assertions import cost_under, tokens_under, duration_under, llm_calls_under

passed, message = cost_under(result.trajectory, 0.05)
passed, message = tokens_under(result.trajectory, 5000)
passed, message = duration_under(result.trajectory, 10.0)
passed, message = llm_calls_under(result.trajectory, 5)
```

### `cost_under(trajectory, limit)`

Returns `(True, message)` if total cost is below the limit.

### `tokens_under(trajectory, limit)`

Returns `(True, message)` if total tokens are below the limit.

### `duration_under(trajectory, limit)`

Returns `(True, message)` if execution duration is below the limit (seconds).

### `llm_calls_under(trajectory, limit)`

Returns `(True, message)` if the number of LLM calls is below the limit.

---

## Error Assertions

### `error_is(exception_type)`

Check if the agent raised a specific exception type (boolean API only).

```python
assert result.error_is(ValueError)
```

### `succeeded` / `failed`

See [Properties](#properties) above.
