# Why Testing AI Agents Is Broken (And How to Fix It)

## The Problem

You're building an AI agent. It uses an LLM to decide which tools to call, what order to call them in, and what arguments to pass. You want to test it.

So you do what any good engineer would do: you write a test.

```python
def test_refund_agent():
    result = agent.run("Refund order 123")
    assert "refund" in result.output.lower()
```

This test is garbage.

It doesn't check if the agent called the right tools. It doesn't verify the order. It doesn't inspect arguments. It just greps the output for a keyword. If the agent says "Sorry, I can't process that refund" — the test passes.

## Attempt 1: Integration Tests

Fine. You write a real integration test. It hits your production database, calls real APIs, processes actual payments.

Now you have new problems:

1. **Slow.** Each test takes 5-10 seconds because you're making real API calls.
2. **Expensive.** Every test costs money (LLM API fees, payment processing fees).
3. **Flaky.** Rate limits, network timeouts, third-party API downtime — all cause random failures.
4. **Side effects.** You're creating real orders, charging real cards, sending real emails. Test isolation is impossible.
5. **Non-deterministic.** The LLM behaves differently each run. Same input, different tool calls. Your test passes 8 times and fails twice.

This isn't sustainable for a test suite that needs to run on every commit.

## Attempt 2: Mock the LLM

Okay, so you mock the LLM response:

```python
@patch("openai.ChatCompletion.create")
def test_refund_agent(mock_llm):
    mock_llm.return_value = {
        "choices": [{"message": {"content": "Here is the refund..."}}]
    }
    # ...
```

This breaks constantly.

You change the system prompt? Test breaks. You add a new tool? Test breaks. OpenAI updates the model? Test breaks. You adjust temperature? Test breaks.

You're not testing your agent anymore. You're testing your ability to predict LLM outputs.

## What You Actually Care About

Here's what matters when testing an agent:

- Did it call `lookup_order` before `process_refund`?
- Did it pass the correct `order_id` to the refund tool?
- Did it skip the refund when the order wasn't eligible?
- Did it handle errors gracefully?

You care about *behavior*, not text output.

## The Solution: Mock Tools, Not LLMs

This is what UnitAI does differently. Instead of mocking the LLM (fragile) or hitting real APIs (slow, expensive), you mock the *tools*.

```python
from unitai.mock import MockToolkit

def test_refund_agent():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered", "amount": 50.0})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-456"})

    result = toolkit.run_callable(refund_agent, "Refund order 123")

    # Assert on what the agent DID
    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")
    
    call = result.get_call("process_refund", 0)
    assert call.args["order_id"] == "123"
    assert call.args["amount"] == 50.0
```

Your agent runs with **real LLM calls** but **mocked tool responses**. No side effects. Deterministic tool behavior. Fast. Cheap.

And when a test fails, you get a full trajectory:

```
Trajectory (3 steps, 0.8s, $0.0012):

[0] 10:23:01.234  llm_call
    model: gpt-4o-mini
    tokens: 234

[1] 10:23:01.456  tool_call → lookup_order
    args: {"order_id": "123"}
    result: {"status": "delivered", "amount": 50.0}

[2] 10:23:01.678  tool_call → process_refund
    args: {"order_id": "123", "amount": 50.0}
    result: {"confirmation": "RF-456"}
```

You see exactly what happened, step by step.

## Handling Non-Determinism

"But the LLM is still non-deterministic! Sometimes it calls tools in a different order."

True. And UnitAI handles this with statistical testing:

```python
from unitai.runner import statistical

@statistical(n=10, threshold=0.9)
def test_agent_uses_correct_tools():
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": [...]})
    result = toolkit.run_callable(agent, "Find the report")
    assert result.tool_was_called("search")
```

This runs the test 10 times. If 9 out of 10 runs pass, the test passes. You're asserting on *rates*, not absolutes.

"This agent calls the right tools 90% of the time" is a valid, useful assertion. It acknowledges reality: LLMs aren't deterministic, and that's okay.

## Framework Support

UnitAI works with any agent framework:

- **LangGraph** — auto-detects `CompiledStateGraph`, replaces tools in `ToolNode`
- **CrewAI** — auto-detects `Crew` and `Agent`, replaces `BaseTool` instances
- **OpenAI Agents SDK** — auto-detects `agents.Agent`, replaces `FunctionTool` objects
- **Generic** — any Python callable that takes `(input, tools)`

For framework-specific agents, tool injection is automatic. Just call `toolkit.run(agent, input)` and UnitAI figures out the rest.

## How We Test AI Agents at [Your Company]

Since adopting UnitAI, our agent test suite:

- Runs in **under 30 seconds** (down from 15 minutes)
- Costs **$0.02 per run** (down from $5-10)
- Catches **real bugs** (like tool call ordering issues we never checked before)
- Runs on **every commit** in CI (too slow before)

We have 50+ agent tests covering refund flows, order lookup, support escalation, and research workflows. They're fast, cheap, and reliable.

## Try It

UnitAI is open source (MIT license) and available on PyPI:

```bash
pip install unitai
```

5-minute quickstart: [link to docs]  
GitHub: [link]  
Examples: [link to examples/]

If you're building AI agents and frustrated with testing, give it a shot. I'd love to hear what you think.

---

**Publishing strategy:**
- Post on personal/company blog
- Submit to HN, r/MachineLearning, r/LangChain
- Share on LinkedIn with case study angle
- Consider submitting to tech publications (The New Stack, InfoQ)
