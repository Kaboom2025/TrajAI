from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from trajai.adapters.base import BaseAdapter
from trajai.core.trajectory import Trajectory, TrajectoryStep

if TYPE_CHECKING:
    from trajai.mock.toolkit import MockToolkit

try:
    from crewai import Agent as CrewAgent
    from crewai import Crew, Task
    from crewai.tools import BaseTool

    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False


class CrewAIAdapter(BaseAdapter):
    """Adapter for CrewAI ``Crew`` and ``Agent`` objects.

    Supports:
    - ``crewai.Crew`` — directly kickoffs the crew
    - ``crewai.Agent`` — wraps in a single-task crew and kickoffs

    Tool injection replaces ``BaseTool`` instances on all agents with mock
    wrappers that call UnitAI mocks. The original objects are not mutated;
    Pydantic ``model_copy()`` is used to create modified copies.
    """

    def __init__(self, toolkit: "MockToolkit") -> None:
        self.toolkit = toolkit

    def can_handle(self, agent: Any) -> bool:
        if not HAS_CREWAI:
            return False
        return isinstance(agent, (Crew, CrewAgent))

    def extract_tools(self, agent: Any) -> list[str]:
        if not HAS_CREWAI:
            return []
        names: list[str] = []
        if isinstance(agent, Crew):
            for crew_agent in getattr(agent, "agents", []) or []:
                for tool in getattr(crew_agent, "tools", []) or []:
                    name = getattr(tool, "name", None)
                    if name:
                        names.append(str(name))
        elif isinstance(agent, CrewAgent):
            for tool in getattr(agent, "tools", []) or []:
                name = getattr(tool, "name", None)
                if name:
                    names.append(str(name))
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    def inject_mocks(self, agent: Any, toolkit: "MockToolkit") -> Any:
        """Return a copy of the Crew/Agent with matching tools replaced by mocks.

        Returns a tuple (wrapped_agent, agent_type) where agent_type is
        "crew" or "agent".
        """
        if not HAS_CREWAI:
            raise ImportError("crewai is not installed. Run: pip install crewai")

        if isinstance(agent, Crew):
            wrapped_agents = [
                self._replace_agent_tools(a, toolkit)
                for a in (getattr(agent, "agents", []) or [])
            ]
            try:
                wrapped_crew = agent.model_copy(update={"agents": wrapped_agents})
            except Exception:
                # Fallback: recreate from dict
                data = agent.model_dump()
                data["agents"] = wrapped_agents
                wrapped_crew = Crew(**data)
            return (wrapped_crew, "crew")

        elif isinstance(agent, CrewAgent):
            wrapped = self._replace_agent_tools(agent, toolkit)
            return (wrapped, "agent")

        raise ValueError(f"Unsupported agent type: {type(agent)}")

    def _replace_agent_tools(
        self, crew_agent: Any, toolkit: "MockToolkit"
    ) -> Any:
        """Return a copy of a CrewAI Agent with matching tools replaced."""
        original_tools: list[Any] = list(getattr(crew_agent, "tools", []) or [])
        new_tools: list[Any] = []

        for original_tool in original_tools:
            tool_name = getattr(original_tool, "name", None)
            if tool_name and tool_name in toolkit._tools:
                mock_obj = toolkit._tools[tool_name]
                new_tools.append(_make_mock_tool(tool_name, mock_obj))
            else:
                new_tools.append(original_tool)

        try:
            return crew_agent.model_copy(update={"tools": new_tools})
        except Exception:
            # Pydantic v1 fallback
            data = crew_agent.dict()
            data["tools"] = new_tools
            return type(crew_agent)(**data)

    def execute(
        self,
        wrapped_agent: Any,
        input: str,
        timeout: float,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> Trajectory:
        if not HAS_CREWAI:
            raise ImportError("crewai is not installed. Run: pip install crewai")

        agent_obj, agent_type = wrapped_agent
        self.toolkit.reset()

        try:
            if agent_type == "crew":
                crew_output = agent_obj.kickoff(inputs={"input": input})
                final_output = _extract_crew_output(crew_output)
            else:
                # Wrap lone agent in a minimal crew
                task = Task(
                    description=input,
                    expected_output="Complete the task.",
                    agent=agent_obj,
                )
                tmp_crew = Crew(agents=[agent_obj], tasks=[task], verbose=False)
                crew_output = tmp_crew.kickoff()
                final_output = _extract_crew_output(crew_output)
        except Exception as e:
            from trajai.mock.toolkit import TrajAIMockError

            if isinstance(e, TrajAIMockError):
                raise
            return self._build_trajectory(input, error=e)

        return self._build_trajectory(input, final_output=final_output)

    def _build_trajectory(
        self,
        input_str: str,
        final_output: str | None = None,
        error: Exception | None = None,
    ) -> Trajectory:
        all_steps: list[TrajectoryStep] = []

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

        all_steps.extend(self.toolkit._recorded_llm_calls)
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_crew_output(crew_output: Any) -> str | None:
    """Extract a string result from a CrewAI kickoff return value."""
    if crew_output is None:
        return None
    # CrewOutput dataclass / object with .raw attribute
    raw = getattr(crew_output, "raw", None)
    if raw is not None:
        return str(raw)
    # String directly
    if isinstance(crew_output, str):
        return crew_output
    return str(crew_output)


def _make_mock_tool(tool_name: str, mock_obj: Any) -> Any:
    """Create a CrewAI BaseTool subclass that delegates _run to a UnitAI mock."""
    if not HAS_CREWAI:
        raise ImportError("crewai is not installed")

    class _MockCrewTool(BaseTool):  # type: ignore[misc]
        name: str = tool_name
        description: str = f"Mock for {tool_name}"

        def _run(self, **kwargs: Any) -> Any:
            return mock_obj.invoke(kwargs)

    instance = _MockCrewTool()
    return instance
