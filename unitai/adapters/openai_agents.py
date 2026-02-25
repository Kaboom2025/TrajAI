from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING, Any, Optional

from unitai.adapters.base import BaseAdapter
from unitai.core.trajectory import Trajectory, TrajectoryStep

if TYPE_CHECKING:
    from unitai.mock.toolkit import MockToolkit

try:
    from agents import Agent, Runner

    HAS_OPENAI_AGENTS = True
except ImportError:
    HAS_OPENAI_AGENTS = False


class OpenAIAgentsAdapter(BaseAdapter):
    """Adapter for the OpenAI Agents SDK (openai-agents package).

    Supports any ``agents.Agent`` instance. Tool injection works by replacing
    ``FunctionTool`` objects in a shallow copy of the agent with wrapper tools
    that call the UnitAI mocks. The original agent is never mutated.
    """

    def __init__(self, toolkit: "MockToolkit") -> None:
        self.toolkit = toolkit

    def can_handle(self, agent: Any) -> bool:
        if not HAS_OPENAI_AGENTS:
            return False
        return isinstance(agent, Agent)

    def extract_tools(self, agent: Any) -> list[str]:
        if not HAS_OPENAI_AGENTS:
            return []
        names: list[str] = []
        for tool in getattr(agent, "tools", []) or []:
            name = getattr(tool, "name", None)
            if name:
                names.append(str(name))
        return names

    def inject_mocks(self, agent: Any, toolkit: "MockToolkit") -> Any:
        """Return a shallow-copied Agent with matching FunctionTools replaced."""
        if not HAS_OPENAI_AGENTS:
            raise ImportError(
                "openai-agents is not installed. Run: pip install openai-agents"
            )

        from agents.tool import FunctionTool

        original_tools: list[Any] = list(getattr(agent, "tools", []) or [])
        new_tools: list[Any] = []

        for original_tool in original_tools:
            if (
                isinstance(original_tool, FunctionTool)
                and original_tool.name in toolkit._tools
            ):
                mock_obj = toolkit._tools[original_tool.name]
                tool_name = original_tool.name
                orig_schema = original_tool.params_json_schema
                orig_description = original_tool.description

                # Build an async on_invoke_tool that delegates to the mock
                def _make_invoke(
                    _name: str, _mock: Any
                ) -> Any:
                    async def _on_invoke(ctx: Any, args_json: str) -> Any:
                        try:
                            kwargs = json.loads(args_json)
                        except (json.JSONDecodeError, ValueError):
                            kwargs = {}
                        return _mock.invoke(kwargs)

                    return _on_invoke

                mock_function_tool = FunctionTool(
                    name=tool_name,
                    description=orig_description,
                    params_json_schema=orig_schema,
                    on_invoke_tool=_make_invoke(tool_name, mock_obj),
                    strict_json_schema=False,  # schema already processed by original
                )
                new_tools.append(mock_function_tool)
            else:
                new_tools.append(original_tool)

        # Shallow copy the agent, then replace its tools list
        wrapped = copy.copy(agent)
        object.__setattr__(wrapped, "tools", new_tools)
        return (wrapped, agent)  # (wrapped, original) — original kept for restore check

    def execute(
        self,
        wrapped_agent: Any,
        input: str,
        timeout: float,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> Trajectory:
        if not HAS_OPENAI_AGENTS:
            raise ImportError(
                "openai-agents is not installed. Run: pip install openai-agents"
            )

        agent_copy, _original = wrapped_agent
        self.toolkit.reset()

        try:
            run_result = Runner.run_sync(agent_copy, input)
        except Exception as e:
            from unitai.mock.toolkit import UnitAIMockError

            if isinstance(e, UnitAIMockError):
                raise
            return self._build_trajectory(input, error=e)

        # Extract final output
        final_output: str | None = None
        raw_output = getattr(run_result, "final_output", None)
        if raw_output is not None:
            final_output = str(raw_output)

        # Extract LLM metadata from raw_responses
        raw_responses = getattr(run_result, "raw_responses", []) or []
        for response in raw_responses:
            model_name = getattr(response, "model", "unknown") or "unknown"
            usage = getattr(response, "usage", None)
            prompt_tokens = 0
            completion_tokens = 0
            if usage is not None:
                prompt_tokens = getattr(usage, "input_tokens", 0) or 0
                completion_tokens = getattr(usage, "output_tokens", 0) or 0
            self.toolkit.record_llm_call(
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        return self._build_trajectory(input, final_output=final_output)

    def _build_trajectory(
        self,
        input_str: str,
        final_output: str | None = None,
        error: Exception | None = None,
    ) -> Trajectory:
        all_steps: list[TrajectoryStep] = []

        # Collect tool calls recorded by MockTool.invoke
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

        # Sort and re-index chronologically
        all_steps.sort(key=lambda x: x.timestamp)
        indexed_steps: list[TrajectoryStep] = []
        for i, step in enumerate(all_steps):
            indexed_steps.append(
                TrajectoryStep(
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
            )

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
