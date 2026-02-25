"""
Scenario 2: Two Tool Calls in Sequence
=======================================

What it simulates:
    An agent that performs multiple actions in sequence (lookup order, then process refund).

Use case:
    Testing multi-step workflows where tool call order matters and you need to assert
    dependencies between actions. This is critical for workflows like:
    - Authentication then resource access
    - Data lookup then processing
    - Validation then action

Key concepts demonstrated:
    - Multiple mocks registered at once
    - Ordering assertions: tool_called_before()
    - call_order() to see the full sequence
    - output_contains() for partial output matching
    - get_call() with specific call details

Real-world example:
    Refund processing that MUST look up the order first to verify it exists before
    processing the refund. If the order is called after the refund, it's a logic error.
"""

import warnings
warnings.filterwarnings("ignore")

from langchain_core.messages import AIMessage
from trajai.mock.toolkit import MockToolkit
from tests.fixtures.langgraph_agent import (
    FakeToolCallingModel,
    build_react_agent,
    get_tool_definitions,
    make_tool_call_message,
)

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"

def print_header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")

def print_ok(label: str, value: object) -> None:
    print(f"  {GREEN}✓{RESET}  {label}: {BOLD}{value}{RESET}")

def print_section(text: str) -> None:
    print(f"\n  {YELLOW}▶ {text}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Setup: Create a multi-step agent
# ─────────────────────────────────────────────────────────────────────────────
print_header("Scenario 2 — Two Tool Calls in Sequence")

# Build an agent that calls lookup_order, then process_refund, then responds
model = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "99"}, call_id="c1"),
        make_tool_call_message("process_refund", {"order_id": "99", "reason": "damaged"}, call_id="c2"),
        AIMessage(content="Refund for order #99 approved."),
    ],
)
agent = build_react_agent(model, get_tool_definitions())

# Register multiple mocks
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"id": "99", "status": "delivered"})
toolkit.mock("process_refund", return_value={"success": True, "refund_id": "R-001"})

# Run the agent
print_section("Running agent with multiple tool calls")
result = toolkit.run(agent, "Refund my damaged order 99")


# ─────────────────────────────────────────────────────────────────────────────
# Assertions: Verify both tools were called AND in correct order
# ─────────────────────────────────────────────────────────────────────────────
print_section("Assertions - Presence and Ordering")

# Both tools were called
print_ok(
    "result.tool_was_called('lookup_order')",
    result.tool_was_called("lookup_order")
)
print_ok(
    "result.tool_was_called('process_refund')",
    result.tool_was_called("process_refund")
)

# CRITICAL: Order matters - lookup must happen BEFORE refund
print_ok(
    "result.tool_called_before('lookup_order', 'process_refund')",
    result.tool_called_before("lookup_order", "process_refund")
)

# Get the call sequence
call_sequence = result.call_order()
print_ok("result.call_order()", call_sequence)

# Check output contains expected content
print_ok(
    "result.output_contains('Refund')",
    result.output_contains("Refund")
)


# ─────────────────────────────────────────────────────────────────────────────
# Tool Call Details: Inspect each call
# ─────────────────────────────────────────────────────────────────────────────
print_section("Tool Call Details (each step)")

lookup_call = result.get_call("lookup_order")
print(f"    lookup_order:")
print(f"      - Arguments: {lookup_call.args}")
print(f"      - Result:    {lookup_call.result}")

refund_call = result.get_call("process_refund")
print(f"    process_refund:")
print(f"      - Arguments: {refund_call.args}")
print(f"      - Result:    {refund_call.result}")


# ─────────────────────────────────────────────────────────────────────────────
# Trajectory: Inspect the full execution sequence
# ─────────────────────────────────────────────────────────────────────────────
print_section("Full Trajectory")
for i, step in enumerate(result.trajectory.steps):
    if step.step_type == "tool_call":
        print(
            f"    Step {i}: [tool_call] {step.tool_name}({step.tool_args})"
            f" → {step.tool_result}"
        )
    elif step.step_type == "llm_call":
        print(
            f"    Step {i}: [llm_call] model={step.model} "
            f"prompt_tokens={step.prompt_tokens}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Advanced: Verify argument passing through the workflow
# ─────────────────────────────────────────────────────────────────────────────
print_section("Advanced - Argument Flow Across Steps")

# Verify that the order_id flows from lookup to refund
lookup_order_id = lookup_call.args.get("order_id")
refund_order_id = refund_call.args.get("order_id")

print(f"    lookup_order was called with order_id: {lookup_order_id}")
print(f"    process_refund was called with order_id: {refund_order_id}")

if lookup_order_id == refund_order_id:
    print_ok("Order IDs match across calls", True)
else:
    print(f"    {RED}✗ Order IDs don't match!{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{GREEN}✓ Scenario 2 complete!{RESET}")
print(f"  This example showed how to:")
print(f"    1. Register multiple mocks for different tools")
print(f"    2. Assert tool_called_before() to enforce ordering")
print(f"    3. Use call_order() to see the full sequence")
print(f"    4. Verify argument flow across workflow steps")
print(f"    5. Check output content with output_contains()")
print()
