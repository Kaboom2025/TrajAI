"""Tests for LangGraphAdapter (Phase 5).

Covers:
- Detection (can_handle)
- Tool extraction
- Mock injection
- Execution & trajectory collection
- Auto-detection via toolkit.run()
"""
from __future__ import annotations

import warnings

import pytest

from trajai.mock.toolkit import MockToolkit, TrajAIMockError

# ── LangGraph imports ─────────────────────────────────────────────────────────

pytest.importorskip("langgraph")

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langgraph.graph import StateGraph
    from langchain_core.messages import AIMessage, HumanMessage

from trajai.adapters.langgraph import LangGraphAdapter

from tests.fixtures.langgraph_agent import (
    FakeToolCallingModel,
    build_react_agent,
    get_tool_definitions,
    lookup_order,
    make_tool_call_message,
    process_refund,
    get_weather,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _simple_agent(responses: list[AIMessage]) -> object:
    """Build a react agent that emits the given response sequence."""
    model = FakeToolCallingModel(responses=responses)
    return build_react_agent(model, get_tool_definitions())


# ── Detection tests ───────────────────────────────────────────────────────────


class TestCanHandle:
    def test_can_handle_compiled_graph(self) -> None:
        agent = _simple_agent([AIMessage(content="hello")])
        adapter = LangGraphAdapter(MockToolkit())
        assert adapter.can_handle(agent) is True

    def test_can_handle_state_graph(self) -> None:
        sg = StateGraph(dict)
        adapter = LangGraphAdapter(MockToolkit())
        assert adapter.can_handle(sg) is True

    def test_cannot_handle_callable(self) -> None:
        adapter = LangGraphAdapter(MockToolkit())
        assert adapter.can_handle(lambda x: x) is False

    def test_cannot_handle_string(self) -> None:
        adapter = LangGraphAdapter(MockToolkit())
        assert adapter.can_handle("not an agent") is False

    def test_cannot_handle_none(self) -> None:
        adapter = LangGraphAdapter(MockToolkit())
        assert adapter.can_handle(None) is False


# ── Tool extraction tests ──────────────────────────────────────────────────────


class TestExtractTools:
    def test_extract_tools_from_compiled(self) -> None:
        agent = _simple_agent([AIMessage(content="hi")])
        toolkit = MockToolkit()
        adapter = LangGraphAdapter(toolkit)
        names = adapter.extract_tools(agent)
        assert set(names) >= {"lookup_order", "process_refund", "get_weather"}

    def test_extract_tools_from_uncompiled_state_graph(self) -> None:
        # Build a minimal valid StateGraph manually with a ToolNode
        from langgraph.graph import START
        from langgraph.prebuilt import ToolNode

        sg = StateGraph(dict)
        sg.add_node("tools", ToolNode([lookup_order]))
        sg.add_edge(START, "tools")
        adapter = LangGraphAdapter(MockToolkit())
        names = adapter.extract_tools(sg)
        assert "lookup_order" in names


# ── Mock injection tests ───────────────────────────────────────────────────────


class TestInjectMocks:
    def test_inject_mocks_replaces_tools(self) -> None:
        """Mock tools should be installed into the ToolNode."""
        agent = _simple_agent([AIMessage(content="ok")])
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"mocked": True})

        adapter = LangGraphAdapter(toolkit)
        compiled, saved = adapter.inject_mocks(agent, toolkit)

        from langgraph.prebuilt import ToolNode
        from langchain_core.tools import StructuredTool

        for _name, spec in compiled.builder.nodes.items():
            if hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode):
                if "lookup_order" in spec.runnable.tools_by_name:
                    installed = spec.runnable.tools_by_name["lookup_order"]
                    assert isinstance(installed, StructuredTool)
                    break
        else:
            pytest.fail("No ToolNode with lookup_order found after injection")

        # Restore to leave agent clean
        adapter._restore_tools(compiled, saved)

    def test_inject_mocks_originals_restored(self) -> None:
        """After execute, original tool objects should be back."""
        agent = _simple_agent([AIMessage(content="ok")])
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value="mocked")

        adapter = LangGraphAdapter(toolkit)

        # Capture original tools
        from langgraph.prebuilt import ToolNode

        originals: dict[str, object] = {}
        for _name, spec in agent.builder.nodes.items():
            if hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode):
                originals.update(spec.runnable.tools_by_name)

        compiled, saved = adapter.inject_mocks(agent, toolkit)
        adapter._restore_tools(compiled, saved)

        # Verify originals restored
        for _name, spec in compiled.builder.nodes.items():
            if hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode):
                for tool_name, orig_tool in originals.items():
                    assert spec.runnable.tools_by_name[tool_name] is orig_tool


# ── Execution & trajectory tests ───────────────────────────────────────────────


class TestExecuteTrajectory:
    def test_execute_captures_tool_calls(self) -> None:
        """Tool name, args, and result should appear in trajectory steps."""
        responses = [
            make_tool_call_message("lookup_order", {"order_id": "42"}),
            AIMessage(content="Order 42 delivered."),
        ]
        agent = _simple_agent(responses)

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "42", "status": "delivered"})

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)
        traj = adapter.execute(wrapped, "check order 42", timeout=30.0)

        tool_steps = [s for s in traj.steps if s.step_type == "tool_call"]
        assert len(tool_steps) == 1
        step = tool_steps[0]
        assert step.tool_name == "lookup_order"
        assert step.tool_args == {"order_id": "42"}
        assert step.tool_result == {"id": "42", "status": "delivered"}

    def test_execute_captures_llm_calls(self) -> None:
        """LLM call steps should be recorded with model + token info."""
        model = FakeToolCallingModel(
            responses=[AIMessage(content="done")],
            prompt_tokens=50,
            completion_tokens=25,
        )
        agent = build_react_agent(model, get_tool_definitions())
        toolkit = MockToolkit()

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)
        traj = adapter.execute(wrapped, "say hello", timeout=30.0)

        llm_steps = [s for s in traj.steps if s.step_type == "llm_call"]
        assert len(llm_steps) >= 1
        step = llm_steps[0]
        assert step.model == "FakeToolCallingModel"
        assert step.prompt_tokens == 50
        assert step.completion_tokens == 25
        assert traj.llm_calls >= 1
        assert traj.total_tokens >= 75

    def test_execute_extracts_final_output(self) -> None:
        """final_output should contain the last AIMessage content."""
        agent = _simple_agent([AIMessage(content="Here is your answer.")])
        toolkit = MockToolkit()

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)
        traj = adapter.execute(wrapped, "hi", timeout=30.0)

        assert traj.final_output == "Here is your answer."

    def test_execute_captures_error(self) -> None:
        """Non-mock errors during execution should be stored in trajectory.error."""

        # Make a model that raises a non-TrajAI error
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.outputs import ChatResult

        class ErrorModel(BaseChatModel):
            @property
            def _llm_type(self) -> str:
                return "error-model"

            def _generate(self, messages: object, **kwargs: object) -> ChatResult:
                raise RuntimeError("agent exploded")

            def bind_tools(self, tools: object, **kwargs: object) -> "ErrorModel":
                return self

        agent = build_react_agent(ErrorModel(), get_tool_definitions())
        toolkit = MockToolkit()

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)
        traj = adapter.execute(wrapped, "do something", timeout=30.0)

        assert traj.error is not None
        assert isinstance(traj.error, RuntimeError)

    def test_execute_reraises_mock_errors(self) -> None:
        """TrajAIMockError subclasses should be re-raised, not captured."""
        responses = [
            make_tool_call_message("lookup_order", {"order_id": "99"}),
        ]
        agent = _simple_agent(responses)

        toolkit = MockToolkit()
        toolkit.mock(
            "lookup_order",
            side_effect=TrajAIMockError("intentional mock error"),
        )

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)

        with pytest.raises(TrajAIMockError):
            adapter.execute(wrapped, "check 99", timeout=30.0)

    def test_execute_multi_tool_order(self) -> None:
        """Multiple tool calls should appear in trajectory in call order."""
        responses = [
            make_tool_call_message("lookup_order", {"order_id": "1"}, call_id="c1"),
            make_tool_call_message("process_refund", {"order_id": "1", "reason": "damaged"}, call_id="c2"),
            AIMessage(content="Refund processed."),
        ]
        agent = _simple_agent(responses)

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "1", "status": "delivered"})
        toolkit.mock("process_refund", return_value={"success": True})

        adapter = LangGraphAdapter(toolkit)
        wrapped = adapter.inject_mocks(agent, toolkit)
        traj = adapter.execute(wrapped, "refund order 1", timeout=30.0)

        tool_names = [s.tool_name for s in traj.steps if s.step_type == "tool_call"]
        assert tool_names == ["lookup_order", "process_refund"]


# ── toolkit.run() auto-detection tests ────────────────────────────────────────


class TestToolkitRun:
    def test_toolkit_run_autodetects_langgraph(self) -> None:
        """toolkit.run(langgraph_agent, input) should work end-to-end."""
        agent = _simple_agent([AIMessage(content="Hello from mock!")])
        toolkit = MockToolkit()

        result = toolkit.run(agent, "say hello")
        assert result.output == "Hello from mock!"

    def test_toolkit_run_adapter_not_found(self) -> None:
        """Passing an unknown agent type should raise AdapterNotFoundError."""
        from trajai.mock.toolkit import AdapterNotFoundError

        toolkit = MockToolkit()

        with pytest.raises(AdapterNotFoundError):
            toolkit.run(object(), "hello")

    def test_toolkit_run_assertions_work(self) -> None:
        """Boolean and assert assertion APIs should work on LangGraph trajectory."""
        responses = [
            make_tool_call_message("lookup_order", {"order_id": "7"}),
            make_tool_call_message("process_refund", {"order_id": "7", "reason": "broken"}, call_id="c2"),
            AIMessage(content="Refund done."),
        ]
        agent = _simple_agent(responses)

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "7", "status": "delivered"})
        toolkit.mock("process_refund", return_value={"success": True})

        result = toolkit.run(agent, "refund order 7")

        assert result.tool_was_called("lookup_order")
        assert result.tool_was_called("process_refund")
        assert result.tool_called_before("lookup_order", "process_refund")
        assert result.output_contains("Refund")

        result.assert_tool_was_called("lookup_order")
        result.assert_tool_was_called("process_refund")
        result.assert_tool_called_before("lookup_order", "process_refund")
        result.assert_output_contains("Refund")

    def test_toolkit_run_tool_not_called(self) -> None:
        """tool_not_called should be True for tools that weren't invoked."""
        agent = _simple_agent([AIMessage(content="just chat")])
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={})
        toolkit.mock("get_weather", return_value={})

        result = toolkit.run(agent, "tell me something")

        assert result.tool_not_called("lookup_order")
        assert result.tool_not_called("get_weather")

    def test_toolkit_run_call_order_contains(self) -> None:
        """call_order_contains should work for LangGraph trajectories."""
        responses = [
            make_tool_call_message("lookup_order", {"order_id": "5"}, call_id="c1"),
            make_tool_call_message("process_refund", {"order_id": "5", "reason": "wrong"}, call_id="c2"),
            AIMessage(content="Done."),
        ]
        agent = _simple_agent(responses)
        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "5"})
        toolkit.mock("process_refund", return_value={"success": True})

        result = toolkit.run(agent, "process refund for 5")

        assert result.call_order_contains(["lookup_order", "process_refund"])
