"""Scenario 8: Statistical Testing with Pass Rate Thresholds

This scenario demonstrates TrajAI's statistical testing feature for handling
non-deterministic LLM behavior.

Key concepts:
- Running tests N times with @statistical decorator
- Pass rate threshold (e.g., 90% success rate)
- Cost budget enforcement
- Handling flaky LLM behavior
- Statistical assertions in CI

Real-world use case: Testing an agent that sometimes misses edge cases due to
LLM non-determinism, but should succeed 90%+ of the time.
"""

from unittest.mock import MagicMock

from trajai.mock.toolkit import MockToolkit
from trajai.runner.statistical import StatisticalRunner

# ---------------------------------------------------------------------------
# Step 1: Create a flaky agent simulator
# ---------------------------------------------------------------------------


def create_flaky_agent() -> MagicMock:
    """Simulate an agent that succeeds ~80% of the time."""
    agent = MagicMock()
    agent.__class__.__name__ = "FlakyAgent"
    return agent


# ---------------------------------------------------------------------------
# Step 2: Write a test with statistical requirements
# ---------------------------------------------------------------------------


def test_agent_with_statistical_runner() -> None:
    """Test an agent with statistical pass rate threshold."""
    # This test requires the agent to succeed 8 out of 10 times (80% threshold)

    def agent_test(mock_toolkit: MockToolkit) -> None:
        """The actual test function that will be run N times."""
        import random

        toolkit = MockToolkit()
        toolkit.mock("lookup_order", return_value={"id": "123", "status": "delivered"})

        # Simulate calling an agent (mocked here)
        # In a real scenario, you'd call: result = toolkit.run(agent, "...")

        # Simulate flaky behavior: 80% success rate
        if random.random() < 0.8:
            # Success case
            pass
        else:
            # Failure case
            raise AssertionError("Agent failed to call lookup_order")

    # Run the test 10 times, requiring 80% pass rate
    runner = StatisticalRunner(n=10, threshold=0.8, budget=1.0)

    try:
        result = runner.run(agent_test)

        print("✓ Statistical test completed")
        print(f"  Total runs: {result.total_runs}")
        print(f"  Passed: {result.passed_runs}")
        print(f"  Failed: {result.failed_runs}")
        print(f"  Pass rate: {result.pass_rate * 100:.1f}%")
        print(f"  Total cost: ${result.total_cost:.4f}")

        if result.pass_rate >= 0.8:
            print("  ✓ Pass rate threshold met")
        else:
            print("  ✗ Pass rate threshold NOT met")

    except Exception as e:
        print(f"Statistical test raised: {e}")


# ---------------------------------------------------------------------------
# Step 3: Using the @statistical decorator (pytest integration)
# ---------------------------------------------------------------------------


def example_pytest_statistical_test() -> None:
    """
    Example of using pytest markers for statistical testing.

    In a real pytest file, you would write:

    @pytest.mark.trajai_statistical(n=10, threshold=0.9)
    def test_my_agent(mock_toolkit):
        # Mock setup
        mock_toolkit.mock("lookup", return_value={"found": True})

        # Run agent
        result = mock_toolkit.run(agent, "find item")

        # Assertions
        result.assert_tool_was_called("lookup")

    The pytest plugin will:
    1. Run this test 10 times
    2. Require 90% pass rate
    3. Report aggregate results
    4. Write cost data to JUnit XML
    """
    print("Example: pytest statistical testing")
    print()
    print("  @pytest.mark.trajai_statistical(n=10, threshold=0.9)")
    print("  def test_my_agent(mock_toolkit):")
    print("      mock_toolkit.mock('lookup', return_value={'found': True})")
    print("      result = mock_toolkit.run(agent, 'find item')")
    print("      result.assert_tool_was_called('lookup')")
    print()
    print("  This will:")
    print("  - Run the test 10 times")
    print("  - Require 90% pass rate (9/10 successes)")
    print("  - Track total cost across all runs")
    print("  - Report pass_rate in JUnit XML output")


# ---------------------------------------------------------------------------
# Step 4: Cost budget enforcement
# ---------------------------------------------------------------------------


def test_with_cost_budget() -> None:
    """Test with cost budget to prevent expensive test runs."""

    def expensive_test(mock_toolkit: MockToolkit) -> None:
        # Simulate a test that uses LLM calls
        # Real LLM calls would accumulate cost via toolkit.record_llm_call()
        pass

    # This runner will abort if total cost exceeds $0.50
    runner = StatisticalRunner(n=5, threshold=0.8, budget=0.50)

    result = runner.run(expensive_test)

    print("✓ Cost budget enforcement example")
    print("  Budget: $0.50")
    print(f"  Actual cost: ${result.total_cost:.4f}")
    print(f"  Status: {'Within budget' if result.total_cost <= 0.50 else 'Exceeded'}")


# ---------------------------------------------------------------------------
# Step 5: CI integration example
# ---------------------------------------------------------------------------


def show_ci_integration() -> None:
    """Show how statistical tests work in CI."""
    print("CI Integration Example:")
    print()
    print("In your .github/workflows/test.yml:")
    print()
    print("  - name: Run TrajAI tests")
    print("    run: trajai test --n 10 --threshold 0.9 --budget 5.00")
    print()
    print("This will:")
    print("- Run all statistical tests 10 times each")
    print("- Require 90% pass rate")
    print("- Fail if total cost exceeds $5.00")
    print("- Write results to JUnit XML with cost metadata")
    print("- Display cost summary in GitHub Actions job summary")


# ---------------------------------------------------------------------------
# Run the scenario
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 70)
    print("Scenario 8: Statistical Testing with Pass Rate Thresholds")
    print("=" * 70)
    print()

    test_agent_with_statistical_runner()
    print()
    print("-" * 70)
    print()

    example_pytest_statistical_test()
    print()
    print("-" * 70)
    print()

    test_with_cost_budget()
    print()
    print("-" * 70)
    print()

    show_ci_integration()
    print()

    print("=" * 70)
    print("Key Takeaways:")
    print("- StatisticalRunner runs tests N times and checks pass rate")
    print("- Use @pytest.mark.trajai_statistical(n=10, threshold=0.9)")
    print("- Cost budget prevents expensive test runs")
    print("- JUnit XML includes pass_rate and cost metadata")
    print("- GitHub Actions displays cost in job summary")
    print("- Perfect for handling LLM non-determinism in CI")
    print("=" * 70)
