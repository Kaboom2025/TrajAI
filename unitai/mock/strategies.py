from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Sequence


class UnitAIMockError(Exception):
    """Base class for errors in the UnitAI mock layer."""
    pass

class MockExhaustedError(UnitAIMockError):
    """Raised when a SequenceStrategy is called more times than provided values."""
    pass

class NoMatchingConditionError(UnitAIMockError):
    """Raised when a ConditionalStrategy has no matching condition for the input."""
    pass

class ResponseStrategy(ABC):
    """Abstract base class for all mock tool response strategies."""

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> Any:
        """Execute the strategy and return a value or raise an error."""
        pass

class StaticStrategy(ResponseStrategy):
    def __init__(self, value: Any):
        self.value = value

    def execute(self, args: dict[str, Any]) -> Any:
        return self.value

class SequenceStrategy(ResponseStrategy):
    def __init__(self, values: Sequence[Any]):
        self.values = values
        self._index = 0

    def execute(self, args: dict[str, Any]) -> Any:
        if self._index >= len(self.values):
            raise MockExhaustedError(
                f"SequenceStrategy exhausted after {len(self.values)} calls"
            )
        val = self.values[self._index]
        self._index += 1
        return val

class ConditionalStrategy(ResponseStrategy):
    def __init__(self, conditions: dict[Callable[[dict[str, Any]], bool], Any]):
        self.conditions = conditions

    def execute(self, args: dict[str, Any]) -> Any:
        for condition, value in self.conditions.items():
            if condition(args):
                return value
        raise NoMatchingConditionError(
            f"No matching condition found for arguments: {args}"
        )

class ErrorStrategy(ResponseStrategy):
    def __init__(self, exception: Exception):
        self.exception = exception

    def execute(self, args: dict[str, Any]) -> Any:
        raise self.exception

class CallableStrategy(ResponseStrategy):
    def __init__(self, fn: Callable[[dict[str, Any]], Any]):
        self.fn = fn

    def execute(self, args: dict[str, Any]) -> Any:
        return self.fn(args)
