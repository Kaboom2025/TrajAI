from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from trajai.adapters.base import BaseAdapter
from trajai.core.trajectory import Trajectory, TrajectoryStep

if TYPE_CHECKING:
    from trajai.mock.toolkit import MockToolkit

class GenericAdapter(BaseAdapter):
    """Adapter for arbitrary Python callables."""

    def __init__(self, toolkit: MockToolkit):
        self.toolkit = toolkit

    def can_handle(self, agent: Any) -> bool:
        return callable(agent)

    def inject_mocks(self, agent: Any, toolkit: MockToolkit) -> Any:
        # User is responsible for wiring mocks in generic mode
        return agent

    def extract_tools(self, agent: Any) -> list[str]:
        return []

    def execute(
        self,
        wrapped_agent: Any,
        input: str,
        timeout: float,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
        tools: dict[str, Any] | None = None
    ) -> Trajectory:
        # Reset toolkit before run
        self.toolkit.reset()

        # Execute the agent
        try:
            if tools is not None:
                output = wrapped_agent(input, tools)
            else:
                output = wrapped_agent()
        except Exception as e:
            # Re-raise mock errors immediately
            from trajai.mock.toolkit import TrajAIMockError
            if isinstance(e, TrajAIMockError):
                raise
            # Capture partial trajectory on other errors
            return self._build_trajectory(input, error=e)

        return self._build_trajectory(input, final_output=str(output))

    def _build_trajectory(
        self,
        input_str: str,
        final_output: str | None = None,
        error: Exception | None = None
    ) -> Trajectory:
        all_steps = []

        # Collect tool calls
        for tool_name, tool in self.toolkit._tools.items():
            for call in tool.calls:
                step = TrajectoryStep(
                    step_index=0, # placeholder
                    step_type="tool_call",
                    timestamp=call.timestamp,
                    tool_name=tool_name,
                    tool_args=call.args,
                    tool_result=call.result,
                    tool_error=call.error
                )
                all_steps.append(step)

        # Collect LLM calls
        all_steps.extend(self.toolkit._recorded_llm_calls)

        # Sort chronologically
        all_steps.sort(key=lambda x: x.timestamp)

        # Re-index
        indexed_steps = []
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
                new_value=step.new_value
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
            error=error
        )
