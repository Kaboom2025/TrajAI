from datetime import datetime

import pytest

from trajai.core.result import AgentRunResult, MockToolCall
from trajai.core.trajectory import Trajectory


def test_mock_tool_call_creation() -> None:
    call = MockToolCall(
        args={"q": "test"},
        result="some result",
        timestamp=datetime.now().timestamp()
    )
    assert call.args["q"] == "test"
    assert call.result == "some result"

def test_test_run_result_properties() -> None:
    traj = Trajectory(
        run_id="test-id",
        input="hi",
        final_output="hello",
        total_cost=0.05,
        duration_seconds=1.5,
        llm_calls=3,
    )
    result = AgentRunResult(trajectory=traj)

    assert result.output == "hello"
    assert result.total_cost == 0.05
    assert result.duration == 1.5
    assert result.llm_calls == 3
    assert result.succeeded is True

def test_test_run_result_error() -> None:
    traj = Trajectory(
        run_id="test-id",
        input="hi",
        error=ValueError("oops")
    )
    result = AgentRunResult(trajectory=traj)

    assert result.failed is True
    assert result.error is not None

def test_test_run_result_implemented() -> None:

    traj = Trajectory()

    result = AgentRunResult(trajectory=traj)

    # Should no longer raise NotImplementedError

    assert result.tool_was_called("any") is False


