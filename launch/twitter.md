# Twitter/X Launch Thread

## Tweet 1 (Hook)

Testing AI agents is broken.

You either:
• Hit real APIs → slow, expensive, flaky
• Mock LLM responses → breaks on every prompt change
• Don't test → pray and ship

There's a better way. 🧵

## Tweet 2 (Problem)

The real behavior you care about isn't what the LLM *says*.

It's what your agent *does*:
• Which tools did it call?
• In what order?
• With what arguments?

You can't assert on that with traditional testing.

## Tweet 3 (Solution)

UnitAI mocks the tools, not the LLM.

Your agent runs with real LLM calls but deterministic tool responses.

Mock → Run → Assert on behavior.

```python
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={...})
toolkit.mock("process_refund", return_value={...})

result = toolkit.run(agent, "Refund order 123")

assert result.tool_called_before("lookup_order", "process_refund")
```

## Tweet 4 (Features)

What you get:
✅ Mock any tool with static values, sequences, conditionals, or side effects
✅ Assert on tool calls, ordering, arguments, and output
✅ Full execution trajectory captured automatically
✅ Statistical testing for LLM non-determinism
✅ Works with LangGraph, CrewAI, OpenAI Agents, or any Python callable

## Tweet 5 (Statistical Testing)

LLMs are still non-deterministic.

UnitAI handles this: run the test N times, assert on pass rate.

"This agent calls the right tools 90% of the time" is a valid test.

```python
@statistical(n=10, threshold=0.9)
def test_agent():
    ...
```

## Tweet 6 (Status)

UnitAI is:
• Open source (MIT)
• Available on PyPI: `pip install unitai`
• Production-ready

Works with pytest out of the box. Integrates with GitHub Actions, GitLab CI, CircleCI.

Docs: [link]
GitHub: [link]

## Tweet 7 (CTA)

If you're building AI agents and frustrated with testing, give it a try.

Would love your feedback.

⭐ Star the repo: [link]
📦 Install: `pip install unitai`
📖 Docs: [link]

---

**Launch timing:**
- Post thread during weekday afternoon (2-4pm ET)
- Pin the thread to profile
- Retweet with additional context after a few hours
- Engage with replies actively
