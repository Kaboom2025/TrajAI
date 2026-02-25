import pytest

from trajai.core.assertions import (
    call_order,
    call_order_contains,
    tool_call_count,
    tool_called_before,
    tool_called_immediately_before,
    tool_called_with,
    tool_called_with_partial,
    tool_not_called,
    tool_was_called,
)
from trajai.core.trajectory import Trajectory, TrajectoryStep


@pytest.fixture
def sample_trajectory() -> Trajectory:
    steps = [
        TrajectoryStep(
            0, "tool_call", 100.0, tool_name="search",
            tool_args={"q": "test"}, tool_result="results"
        ),
        TrajectoryStep(1, "llm_call", 101.0, model="gpt-4"),
        TrajectoryStep(
            2, "tool_call", 102.0, tool_name="calculator",
            tool_args={"expression": "1+1"}, tool_result="2"
        ),
        TrajectoryStep(
            3, "tool_call", 103.0, tool_name="search",
            tool_args={"q": "more"}, tool_result="even more results"
        ),
    ]
    return Trajectory(steps=steps)

def test_tool_was_called(sample_trajectory: Trajectory) -> None:
    passed, msg = tool_was_called(sample_trajectory, "search")
    assert passed is True

    passed, msg = tool_was_called(sample_trajectory, "missing")
    assert passed is False
    assert "missing" in msg

def test_tool_not_called(sample_trajectory: Trajectory) -> None:
    passed, msg = tool_not_called(sample_trajectory, "missing")
    assert passed is True

    passed, msg = tool_not_called(sample_trajectory, "search")
    assert passed is False
    assert "search" in msg

def test_tool_call_count(sample_trajectory: Trajectory) -> None:
    passed, msg = tool_call_count(sample_trajectory, "search", 2)
    assert passed is True

    passed, msg = tool_call_count(sample_trajectory, "calculator", 1)
    assert passed is True

    passed, msg = tool_call_count(sample_trajectory, "search", 1)
    assert passed is False
    assert "2" in msg

def test_tool_called_with(sample_trajectory: Trajectory) -> None:
    passed, msg = tool_called_with(sample_trajectory, "search", q="test")
    assert passed is True

    passed, msg = tool_called_with(sample_trajectory, "search", q="wrong")
    assert passed is False

    passed, msg = tool_called_with(
        sample_trajectory, "search", q="test", extra="none"
    )
    assert passed is False

def test_tool_called_with_partial(sample_trajectory: Trajectory) -> None:
    # Adding a tool call with multiple args for testing partial
    steps = [
        TrajectoryStep(
            0, "tool_call", 100.0, tool_name="email",
            tool_args={"to": "a@b.com", "body": "hi"}
        ),
    ]
    traj = Trajectory(steps=steps)

    passed, msg = tool_called_with_partial(traj, "email", to="a@b.com")
    assert passed is True

    passed, msg = tool_called_with_partial(traj, "email", body="hi")
    assert passed is True

    passed, msg = tool_called_with_partial(
        traj, "email", to="a@b.com", body="wrong"
    )
    assert passed is False

def test_tool_called_before(sample_trajectory: Trajectory) -> None:
    passed, msg = tool_called_before(sample_trajectory, "search", "calculator")
    assert passed is True

    passed, msg = tool_called_before(sample_trajectory, "calculator", "search")
    # calculator (2) is after first search (0), but before second search (3).
    # "first occurrence of each" per spec
    assert passed is False

    passed, msg = tool_called_before(sample_trajectory, "search", "missing")
    assert passed is False

def test_tool_called_immediately_before(sample_trajectory: Trajectory) -> None:
    # search(0), llm(1), calculator(2), search(3)
    # tool_called_immediately_before ignores non-tool steps
    passed, msg = tool_called_immediately_before(
        sample_trajectory, "search", "calculator"
    )
    assert passed is True

    passed, msg = tool_called_immediately_before(
        sample_trajectory, "calculator", "search"
    )
    assert passed is True # calculator(2) is immediately before search(3)

    passed, msg = tool_called_immediately_before(
        sample_trajectory, "search", "search"
    )
    assert passed is False # search(0) is followed by calculator(2)

def test_call_order(sample_trajectory: Trajectory) -> None:
    order = call_order(sample_trajectory)
    assert order == ["search", "calculator", "search"]

def test_call_order_contains(sample_trajectory: Trajectory) -> None:
    passed, msg = call_order_contains(
        sample_trajectory, ["search", "calculator"]
    )
    assert passed is True

    passed, msg = call_order_contains(sample_trajectory, ["search", "search"])
    assert passed is True

    passed, msg = call_order_contains(
        sample_trajectory, ["calculator", "missing"]
    )
    assert passed is False
