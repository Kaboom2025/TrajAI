import pytest
from unitai.runner.statistical import StatisticalResult

def test_statistical_result_initialization():
    """Test that StatisticalResult initializes with correct defaults and computed properties."""
    result = StatisticalResult(
        total_runs=10,
        passed_runs=7,
        failed_runs=3,
        total_cost=0.50,
        failure_modes={
            "AssertionError: Tool 'search' not called": 2,
            "AssertionError: Output mismatch": 1
        }
    )
    
    assert result.total_runs == 10
    assert result.passed_runs == 7
    assert result.failed_runs == 3
    assert result.pass_rate == 0.7
    assert result.total_cost == 0.50
    assert len(result.failure_modes) == 2

def test_statistical_result_summary_formatting():
    """Test that summary() produces a readable string report."""
    result = StatisticalResult(
        total_runs=10,
        passed_runs=8,
        failed_runs=2,
        total_cost=1.25,
        failure_modes={
            "AssertionError: Timeout": 2
        }
    )
    
    summary = result.summary()
    
    assert "Statistical Result: 8/10 passed (80.0%)" in summary
    assert "Total Cost: $1.2500" in summary
    assert "Failure Modes:" in summary
    assert "2x — AssertionError: Timeout" in summary

def test_statistical_result_empty_failures():
    """Test summary formatting when there are no failures."""
    result = StatisticalResult(
        total_runs=5,
        passed_runs=5,
        failed_runs=0,
        total_cost=0.10,
        failure_modes={}
    )
    
    summary = result.summary()
    
    assert "Statistical Result: 5/5 passed (100.0%)" in summary
    assert "Failure Modes" not in summary
