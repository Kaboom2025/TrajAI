import pytest

from unitai.core.assertions import UnitAIAssertionError
from unitai.core.result import AgentRunResult, MockToolCall
from unitai.core.trajectory import Trajectory, TrajectoryStep


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
    with pytest.raises(UnitAIAssertionError) as excinfo:
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
