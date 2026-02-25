"""Test fixtures for OpenAI Agents SDK adapter tests.

Provides:
- Tool definitions as FunctionTool objects
- A helper to build an Agent with those tools
- FakeModel: a fake model class that returns preset responses without real API calls
"""
from __future__ import annotations

import json
from typing import Any

import pytest

pytest.importorskip("agents")

from agents import Agent  # noqa: E402
from agents.tool import FunctionTool  # noqa: E402

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


async def _lookup_order_fn(ctx: Any, args_json: str) -> str:
    kwargs = json.loads(args_json)
    order_id = kwargs.get("order_id", "")
    return json.dumps({"id": order_id, "status": "delivered"})


async def _process_refund_fn(ctx: Any, args_json: str) -> str:
    kwargs = json.loads(args_json)
    return json.dumps({"success": True, "order_id": kwargs.get("order_id", "")})


async def _get_weather_fn(ctx: Any, args_json: str) -> str:
    kwargs = json.loads(args_json)
    return json.dumps({"city": kwargs.get("city", ""), "temperature": "22C"})


LOOKUP_ORDER_TOOL = FunctionTool(
    name="lookup_order",
    description="Look up an order by ID.",
    params_json_schema={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
    on_invoke_tool=_lookup_order_fn,
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
    on_invoke_tool=_process_refund_fn,
    strict_json_schema=False,
)

GET_WEATHER_TOOL = FunctionTool(
    name="get_weather",
    description="Get the current weather for a city.",
    params_json_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
    on_invoke_tool=_get_weather_fn,
    strict_json_schema=False,
)


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


def build_agent(tools: list[Any] | None = None) -> Agent:  # type: ignore[type-arg]
    """Build an Agent with the standard test tools."""
    if tools is None:
        tools = [LOOKUP_ORDER_TOOL, PROCESS_REFUND_TOOL, GET_WEATHER_TOOL]
    return Agent(
        name="TestAgent",
        instructions="You are a helpful test agent.",
        tools=tools,
        model="gpt-4o-mini",
    )


def get_tool_definitions() -> list[Any]:
    return [LOOKUP_ORDER_TOOL, PROCESS_REFUND_TOOL, GET_WEATHER_TOOL]
