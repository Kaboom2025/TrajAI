from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Optional, Union
import uuid

@dataclass(frozen=True)
class TrajectoryStep:
    step_index: int
    step_type: str  # "tool_call", "llm_call", "state_change"
    timestamp: float
    
    # Tool call fields
    tool_name: Optional[str] = None
    tool_args: Optional[dict[str, Any]] = None
    tool_result: Optional[Any] = None
    tool_error: Optional[Union[Exception, dict[str, Any]]] = None
    
    # LLM call fields
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost: Optional[float] = None
    
    # State change fields
    key: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    def __post_init__(self) -> None:
        valid_types = {"tool_call", "llm_call", "state_change"}
        if self.step_type not in valid_types:
            raise ValueError(f"Invalid step_type: {self.step_type}. Must be one of {valid_types}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.tool_error and isinstance(self.tool_error, Exception):
            data["tool_error"] = {
                "type": type(self.tool_error).__name__,
                "message": str(self.tool_error),
                "module": type(self.tool_error).__module__
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrajectoryStep:
        return cls(**data)

@dataclass(frozen=True)
class Trajectory:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input: str = ""
    steps: list[TrajectoryStep] = field(default_factory=list)
    final_output: Optional[str] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_seconds: float = 0.0
    llm_calls: int = 0
    error: Optional[Union[Exception, dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.to_dict() for step in self.steps]
        if self.error and isinstance(self.error, Exception):
            data["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error),
                "module": type(self.error).__module__
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trajectory:
        steps_data = data.pop("steps", [])
        steps = [TrajectoryStep.from_dict(s) for s in steps_data]
        return cls(steps=steps, **data)
