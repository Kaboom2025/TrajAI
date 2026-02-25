"""
Scenario 1: Single Tool Call
============================

What it simulates:
    A simple order lookup agent that calls a single tool.

Use case:
    Testing basic agent behavior where an agent is expected to call exactly one tool
    to answer a question.

Key concepts demonstrated:
    - Basic mock setup with return_value
    - Simple assertions: tool_was_called, tool_not_called
    - Accessing result metadata: output, llm_calls, total_tokens
    - Iterating through trajectory steps

Real-world example:
    Customer service chatbot checking order status without needing to take action.
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
from trajai.mock.toolkit import MockToolkit  # noqa: E402

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
# Setup: Create a mock agent and toolkit
# ─────────────────────────────────────────────────────────────────────────────
print_header("Scenario 1 — Single Tool Call")

# Build an agent that will call lookup_order and then respond
model = FakeToolCallingModel(
    responses=[
        make_tool_call_message("lookup_order", {"order_id": "42"}),
        AIMessage(content="Your order #42 has been delivered."),
    ],
    prompt_tokens=30,
    completion_tokens=15,
)
agent = build_react_agent(model, get_tool_definitions())

# Create toolkit and register the mock
toolkit = MockToolkit()
toolkit.mock("lookup_order", return_value={"id": "42", "status": "delivered"})

# Run the agent
print_section("Running agent with mocked lookup_order tool")
result = toolkit.run(agent, "What is the status of order 42?")


# ─────────────────────────────────────────────────────────────────────────────
# Assertions: Verify behavior
# ─────────────────────────────────────────────────────────────────────────────
print_section("Assertions")

# Positive assertion: this tool WAS called
print_ok(
    "result.tool_was_called('lookup_order')",
    result.tool_was_called("lookup_order")
)

# Negative assertion: this tool was NOT called
print_ok(
    "result.tool_not_called('process_refund')",
    result.tool_not_called("process_refund")
)

# Access output
print_ok("result.output", result.output)

# Check LLM API calls
print_ok("result.llm_calls (count)", result.llm_calls)

# Check token usage
print_ok("result.total_tokens", result.total_tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Trajectory: Inspect the sequence of steps
# ─────────────────────────────────────────────────────────────────────────────
print_section("Trajectory Steps (agent execution sequence)")
for i, step in enumerate(result.trajectory.steps):
    if step.step_type == "tool_call":
        print(
            f"    Step {i}: [tool_call] {step.tool_name}({step.tool_args})"
            f" → {step.tool_result}"
        )
    elif step.step_type == "llm_call":
        print(
            f"    Step {i}: [llm_call] model={step.model} "
            f"prompt_tokens={step.prompt_tokens} "
            f"completion_tokens={step.completion_tokens}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Deep dive: Get specific tool call details
# ─────────────────────────────────────────────────────────────────────────────
print_section("Tool Call Details (deep inspection)")
lookup_call = result.get_call("lookup_order")
print(f"    Arguments:  {lookup_call.args}")
print(f"    Result:     {lookup_call.result}")
print(f"    Timestamp:  {lookup_call.timestamp}")
print(f"    Error:      {lookup_call.error}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{GREEN}✓ Scenario 1 complete!{RESET}")
print("  This example showed how to:")
print("    1. Create a simple mock tool with return_value")
print("    2. Use tool_was_called() and tool_not_called() assertions")
print("    3. Access result metadata (output, llm_calls, total_tokens)")
print("    4. Inspect the trajectory for detailed execution info")
print()
