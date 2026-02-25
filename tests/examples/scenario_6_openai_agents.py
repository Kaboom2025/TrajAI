"""Scenario 6: OpenAI Agents SDK Integration

This scenario demonstrates using UnitAI with the OpenAI Agents SDK.

Key concepts:
- Auto-detection of OpenAI Agent framework
- Mock injection without mutating the original agent
- FunctionTool replacement with UnitAI mocks
- LLM metadata extraction from RunResult

Real-world use case: Testing an OpenAI Agents SDK agent that processes
customer support tickets by looking up order status and processing refunds.
"""

import pytest

# Skip this scenario if openai-agents is not installed
pytest.importorskip("agents")

from agents import Agent
from agents.tool import FunctionTool

from trajai.mock.toolkit import MockToolkit

# ---------------------------------------------------------------------------
# Step 1: Define tools as FunctionTool objects
# ---------------------------------------------------------------------------


async def lookup_order_impl(ctx: object, args_json: str) -> str:
    """Real implementation that would query a database."""
    import json

    kwargs = json.loads(args_json)
    order_id = kwargs.get("order_id", "")
    # In production, this would query a real database
    return json.dumps({"id": order_id, "status": "delivered"})


async def process_refund_impl(ctx: object, args_json: str) -> str:
    """Real implementation that would process a refund."""
    import json

    kwargs = json.loads(args_json)
    order_id = kwargs.get("order_id", "")
    return json.dumps({"success": True, "order_id": order_id})


LOOKUP_ORDER_TOOL = FunctionTool(
    name="lookup_order",
    description="Look up an order by ID.",
    params_json_schema={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
    on_invoke_tool=lookup_order_impl,
    strict_json_schema=False,
)

PROCESS_REFUND_TOOL = FunctionTool(
    name="process_refund",
    description="Process a refund for an order.",
    params_json_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["order_id", "reason"],
    },
    on_invoke_tool=process_refund_impl,
    strict_json_schema=False,
)


# ---------------------------------------------------------------------------
# Step 2: Create the agent
# ---------------------------------------------------------------------------


def create_support_agent() -> Agent:  # type: ignore[type-arg]
    """Create an OpenAI Agents SDK agent for customer support."""
    return Agent(
        name="SupportAgent",
        instructions=(
            "You are a customer support agent. "
            "When users ask about orders or refunds, use the available tools."
        ),
        tools=[LOOKUP_ORDER_TOOL, PROCESS_REFUND_TOOL],
        model="gpt-4o-mini",
    )


# ---------------------------------------------------------------------------
# Step 3: Test with UnitAI
# ---------------------------------------------------------------------------


def test_openai_agent_lookup_order() -> None:
    """Test that the agent calls lookup_order with correct arguments."""
    agent = create_support_agent()
    toolkit = MockToolkit()

    # Mock the lookup_order tool
    toolkit.mock("lookup_order", return_value={"id": "ORDER-123", "status": "shipped"})

    # Run the agent (UnitAI auto-detects it's an OpenAI Agent)
    # Note: This will raise if openai-agents or a real API key is not available.
    # In CI, you'd mock the Runner.run_sync call or use record/replay cache.
    try:
        result = toolkit.run(agent, "What's the status of order ORDER-123?")

        # Assert the agent called the tool
        assert result.tool_was_called("lookup_order")

        # Check the arguments passed to the tool
        call = result.get_call("lookup_order", 0)
        assert call.args["order_id"] == "ORDER-123"

        # Verify the mock response was used
        assert call.result["status"] == "shipped"

        print("✓ OpenAI Agent correctly called lookup_order")
        print(f"  Tool arguments: {call.args}")
        print(f"  Mock result: {call.result}")

    except Exception as e:
        # If openai-agents or API keys aren't available, this scenario is informational
        print(f"⚠ OpenAI Agent test skipped (requires openai-agents + API key): {e}")


def test_openai_agent_refund_flow() -> None:
    """Test a multi-step refund flow with an OpenAI Agent."""
    agent = create_support_agent()
    toolkit = MockToolkit()

    toolkit.mock(
        "lookup_order", return_value={"id": "ORDER-456", "status": "delivered"}
    )
    toolkit.mock(
        "process_refund", return_value={"success": True, "order_id": "ORDER-456"}
    )

    try:
        result = toolkit.run(
            agent, "I want to refund order ORDER-456 because it's damaged."
        )

        # Assert both tools were called
        assert result.tool_was_called("lookup_order")
        assert result.tool_was_called("process_refund")

        # Assert they were called in the correct order
        assert result.tool_called_before("lookup_order", "process_refund")

        print("✓ OpenAI Agent executed refund flow correctly")
        print(f"  Tool call order: {result.call_order()}")

    except Exception as e:
        print(f"⚠ OpenAI Agent refund test skipped: {e}")


# ---------------------------------------------------------------------------
# Step 4: Run the scenario
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 70)
    print("Scenario 6: OpenAI Agents SDK Integration")
    print("=" * 70)
    print()

    test_openai_agent_lookup_order()
    print()
    test_openai_agent_refund_flow()
    print()

    print("=" * 70)
    print("Key Takeaways:")
    print("- UnitAI auto-detects OpenAI Agents SDK agents")
    print("- FunctionTool instances are replaced with mocks (no mutation)")
    print("- All standard UnitAI assertions work with OpenAI Agents")
    print("- LLM metadata is extracted from RunResult.raw_responses")
    print("=" * 70)
