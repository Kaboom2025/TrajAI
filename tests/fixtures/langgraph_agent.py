"""Test fixtures for LangGraph adapter tests.

Provides:
- Tool definitions decorated with @tool
- FakeToolCallingModel: configurable fake LLM that returns preset AIMessage responses
- Helper functions for building test agents
"""
from __future__ import annotations

import warnings
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


@tool
def lookup_order(order_id: str) -> dict[str, str]:
    """Look up an order by ID."""
    return {"id": order_id, "status": "delivered"}


@tool
def process_refund(order_id: str, reason: str) -> dict[str, Any]:
    """Process a refund for an order."""
    return {"success": True, "order_id": order_id, "reason": reason}


@tool
def get_weather(city: str) -> dict[str, str]:
    """Get the current weather for a city."""
    return {"city": city, "temperature": "22C", "condition": "sunny"}


# ---------------------------------------------------------------------------
# FakeToolCallingModel
# ---------------------------------------------------------------------------


class FakeToolCallingModel(BaseChatModel):
    """Configurable fake LLM that returns pre-set AIMessage responses.

    Supports bind_tools() as a no-op so it works with create_react_agent.
    Reports configurable token usage in llm_output.
    """

    responses: list[AIMessage]
    prompt_tokens: int = 10
    completion_tokens: int = 20

    model_config = {"arbitrary_types_allowed": True}

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling-model"

    def _generate(
        self,
        messages: Any,
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Cycle through responses
        idx = getattr(self, "_call_count", 0)
        response = self.responses[idx % len(self.responses)]
        object.__setattr__(self, "_call_count", idx + 1)

        return ChatResult(
            generations=[ChatGeneration(message=response)],
            llm_output={
                "token_usage": {
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                }
            },
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> FakeToolCallingModel:
        """No-op: return self (tools are mocked at the ToolNode level)."""
        return self


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_tool_definitions() -> list[Any]:
    """Return the list of test tool definitions."""
    return [lookup_order, process_refund, get_weather]


def build_react_agent(model: BaseChatModel, tools: list[Any]) -> Any:
    """Build a LangGraph react agent with the given model and tools."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from langgraph.prebuilt import create_react_agent

        return create_react_agent(model, tools)


def make_tool_call_message(
    tool_name: str, args: dict[str, Any], call_id: str = "call_1"
) -> AIMessage:
    """Create an AIMessage with a single tool call."""
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": tool_name,
                "args": args,
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )
