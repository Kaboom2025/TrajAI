from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional, Sequence, TYPE_CHECKING
from unitai.core.result import MockToolCall
if TYPE_CHECKING:
    from unitai.core.trajectory import TrajectoryStep

from unitai.mock.strategies import (
    CallableStrategy,
    ConditionalStrategy,
    ErrorStrategy,
    ResponseStrategy,
    SequenceStrategy,
    StaticStrategy,
)


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

    def __init__(self) -> None:

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



    def as_dict(self) -> dict[str, Callable[[dict[str, Any]], Any]]:

        return {name: tool.invoke for name, tool in self._tools.items()}



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

        from unitai.core.trajectory import TrajectoryStep

        

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



    def run(self, *args: Any, **kwargs: Any) -> Any:


        raise NotImplementedError("run() will be implemented in Phase 2/5")
