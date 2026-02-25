# Refund Agent Example

A multi-step refund workflow agent tested with TrajAI. Demonstrates ordering constraints, argument validation, sequence mocks, and error handling.

## What This Shows

- Enforcing tool call ordering (`lookup_order` before `process_refund`)
- Validating tool call arguments
- Sequence mocks for repeated tool calls
- Output content assertions
- Negative assertions for edge cases

## Run

```bash
cd examples/refund_agent
pytest test_refund.py -v
```

## Files

- `agent.py` — A refund processing agent with lookup, eligibility check, and refund tools
- `test_refund.py` — Five tests covering multi-step workflow patterns
