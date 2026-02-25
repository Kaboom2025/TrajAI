"""
Scenario 4: Sequence Mock (Tool Called Multiple Times)
======================================================

What it simulates:
    An agent that calls the same tool multiple times, with different return values
    each time. The sequence mock provides a list of values to return in order.

Use case:
    Testing agents that iterate or batch-process items, where each call should get
    a different response. Critical for:
    - Batch processing workflows (check multiple orders, process each)
    - Iteration patterns (loop through items)
    - State-dependent behavior (responses change based on iteration)

Key concepts demonstrated:
    - sequence mock parameter (list of return values)
    - tool_call_count() assertion (verify N calls)
    - get_call(tool_name, index) to access nth invocation
    - Verifying each call got the expected result

Real-world example:
    Agent checking multiple order IDs in a loop. First call returns "shipped",
    second returns "delivered". The agent needs different data for each iteration.
"""

import warnings
warnings.filterwarnings("ignore")

from langchain_core.messages import AIMessage
from unitai.mock.toolkit import MockToolkit
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
# Setup: Create an agent that calls the same tool twice
# ─────────────────────────────────────────────────────────────────────────────
print_header("Scenario 4 — Sequence Mock (Repeated Tool Calls)")

# Build an agent that calls lookup_order twice (for different order IDs)
model = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "1"}, call_id="x1"),
        make_tool_call_message("lookup_order", {"order_id": "2"}, call_id="x2"),
        AIMessage(content="Both orders checked."),
    ],
)
agent = build_react_agent(model, get_tool_definitions())

# Register a sequence mock: each call to lookup_order gets the next value in the list
toolkit = MockToolkit()
toolkit.mock(
    "lookup_order",
    sequence=[
        {"id": "1", "status": "shipped"},
        {"id": "2", "status": "delivered"},
    ],
)

# Run the agent
print_section("Running agent that calls lookup_order twice")
result = toolkit.run(agent, "Check orders 1 and 2")


# ─────────────────────────────────────────────────────────────────────────────
# Assertions: Verify the tool was called N times with correct results
# ─────────────────────────────────────────────────────────────────────────────
print_section("Assertions - Multiple Calls with Sequence Mock")

# Verify the tool was called exactly twice
print_ok(
    "result.tool_call_count('lookup_order', 2)",
    result.tool_call_count("lookup_order", 2)
)

# Verify it wasn't called more or fewer times
if result.tool_call_count("lookup_order", 2):
    print_ok("Tool called exactly twice", True)
else:
    actual_count = len([s for s in result.trajectory.steps if s.step_type == "tool_call" and s.tool_name == "lookup_order"])
    print(f"  {RED}✗ Expected 2 calls, got {actual_count}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Access each individual call result
# ─────────────────────────────────────────────────────────────────────────────
print_section("Results from Each Call")

# First call (index 0)
call_0 = result.get_call("lookup_order", 0)
print(f"    Call 0:")
print(f"      - Arguments: {call_0.args}")
print(f"      - Result:    {call_0.result}")
print_ok(
    "Call 0 result status",
    call_0.result.get("status") == "shipped"
)

# Second call (index 1)
call_1 = result.get_call("lookup_order", 1)
print(f"    Call 1:")
print(f"      - Arguments: {call_1.args}")
print(f"      - Result:    {call_1.result}")
print_ok(
    "Call 1 result status",
    call_1.result.get("status") == "delivered"
)


# ─────────────────────────────────────────────────────────────────────────────
# Trajectory: Show each call in sequence
# ─────────────────────────────────────────────────────────────────────────────
print_section("Full Trajectory (execution order)")

for i, step in enumerate(result.trajectory.steps):
    if step.step_type == "tool_call":
        print(
            f"    Step {i}: [tool_call] {step.tool_name}({step.tool_args})"
            f" → {step.tool_result}"
        )
    elif step.step_type == "llm_call":
        print(
            f"    Step {i}: [llm_call] model={step.model}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Advanced: Verify order_id tracking across iterations
# ─────────────────────────────────────────────────────────────────────────────
print_section("Advanced - Argument Tracking Across Calls")

# Collect all arguments from lookup_order calls
lookup_calls = result.get_calls("lookup_order")

print(f"    lookup_order calls made with order_ids:")
for i, call in enumerate(lookup_calls):
    order_id = call.args.get("order_id")
    status = call.result.get("status")
    print(f"      Call {i}: order_id={order_id} → status={status}")


# ─────────────────────────────────────────────────────────────────────────────
# Why sequences matter
# ─────────────────────────────────────────────────────────────────────────────
print_section("Why Sequence Mocks Are Important")
print("  ✓ Different return values for each iteration")
print("  ✓ Simulates real batch-processing behavior")
print("  ✓ Tests agent handles varying data correctly")
print("  ✓ Avoids side_effect complexity for simple sequences")


# ─────────────────────────────────────────────────────────────────────────────
# Common pattern: What if you have 3+ calls?
# ─────────────────────────────────────────────────────────────────────────────
print_section("Pattern: Accessing Multiple Calls")
print("  # For a tool called N times:")
print("  for i in range(result.tool_call_count('my_tool')):")
print("      call = result.get_call('my_tool', i)")
print("      print(f'Call {i}: {call.args} → {call.result}')")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{GREEN}✓ Scenario 4 complete!{RESET}")
print(f"  This example showed how to:")
print(f"    1. Use sequence mock for repeated tool calls")
print(f"    2. Verify tool_call_count() for N invocations")
print(f"    3. Access each call result with get_call(name, index)")
print(f"    4. Verify argument flow across multiple iterations")
print(f"    5. Test batch-processing agent behavior")
print()
