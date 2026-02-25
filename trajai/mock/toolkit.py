from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Sequence

from trajai.core.result import MockToolCall

if TYPE_CHECKING:
    from trajai.core.result import AgentRunResult
    from trajai.core.trajectory import TrajectoryStep

from trajai.mock.strategies import (
    CallableStrategy,
    ConditionalStrategy,
    ErrorStrategy,
    ResponseStrategy,
    SequenceStrategy,
    StaticStrategy,
)


class TrajAIMockError(Exception):
    """Base class for errors in the UnitAI mock layer."""
    pass

class UnmockedToolError(TrajAIMockError):
    """Raised when an agent calls a tool that has no mock registered in strict mode."""
    pass

class AgentTimeoutError(TrajAIMockError):
    """Raised when an agent exceeds the configured timeout."""
    def __init__(self, message: str, partial_result: Optional[AgentRunResult] = None):
        super().__init__(message)
        self.partial_result = partial_result

class AdapterNotFoundError(TrajAIMockError):
    """Raised when no adapter can handle the given agent type."""
    pass

class MockToolDict(dict): # type: ignore
    def __init__(
        self,
        tools: Any,
        strict: bool = True
    ):
        super().__init__(tools)
        self._strict = strict

    def __getitem__(self, key: str) -> Any:
        if key not in self:
            if self._strict:
                raise UnmockedToolError(
                    f"Agent called tool '{key}' which has no mock registered. "
                    f"Registered mocks: {list(self.keys())}"
                )
            else:
                raise KeyError(key)
        return super().__getitem__(key)

class MockTool:
    def __init__(self, name: str, strategy: ResponseStrategy):
        self.name = name
        self.strategy = strategy
        self.calls: list[MockToolCall] = []

    def invoke(self, args: dict[str, Any]) -> Any:
        timestamp = datetime.now().timestamp()
        result = None
        error = None

        try:
            result = self.strategy.execute(args)
            return result
        except Exception as e:
            error = e
            raise
        finally:
            call = MockToolCall(
                args=args,
                result=result,
                timestamp=timestamp,
                error=error
            )
            self.calls.append(call)

    def reset(self) -> None:
        self.calls = []

class MockToolkit:
    def __init__(self, strict: bool | None = None) -> None:
        """Initialize MockToolkit.

        Args:
            strict: If True, raise UnmockedToolError on unmocked tool calls.
                   If None, use config default.
        """
        from trajai.config import get_config

        config = get_config()
        self._strict = strict if strict is not None else config.strict_mocks
        self._tools: dict[str, MockTool] = {}
        self._recorded_llm_calls: list[TrajectoryStep] = []

    def mock(
        self,
        name: str,
        return_value: Any = None,
        side_effect: Optional[Callable[[dict[str, Any]], Any] | Exception] = None,
        sequence: Optional[Sequence[Any]] = None,
        conditional: Optional[dict[Callable[[dict[str, Any]], bool], Any]] = None,
    ) -> MockTool:
        strategy: ResponseStrategy

        if sequence is not None:
            strategy = SequenceStrategy(sequence)
        elif conditional is not None:
            strategy = ConditionalStrategy(conditional)
        elif isinstance(side_effect, Exception):
            strategy = ErrorStrategy(side_effect)
        elif callable(side_effect):
            strategy = CallableStrategy(side_effect)
        else:
            strategy = StaticStrategy(return_value)

        tool = MockTool(name, strategy)
        self._tools[name] = tool
        return tool

    def get_tool(self, name: str) -> MockTool:
        if name not in self._tools:
            raise KeyError(f"No mock tool registered with name: {name}")
        return self._tools[name]

    def as_dict(self, strict: bool | None = None) -> Dict[str, Any]:
        """Get mock tools as a dictionary.

        Args:
            strict: If None, use instance default (from config).
        """
        if strict is None:
            strict = self._strict
        tools = {name: tool.invoke for name, tool in self._tools.items()}
        return MockToolDict(tools, strict=strict)

    def reset(self) -> None:
        for tool in self._tools.values():
            tool.reset()
        self._recorded_llm_calls = []

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        from trajai.core.trajectory import TrajectoryStep

        step = TrajectoryStep(
            step_index=0,  # Will be re-indexed during aggregation
            step_type="llm_call",
            timestamp=datetime.now().timestamp(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )
        self._recorded_llm_calls.append(step)

    def run(
        self,
        agent: Any,
        input: Any,
        timeout: float = 60.0,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> AgentRunResult:
        import asyncio
        import os

        from trajai.config import get_config
        from trajai.core.result import AgentRunResult

        config = get_config()

        # Determine cache settings
        if cache is None and config.cache_enabled:
            from trajai.runner.replay import ReplayCache
            cache = ReplayCache(
                directory=config.cache_directory,
                ttl_hours=config.cache_ttl_hours,
            )
            # Check environment for cache mode override
            env_mode = os.environ.get("TRAJAI_CACHE_MODE", "auto")
            if env_mode != "auto":
                cache_mode = env_mode

        adapter = self._resolve_adapter(agent)
        wrapped = adapter.inject_mocks(agent, self)

        async def _execute() -> AgentRunResult:
            try:
                trajectory = await asyncio.wait_for(
                    asyncio.to_thread(
                        adapter.execute,
                        wrapped,
                        str(input),
                        timeout,
                        cache,
                        cache_mode,
                    ),
                    timeout=timeout,
                )
                return AgentRunResult(trajectory=trajectory)
            except asyncio.TimeoutError:
                # Use the resolved adapter's _build_trajectory if available,
                # otherwise fall back to a generic minimal trajectory builder.
                build_fn = getattr(adapter, "_build_trajectory", None)
                if build_fn is not None:
                    partial_traj = build_fn(
                        str(input),
                        error=AgentTimeoutError(f"Agent exceeded {timeout}s timeout"),
                    )
                else:
                    from trajai.adapters.generic import GenericAdapter
                    partial_traj = GenericAdapter(self)._build_trajectory(
                        str(input),
                        error=AgentTimeoutError(f"Agent exceeded {timeout}s timeout"),
                    )
                partial_result = AgentRunResult(trajectory=partial_traj)
                raise AgentTimeoutError(
                    f"Agent exceeded {timeout}s timeout",
                    partial_result=partial_result,
                ) from None

        return asyncio.run(_execute())

    def _resolve_adapter(self, agent: Any) -> Any:
        try:
            from trajai.adapters.langgraph import LangGraphAdapter
            adapter: Any = LangGraphAdapter(self)
            if adapter.can_handle(agent):
                return adapter
        except ImportError:
            pass

        try:
            from trajai.adapters.openai_agents import OpenAIAgentsAdapter
            adapter = OpenAIAgentsAdapter(self)
            if adapter.can_handle(agent):
                return adapter
        except ImportError:
            pass

        try:
            from trajai.adapters.crewai import CrewAIAdapter
            adapter = CrewAIAdapter(self)
            if adapter.can_handle(agent):
                return adapter
        except ImportError:
            pass

        raise AdapterNotFoundError(
            f"No adapter found for agent type '{type(agent).__name__}'. "
            "Supported: LangGraph CompiledStateGraph/StateGraph, "
            "OpenAI Agents SDK Agent, CrewAI Crew/Agent. "
            "Install extras: trajai[langgraph], "
            "trajai[openai-agents], or trajai[crewai]."
        )

    def run_generic(
        self,
        callable_agent: Callable[[], Any],
        timeout: float = 60.0,
        _cleanup_callback: Optional[Callable[[], None]] = None,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> AgentRunResult:
        import asyncio

        from trajai.adapters.generic import GenericAdapter
        from trajai.core.result import AgentRunResult

        adapter = GenericAdapter(self)

        async def _execute() -> AgentRunResult:
            try:
                # Wrap synchronous agent in a thread to avoid blocking the event loop
                trajectory = await asyncio.wait_for(
                    asyncio.to_thread(
                        adapter.execute,
                        callable_agent,
                        "generic",
                        timeout,
                        cache,
                        cache_mode,
                    ),
                    timeout=timeout
                )
                return AgentRunResult(trajectory=trajectory)
            except asyncio.TimeoutError:
                if _cleanup_callback:
                    _cleanup_callback()
                # Build partial trajectory
                partial_traj = adapter._build_trajectory(
                    "generic",
                    error=AgentTimeoutError(f"Agent exceeded {timeout}s timeout")
                )
                partial_result = AgentRunResult(trajectory=partial_traj)
                raise AgentTimeoutError(
                    f"Agent exceeded {timeout}s timeout",
                    partial_result=partial_result
                ) from None

        return asyncio.run(_execute())

    def run_callable(
        self,
        fn: Callable[[Any, dict[str, Any]], Any],
        input: Any,
        timeout: float = 60.0,
        strict: bool | None = None,
        _cleanup_callback: Optional[Callable[[], None]] = None,
        cache: Optional[Any] = None,
        cache_mode: str = "auto",
    ) -> AgentRunResult:
        import asyncio

        from trajai.adapters.generic import GenericAdapter
        from trajai.core.result import AgentRunResult

        adapter = GenericAdapter(self)
        tools = self.as_dict(strict=strict)

        async def _execute() -> AgentRunResult:
            try:
                trajectory = await asyncio.wait_for(
                    asyncio.to_thread(
                        adapter.execute,
                        fn,
                        str(input),
                        timeout,
                        cache,
                        cache_mode,
                        tools,
                    ),
                    timeout=timeout
                )
                return AgentRunResult(trajectory=trajectory)
            except asyncio.TimeoutError:
                if _cleanup_callback:
                    _cleanup_callback()
                partial_traj = adapter._build_trajectory(
                    str(input),
                    error=AgentTimeoutError(f"Agent exceeded {timeout}s timeout")
                )
                partial_result = AgentRunResult(trajectory=partial_traj)
                raise AgentTimeoutError(
                    f"Agent exceeded {timeout}s timeout",
                    partial_result=partial_result
                ) from None

        return asyncio.run(_execute())
