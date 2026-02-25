# TrajAI Examples — Quick Start

Welcome! This folder has 5 hands-on scenarios showing how to test AI agents with TrajAI.

## 🚀 Run All Examples

```bash
# Run all scenarios at once
python -m pytest tests/examples/ -v

# Or run individual scenarios
python tests/examples/scenario_1_single_tool_call.py
python tests/examples/scenario_2_two_tool_calls_sequence.py
python tests/examples/scenario_3_no_tool_call.py
python tests/examples/scenario_4_sequence_mock.py
python tests/examples/scenario_5_error_handling.py
```

## 📚 What You'll Learn

| Scenario | Focus | What You'll Practice |
|----------|-------|---------------------|
| 1️⃣ **Single Tool Call** | Basics | Simple mocks, basic assertions, inspecting results |
| 2️⃣ **Two Tool Calls** | Ordering | Multiple mocks, enforcing call order, argument flow |
| 3️⃣ **No Tool Call** | Negative Testing | Assertions for tools NOT called, cost optimization |
| 4️⃣ **Sequence Mock** | Iteration | Repeated calls, sequence mock strategy, batch processing |
| 5️⃣ **Error Handling** | Edge Cases | Catching exceptions, handling unsupported frameworks |

## 💡 Key Patterns You'll See

### Pattern 1: Basic Mock + Assert
```python
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"status": "delivered"})
result = toolkit.run(agent, "Check my order")
assert result.tool_was_called("lookup_order")
```

### Pattern 2: Multiple Tools + Ordering
```python
toolkit = MockToolkit()
toolkit.mock("lookup", return_value={"id": "123"})
toolkit.mock("refund", return_value={"success": True})
result = toolkit.run(agent, "Refund order 123")
assert result.tool_called_before("lookup", "refund")
```

### Pattern 3: Sequence Mock (Repeated Calls)
```python
toolkit = MockToolkit()
toolkit.mock("check_status", sequence=[
    {"id": "1", "status": "shipped"},
    {"id": "2", "status": "delivered"},
])
result = toolkit.run(agent, "Check orders 1 and 2")
assert result.tool_call_count("check_status", 2)
```

## 🎯 Learning Path

1. Start with **Scenario 1** — Get comfortable with basic setup
2. Move to **Scenario 2** — Learn multi-step workflows
3. Try **Scenario 3** — Understand negative assertions
4. Explore **Scenario 4** — Master sequence mocks
5. Finish with **Scenario 5** — Handle edge cases

After completing all 5, check:
- `CLAUDE.md` — Full API reference
- `demo.py` — All scenarios combined with colored output
- `tests/` — Real unit tests for each feature

## 📖 Full Documentation

For more details on each scenario, see [README.md](./README.md)

---

**Ready?** Start with Scenario 1:
```bash
python tests/examples/scenario_1_single_tool_call.py
```
