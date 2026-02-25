import pytest

from trajai.core.assertions import TrajAIAssertionError
from trajai.core.result import AgentRunResult, MockToolCall
from trajai.core.trajectory import Trajectory, TrajectoryStep


@pytest.fixture
def sample_trajectory() -> Trajectory:
    steps = [
        TrajectoryStep(
            0, "tool_call", 100.0, tool_name="search",
            tool_args={"q": "test"}, tool_result="results"
        ),
        TrajectoryStep(1, "llm_call", 101.0, model="gpt-4"),
    ]
    return Trajectory(steps=steps, final_output="Hello world")

def test_result_boolean_api(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    assert result.tool_was_called("search") is True
    assert result.tool_was_called("missing") is False
    assert result.output_equals("Hello world") is True

def test_result_assert_api_success(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    result.assert_tool_was_called("search")
    result.assert_output_contains("Hello")

def test_result_assert_api_failure(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    with pytest.raises(TrajAIAssertionError) as excinfo:
        result.assert_tool_was_called("missing")

    assert "Tool 'missing' was never called." in str(excinfo.value)
    assert "Actual trajectory" in str(excinfo.value)

def test_result_query_api(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)

    calls = result.get_calls("search")
    assert len(calls) == 1
    assert isinstance(calls[0], MockToolCall)
    assert calls[0].args == {"q": "test"}

    call = result.get_call("search", 0)
    assert call.args == {"q": "test"}

def test_result_get_call_index_error(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    with pytest.raises(IndexError, match="was called 1 times"):
        result.get_call("search", 1)

def test_result_call_order(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    assert result.call_order() == ["search"]


def test_result_output_not_contains(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    assert result.output_not_contains("goodbye") is True
    assert result.output_not_contains("Hello") is False


def test_result_call_order_contains() -> None:
    steps = [
        TrajectoryStep(0, "tool_call", 100.0, tool_name="a",
                       tool_args={}, tool_result=None),
        TrajectoryStep(1, "tool_call", 101.0, tool_name="b",
                       tool_args={}, tool_result=None),
        TrajectoryStep(2, "tool_call", 102.0, tool_name="c",
                       tool_args={}, tool_result=None),
    ]
    traj = Trajectory(steps=steps, final_output="done")
    result = AgentRunResult(traj)
    assert result.call_order_contains(["a", "c"]) is True
    assert result.call_order_contains(["c", "a"]) is False


def test_result_error_is() -> None:
    traj = Trajectory(error=ValueError("bad"))
    result = AgentRunResult(traj)
    assert result.error_is(ValueError) is True
    assert result.error_is(TypeError) is False


def test_result_llm_calls_property() -> None:
    traj = Trajectory(llm_calls=5)
    result = AgentRunResult(traj)
    assert result.llm_calls == 5


def test_result_assert_output_not_contains(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    result.assert_output_not_contains("goodbye")
    with pytest.raises(TrajAIAssertionError):
        result.assert_output_not_contains("Hello")


def test_result_assert_tool_call_count(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    result.assert_tool_call_count("search", 1)
    with pytest.raises(TrajAIAssertionError):
        result.assert_tool_call_count("search", 2)


def test_result_assert_output_equals(sample_trajectory: Trajectory) -> None:
    result = AgentRunResult(sample_trajectory)
    result.assert_output_equals("Hello world")
    with pytest.raises(TrajAIAssertionError):
        result.assert_output_equals("wrong")
