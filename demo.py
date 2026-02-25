"""
TrajAI Phase 5 Demo — LangGraph Adapter
========================================
Run with:  python demo.py
"""
import warnings

warnings.filterwarnings("ignore")

from langchain_core.messages import AIMessage  # noqa: E402
from tests.fixtures.langgraph_agent import (  # noqa: E402
    FakeToolCallingModel,
    build_react_agent,
    get_tool_definitions,
    make_tool_call_message,
)
from trajai.mock.toolkit import AdapterNotFoundError, MockToolkit  # noqa: E402

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"

def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")

def ok(label: str, value: object) -> None:
    print(f"  {GREEN}✓{RESET}  {label}: {BOLD}{value}{RESET}")

def section(text: str) -> None:
    print(f"\n  {YELLOW}▶ {text}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1: Single tool call (order lookup)
# ─────────────────────────────────────────────────────────────────────────────
header("Scenario 1 — Single tool call")

model = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "42"}),
        AIMessage(content="Your order #42 has been delivered."),
    ],
    prompt_tokens=30,
    completion_tokens=15,
)
agent = build_react_agent(model, get_tool_definitions())

toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"id": "42", "status": "delivered"})

result = toolkit.run(agent, "What is the status of order 42?")

section("Assertions")
ok("tool_was_called('lookup_order')",         result.tool_was_called("lookup_order"))
ok("tool_not_called('process_refund')",       result.tool_not_called("process_refund"))
ok("output",                                  result.output)
ok("llm_calls",                               result.llm_calls)
ok("total_tokens",                            result.total_tokens)

section("Trajectory steps")
for step in result.trajectory.steps:
    if step.step_type == "tool_call":
        print(
            f"    [tool_call]  {step.tool_name}({step.tool_args})"
            f"  →  {step.tool_result}"
        )
    elif step.step_type == "llm_call":
        print(
            f"    [llm_call]   model={step.model}"
            f"  prompt={step.prompt_tokens}"
            f"  completion={step.completion_tokens}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2: Two tool calls in sequence (lookup → refund)
# ─────────────────────────────────────────────────────────────────────────────
header("Scenario 2 — Two tool calls in order")

model2 = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "99"}, call_id="c1"),
        make_tool_call_message(
            "process_refund", {"order_id": "99", "reason": "damaged"}, call_id="c2"
        ),
        AIMessage(content="Refund for order #99 approved."),
    ],
)
agent2 = build_react_agent(model2, get_tool_definitions())

toolkit2 = MockToolkit()
toolkit2.mock("lookup_order",  return_value={"id": "99", "status": "delivered"})
toolkit2.mock("process_refund", return_value={"success": True, "refund_id": "R-001"})

result2 = toolkit2.run(agent2, "Refund my damaged order 99")

section("Assertions")
ok("tool_was_called('lookup_order')",  result2.tool_was_called("lookup_order"))
ok("tool_was_called('process_refund')", result2.tool_was_called("process_refund"))
ok(
    "tool_called_before('lookup_order', 'process_refund')",
    result2.tool_called_before("lookup_order", "process_refund"),
)
ok("call_order()",            result2.call_order())
ok("output_contains('Refund')", result2.output_contains("Refund"))

section("Tool call details")
lookup_call  = result2.get_call("lookup_order")
refund_call  = result2.get_call("process_refund")
ok("lookup_order args",   lookup_call.args)
ok("process_refund args", refund_call.args)
ok("process_refund result", refund_call.result)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3: No tool call (pure chat)
# ─────────────────────────────────────────────────────────────────────────────
header("Scenario 3 — No tool called (pure chat)")

model3 = FakeToolCallingModel(
    responses=[AIMessage(content="The weather in London is lovely today!")],
)
agent3 = build_react_agent(model3, get_tool_definitions())

toolkit3 = MockToolkit()
toolkit3.mock("get_weather", return_value={"city": "London", "temperature": "18C"})

result3 = toolkit3.run(agent3, "Tell me something nice about London")

section("Assertions")
ok("tool_not_called('get_weather')",   result3.tool_not_called("get_weather"))
ok("tool_not_called('lookup_order')",  result3.tool_not_called("lookup_order"))
ok("output",                           result3.output)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4: Mock returns a custom sequence
# ─────────────────────────────────────────────────────────────────────────────
header("Scenario 4 — Sequence mock (called twice)")

model4 = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "1"}, call_id="x1"),
        make_tool_call_message("lookup_order", {"order_id": "2"}, call_id="x2"),
        AIMessage(content="Both orders checked."),
    ],
)
agent4 = build_react_agent(model4, get_tool_definitions())

toolkit4 = MockToolkit()
toolkit4.mock(
    "lookup_order",
    sequence=[
        {"id": "1", "status": "shipped"},
        {"id": "2", "status": "delivered"},
    ],
)

result4 = toolkit4.run(agent4, "Check orders 1 and 2")

section("Assertions")
ok("tool_call_count('lookup_order', 2)", result4.tool_call_count("lookup_order", 2))
ok("call 0 result",                      result4.get_call("lookup_order", 0).result)
ok("call 1 result",                      result4.get_call("lookup_order", 1).result)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 5: AdapterNotFoundError for unknown agent type
# ─────────────────────────────────────────────────────────────────────────────
header("Scenario 5 — AdapterNotFoundError for unknown agent")

toolkit5 = MockToolkit()
try:
    toolkit5.run(object(), "hello")
    print(f"  {RED}✗  Expected AdapterNotFoundError but nothing was raised{RESET}")
except AdapterNotFoundError as e:
    ok("AdapterNotFoundError raised", True)
    print(f"     message: {e}")

print(f"\n{BOLD}{GREEN}All scenarios complete.{RESET}\n")
