import pytest
import time
import asyncio
from unitai.mock.toolkit import MockToolkit, AgentTimeoutError
from unitai.core.result import AgentRunResult

def test_run_generic_basic() -> None:
    toolkit = MockToolkit()
    toolkit.mock("tool1", return_value="res1")
    
    def my_agent():
        return toolkit.get_tool("tool1").invoke({})
    
    result = toolkit.run_generic(my_agent)
    assert isinstance(result, AgentRunResult)
    assert result.output == "res1"
    assert len(result.trajectory.steps) == 1

def test_run_callable_basic() -> None:
    toolkit = MockToolkit()
    toolkit.mock("greet", side_effect=lambda args: f"Hello {args['name']}")
    
    def my_agent(name, tools):
        return tools["greet"]({"name": name})
    
    result = toolkit.run_callable(
        fn=lambda input: my_agent(input, tools=toolkit.as_dict()),
        input="Alice"
    )
    assert result.output == "Hello Alice"

def test_run_generic_timeout() -> None:
    toolkit = MockToolkit()
    toolkit.mock("fast", return_value="fast_res")
    
    def slow_agent():
        toolkit.get_tool("fast").invoke({})
        time.sleep(2)
        return "slow_res"
    
    with pytest.raises(AgentTimeoutError):
        toolkit.run_generic(slow_agent, timeout=0.5)
    
    # Check if we can get partial results?
    # The requirement says: raise AgentTimeoutError AND return result containing partial trajectory.
    # But raising means we don't return. Let's re-read spec.
    # "If the timeout expires, stop waiting, raise AgentTimeoutError, and return an AgentRunResult containing the partial trajectory recorded up to that point."
    # This implies the exception might carry the result.
    
def test_run_generic_timeout_result() -> None:
    toolkit = MockToolkit()
    toolkit.mock("fast", return_value="fast_res")
    
    def slow_agent():
        toolkit.get_tool("fast").invoke({})
        time.sleep(1)
        return "slow_res"
    
    try:
        toolkit.run_generic(slow_agent, timeout=0.1)
    except AgentTimeoutError as e:
        assert e.partial_result is not None
        assert len(e.partial_result.trajectory.steps) == 1
        assert e.partial_result.trajectory.steps[0].tool_name == "fast"
