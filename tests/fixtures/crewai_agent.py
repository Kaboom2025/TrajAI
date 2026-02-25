"""Test fixtures for CrewAI adapter tests.

Provides:
- Tool definitions as BaseTool subclasses
- Helper functions to build CrewAI Agent and Crew objects
"""
from __future__ import annotations

from typing import Any, Type

import pytest

pytest.importorskip("crewai")

from crewai import Agent as CrewAgent  # noqa: E402
from crewai import Crew, Task  # noqa: E402
from crewai.tools import BaseTool  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------


class LookupOrderInput(BaseModel):
    order_id: str = Field(..., description="The order ID to look up.")


class ProcessRefundInput(BaseModel):
    order_id: str = Field(..., description="The order ID.")
    reason: str = Field(..., description="Reason for the refund.")


class GetWeatherInput(BaseModel):
    city: str = Field(..., description="The city name.")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


class LookupOrderTool(BaseTool):  # type: ignore[misc]
    name: str = "lookup_order"
    description: str = "Look up an order by ID."
    args_schema: Type[BaseModel] = LookupOrderInput

    def _run(self, order_id: str) -> str:
        return f'{{"id": "{order_id}", "status": "delivered"}}'


class ProcessRefundTool(BaseTool):  # type: ignore[misc]
    name: str = "process_refund"
    description: str = "Process a refund for an order."
    args_schema: Type[BaseModel] = ProcessRefundInput

    def _run(self, order_id: str, reason: str) -> str:
        return f'{{"success": true, "order_id": "{order_id}"}}'


class GetWeatherTool(BaseTool):  # type: ignore[misc]
    name: str = "get_weather"
    description: str = "Get the current weather for a city."
    args_schema: Type[BaseModel] = GetWeatherInput

    def _run(self, city: str) -> str:
        return f'{{"city": "{city}", "temperature": "22C"}}'


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_agent(tools: list[Any] | None = None) -> CrewAgent:
    """Build a CrewAI Agent with the standard test tools."""
    if tools is None:
        tools = [LookupOrderTool(), ProcessRefundTool(), GetWeatherTool()]
    return CrewAgent(
        role="Test Agent",
        goal="Complete the given task using available tools.",
        backstory="You are a test agent for unit testing purposes.",
        tools=tools,
        llm="gpt-4o-mini",
        verbose=False,
    )


def build_crew(
    agent: CrewAgent | None = None,
    task_description: str = "Test task.",
) -> Crew:
    """Build a minimal CrewAI Crew with one agent and one task."""
    if agent is None:
        agent = build_agent()
    task = Task(
        description=task_description,
        expected_output="Complete the task.",
        agent=agent,
    )
    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
    )


def get_tool_definitions() -> list[Any]:
    return [LookupOrderTool(), ProcessRefundTool(), GetWeatherTool()]
