import pytest
from unitai.mock.toolkit import MockToolkit, UnmockedToolError
from tests.fixtures.simple_agent import simple_tool_agent, metadata_agent

def test_e2e_tool_calls() -> None:
    toolkit = MockToolkit()
    toolkit.mock("search", return_value="UnitAI repository")
    toolkit.mock("calculator", return_value="42")
    
    # Test search flow
    result = toolkit.run_callable(
        fn=simple_tool_agent,
        input="search: Who is the best?"
    )
    assert result.output == "Found: UnitAI repository"
    assert len(result.trajectory.steps) == 1
    assert result.trajectory.steps[0].tool_name == "search"
    assert result.trajectory.steps[0].tool_args == {"q": "Who is the best?"}
    
    # Test calc flow
    result = toolkit.run_callable(
        fn=simple_tool_agent,
        input="calc: 21 * 2"
    )
    assert result.output == "Result is 42"
    assert len(result.trajectory.steps) == 1
    assert result.trajectory.steps[0].tool_name == "calculator"

def test_e2e_strict_mode() -> None:
    toolkit = MockToolkit()
    # No mocks registered
    
    with pytest.raises(UnmockedToolError):
        toolkit.run_callable(
            fn=simple_tool_agent,
            input="search: something",
            strict=True
        )

def test_e2e_metadata() -> None:
    toolkit = MockToolkit()
    
    result = toolkit.run_generic(
        lambda: metadata_agent("test metadata", toolkit=toolkit)
    )
    
    assert len(result.trajectory.steps) == 1
    step = result.trajectory.steps[0]
    assert step.step_type == "llm_call"
    assert step.model == "gpt-4o"
    assert step.prompt_tokens == 100
    assert step.cost == 0.002
    
    assert result.total_cost == 0.002
    assert result.total_tokens == 150
