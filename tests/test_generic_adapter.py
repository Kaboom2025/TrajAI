from trajai.adapters.generic import GenericAdapter
from trajai.core.trajectory import Trajectory
from trajai.mock.toolkit import MockToolkit


def test_generic_adapter_execute() -> None:
    toolkit = MockToolkit()
    adapter = GenericAdapter(toolkit=toolkit)

    def my_agent() -> str:
        toolkit.get_tool("tool1").invoke({"a": 1})
        toolkit.record_llm_call(model="gpt-4", prompt_tokens=10, completion_tokens=5)
        return "done"

    toolkit.mock("tool1", return_value="res1")

    trajectory = adapter.execute(my_agent, input="start", timeout=10)

    assert isinstance(trajectory, Trajectory)
    assert len(trajectory.steps) == 2
    assert trajectory.steps[0].step_type == "tool_call"
    assert trajectory.steps[1].step_type == "llm_call"
    assert trajectory.final_output == "done"
