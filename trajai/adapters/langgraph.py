from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from trajai.adapters.base import BaseAdapter
from trajai.core.trajectory import Trajectory, TrajectoryStep

if TYPE_CHECKING:
    from trajai.mock.toolkit import MockToolkit

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain_core.tools import StructuredTool
    from langgraph.graph import StateGraph
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.prebuilt import ToolNode

    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


if HAS_LANGGRAPH:
    _BaseCallbackHandlerClass = BaseCallbackHandler
else:
    _BaseCallbackHandlerClass = object  # type: ignore[assignment,misc]


class _TrajectoryCallbackHandler(_BaseCallbackHandlerClass):
    """Captures LLM calls from LangChain callbacks.

    Tool calls are already recorded by MockTool.invoke, so this handler
    only tracks LLM calls (model name, token usage).
    """

    def __init__(self, toolkit: MockToolkit) -> None:
        if HAS_LANGGRAPH:
            super().__init__()
        self.toolkit = toolkit
        self._pending: dict[Any, str] = {}  # run_id -> model name

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: Any,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        model_name = serialized.get("name", "unknown")
        if run_id is not None:
            self._pending[run_id] = model_name

    def on_llm_end(self, response: Any, run_id: Any = None, **kwargs: Any) -> None:
        model_name = (
            self._pending.pop(run_id, "unknown") if run_id is not None else "unknown"
        )

        prompt_tokens = 0
        completion_tokens = 0

        # Try llm_output first
        llm_output = getattr(response, "llm_output", None) or {}
        token_usage = llm_output.get("token_usage", {}) if llm_output else {}
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
        else:
            # Fallback: use usage_metadata from the first generation message
            try:
                gen = response.generations[0][0]
                usage = getattr(gen.message, "usage_metadata", None) or {}
                prompt_tokens = usage.get("input_tokens", 0)
                completion_tokens = usage.get("output_tokens", 0)
            except (IndexError, AttributeError):
                pass

        self.toolkit.record_llm_call(
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class LangGraphAdapter(BaseAdapter):
    """Adapter for LangGraph CompiledStateGraph agents."""

    def __init__(self, toolkit: MockToolkit) -> None:
        self.toolkit = toolkit

    def can_handle(self, agent: Any) -> bool:
        if not HAS_LANGGRAPH:
            return False
        return isinstance(agent, (CompiledStateGraph, StateGraph))

    def extract_tools(self, agent: Any) -> list[str]:
        if not HAS_LANGGRAPH:
            return []

        # Compile if uncompiled StateGraph
        compiled = self._ensure_compiled(agent)

        tool_names: list[str] = []
        for _node_name, spec in compiled.builder.nodes.items():
            if hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode):
                tool_names.extend(spec.runnable.tools_by_name.keys())
        return tool_names

    def inject_mocks(self, agent: Any, toolkit: MockToolkit) -> Any:
        """Replace real tools with mocks using save-replace-restore pattern.

        Returns a tuple (compiled_agent, saved_tools) for use in execute().
        """
        if not HAS_LANGGRAPH:
            raise ImportError("langgraph is not installed")

        compiled = self._ensure_compiled(agent)

        # Save original tools and replace with mocks
        saved: dict[str, dict[str, Any]] = {}
        for node_name, spec in compiled.builder.nodes.items():
            if not (hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode)):
                continue
            tool_node = spec.runnable
            saved[node_name] = dict(tool_node.tools_by_name)

            for tool_name, original_tool in list(tool_node.tools_by_name.items()):
                if tool_name not in toolkit._tools:
                    continue

                mock_tool_obj = toolkit._tools[tool_name]
                orig_schema: Any = getattr(original_tool, "args_schema", None)

                # Capture tool_name and mock_tool_obj in closure
                def _make_wrapper(
                    _name: str, _mock: Any
                ) -> Any:
                    def _wrapper(**kwargs: Any) -> Any:
                        return _mock.invoke(kwargs)
                    return _wrapper

                wrapper_fn = _make_wrapper(tool_name, mock_tool_obj)

                mock_structured = StructuredTool(
                    name=tool_name,
                    description=f"Mock for {tool_name}",
                    func=wrapper_fn,
                    args_schema=orig_schema,
                    coroutine=None,
                )
                tool_node.tools_by_name[tool_name] = mock_structured

        return (compiled, saved)

    def execute(
        self,
        wrapped_agent: Any,
        input: str,
        timeout: float,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> Trajectory:
        if not HAS_LANGGRAPH:
            raise ImportError("langgraph is not installed")

        compiled, saved = wrapped_agent

        self.toolkit.reset()

        handler = _TrajectoryCallbackHandler(self.toolkit)

        try:
            result_state = compiled.invoke(
                {"messages": [HumanMessage(content=input)]},
                config={"callbacks": [handler]},
            )
            final_output = self._extract_final_output(result_state)
        except Exception as e:
            from trajai.mock.toolkit import TrajAIMockError

            self._restore_tools(compiled, saved)
            if isinstance(e, TrajAIMockError):
                raise
            return self._build_trajectory(input, error=e)
        finally:
            self._restore_tools(compiled, saved)

        return self._build_trajectory(input, final_output=final_output)

    def _ensure_compiled(self, agent: Any) -> Any:
        if HAS_LANGGRAPH and isinstance(agent, StateGraph):
            return agent.compile()
        return agent

    def _restore_tools(
        self, compiled: Any, saved: dict[str, dict[str, Any]]
    ) -> None:
        if not HAS_LANGGRAPH:
            return
        for node_name, spec in compiled.builder.nodes.items():
            if hasattr(spec, "runnable") and isinstance(spec.runnable, ToolNode):
                if node_name in saved:
                    spec.runnable.tools_by_name.clear()
                    spec.runnable.tools_by_name.update(saved[node_name])

    def _extract_final_output(self, result_state: Any) -> str | None:
        messages = result_state.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                content = msg.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    # Extract text from content blocks
                    parts = [
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    return "".join(parts) or None
        return None

    def _build_trajectory(
        self,
        input_str: str,
        final_output: str | None = None,
        error: Exception | None = None,
    ) -> Trajectory:
        all_steps: list[TrajectoryStep] = []

        # Collect tool calls
        for tool_name, tool in self.toolkit._tools.items():
            for call in tool.calls:
                step = TrajectoryStep(
                    step_index=0,
                    step_type="tool_call",
                    timestamp=call.timestamp,
                    tool_name=tool_name,
                    tool_args=call.args,
                    tool_result=call.result,
                    tool_error=call.error,
                )
                all_steps.append(step)

        # Collect LLM calls
        all_steps.extend(self.toolkit._recorded_llm_calls)

        # Sort chronologically
        all_steps.sort(key=lambda x: x.timestamp)

        # Re-index
        indexed_steps: list[TrajectoryStep] = []
        for i, step in enumerate(all_steps):
            new_step = TrajectoryStep(
                step_index=i,
                step_type=step.step_type,
                timestamp=step.timestamp,
                tool_name=step.tool_name,
                tool_args=step.tool_args,
                tool_result=step.tool_result,
                tool_error=step.tool_error,
                model=step.model,
                prompt_tokens=step.prompt_tokens,
                completion_tokens=step.completion_tokens,
                cost=step.cost,
                key=step.key,
                old_value=step.old_value,
                new_value=step.new_value,
            )
            indexed_steps.append(new_step)

        # Compute aggregates
        total_tokens = sum(
            (s.prompt_tokens or 0) + (s.completion_tokens or 0)
            for s in indexed_steps
            if s.step_type == "llm_call"
        )
        total_cost = sum(
            s.cost or 0.0 for s in indexed_steps if s.step_type == "llm_call"
        )
        llm_calls = sum(1 for s in indexed_steps if s.step_type == "llm_call")

        return Trajectory(
            input=input_str,
            steps=indexed_steps,
            final_output=final_output,
            total_tokens=total_tokens,
            total_cost=total_cost,
            llm_calls=llm_calls,
            error=error,
        )
