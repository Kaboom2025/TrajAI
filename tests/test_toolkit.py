import pytest
from unitai.mock.toolkit import MockToolkit
from unitai.mock.strategies import StaticStrategy

def test_mock_tool_invocation() -> None:
    toolkit = MockToolkit()
    toolkit.mock("search", return_value="results")
    
    tool = toolkit.get_tool("search")
    result = tool.invoke({"q": "test"})
    
    assert result == "results"
    assert len(tool.calls) == 1
    assert tool.calls[0].args == {"q": "test"}

def test_mock_toolkit_as_dict() -> None:
    toolkit = MockToolkit()
    toolkit.mock("tool1", return_value=1)
    toolkit.mock("tool2", return_value=2)
    
    tools = toolkit.as_dict()
    assert tools["tool1"]({"any": "args"}) == 1
    assert tools["tool2"]({}) == 2

def test_mock_toolkit_reset() -> None:
    toolkit = MockToolkit()
    toolkit.mock("tool1", return_value=1)
    
    toolkit.get_tool("tool1").invoke({})
    assert len(toolkit.get_tool("tool1").calls) == 1
    
    toolkit.reset()
    assert len(toolkit.get_tool("tool1").calls) == 0
    # Mock should still be there
    assert toolkit.get_tool("tool1").invoke({}) == 1

def test_callable_strategy_error_recording() -> None:
    def failing_fn(args):
        raise RuntimeError("custom error")
    
    toolkit = MockToolkit()
    toolkit.mock("fail", side_effect=failing_fn)
    
    tool = toolkit.get_tool("fail")
    with pytest.raises(RuntimeError, match="custom error"):
        tool.invoke({})
    
    assert len(tool.calls) == 1
    assert isinstance(tool.calls[0].error, RuntimeError)
