# Research Agent Example

A research agent with multiple tools, tested with UnitAI including statistical testing for handling LLM non-determinism.

## What This Shows

- Agents with 5+ tools
- Subsequence ordering assertions
- Statistical test decorator for non-deterministic behavior
- Cost budget assertions via trajectory metadata
- Query API for inspecting specific tool calls

## Run

```bash
cd examples/research_agent
pytest test_research.py -v
```

Note: Statistical tests run the test function multiple times. Tests using `@statistical` will take longer as they execute N iterations.

## Files

- `agent.py` — A research agent that searches, fetches, summarizes, cites, and exports
- `test_research.py` — Tests including statistical pass rate assertions
