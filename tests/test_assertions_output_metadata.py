import pytest

from trajai.core.assertions import (
    cost_under,
    duration_under,
    error_is,
    failed,
    llm_calls_under,
    output_contains,
    output_equals,
    output_matches,
    output_not_contains,
    succeeded,
    tokens_under,
)
from trajai.core.trajectory import Trajectory


@pytest.fixture
def sample_trajectory() -> Trajectory:
    return Trajectory(
        input="test input",
        final_output="Result is 42",
        total_cost=0.005,
        total_tokens=150,
        duration_seconds=1.2,
        llm_calls=2
    )

def test_output_equals(sample_trajectory: Trajectory) -> None:
    passed, msg = output_equals(sample_trajectory, "Result is 42")
    assert passed is True

    passed, msg = output_equals(sample_trajectory, "result is 42") # Case sensitive
    assert passed is False

    passed, msg = output_equals(sample_trajectory, "Result is 42 ") # No trim
    assert passed is False

def test_output_contains(sample_trajectory: Trajectory) -> None:
    passed, msg = output_contains(sample_trajectory, "42")
    assert passed is True

    passed, msg = output_contains(sample_trajectory, "missing")
    assert passed is False

def test_output_not_contains(sample_trajectory: Trajectory) -> None:
    passed, msg = output_not_contains(sample_trajectory, "missing")
    assert passed is True

    passed, msg = output_not_contains(sample_trajectory, "42")
    assert passed is False

def test_output_matches(sample_trajectory: Trajectory) -> None:
    passed, msg = output_matches(sample_trajectory, r"Result is \d+")
    assert passed is True

    passed, msg = output_matches(sample_trajectory, r"Wrong \d+")
    assert passed is False

def test_metadata_assertions(sample_trajectory: Trajectory) -> None:
    assert cost_under(sample_trajectory, 0.01)[0] is True
    assert cost_under(sample_trajectory, 0.001)[0] is False

    assert tokens_under(sample_trajectory, 200)[0] is True
    assert tokens_under(sample_trajectory, 100)[0] is False

    assert duration_under(sample_trajectory, 2.0)[0] is True
    assert duration_under(sample_trajectory, 1.0)[0] is False

    assert llm_calls_under(sample_trajectory, 3)[0] is True
    assert llm_calls_under(sample_trajectory, 1)[0] is False

def test_error_assertions() -> None:
    traj_ok = Trajectory(error=None)
    assert succeeded(traj_ok)[0] is True
    assert failed(traj_ok)[0] is False

    traj_err = Trajectory(error=ValueError("oops"))
    assert succeeded(traj_err)[0] is False
    assert failed(traj_err)[0] is True
    assert error_is(traj_err, ValueError)[0] is True
    assert error_is(traj_err, TypeError)[0] is False

def test_none_output() -> None:
    traj = Trajectory(final_output=None)
    assert output_equals(traj, "anything")[0] is False
    assert output_contains(traj, "anything")[0] is False
    assert output_matches(traj, ".*")[0] is False
