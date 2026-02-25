# Framework Adapters

UnitAI supports multiple AI agent frameworks through adapters. Each adapter handles tool injection (replacing real tools with mocks) and trajectory collection (recording what the agent did).

---

## Generic Adapter (Any Python Callable)

The generic adapter works with any Python function. You write the agent, you wire the tools.

### Install

```bash
pip install trajai
```

No extras needed.

### Usage

Your agent function receives an input string and a tools dictionary:

```python
def my_agent(input: str, tools: dict) -> str:
    result = tools["lookup_order"]({"order_id": "123"})
    return f"Order status: {result['status']}"
```

Test it with `run_callable`:

```python
from trajai.mock import MockToolkit

def test_agent():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered", "id": "123"})

    result = toolkit.run_callable(my_agent, "Check order 123")

    assert result.tool_was_called("lookup_order")
    assert result.output_contains("delivered")
```

### Alternative: `run_generic`

For agents that don't take input/tools parameters (e.g., agents that capture these via closure):

```python
def test_with_closure():
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": ["doc1"]})
    tools = toolkit.as_dict()

    def agent():
        return tools["search"]({"query": "report"})

    result = toolkit.run_generic(agent)
    assert result.tool_was_called("search")
```

### Known Limitations

- You must wire tools manually (no auto-injection).
- LLM calls are not automatically recorded. Use `toolkit.record_llm_call()` if you need LLM metadata in the trajectory.

---

## LangGraph Adapter

Auto-detects `CompiledStateGraph` and `StateGraph` instances. Tools are automatically replaced with mocks inside `ToolNode` nodes.

### Install

```bash
pip install trajai[langgraph]
```

### Usage

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return {"order_id": order_id, "status": "delivered"}

@tool
def process_refund(order_id: str, amount: float) -> dict:
    """Process a refund for an order."""
    return {"order_id": order_id, "confirmation": "RF-001"}

# Build your LangGraph agent
tools = [lookup_order, process_refund]
model = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)

def call_model(state: MessagesState):
    return {"messages": [model.invoke(state["messages"])]}

def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if last.tool_calls:
        return "tools"
    return "__end__"

graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "__end__": "__end__"})
graph.add_edge("tools", "agent")
agent = graph.compile()
```

Test it with `run()` — UnitAI auto-detects the framework:

```python
from trajai.mock import MockToolkit

def test_langgraph_refund():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})
    toolkit.mock("process_refund", return_value={"confirmation": "RF-456"})

    result = toolkit.run(agent, "Refund order 123")

    assert result.tool_was_called("lookup_order")
    assert result.tool_called_before("lookup_order", "process_refund")
```

### How It Works

1. UnitAI finds all `ToolNode` instances in the graph.
2. For each tool with a registered mock, the real `StructuredTool` is swapped with a mock wrapper.
3. The agent runs normally with real LLM calls but mocked tool responses.
4. After execution, original tools are restored (the original graph is never mutated).
5. LLM calls are captured via a LangChain callback handler.

### Known Limitations

- Only tools inside `ToolNode` are detected. Custom tool-calling nodes require manual wiring.
- The callback handler captures token usage from LangChain's `llm_output` or `usage_metadata`. Some models may not report tokens.

---

## CrewAI Adapter

Supports `Crew` and `Agent` objects. Tools are replaced using Pydantic `model_copy()` to avoid mutating the original objects.

### Install

```bash
pip install trajai[crewai]
```

### Usage

```python
from crewai import Agent, Crew, Task
from crewai.tools import BaseTool

class LookupOrderTool(BaseTool):
    name: str = "lookup_order"
    description: str = "Look up an order by ID"

    def _run(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "delivered"}

agent = Agent(
    role="Customer Service",
    goal="Help customers with orders",
    backstory="You are a helpful agent.",
    tools=[LookupOrderTool()],
)

crew = Crew(
    agents=[agent],
    tasks=[Task(description="Handle refund", expected_output="Refund result", agent=agent)],
)
```

Test it:

```python
from trajai.mock import MockToolkit

def test_crewai_agent():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})

    result = toolkit.run(crew, "Refund order 123")

    assert result.tool_was_called("lookup_order")
```

You can also pass a single `Agent` instead of a `Crew` — UnitAI wraps it in a minimal crew automatically.

### How It Works

1. For each agent in the crew, tools with matching mock names are replaced with mock `BaseTool` subclasses.
2. The crew/agent is copied via `model_copy()` — the original is never modified.
3. `crew.kickoff()` (or a wrapper crew for lone agents) is called.
4. Tool calls are recorded by the mock layer.

### Known Limitations

- CrewAI agents make real LLM calls. LLM token/cost metadata requires manual recording via `toolkit.record_llm_call()`.
- Crew-level callbacks for LLM tracking are not yet auto-injected.

---

## OpenAI Agents SDK Adapter

Supports `agents.Agent` instances from the `openai-agents` package. Tool injection replaces `FunctionTool` objects with mock wrappers.

### Install

```bash
pip install trajai[openai-agents]
```

### Usage

```python
from agents import Agent, function_tool

@function_tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return {"order_id": order_id, "status": "delivered"}

agent = Agent(
    name="Customer Service",
    instructions="Help customers with their orders.",
    tools=[lookup_order],
)
```

Test it:

```python
from trajai.mock import MockToolkit

def test_openai_agent():
    toolkit = MockToolkit()
    toolkit.mock("lookup_order", return_value={"status": "delivered"})

    result = toolkit.run(agent, "Check order 123")

    assert result.tool_was_called("lookup_order")
```

### How It Works

1. The agent is shallow-copied via `copy.copy()`.
2. `FunctionTool` objects with matching mock names get async `on_invoke_tool` wrappers that delegate to UnitAI mocks.
3. `Runner.run_sync()` executes the agent.
4. LLM metadata (model, tokens) is extracted from `run_result.raw_responses`.

### Known Limitations

- Only `FunctionTool` objects are replaceable. Other tool types (e.g., hosted tools) are passed through unchanged.
- The agent must be compatible with `Runner.run_sync()`.

---

## Auto-Detection

When you call `toolkit.run(agent, input)`, UnitAI checks adapters in this order:

1. **LangGraph** — Is it a `CompiledStateGraph` or `StateGraph`?
2. **OpenAI Agents** — Is it an `agents.Agent`?
3. **CrewAI** — Is it a `Crew` or `crewai.Agent`?

If no adapter matches, an `AdapterNotFoundError` is raised with a message listing supported frameworks and install commands.

For the generic adapter, use `toolkit.run_callable()` or `toolkit.run_generic()` explicitly.
