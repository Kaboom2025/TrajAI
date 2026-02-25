# Show HN: TrajAI — Testing Framework for AI Agents

Hi HN,

I've been building AI agents and kept running into the same problem: there's no good way to test them. You either write integration tests that hit real APIs (slow, expensive, non-deterministic) or you just... don't test them at all. So I built TrajAI.

**What is it?**

TrajAI is a testing framework for AI agents. Mock tools, capture execution trajectories, and assert on what your agent *did* — not just what it said.

```python
from trajai.mock import MockToolkit

def test_refund_flow():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-456"})

    result = toolkit.run_callable(my_agent, "Refund order 123")

    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")
    assert result.output_contains("RF-456")
```

**Why mock tools instead of LLMs?**

At first I tried mocking LLM responses. It broke constantly — prompt changes, model updates, temperature variations all caused failures. The real behavior you care about is: did the agent call the right tools in the right order with the right arguments?

So TrajAI mocks the tools, not the LLM. Your agent runs with real LLM calls but deterministic tool responses. No side effects, fast tests, and you're asserting on actual behavior.

**Handling non-determinism:**

Even with mocked tools, LLMs are still non-deterministic. TrajAI includes a statistical test runner: run the test N times, assert on pass rate. "This agent calls the right tools 90% of the time" is a valid, useful test.

```python
@statistical(n=10, threshold=0.9)
def test_agent_behavior():
    ...
```

**Framework support:**

Works with LangGraph, CrewAI, OpenAI Agents SDK, or any Python callable. Tool injection is automatic for framework-specific agents. Generic adapter for custom agents.

**Current status:**

- Core: ✅ Mocking, trajectories, assertions
- Runners: ✅ Statistical testing with cost budgets
- Adapters: ✅ Generic, LangGraph, CrewAI, OpenAI Agents
- pytest plugin: ✅ Markers, fixtures, JUnit XML
- CLI: ✅ `trajai test` command
- Cache/replay: ✅ Record LLM responses for deterministic re-runs

It's MIT licensed and available on PyPI: `pip install trajai`

GitHub: https://github.com/saalik/trajai  
Docs: https://github.com/saalik/trajai/tree/main/docs

I'd love feedback on the approach. Is this a problem you've run into? How are you testing your agents today?

---

**Meta notes for launch:**
- Post during peak HN hours (weekday morning US time, ~10am-12pm ET)
- Respond to comments actively in the first few hours
- Have examples ready to share for different frameworks
- Be prepared to answer: "Why not just mock the LLM?" (answer is above)
