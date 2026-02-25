import time
from typing import Any

import pytest

from trajai.core.result import AgentRunResult
from trajai.mock.toolkit import AgentTimeoutError, MockToolkit


def test_run_generic_basic() -> None:
    toolkit = MockToolkit()
    toolkit.mock("tool1", return_value="res1")

    def my_agent() -> Any:
        return toolkit.get_tool("tool1").invoke({})

    result = toolkit.run_generic(my_agent)
    assert isinstance(result, AgentRunResult)
    assert result.output == "res1"
    assert len(result.trajectory.steps) == 1

def test_run_callable_basic() -> None:
    toolkit = MockToolkit()
    toolkit.mock("greet", side_effect=lambda args: f"Hello {args['name']}")

    def my_agent(name: str, tools: dict[str, Any]) -> Any:
        return tools["greet"]({"name": name})

    result = toolkit.run_callable(
        fn=my_agent,
        input="Alice"
    )
    assert result.output == "Hello Alice"

def test_run_generic_timeout() -> None:
    toolkit = MockToolkit()
    toolkit.mock("fast", return_value="fast_res")

    def slow_agent() -> str:
        toolkit.get_tool("fast").invoke({})
        time.sleep(2)
        return "slow_res"

    with pytest.raises(AgentTimeoutError):
        toolkit.run_generic(slow_agent, timeout=0.5)

def test_run_generic_timeout_result() -> None:
    toolkit = MockToolkit()
    toolkit.mock("fast", return_value="fast_res")

    def slow_agent() -> str:
        toolkit.get_tool("fast").invoke({})
        time.sleep(1)
        return "slow_res"

    try:
        toolkit.run_generic(slow_agent, timeout=0.1)
    except AgentTimeoutError as e:
        assert e.partial_result is not None
        assert len(e.partial_result.trajectory.steps) == 1
        assert e.partial_result.trajectory.steps[0].tool_name == "fast"
