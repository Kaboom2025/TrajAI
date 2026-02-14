from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Optional, Union
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

    def tool_was_called(self, name: str) -> bool:
        raise NotImplementedError("Assertion methods implemented in Phase 3")

    def tool_not_called(self, name: str) -> bool:
        raise NotImplementedError("Assertion methods implemented in Phase 3")

    def tool_called_before(self, first: str, second: str) -> bool:
        raise NotImplementedError("Assertion methods implemented in Phase 3")

    def tool_called_with(self, name: str, **kwargs: Any) -> bool:
        raise NotImplementedError("Assertion methods implemented in Phase 3")

    def tool_call_count(self, name: str) -> int:
        raise NotImplementedError("Assertion methods implemented in Phase 3")

    def call_order(self) -> list[str]:
        raise NotImplementedError("Assertion methods implemented in Phase 3")
