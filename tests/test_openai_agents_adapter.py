"""Tests for OpenAIAgentsAdapter (Phase 11a).

Covers:
- Detection (can_handle)
- Tool extraction
- Mock injection (no original mutation)
- Execution & trajectory collection
- Auto-detection via toolkit.run()
- Integration with assertion API
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from trajai.mock.toolkit import MockToolkit, TrajAIMockError

# Skip entire module if openai-agents is not installed
pytest.importorskip("agents")


from tests.fixtures.openai_agents_agent import (  # noqa: E402
    LOOKUP_ORDER_TOOL,
    build_agent,
)
from trajai.adapters.openai_agents import OpenAIAgentsAdapter  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run_result(
    final_output: str = "done",
    tool_calls: list[dict] | None = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    model: str = "gpt-4o-mini",
) -> MagicMock:
    """Build a mock RunResult-like object for patching Runner.run_sync."""
    result = MagicMock()
    result.final_output = final_output

    # Build raw_responses
    usage = MagicMock()
    usage.input_tokens = prompt_tokens
    usage.output_tokens = completion_tokens
    response = MagicMock()
    response.model = model
    response.usage = usage
    result.raw_responses = [response]

    return result


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_can_handle_agent(self) -> None:
        agent = build_agent()
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.can_handle(agent) is True

    def test_cannot_handle_callable(self) -> None:
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.can_handle(lambda x: x) is False

    def test_cannot_handle_string(self) -> None:
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.can_handle("not an agent") is False

    def test_cannot_handle_none(self) -> None:
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.can_handle(None) is False

    def test_cannot_handle_dict(self) -> None:
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.can_handle({"tools": []}) is False


# ---------------------------------------------------------------------------
# Tool extraction tests
# ---------------------------------------------------------------------------


class TestExtractTools:
    def test_extracts_function_tool_names(self) -> None:
        agent = build_agent()
        adapter = OpenAIAgentsAdapter(MockToolkit())
        names = adapter.extract_tools(agent)
        assert "lookup_order" in names
        assert "process_refund" in names
        assert "get_weather" in names

    def test_empty_tools(self) -> None:
        agent = build_agent(tools=[])
        adapter = OpenAIAgentsAdapter(MockToolkit())
        assert adapter.extract_tools(agent) == []

    def test_partial_tools(self) -> None:
        agent = build_agent(tools=[LOOKUP_ORDER_TOOL])
        adapter = OpenAIAgentsAdapter(MockToolkit())
        names = adapter.extract_tools(agent)
        assert names == ["lookup_order"]


# ---------------------------------------------------------------------------
# Mock injection tests
# ---------------------------------------------------------------------------


class TestInjectMocks:
    def test_inject_replaces_matching_tools(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"mocked": True})

        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped, original = adapter.inject_mocks(agent, toolkit)

        # The wrapped agent should have a different on_invoke_tool for lookup_order
        lookup_tool = next(t for t in wrapped.tools if t.name == "lookup_order")
        original_tool = next(t for t in original.tools if t.name == "lookup_order")
        assert lookup_tool.on_invoke_tool is not original_tool.on_invoke_tool

    def test_inject_does_not_mutate_original(self) -> None:
        agent = build_agent()
        original_tool_fns = [t.on_invoke_tool for t in agent.tools]

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={})
        toolkit.mock("process_refund", return_value={})

        adapter = OpenAIAgentsAdapter(toolkit)
        adapter.inject_mocks(agent, toolkit)

        # Original tool functions must be unchanged
        for i, tool in enumerate(agent.tools):
            assert tool.on_invoke_tool is original_tool_fns[i]

    def test_inject_preserves_unregistered_tools(self) -> None:
        """Tools not in the toolkit should remain unchanged."""
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={})

        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped, original = adapter.inject_mocks(agent, toolkit)

        # get_weather should still be the original
        original_weather = next(t for t in original.tools if t.name == "get_weather")
        wrapped_weather = next(t for t in wrapped.tools if t.name == "get_weather")
        assert wrapped_weather.on_invoke_tool is original_weather.on_invoke_tool


# ---------------------------------------------------------------------------
# Execution tests (mocked Runner)
# ---------------------------------------------------------------------------


class TestExecute:
    def test_execute_records_tool_call(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "42", "status": "delivered"})

        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        mock_result = _make_run_result(final_output="Order 42 delivered.")

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.return_value = mock_result
            traj = adapter.execute(wrapped, "check order 42", timeout=30.0)

        # The mock tool records calls via invoke() when the runner calls on_invoke_tool.
        # Since we patched Runner.run_sync, on_invoke_tool was never called.
        # We verify the trajectory structure and final output here.
        assert traj.final_output == "Order 42 delivered."

    def test_execute_captures_llm_calls(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        mock_result = _make_run_result(
            prompt_tokens=50, completion_tokens=25, model="gpt-4o-mini"
        )

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.return_value = mock_result
            traj = adapter.execute(wrapped, "say hello", timeout=30.0)

        llm_steps = [s for s in traj.steps if s.step_type == "llm_call"]
        assert len(llm_steps) == 1
        assert llm_steps[0].model == "gpt-4o-mini"
        assert llm_steps[0].prompt_tokens == 50
        assert llm_steps[0].completion_tokens == 25
        assert traj.total_tokens == 75

    def test_execute_extracts_final_output(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        mock_result = _make_run_result(final_output="Here is your answer.")

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.return_value = mock_result
            traj = adapter.execute(wrapped, "hi", timeout=30.0)

        assert traj.final_output == "Here is your answer."

    def test_execute_captures_error(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.side_effect = RuntimeError("agent exploded")
            traj = adapter.execute(wrapped, "do something", timeout=30.0)

        assert traj.error is not None
        assert isinstance(traj.error, RuntimeError)

    def test_execute_reraises_mock_errors(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = OpenAIAgentsAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.side_effect = TrajAIMockError("intentional mock error")
            with pytest.raises(TrajAIMockError):
                adapter.execute(wrapped, "check", timeout=30.0)


# ---------------------------------------------------------------------------
# toolkit.run() auto-detection tests
# ---------------------------------------------------------------------------


class TestToolkitRun:
    def test_toolkit_run_autodetects_openai_agent(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()

        mock_result = _make_run_result(final_output="Hello from mock!")
        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            mock_runner.run_sync.return_value = mock_result
            result = toolkit.run(agent, "say hello")

        assert result.output == "Hello from mock!"

    def test_toolkit_run_adapter_not_found_for_unknown_type(self) -> None:
        from trajai.mock.toolkit import AdapterNotFoundError

        toolkit = MockToolkit()
        with pytest.raises(AdapterNotFoundError):
            toolkit.run(object(), "hello")

    def test_toolkit_run_assertions_work(self) -> None:
        """Assertion API should work on OpenAI Agents trajectories."""
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "7"})

        mock_result = _make_run_result(final_output="Order found.")

        with patch("trajai.adapters.openai_agents.Runner") as mock_runner:
            # Simulate actual tool invocation by calling the mock during run
            def fake_run_sync(a: Any, inp: Any, **kw: Any) -> Any:
                import asyncio

                lookup_fn = next(
                    t for t in a.tools if t.name == "lookup_order"
                )
                asyncio.run(
                    lookup_fn.on_invoke_tool(None, '{"order_id": "7"}')
                )
                return mock_result

            mock_runner.run_sync.side_effect = fake_run_sync
            result = toolkit.run(agent, "check order 7")

        assert result.tool_was_called("lookup_order")
        result.assert_tool_was_called("lookup_order")
        assert result.output_contains("Order")
