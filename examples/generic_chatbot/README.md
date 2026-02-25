# Generic Chatbot Example

A simple chatbot agent tested with UnitAI. Demonstrates basic mocking, assertions, and negative testing.

## What This Shows

- Mocking a single tool and asserting it was called
- Asserting on agent output content
- Negative assertions (tool was NOT called)

## Run

```bash
cd examples/generic_chatbot
pytest test_chatbot.py -v
```

## Files

- `agent.py` — A simple chatbot that uses a `knowledge_base` tool
- `test_chatbot.py` — Three tests covering basic assertion patterns
