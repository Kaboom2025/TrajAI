import pytest
from unitai.core.trajectory import Trajectory, TrajectoryStep
from unitai.core.formatter import TrajectoryFormatter

@pytest.fixture
def sample_trajectory() -> Trajectory:
    steps = [
        TrajectoryStep(0, "tool_call", 100.0, tool_name="search", tool_args={"q": "a" * 200}, tool_result="b" * 200),
        TrajectoryStep(1, "llm_call", 101.0, model="gpt-4", prompt_tokens=50, cost=0.001),
        TrajectoryStep(2, "state_change", 102.0, key="status", old_value="idle", new_value="working"),
    ]
    return Trajectory(steps=steps)

def test_basic_formatting(sample_trajectory: Trajectory) -> None:
    formatter = TrajectoryFormatter()
    output = formatter.format(sample_trajectory)
    
    assert "1. [tool]  search" in output
    assert "2. [llm]   gpt-4" in output
    assert "3. [state] status" in output
    assert "..." in output # Value truncation

def test_highlighting(sample_trajectory: Trajectory) -> None:
    formatter = TrajectoryFormatter()
    # Highlight step 0 and 2
    highlights = {0: "called first", 2: "called second"}
    output = formatter.format(sample_trajectory, highlights=highlights)
    
    assert "← called first" in output
    assert "← called second" in output

def test_smart_truncation() -> None:
    # 25 steps
    steps = [TrajectoryStep(i, "tool_call", 100.0 + i, tool_name=f"tool_{i}") for i in range(25)]
    traj = Trajectory(steps=steps)
    
    formatter = TrajectoryFormatter()
    # Highlight step 5 and 20
    highlights = {5: "start", 20: "end"}
    output = formatter.format(traj, highlights=highlights)
    
    assert "tool_0" in output
    assert "tool_5" in output
    assert "tool_20" in output
    assert "tool_24" in output
    assert "... (12 more steps) ..." in output # Example of middle truncation
