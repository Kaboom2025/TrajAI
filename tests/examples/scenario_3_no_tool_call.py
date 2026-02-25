"""
Scenario 3: No Tool Call (Pure Chat)
====================================

What it simulates:
    An agent that responds with pure conversation, not calling any tools.

Use case:
    Testing that an agent correctly recognizes when a question doesn't require tool use.
    This is important for:
    - Verifying agent doesn't make unnecessary API calls (cost, latency)
    - Ensuring general knowledge questions don't trigger tool invocation
    - Testing agent's judgment about when tools are needed

Key concepts demonstrated:
    - Negative assertions: tool_not_called()
    - Handling pure LLM responses without tool invocation
    - Verifying output content when tools aren't used

Real-world example:
    Chatbot responding to casual conversation or general knowledge questions
    without needing to call external data sources. The agent should know to
    respond directly without wasting API calls.
"""

import warnings
warnings.filterwarnings("ignore")

from langchain_core.messages import AIMessage
from unitai.mock.toolkit import MockToolkit
from tests.fixtures.langgraph_agent import (
    FakeToolCallingModel,
    build_react_agent,
    get_tool_definitions,
)

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"

def print_header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")

def print_ok(label: str, value: object) -> None:
    print(f"  {GREEN}✓{RESET}  {label}: {BOLD}{value}{RESET}")

def print_section(text: str) -> None:
    print(f"\n  {YELLOW}▶ {text}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Setup: Create an agent that won't call tools
# ─────────────────────────────────────────────────────────────────────────────
print_header("Scenario 3 — No Tool Called (Pure Chat)")

# Build an agent that will NOT call any tools, just respond directly
model = FakeToolCallingModel(
    responses=[AIMessage(content="The weather in London is lovely today!")],
)
agent = build_react_agent(model, get_tool_definitions())

# Register mocks (even though they won't be used)
# This demonstrates that you can mock tools but the agent won't necessarily call them
toolkit = MockToolkit()
toolkit.mock("get_weather", return_value={"city": "London", "temperature": "18C"})
toolkit.mock("lookup_order", return_value={"id": "123", "status": "shipped"})

# Run the agent with a general knowledge question
print_section("Running agent with question that doesn't need tools")
result = toolkit.run(agent, "Tell me something nice about London")


# ─────────────────────────────────────────────────────────────────────────────
# Assertions: Verify that NO tools were called
# ─────────────────────────────────────────────────────────────────────────────
print_section("Assertions - No Tools Were Called")

# These tools were NOT called (even though we mocked them)
print_ok(
    "result.tool_not_called('get_weather')",
    result.tool_not_called("get_weather")
)
print_ok(
    "result.tool_not_called('lookup_order')",
    result.tool_not_called("lookup_order")
)

# Verify the output is what we expect (pure LLM response)
print_ok(
    "result.output",
    result.output
)

# How many tool calls were made in total?
print_ok(
    "Total tool calls in trajectory",
    sum(1 for step in result.trajectory.steps if step.step_type == "tool_call")
)


# ─────────────────────────────────────────────────────────────────────────────
# Trajectory: Show that it only contains LLM calls, no tool calls
# ─────────────────────────────────────────────────────────────────────────────
print_section("Trajectory (only LLM steps, no tool calls)")

tool_call_steps = []
llm_call_steps = []

for step in result.trajectory.steps:
    if step.step_type == "tool_call":
        tool_call_steps.append(step)
    elif step.step_type == "llm_call":
        llm_call_steps.append(step)

print(f"    Tool call steps:  {len(tool_call_steps)}")
print(f"    LLM call steps:   {len(llm_call_steps)}")

for i, step in enumerate(llm_call_steps):
    print(f"    Step {i}: [llm_call] model={step.model}")


# ─────────────────────────────────────────────────────────────────────────────
# Why this matters
# ─────────────────────────────────────────────────────────────────────────────
print_section("Why This Test Matters")
print("  ✓ Prevents unnecessary API calls (cost + latency)")
print("  ✓ Verifies agent's judgment about when tools are needed")
print("  ✓ Ensures general knowledge doesn't trigger tool invocation")
print("  ✓ Tests agent's common sense / reasoning ability")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{GREEN}✓ Scenario 3 complete!{RESET}")
print(f"  This example showed how to:")
print(f"    1. Assert that specific tools were NOT called")
print(f"    2. Verify agent responds directly for general knowledge")
print(f"    3. Inspect trajectory for no tool_call steps")
print(f"    4. Validate agent cost-efficiency by avoiding unnecessary APIs")
print()
