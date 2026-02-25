# Reference: demo.py to Examples Mapping

This document shows how the scenarios in `demo.py` map to the individual example files in the `tests/examples/` folder.

## Mapping

| demo.py Scenario | Example File | Focus Area |
|------------------|--------------|-----------|
| Scenario 1 | `scenario_1_single_tool_call.py` | Basic mock and assertions |
| Scenario 2 | `scenario_2_two_tool_calls_sequence.py` | Tool ordering and multi-step workflows |
| Scenario 3 | `scenario_3_no_tool_call.py` | Negative assertions (tools not called) |
| Scenario 4 | `scenario_4_sequence_mock.py` | Sequence mocks for repeated calls |
| Scenario 5 | `scenario_5_error_handling.py` | Error handling and edge cases |

## Differences Between demo.py and Individual Examples

### demo.py
- **Purpose**: Show all scenarios at once with colored output
- **Format**: Single file with 5 scenarios sequentially
- **Output**: Pretty-printed with ANSI colors
- **Audience**: Visual learners, quick overview

**Run with:**
```bash
python demo.py
```

### Individual Example Files
- **Purpose**: Deep dive into each scenario with extensive comments
- **Format**: Standalone files with detailed docstrings and section headers
- **Output**: Colored output + detailed explanations
- **Audience**: Hands-on learners, building understanding

**Run with:**
```bash
python tests/examples/scenario_1_single_tool_call.py
python tests/examples/scenario_2_two_tool_calls_sequence.py
# ... etc
```

## Which Should You Use?

### Use `demo.py` if you want to:
- Get a quick visual overview of all scenarios
- See everything at once (takes ~3 min to run)
- Share a demo with colleagues
- Understand the breadth of UnitAI capabilities

### Use Individual Example Files if you want to:
- Study one scenario deeply
- Learn at your own pace
- Modify and experiment with the code
- Reference specific patterns for your tests
- Teach others (each file is self-contained)

## Code Duplication Policy

The individual scenario files intentionally duplicate code from `demo.py` because:

1. **Self-contained learning** — Each file can be studied independently
2. **Easier modification** — Students can edit without affecting others
3. **Clear documentation** — Each file has detailed docstrings for that specific pattern
4. **Pedagogical value** — Repetition aids learning
5. **Low maintenance cost** — Changes to both are infrequent

This is a conscious trade-off favoring learnability over DRY principles.

## Integration with Tests

These examples are **NOT** part of the test suite. They are learning resources that happen to use the same agents and mocks as the tests.

- Examples: `tests/examples/*.py` — Learning resources
- Unit tests: `tests/test_*.py` — Actual test coverage
- Both use: `tests/fixtures/` — Shared test agents

You can run examples independently:
```bash
# Examples (educational)
python tests/examples/scenario_1_single_tool_call.py

# Tests (verification)
pytest tests/test_assertions_tool_calls.py
```

## Quick Reference: What Each Scenario Covers

```
Scenario 1: Single Tool Call
├── Mock: return_value parameter
├── Assertions: tool_was_called(), tool_not_called()
├── Result: output, llm_calls, total_tokens
└── Trajectory: Iterating steps

Scenario 2: Two Tool Calls in Sequence
├── Mock: Multiple tools registered
├── Assertions: tool_called_before(), call_order()
├── Result: output_contains()
└── Workflow: Argument flow verification

Scenario 3: No Tool Call (Pure Chat)
├── Mock: Tools registered but not used
├── Assertions: Negative assertions (tool_not_called)
├── Result: Cost-efficiency validation
└── Pattern: General knowledge handling

Scenario 4: Sequence Mock (Repeated Calls)
├── Mock: sequence parameter (list of return values)
├── Assertions: tool_call_count(), get_call(n)
├── Result: Batch processing behavior
└── Pattern: Iterative loops with different data

Scenario 5: Error Handling
├── Exception: AdapterNotFoundError
├── Pattern: try/except with expected failures
├── Testing: pytest.raises() pattern
└── Pattern: Graceful error handling
```

## Tips for Using Both

1. **Start with demo.py** — Get the big picture (5 min)
2. **Explore individual files** — Deep dive into each (30 min)
3. **Modify examples** — Try changing return values, assertions (10 min)
4. **Write your own** — Create tests for your agent (ongoing)

## See Also

- `QUICK_START.md` — Fast onboarding guide
- `README.md` — Comprehensive documentation
- `demo.py` — All scenarios with visual output
- `CLAUDE.md` — Full API reference
