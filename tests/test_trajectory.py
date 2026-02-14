import pytest
import json
from datetime import datetime
from unitai.core.trajectory import Trajectory, TrajectoryStep

def test_trajectory_step_creation():
    step = TrajectoryStep(
        step_index=0,
        step_type="tool_call",
        timestamp=datetime.now().timestamp(),
        tool_name="test_tool",
        tool_args={"arg1": "val1"},
        tool_result="success"
    )
    assert step.step_index == 0
    assert step.step_type == "tool_call"

def test_trajectory_step_invalid_type():
    with pytest.raises(ValueError, match="Invalid step_type"):
        TrajectoryStep(
            step_index=0,
            step_type="invalid_type",
            timestamp=datetime.now().timestamp()
        )

def test_trajectory_serialization():
    step = TrajectoryStep(
        step_index=0,
        step_type="tool_call",
        timestamp=123456789.0,
        tool_name="test_tool",
        tool_args={"arg1": "val1"},
        tool_result="success"
    )
    traj = Trajectory(
        run_id="test-run",
        input="test input",
        steps=[step]
    )
    
    data = traj.to_dict()
    assert data["run_id"] == "test-run"
    assert data["steps"][0]["tool_name"] == "test_tool"
    
    # Test round-trip
    traj_back = Trajectory.from_dict(data)
    assert traj_back.run_id == traj.run_id
    assert traj_back.steps[0].tool_name == traj.steps[0].tool_name
    assert traj_back.steps[0].timestamp == traj.steps[0].timestamp

def test_exception_serialization():
    try:
        raise ValueError("test error")
    except ValueError as e:
        error_step = TrajectoryStep(
            step_index=1,
            step_type="tool_call",
            timestamp=123456789.0,
            tool_name="fail_tool",
            tool_args={},
            tool_error=e
        )
    
    traj = Trajectory(run_id="err-run", input="err", steps=[error_step])
    data = traj.to_dict()
    
    assert data["steps"][0]["tool_error"]["type"] == "ValueError"
    assert data["steps"][0]["tool_error"]["message"] == "test error"
    
    traj_back = Trajectory.from_dict(data)
    # We expect tool_error to be a dict or a reconstructed object that behaves like one for now
    assert traj_back.steps[0].tool_error["type"] == "ValueError"
