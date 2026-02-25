# r/LangChain Post: UnitAI — Testing Framework for AI Agents

**Title:** I built a testing framework for LangGraph/LangChain agents (mocks tools, not LLMs)

---

Hey r/LangChain,

I've been working with LangGraph for a while and kept running into the same problem: testing agents is really hard. You either write integration tests that hit real APIs (slow, expensive, flaky) or you just... ship and hope.

So I built **UnitAI** — a testing framework specifically for AI agents.

## The Core Idea

Instead of mocking LLM responses (which breaks every time you change a prompt), UnitAI mocks the *tools*. Your agent runs with real LLM calls but deterministic tool responses.

```python
from trajai.mock import MockToolkit

def test_my_agent():
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": ["doc1", "doc2"]})
    toolkit.mock("summarize", return_value={"summary": "..."})

    result = toolkit.run(my_langgraph_agent, "Find and summarize the report")

    # Assert on what the agent DID
    assert result.tool_was_called("search")
    assert result.tool_called_before("search", "summarize")
```

## Why This Works

When you test an agent, you don't really care about the exact text it produces. You care about:

- Did it call the right tools?
- In the right order?
- With the right arguments?
- Did it skip tools when it should?

UnitAI captures all of that in a `Trajectory` object and gives you assertion methods to check everything.

## LangGraph Support

For LangGraph, UnitAI automatically:

1. Finds all `ToolNode` instances in your graph
2. Replaces tools with mock wrappers
3. Records LLM calls via callback handler
4. Restores original tools after execution (your graph is never mutated)

Just call `toolkit.run(compiled_graph, input)` and it works.

## Handling Non-Determinism

LLMs are non-deterministic. Sometimes your agent calls tools in a slightly different order. UnitAI handles this with statistical testing:

```python
@statistical(n=10, threshold=0.9)
def test_agent():
    # Runs the test 10 times
    # Passes if 9+ runs pass
    ...
```

You're asserting on *behavior rates*, not absolutes. "This agent uses the correct tools 90% of the time" is a valid, useful test.

## Example: Testing a Refund Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from trajai.mock import MockToolkit

# Your LangGraph agent (simplified)
tools = [lookup_order, process_refund]
model = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
# ... build graph ...
agent = graph.compile()

def test_refund_flow():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-456"})

    result = toolkit.run(agent, "Refund order 123")

    assert result.tool_called_before("lookup_order", "process_refund")
    assert result.output_contains("RF-456")
```

## Features

- ✅ Works with LangGraph, CrewAI, OpenAI Agents, or any Python callable
- ✅ Mock strategies: static, sequence, conditional, side effects, errors
- ✅ Assertions: tool calls, ordering, arguments, output content
- ✅ Statistical test runner for non-determinism
- ✅ pytest integration (markers, fixtures, JUnit XML)
- ✅ Cost budget protection (abort if tests exceed budget)
- ✅ Cache/replay mode for deterministic CI runs

## Install

```bash
pip install trajai[langgraph]
```

## Links

- GitHub: https://github.com/saalik/trajai
- Docs: https://github.com/saalik/trajai/tree/main/docs
- Quick Start: https://github.com/saalik/trajai/blob/main/docs/quickstart.md
- LangGraph Examples: https://github.com/saalik/trajai/tree/main/examples

It's MIT licensed and works with pytest out of the box.

I'd love to hear your thoughts or answer questions. How are you testing your LangGraph agents today?

---

**r/LangChain posting tips:**
- Post during weekday mornings/early afternoons US time
- Use code formatting for examples
- Be responsive to questions in the first few hours
- Crosspost to r/LangChainCommunity if allowed
- Consider posting to r/MachineLearning and r/LocalLLaMA as well
