from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trajai.core.trajectory import Trajectory

class TrajAIAssertionError(AssertionError):
    """Raised when a UnitAI assertion fails."""
    pass

# --- Tool Call Assertions ---

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

def tool_call_count(
    trajectory: Trajectory, name: str, expected_count: int
) -> tuple[bool, str]:
    """Check if a tool was called exactly N times."""
    count = sum(
        1 for s in trajectory.steps
        if s.step_type == "tool_call" and s.tool_name == name
    )
    if count == expected_count:
        return True, f"Tool '{name}' was called {count} times."
    return (
        False,
        f"Tool '{name}' was called {count} times, expected {expected_count}."
    )

def tool_called_with(
    trajectory: Trajectory, name: str, **kwargs: Any
) -> tuple[bool, str]:
    """Check if a tool was called with exact arguments at least once."""
    for step in trajectory.steps:
        if step.step_type == "tool_call" and step.tool_name == name:
            if step.tool_args == kwargs:
                return True, f"Tool '{name}' was called with exact args: {kwargs}"
    return False, f"Tool '{name}' was never called with exact args: {kwargs}"

def tool_called_with_partial(
    trajectory: Trajectory, name: str, **kwargs: Any
) -> tuple[bool, str]:
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
                return (
                    True,
                    f"Tool '{name}' was called with partial args: {kwargs}"
                )
    return (
        False,
        f"Tool '{name}' was never called with partial args matching: {kwargs}"
    )

def tool_called_before(
    trajectory: Trajectory, first: str, second: str
) -> tuple[bool, str]:
    """Check if first tool was called before second (first occurrence)."""
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
        return (
            True,
            f"Tool '{first}' (step {first_idx}) was called before "
            f"'{second}' (step {second_idx})."
        )
    return (
        False,
        f"Tool '{first}' (step {first_idx}) was NOT called before "
        f"'{second}' (step {second_idx})."
    )

def tool_called_immediately_before(
    trajectory: Trajectory, first: str, second: str
) -> tuple[bool, str]:
    """Check if first tool was called directly before second."""
    tool_steps = [s for s in trajectory.steps if s.step_type == "tool_call"]
    for i in range(len(tool_steps) - 1):
        if tool_steps[i].tool_name == first and tool_steps[i+1].tool_name == second:
            return True, f"Tool '{first}' was called immediately before '{second}'."
    return False, f"Tool '{first}' was NOT called immediately before '{second}'."

def call_order(trajectory: Trajectory) -> list[str]:
    """Return list of tool names in order."""
    return [
        s.tool_name for s in trajectory.steps
        if s.step_type == "tool_call" and s.tool_name is not None
    ]

def call_order_contains(
    trajectory: Trajectory, subsequence: list[str]
) -> tuple[bool, str]:
    """Check if this subsequence of tool calls appears in order."""
    actual_order = call_order(trajectory)
    sub_idx = 0
    for name in actual_order:
        if sub_idx < len(subsequence) and name == subsequence[sub_idx]:
            sub_idx += 1

    if sub_idx == len(subsequence):
        return True, f"Trajectory contains tool call subsequence: {subsequence}"
    return (
        False,
        f"Trajectory does NOT contain tool call subsequence: {subsequence}"
    )

# --- Output Assertions ---

def output_equals(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    """Check if final agent output matches text exactly."""
    if trajectory.final_output is None:
        return False, "Agent produced no output (final_output is None)."
    if trajectory.final_output == text:
        return True, f"Agent output matches exactly: '{text}'"
    return (
        False,
        f"Agent output does NOT match. Expected: '{text}', "
        f"Actual: '{trajectory.final_output}'"
    )

def output_contains(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    """Check if final agent output contains text."""
    if trajectory.final_output is None:
        return False, "Agent produced no output (final_output is None)."
    if text in trajectory.final_output:
        return True, f"Agent output contains: '{text}'"
    return False, f"Agent output does NOT contain: '{text}'"

def output_not_contains(trajectory: Trajectory, text: str) -> tuple[bool, str]:
    """Check if final agent output does NOT contain text."""
    contained, _ = output_contains(trajectory, text)
    if contained:
        return False, f"Agent output contains '{text}' but expected not to."
    return True, f"Agent output does not contain: '{text}'"

def output_matches(trajectory: Trajectory, pattern: str) -> tuple[bool, str]:
    """Check if final agent output matches regex pattern."""
    if trajectory.final_output is None:
        return False, "Agent produced no output (final_output is None)."
    if re.search(pattern, trajectory.final_output):
        return True, f"Agent output matches pattern: '{pattern}'"
    return False, f"Agent output does NOT match pattern: '{pattern}'"

# --- Metadata Assertions ---

def cost_under(trajectory: Trajectory, limit: float) -> tuple[bool, str]:
    """Check if total cost is under limit."""
    cost = trajectory.total_cost
    if cost < limit:
        return True, f"Total cost ${cost:.4f} is under limit ${limit:.4f}."
    return False, f"Total cost ${cost:.4f} exceeds limit ${limit:.4f}."

def tokens_under(trajectory: Trajectory, limit: int) -> tuple[bool, str]:
    """Check if total tokens are under limit."""
    tokens = trajectory.total_tokens
    if tokens < limit:
        return True, f"Total tokens {tokens} are under limit {limit}."
    return False, f"Total tokens {tokens} exceed limit {limit}."

def duration_under(trajectory: Trajectory, limit: float) -> tuple[bool, str]:
    """Check if total duration is under limit."""
    dur = trajectory.duration_seconds
    if dur < limit:
        return True, f"Duration {dur:.2f}s is under limit {limit:.2f}s."
    return False, f"Duration {dur:.2f}s exceeds limit {limit:.2f}s."

def llm_calls_under(trajectory: Trajectory, limit: int) -> tuple[bool, str]:
    """Check if number of LLM calls is under limit."""
    calls = trajectory.llm_calls
    if calls < limit:
        return True, f"Number of LLM calls {calls} is under limit {limit}."
    return False, f"Number of LLM calls {calls} exceeds limit {limit}."

# --- Error Assertions ---

def succeeded(trajectory: Trajectory) -> tuple[bool, str]:
    """Check if the agent execution completed without raising."""
    if trajectory.error is None:
        return True, "Agent execution succeeded."
    return False, f"Agent execution failed with error: {trajectory.error}"

def failed(trajectory: Trajectory) -> tuple[bool, str]:
    """Check if the agent execution raised an exception."""
    if trajectory.error is not None:
        return (
            True,
            f"Agent execution failed as expected with error: {trajectory.error}"
        )
    return False, "Agent execution succeeded but was expected to fail."

def error_is(
    trajectory: Trajectory, exception_type: type[Exception]
) -> tuple[bool, str]:
    """Check if the agent raised a specific exception type."""
    if trajectory.error is None:
        return False, f"Agent succeeded, expected exception {exception_type.__name__}."

    actual_error = trajectory.error
    if isinstance(actual_error, Exception):
        if isinstance(actual_error, exception_type):
            return True, f"Agent raised expected exception: {exception_type.__name__}"
        return (
            False,
            f"Agent raised {type(actual_error).__name__}, "
            f"expected {exception_type.__name__}."
        )

    if isinstance(actual_error, dict):
        if actual_error.get("type") == exception_type.__name__:
            return True, f"Agent raised expected exception: {exception_type.__name__}"
        return (
            False,
            f"Agent raised {actual_error.get('type')}, "
            f"expected {exception_type.__name__}."
        )

    return False, f"Unknown error format in trajectory: {type(actual_error)}"
