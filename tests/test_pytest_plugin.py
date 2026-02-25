"""Tests for the TrajAI pytest plugin (Phase 6).

Uses pytest's pytester fixture to run sub-processes and inspect results.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_conftest(pytester: pytest.Pytester) -> None:
    """Write a minimal conftest that re-exports the plugin fixtures for pytester runs.

    The plugin itself is already loaded via the pytest11 entry point, so we
    just need the fixtures available in the sub-process.
    """
    pytester.makeconftest(
        """
# Plugin is loaded automatically via pytest11 entry point.
# Explicitly import fixtures so they're available in this test directory.
from trajai.pytest_plugin.fixtures import mock_toolkit, trajai_config  # noqa: F401
"""
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPluginMarkers:
    def test_plugin_registers_markers(self, pytester: pytest.Pytester) -> None:
        """No unknown-marker warnings when plugin is active."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_statistical(n=1, threshold=0.0)
            def test_marked():
                pass
            """
        )
        result = pytester.runpytest("-W", "error::pytest.PytestUnknownMarkWarning")
        result.assert_outcomes(passed=1)


class TestMockToolkitFixture:
    def test_mock_toolkit_fixture_provides_fresh_toolkit(
        self, pytester: pytest.Pytester
    ) -> None:
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            from trajai.mock.toolkit import MockToolkit

            def test_fixture_type(mock_toolkit):
                assert isinstance(mock_toolkit, MockToolkit)
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(passed=1)

    def test_mock_toolkit_fixture_resets_on_teardown(
        self, pytester: pytest.Pytester
    ) -> None:
        """Each test gets a toolkit with no leftover calls from a previous test."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            def test_first(mock_toolkit):
                mock_toolkit.mock("tool_a", return_value="x")
                mock_toolkit.get_tool("tool_a").invoke({})

            def test_second(mock_toolkit):
                # toolkit should be fresh — no calls recorded
                assert mock_toolkit._recorded_llm_calls == []
                # and no tools registered from previous test
                assert len(mock_toolkit._tools) == 0
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(passed=2)


class TestStatisticalMarker:
    def test_statistical_marker_passes(self, pytester: pytest.Pytester) -> None:
        """Always-passing test with loose threshold should pass."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_statistical(n=3, threshold=0.5)
            def test_always_passes():
                assert 1 == 1
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(passed=1)

    def test_statistical_marker_fails(self, pytester: pytest.Pytester) -> None:
        """Always-failing test should fail when threshold > 0."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_statistical(n=3, threshold=0.5)
            def test_always_fails():
                assert 1 == 2, "always fails"
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=1)

    def test_statistical_marker_output(self, pytester: pytest.Pytester) -> None:
        """Failure output should mention pass rate."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_statistical(n=3, threshold=0.9)
            def test_always_fails():
                assert False, "nope"
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=1)
        result.stdout.fnmatch_lines(["*Statistical failure*"])


class TestBudgetMarker:
    def test_budget_marker_aborts(self, pytester: pytest.Pytester) -> None:
        """Test that exceeds cost budget raises CostLimitExceeded."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest
            from trajai.core.trajectory import TrajectoryStep

            @pytest.mark.trajai_budget(max_cost=0.001)
            def test_expensive(mock_toolkit):
                # Simulate an expensive LLM call
                mock_toolkit.record_llm_call(
                    model="gpt-4",
                    prompt_tokens=1000,
                    completion_tokens=500,
                    cost=1.50,
                )
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=1)
        result.stdout.fnmatch_lines(["*cost budget*"])


class TestSkipIfNoApiKey:
    def test_skip_if_no_api_key_skips(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test is skipped when the env var is absent."""
        monkeypatch.delenv("TRAJAI_TEST_KEY_SKIP", raising=False)
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_skip_if_no_api_key(env_var="TRAJAI_TEST_KEY_SKIP")
            def test_needs_key():
                pass
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(skipped=1)

    def test_skip_if_no_api_key_runs(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test runs normally when the env var is present."""
        monkeypatch.setenv("TRAJAI_TEST_KEY_PRESENT", "some-key")
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.trajai_skip_if_no_api_key(env_var="TRAJAI_TEST_KEY_PRESENT")
            def test_needs_key():
                assert True
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(passed=1)


class TestFailureOutput:
    def test_failure_output_contains_trajectory(
        self, pytester: pytest.Pytester
    ) -> None:
        """TrajAIAssertionError failure should show trajectory in output."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            from trajai.mock.toolkit import MockToolkit
            from trajai.core.trajectory import Trajectory

            def test_assertion_shows_trajectory(mock_toolkit):
                mock_toolkit.mock("search", return_value={"result": "ok"})

                def agent(input_str, tools):
                    tools["search"]({"query": input_str})
                    return "done"

                result = mock_toolkit.run_callable(agent, "hello")
                # This should fail and show trajectory
                result.assert_tool_was_called("nonexistent_tool")
            """
        )
        result = pytester.runpytest("-v")
        result.assert_outcomes(failed=1)
        # The TrajAIAssertionError message includes "never called"
        result.stdout.fnmatch_lines(["*never called*"])


class TestJUnitXML:
    def test_junit_xml_properties(
        self, pytester: pytest.Pytester, tmp_path: Path
    ) -> None:
        """Running with --junitxml produces a valid XML file."""
        _write_conftest(pytester)
        pytester.makepyfile(
            """
            def test_simple():
                assert 1 + 1 == 2
            """
        )
        xml_file = tmp_path / "results.xml"
        result = pytester.runpytest(f"--junitxml={xml_file}")
        result.assert_outcomes(passed=1)
        assert xml_file.exists()
        tree = ET.parse(xml_file)
        root = tree.getroot()
        assert root is not None


class TestConfig:
    def test_config_loads_defaults(self) -> None:
        """TrajAIConfig has correct defaults."""
        from trajai.pytest_plugin.config import TrajAIConfig

        cfg = TrajAIConfig()
        assert cfg.default_n == 10
        assert cfg.default_threshold == 0.95
        assert cfg.max_workers == 5
        assert cfg.cost_budget_per_test == 1.00
        assert cfg.cost_budget_per_suite == 10.00
        assert cfg.strict_mocks is True
        assert cfg.junit_xml == "test-results/trajai.xml"
        assert cfg.verbose is False

    def test_config_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TRAJAI_DEFAULT_N env var overrides file config."""
        monkeypatch.setenv("TRAJAI_DEFAULT_N", "42")
        monkeypatch.setenv("TRAJAI_DEFAULT_THRESHOLD", "0.80")

        from trajai.pytest_plugin.config import load_trajai_config

        cfg = load_trajai_config()
        assert cfg.default_n == 42
        assert cfg.default_threshold == 0.80

        # Cleanup is handled by monkeypatch
