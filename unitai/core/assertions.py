from __future__ import annotations
from typing import Any, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from unitai.core.trajectory import Trajectory

def tool_was_called(trajectory: Trajectory, name: str) -> tuple[bool, str]:
    """Check if a tool was called at least once."""
    for step in trajectory.steps:
        if step.step_type == "tool_call" and step.tool_name == name:
            return True, f"Tool '{name}' was called."
    return False, f"Tool '{name}' was never called."

def tool_not_called(trajectory: Trajectory, name: str) -> tuple[bool, str]:
    """Check if a tool was never called."""
    called, _ = tool_was_called(trajectory, name)
    if called:
        return False, f"Tool '{name}' was called but expected not to be."
    return True, f"Tool '{name}' was not called."

def tool_call_count(trajectory: Trajectory, name: str, expected_count: int) -> tuple[bool, str]:
    """Check if a tool was called exactly N times."""
    count = sum(1 for s in trajectory.steps if s.step_type == "tool_call" and s.tool_name == name)
    if count == expected_count:
        return True, f"Tool '{name}' was called {count} times."
    return False, f"Tool '{name}' was called {count} times, expected {expected_count}."

def tool_called_with(trajectory: Trajectory, name: str, **kwargs: Any) -> tuple[bool, str]:
    """Check if a tool was called with exact arguments at least once."""
    for step in trajectory.steps:
        if step.step_type == "tool_call" and step.tool_name == name:
            if step.tool_args == kwargs:
                return True, f"Tool '{name}' was called with exact args: {kwargs}"
    return False, f"Tool '{name}' was never called with exact args: {kwargs}"

def tool_called_with_partial(trajectory: Trajectory, name: str, **kwargs: Any) -> tuple[bool, str]:
    """Check if a tool was called with args including these key-value pairs."""
    for step in trajectory.steps:
        if step.step_type == "tool_call" and step.tool_name == name:
            args = step.tool_args or {}
            match = True
            for k, v in kwargs.items():
                if k not in args or args[k] != v:
                    match = False
                    break
            if match:
                return True, f"Tool '{name}' was called with partial args matching: {kwargs}"
    return False, f"Tool '{name}' was never called with partial args matching: {kwargs}"

def tool_called_before(trajectory: Trajectory, first: str, second: str) -> tuple[bool, str]:
    """Check if first tool was called before second tool (first occurrence of each)."""
    first_idx = -1
    second_idx = -1
    for step in trajectory.steps:
        if step.step_type == "tool_call":
            if first_idx == -1 and step.tool_name == first:
                first_idx = step.step_index
            if second_idx == -1 and step.tool_name == second:
                second_idx = step.step_index
    
    if first_idx == -1:
        return False, f"Tool '{first}' was never called."
    if second_idx == -1:
        return False, f"Tool '{second}' was never called."
    
    if first_idx < second_idx:
        return True, f"Tool '{first}' (step {first_idx}) was called before '{second}' (step {second_idx})."
    return False, f"Tool '{first}' (step {first_idx}) was NOT called before '{second}' (step {second_idx})."

def tool_called_immediately_before(trajectory: Trajectory, first: str, second: str) -> tuple[bool, str]:
    """Check if first tool was called directly before second (ignoring non-tool steps)."""
    tool_steps = [s for s in trajectory.steps if s.step_type == "tool_call"]
    for i in range(len(tool_steps) - 1):
        if tool_steps[i].tool_name == first and tool_steps[i+1].tool_name == second:
            return True, f"Tool '{first}' was called immediately before '{second}'."
    return False, f"Tool '{first}' was NOT called immediately before '{second}'."

def call_order(trajectory: Trajectory) -> list[str]:
    """Return list of tool names in order."""
    return [s.tool_name for s in trajectory.steps if s.step_type == "tool_call" and s.tool_name is not None]

def call_order_contains(trajectory: Trajectory, subsequence: list[str]) -> tuple[bool, str]:
    """Check if this subsequence of tool calls appears in order."""
    actual_order = call_order(trajectory)
    sub_idx = 0
    for name in actual_order:
        if sub_idx < len(subsequence) and name == subsequence[sub_idx]:
            sub_idx += 1
    
    if sub_idx == len(subsequence):
        return True, f"Trajectory contains tool call subsequence: {subsequence}"
    return False, f"Trajectory does NOT contain tool call subsequence: {subsequence}"

# Placeholders for Output & Metadata Assertions
def output_equals(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    return False, "Not implemented"

def output_contains(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    return False, "Not implemented"

def output_not_contains(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    return False, "Not implemented"

def output_matches(trajectory: Trajectory, pattern: str) -> tuple[bool, str]:
    return False, "Not implemented"

def cost_under(trajectory: Trajectory, limit: float) -> tuple[bool, str]:
    return False, "Not implemented"

def tokens_under(trajectory: Trajectory, limit: int) -> tuple[bool, str]:
    return False, "Not implemented"

def duration_under(trajectory: Trajectory, limit: float) -> tuple[bool, str]:
    return False, "Not implemented"

def llm_calls_under(trajectory: Trajectory, limit: int) -> tuple[bool, str]:
    return False, "Not implemented"

def succeeded(trajectory: Trajectory) -> tuple[bool, str]:
    return False, "Not implemented"

def failed(trajectory: Trajectory) -> tuple[bool, str]:
    return False, "Not implemented"

def error_is(trajectory: Trajectory, exception_type: type[Exception]) -> tuple[bool, str]:
    return False, "Not implemented"
