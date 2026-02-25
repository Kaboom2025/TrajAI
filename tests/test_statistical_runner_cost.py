import pytest

from trajai.mock.toolkit import MockToolkit
from trajai.runner.statistical import CostLimitExceeded, StatisticalRunner


def test_cost_safety_abort_on_calibration():
    """Test that runner aborts after first run if estimate exceeds budget."""
    def test_fn(mock_toolkit: MockToolkit):
        mock_toolkit.record_llm_call(model="expensive", cost=2.0)

    # N=3, budget=5.0. First run cost=2.0, estimate=6.0. Should abort.
    runner = StatisticalRunner(n=3, budget=5.0)
    with pytest.raises(CostLimitExceeded) as excinfo:
        runner.run(test_fn)

    assert "Estimated total for 3 runs: $6.0000" in str(excinfo.value)
    assert "--budget=6.00" in str(excinfo.value)

def test_cost_safety_abort_mid_run():
    """Test that runner aborts mid-run if actual cumulative cost exceeds budget."""
    state = {"count": 0}
    def test_fn(mock_toolkit: MockToolkit):
        state["count"] += 1
        # First run is cheap, subsequent runs are expensive
        cost = 0.5 if state["count"] == 1 else 4.0
        mock_toolkit.record_llm_call(model="dynamic", cost=cost)

    # N=5, budget=5.0
    # Run 1: cost=0.5. OK.
    # Run 2: cost=4.0. Total 4.5. OK.
    # Run 3: cost=4.0. Total 8.5. Should abort.

    runner = StatisticalRunner(n=5, budget=5.0)
    with pytest.raises(CostLimitExceeded):
        runner.run(test_fn)

    # Should not have completed all 5 runs
    assert state["count"] < 5

def test_cost_safety_first_run_itself_exceeds_budget():
    """Test abort if the first run itself exceeds the budget."""
    def test_fn(mock_toolkit: MockToolkit):
        mock_toolkit.record_llm_call(model="ultra-expensive", cost=10.0)

    runner = StatisticalRunner(n=1, budget=5.0)
    with pytest.raises(CostLimitExceeded):
        runner.run(test_fn)
