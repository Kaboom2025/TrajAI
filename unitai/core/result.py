from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

from unitai.core import assertions
from unitai.core.formatter import TrajectoryFormatter
from unitai.core.trajectory import Trajectory


@dataclass(frozen=True)
class MockToolCall:
    args: dict[str, Any]
    result: Any
    timestamp: float
    error: Optional[Union[Exception, dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.error and isinstance(self.error, Exception):
            data["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error),
                "module": type(self.error).__module__
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MockToolCall:
        return cls(**data)

@dataclass(frozen=True)
class AgentRunResult:
    trajectory: Trajectory

    @property
    def output(self) -> Optional[str]:
        return self.trajectory.final_output

    @property
    def total_cost(self) -> float:
        return self.trajectory.total_cost

    @property
    def total_tokens(self) -> int:
        return self.trajectory.total_tokens

    @property
    def duration(self) -> float:
        return self.trajectory.duration_seconds

    @property
    def error(self) -> Optional[Union[Exception, dict[str, Any]]]:
        return self.trajectory.error

    @property
    def succeeded(self) -> bool:
        return self.trajectory.error is None

    @property
    def failed(self) -> bool:
        return self.trajectory.error is not None

    @property
    def llm_calls(self) -> int:
        return self.trajectory.llm_calls

    # --- Query API ---

    def get_calls(self, name: str) -> List[MockToolCall]:
        """Return all mock tool calls for a specific tool name."""
        calls = []
        for step in self.trajectory.steps:
            if step.step_type == "tool_call" and step.tool_name == name:
                calls.append(MockToolCall(
                    args=step.tool_args or {},
                    result=step.tool_result,
                    timestamp=step.timestamp,
                    error=step.tool_error
                ))
        return calls

    def get_call(self, name: str, n: int = 0) -> MockToolCall:
        """Return the Nth call to a specific tool."""
        calls = self.get_calls(name)
        if n >= len(calls):
            raise IndexError(
                f"Tool '{name}' was called {len(calls)} times, "
                f"requested call index {n}"
            )
        return calls[n]

    def call_order(self) -> List[str]:
        """Return the sequence of all tool names called."""
        return assertions.call_order(self.trajectory)

    # --- Boolean API ---

    def tool_was_called(self, name: str) -> bool:
        return assertions.tool_was_called(self.trajectory, name)[0]

    def tool_not_called(self, name: str) -> bool:
        return assertions.tool_not_called(self.trajectory, name)[0]

    def tool_call_count(self, name: str, count: int) -> bool:
        return assertions.tool_call_count(self.trajectory, name, count)[0]

    def tool_called_with(self, name: str, **kwargs: Any) -> bool:
        return assertions.tool_called_with(self.trajectory, name, **kwargs)[0]

    def tool_called_with_partial(self, name: str, **kwargs: Any) -> bool:
        return assertions.tool_called_with_partial(
            self.trajectory, name, **kwargs
        )[0]

    def tool_called_before(self, first: str, second: str) -> bool:
        return assertions.tool_called_before(self.trajectory, first, second)[0]

    def tool_called_immediately_before(self, first: str, second: str) -> bool:
        return assertions.tool_called_immediately_before(
            self.trajectory, first, second
        )[0]

    def output_equals(self, text: str) -> bool:
        return assertions.output_equals(self.trajectory, text)[0]

    def output_contains(self, text: str) -> bool:
        return assertions.output_contains(self.trajectory, text)[0]

    def output_not_contains(self, text: str) -> bool:
        return assertions.output_not_contains(self.trajectory, text)[0]

    def output_matches(self, pattern: str) -> bool:
        return assertions.output_matches(self.trajectory, pattern)[0]

    def call_order_contains(self, subsequence: list[str]) -> bool:
        return assertions.call_order_contains(self.trajectory, subsequence)[0]

    def error_is(self, exception_type: type[Exception]) -> bool:
        return assertions.error_is(self.trajectory, exception_type)[0]

    # --- Assert API ---

    def assert_tool_was_called(self, name: str) -> None:
        self._check(assertions.tool_was_called(self.trajectory, name))

    def assert_tool_not_called(self, name: str) -> None:
        self._check(assertions.tool_not_called(self.trajectory, name))

    def assert_tool_called_before(self, first: str, second: str) -> None:
        self._check(assertions.tool_called_before(self.trajectory, first, second))

    def assert_tool_call_count(self, name: str, count: int) -> None:
        self._check(assertions.tool_call_count(self.trajectory, name, count))

    def assert_tool_called_with(self, name: str, **kwargs: Any) -> None:
        self._check(assertions.tool_called_with(self.trajectory, name, **kwargs))

    def assert_tool_called_with_partial(self, name: str, **kwargs: Any) -> None:
        self._check(
            assertions.tool_called_with_partial(self.trajectory, name, **kwargs)
        )

    def assert_tool_called_immediately_before(
        self, first: str, second: str
    ) -> None:
        self._check(
            assertions.tool_called_immediately_before(
                self.trajectory, first, second
            )
        )

    def assert_call_order_contains(self, subsequence: list[str]) -> None:
        self._check(
            assertions.call_order_contains(self.trajectory, subsequence)
        )

    def assert_output_contains(self, text: str) -> None:
        self._check(assertions.output_contains(self.trajectory, text))

    def assert_output_not_contains(self, text: str) -> None:
        self._check(assertions.output_not_contains(self.trajectory, text))

    def assert_output_equals(self, text: str) -> None:
        self._check(assertions.output_equals(self.trajectory, text))

    def assert_output_matches(self, pattern: str) -> None:
        self._check(assertions.output_matches(self.trajectory, pattern))

    def _check(
        self,
        result: tuple[bool, str],
        highlights: Optional[Dict[int, str]] = None
    ) -> None:
        passed, message = result
        if not passed:
            formatter = TrajectoryFormatter()
            traj_summary = formatter.format(self.trajectory, highlights=highlights)
            error_msg = f"{message}\n\n{traj_summary}"
            raise assertions.UnitAIAssertionError(error_msg)
