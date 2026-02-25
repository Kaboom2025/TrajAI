"""Tests for CrewAIAdapter (Phase 11b).

Covers:
- Detection (can_handle)
- Tool extraction from Crew and Agent
- Mock injection (no original mutation)
- Execution & trajectory collection
- Auto-detection via toolkit.run()
- Integration with assertion API
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from unitai.mock.toolkit import MockToolkit, UnitAIMockError

# Skip entire module if crewai is not installed
pytest.importorskip("crewai")

from crewai import Crew  # noqa: E402
from crewai.tools import BaseTool  # noqa: E402

from tests.fixtures.crewai_agent import (  # noqa: E402
    GetWeatherTool,
    LookupOrderTool,
    build_agent,
    build_crew,
)
from unitai.adapters.crewai import CrewAIAdapter, _make_mock_tool  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_crew_output(raw: str = "Task completed.") -> MagicMock:
    result = MagicMock()
    result.raw = raw
    return result


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_can_handle_crew(self) -> None:
        crew = build_crew()
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.can_handle(crew) is True

    def test_can_handle_agent(self) -> None:
        agent = build_agent()
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.can_handle(agent) is True

    def test_cannot_handle_callable(self) -> None:
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.can_handle(lambda x: x) is False

    def test_cannot_handle_string(self) -> None:
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.can_handle("not an agent") is False

    def test_cannot_handle_none(self) -> None:
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.can_handle(None) is False


# ---------------------------------------------------------------------------
# Tool extraction tests
# ---------------------------------------------------------------------------


class TestExtractTools:
    def test_extract_tools_from_agent(self) -> None:
        agent = build_agent()
        adapter = CrewAIAdapter(MockToolkit())
        names = adapter.extract_tools(agent)
        assert "lookup_order" in names
        assert "process_refund" in names
        assert "get_weather" in names

    def test_extract_tools_from_crew(self) -> None:
        crew = build_crew()
        adapter = CrewAIAdapter(MockToolkit())
        names = adapter.extract_tools(crew)
        assert "lookup_order" in names

    def test_extract_tools_empty_agent(self) -> None:
        agent = build_agent(tools=[])
        adapter = CrewAIAdapter(MockToolkit())
        assert adapter.extract_tools(agent) == []

    def test_extract_tools_deduplicates(self) -> None:
        """Multiple agents with same tool should not duplicate names."""
        from crewai import Task as CrewTask

        tool1 = LookupOrderTool()
        tool2 = LookupOrderTool()
        agent1 = build_agent(tools=[tool1])
        agent2 = build_agent(tools=[tool2])
        crew = Crew(
            agents=[agent1, agent2],
            tasks=[
                CrewTask(
                    description="t1",
                    expected_output="done",
                    agent=agent1,
                )
            ],
            verbose=False,
        )
        adapter = CrewAIAdapter(MockToolkit())
        names = adapter.extract_tools(crew)
        assert names.count("lookup_order") == 1


# ---------------------------------------------------------------------------
# Mock injection tests
# ---------------------------------------------------------------------------


class TestInjectMocks:
    def test_inject_agent_replaces_matching_tools(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"mocked": True})

        adapter = CrewAIAdapter(toolkit)
        wrapped, agent_type = adapter.inject_mocks(agent, toolkit)

        assert agent_type == "agent"
        tool = next(t for t in wrapped.tools if t.name == "lookup_order")
        assert not isinstance(tool, LookupOrderTool)

    def test_inject_crew_replaces_tools(self) -> None:
        crew = build_crew()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"mocked": True})

        adapter = CrewAIAdapter(toolkit)
        wrapped, agent_type = adapter.inject_mocks(crew, toolkit)

        assert agent_type == "crew"
        agent = wrapped.agents[0]
        tool = next(t for t in agent.tools if t.name == "lookup_order")
        assert not isinstance(tool, LookupOrderTool)

    def test_inject_does_not_mutate_original_agent(self) -> None:
        agent = build_agent()
        original_tool_types = [type(t) for t in agent.tools]

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={})

        adapter = CrewAIAdapter(toolkit)
        adapter.inject_mocks(agent, toolkit)

        # Original tool types must be unchanged
        for i, tool in enumerate(agent.tools):
            assert type(tool) is original_tool_types[i]

    def test_inject_preserves_unregistered_tools(self) -> None:
        """Tools not in the toolkit should remain as original type."""
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={})

        adapter = CrewAIAdapter(toolkit)
        wrapped, _ = adapter.inject_mocks(agent, toolkit)

        # get_weather not in toolkit → should be original type
        weather_tool = next(t for t in wrapped.tools if t.name == "get_weather")
        assert isinstance(weather_tool, GetWeatherTool)


# ---------------------------------------------------------------------------
# _make_mock_tool helper
# ---------------------------------------------------------------------------


class TestMakeMockTool:
    def test_returns_base_tool_subclass(self) -> None:
        toolkit = MockToolkit()
        mock_obj = toolkit.mock("lookup_order", return_value={"id": "1"})
        tool = _make_mock_tool("lookup_order", mock_obj)
        assert isinstance(tool, BaseTool)
        assert tool.name == "lookup_order"

    def test_run_calls_mock(self) -> None:
        toolkit = MockToolkit()
        mock_obj = toolkit.mock(
            "lookup_order", return_value={"id": "42", "status": "ok"}
        )
        tool = _make_mock_tool("lookup_order", mock_obj)
        result = tool._run(order_id="42")
        assert result == {"id": "42", "status": "ok"}
        assert len(mock_obj.calls) == 1


# ---------------------------------------------------------------------------
# Execution tests (mocked kickoff)
# ---------------------------------------------------------------------------


class TestExecute:
    def test_execute_agent_captures_final_output(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = CrewAIAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        mock_output = _make_crew_output("Task is done.")

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.return_value = mock_output
            traj = adapter.execute(wrapped, "do task", timeout=30.0)

        assert traj.final_output == "Task is done."

    def test_execute_crew_captures_final_output(self) -> None:
        crew = build_crew()
        toolkit = MockToolkit()
        adapter = CrewAIAdapter(toolkit)
        wrapped = adapter.inject_mocks(crew, toolkit)

        mock_output = _make_crew_output("Crew done.")

        wrapped_crew, agent_type = wrapped
        with patch.object(wrapped_crew, "kickoff", return_value=mock_output):
            traj = adapter.execute((wrapped_crew, agent_type), "do task", timeout=30.0)

        assert traj.final_output == "Crew done."

    def test_execute_captures_error(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = CrewAIAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.side_effect = RuntimeError("crew exploded")
            traj = adapter.execute(wrapped, "do task", timeout=30.0)

        assert traj.error is not None
        assert isinstance(traj.error, RuntimeError)

    def test_execute_reraises_mock_errors(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()
        adapter = CrewAIAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.side_effect = UnitAIMockError("intentional")
            with pytest.raises(UnitAIMockError):
                adapter.execute(wrapped, "do task", timeout=30.0)

    def test_execute_records_tool_calls(self) -> None:
        """When the mock tool is actually invoked, trajectory should record it."""
        agent = build_agent()
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "1", "status": "ok"})

        adapter = CrewAIAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        mock_output = _make_crew_output("Found order.")

        def fake_kickoff(**kwargs: object) -> object:
            # Simulate the agent calling lookup_order
            injected_tool = next(
                t for t in wrapped[0].tools if t.name == "lookup_order"
            )
            injected_tool._run(order_id="1")
            return mock_output

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.side_effect = fake_kickoff
            traj = adapter.execute(wrapped, "find order", timeout=30.0)

        tool_steps = [s for s in traj.steps if s.step_type == "tool_call"]
        assert len(tool_steps) == 1
        assert tool_steps[0].tool_name == "lookup_order"


# ---------------------------------------------------------------------------
# toolkit.run() auto-detection tests
# ---------------------------------------------------------------------------


class TestToolkitRun:
    def test_toolkit_run_autodetects_crew(self) -> None:
        crew = build_crew()
        toolkit = MockToolkit()

        mock_output = _make_crew_output("Crew completed.")

        with patch.object(
            Crew, "kickoff", return_value=mock_output
        ):
            result = toolkit.run(crew, "do something")

        assert result.output == "Crew completed."

    def test_toolkit_run_autodetects_crewai_agent(self) -> None:
        agent = build_agent()
        toolkit = MockToolkit()

        mock_output = _make_crew_output("Agent done.")

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.return_value = mock_output
            result = toolkit.run(agent, "do something")

        assert result.output == "Agent done."

    def test_toolkit_run_assertions_work(self) -> None:
        """Assertion API should work on CrewAI trajectories."""
        agent = build_agent()
        toolkit = MockToolkit()
        mock_tool = toolkit.mock("lookup_order", return_value={"id": "5"})

        mock_output = _make_crew_output("Found order 5.")

        def fake_kickoff(**kwargs: object) -> object:
            # Simulate actual tool call
            mock_tool.invoke({"order_id": "5"})
            return mock_output

        with patch("unitai.adapters.crewai.Crew") as mock_crew:
            mock_crew.return_value.kickoff.side_effect = fake_kickoff
            result = toolkit.run(agent, "find order 5")

        assert result.tool_was_called("lookup_order")
        result.assert_tool_was_called("lookup_order")
        assert result.output_contains("Found")
