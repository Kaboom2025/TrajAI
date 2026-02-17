import pytest
from unitai.runner.statistical import StatisticalRunner, StatisticalResult
from unitai.mock.toolkit import MockToolkit
from unitai.core.assertions import UnitAIAssertionError

def test_runner_deterministic_pass():
    """Test that an always-passing function results in 100% pass rate."""
    def test_fn():
        assert 1 == 1
        
    runner = StatisticalRunner(n=5)
    result = runner.run(test_fn)
    
    assert result.total_runs == 5
    assert result.passed_runs == 5
    assert result.failed_runs == 0
    assert result.pass_rate == 1.0

def test_runner_deterministic_fail():
    """Test that an always-failing function results in 0% pass rate."""
    def test_fn():
        assert 1 == 2, "Always fails"
        
    runner = StatisticalRunner(n=5)
    result = runner.run(test_fn)
    
    assert result.total_runs == 5
    assert result.passed_runs == 0
    assert result.failed_runs == 5
    assert result.failure_modes == {"AssertionError: Always fails": 5}

def test_runner_stochastic():
    """Test runner with a function that fails sometimes."""
    state = {"count": 0}
    def test_fn():
        state["count"] += 1
        if state["count"] <= 3:
            assert False, "Fail first three"
        # remainder pass
            
    runner = StatisticalRunner(n=10)
    result = runner.run(test_fn)
    
    assert result.total_runs == 10
    assert result.passed_runs == 7
    assert result.failed_runs == 3
    assert result.failure_modes == {"AssertionError: Fail first three": 3}

def test_runner_non_assertion_error_propagates():
    """Test that non-assertion errors (e.g. ValueError) halt execution immediately."""
    state = {"count": 0}
    def test_fn():
        state["count"] += 1
        if state["count"] == 2:
            raise ValueError("Unexpected crash")
        assert True
        
    runner = StatisticalRunner(n=5, max_workers=1)
    with pytest.raises(ValueError, match="Unexpected crash"):
        runner.run(test_fn)
        
    # Should have halted at run 2
    assert state["count"] == 2

def test_runner_with_mock_toolkit_cost():
    """Test that cost is accumulated from mock_toolkit if used."""
    def test_fn(mock_toolkit: MockToolkit):
        mock_toolkit.record_llm_call(model="test", cost=0.05)
        
    runner = StatisticalRunner(n=4)
    result = runner.run(test_fn)
    
    assert result.total_cost == 0.20

def test_runner_unitaiassertionerror_captured():
    """Test that UnitAIAssertionError is also captured as a failure."""
    def test_fn():
        raise UnitAIAssertionError("UnitAI specific failure")
        
    runner = StatisticalRunner(n=3)
    result = runner.run(test_fn)
    
    assert result.failed_runs == 3
    assert "UnitAI specific failure" in list(result.failure_modes.keys())[0]
