from __future__ import annotations

import inspect
from typing import Any, Dict, Generator, List, Optional

import pytest

from unitai.pytest_plugin.config import UnitAIConfig, load_unitai_config
from unitai.pytest_plugin.fixtures import _UNITAI_CONFIG_KEY  # noqa: F401
from unitai.runner.statistical import (
    CostLimitExceeded,
    StatisticalResult,
    StatisticalRunner,
    UnitAIStatisticalError,
)

# Stash keys
_STATISTICAL_RESULT_KEY = pytest.StashKey[Optional[StatisticalResult]]()
_TEST_COST_KEY = pytest.StashKey[float]()
_TEST_TOKENS_KEY = pytest.StashKey[int]()
_TEST_DURATION_KEY = pytest.StashKey[float]()
_TEST_PASS_RATE_KEY = pytest.StashKey[Optional[float]]()


# ---------------------------------------------------------------------------
# Plugin hooks
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register markers and load UnitAIConfig into stash."""
    config.addinivalue_line(
        "markers",
        "unitai_statistical(n=10, threshold=0.95): "
        "Run the test N times and require at least threshold pass rate.",
    )
    config.addinivalue_line(
        "markers",
        "unitai_budget(max_cost=1.0): "
        "Abort the test if mock_toolkit cost exceeds max_cost.",
    )
    config.addinivalue_line(
        "markers",
        "unitai_skip_if_no_api_key(env_var='OPENAI_API_KEY'): "
        "Skip the test if the given environment variable is not set.",
    )

    unitai_cfg = load_unitai_config()
    config.stash[_UNITAI_CONFIG_KEY] = unitai_cfg


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    """Skip tests marked with unitai_skip_if_no_api_key when the env var is absent."""
    import os

    for item in items:
        marker = item.get_closest_marker("unitai_skip_if_no_api_key")
        if marker is None:
            continue
        env_var: str = marker.kwargs.get("env_var", "OPENAI_API_KEY")
        if not env_var:
            env_var = "OPENAI_API_KEY"
        if not os.environ.get(env_var):
            item.add_marker(
                pytest.mark.skip(reason=f"Environment variable '{env_var}' is not set.")
            )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, Any, None]:
    """Wrap test execution for statistical and budget markers."""
    unitai_cfg: UnitAIConfig = item.config.stash[_UNITAI_CONFIG_KEY]

    stat_marker = item.get_closest_marker("unitai_statistical")
    budget_marker = item.get_closest_marker("unitai_budget")

    if stat_marker is not None:
        n: int = stat_marker.kwargs.get("n", unitai_cfg.default_n)
        threshold: float = stat_marker.kwargs.get(
            "threshold", unitai_cfg.default_threshold
        )
        budget: float = stat_marker.kwargs.get(
            "budget", unitai_cfg.cost_budget_per_test
        )

        test_fn = item.obj  # type: ignore[attr-defined]

        # Build kwargs from funcargs, excluding mock_toolkit (runner manages it)
        kwargs: Dict[str, Any] = {}
        if hasattr(item, "funcargs"):
            sig = inspect.signature(test_fn)
            for param_name, _param in sig.parameters.items():
                if param_name != "mock_toolkit" and param_name in item.funcargs:  # type: ignore[attr-defined]
                    kwargs[param_name] = item.funcargs[param_name]  # type: ignore[attr-defined]

        runner = StatisticalRunner(n=n, threshold=threshold, budget=budget)
        stat_result = runner.run(test_fn, **kwargs)

        item.stash[_STATISTICAL_RESULT_KEY] = stat_result
        item.stash[_TEST_COST_KEY] = stat_result.total_cost
        item.stash[_TEST_TOKENS_KEY] = 0
        item.stash[_TEST_PASS_RATE_KEY] = stat_result.pass_rate

        # Replace the test function with a no-op — we already ran it above
        item.obj = lambda *a, **kw: None  # type: ignore[attr-defined]

        # Now yield so pytest calls the no-op
        outcome = yield

        # If pass rate is below threshold, replace the (passing) outcome with a failure
        if stat_result.pass_rate < threshold:
            pct = stat_result.pass_rate * 100
            error_msg = (
                f"Statistical failure: "
                f"{stat_result.passed_runs}/{stat_result.total_runs} passed "
                f"({pct:.1f}%) — required: {threshold * 100:.1f}%\n\n"
                f"{stat_result.summary()}"
            )
            outcome.force_exception(UnitAIStatisticalError(error_msg))
        return

    if budget_marker is not None:
        max_cost: float = budget_marker.kwargs.get(
            "max_cost", unitai_cfg.cost_budget_per_test
        )

        # Get mock_toolkit fixture if present
        toolkit = None
        if hasattr(item, "funcargs") and "mock_toolkit" in item.funcargs:  # type: ignore[attr-defined]
            toolkit = item.funcargs["mock_toolkit"]  # type: ignore[attr-defined]

        outcome = yield  # run the actual test

        if toolkit is not None:
            cost = sum(call.cost or 0.0 for call in toolkit._recorded_llm_calls)
            item.stash[_TEST_COST_KEY] = cost
            if cost > max_cost:
                outcome.force_exception(
                    CostLimitExceeded(
                        f"Test exceeded cost budget: ${cost:.4f} > ${max_cost:.2f}"
                    )
                )
        return

    # No special marker — normal execution
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]  # type: ignore[type-arg]
) -> Generator[None, Any, None]:
    """Append cost/token/duration metadata to failure reports."""
    outcome = yield
    report: pytest.TestReport = outcome.get_result()

    if call.when != "call":
        return

    # Add UnitAI metadata footer on failures
    if report.failed:
        parts: List[str] = []

        cost = item.stash.get(_TEST_COST_KEY, None)
        tokens = item.stash.get(_TEST_TOKENS_KEY, None)
        pass_rate = item.stash.get(_TEST_PASS_RATE_KEY, None)

        if cost is not None:
            parts.append(f"cost=${cost:.4f}")
        if tokens is not None and tokens > 0:
            parts.append(f"tokens={tokens}")
        if pass_rate is not None:
            parts.append(f"pass_rate={pass_rate * 100:.1f}%")

        if parts:
            report.sections.append(("UnitAI Metadata", " | ".join(parts)))


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Add UnitAI properties to report.user_properties for JUnit XML output."""
    if report.when != "call":
        return

    for section_name, content in report.sections:
        if section_name == "UnitAI Metadata":
            for part in content.split(" | "):
                if "=" in part:
                    key, _, val = part.partition("=")
                    report.user_properties.append((f"unitai_{key}", val))


@pytest.hookimpl
def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: int, config: pytest.Config
) -> None:
    """Print aggregate UnitAI summary and write GitHub Actions step summary."""
    import os

    total_cost = 0.0
    total_tokens = 0

    all_reports = (
        terminalreporter.stats.get("passed", [])
        + terminalreporter.stats.get("failed", [])
    )

    # Collect per-test metadata for the step summary table
    test_rows: List[tuple[str, str, str, str]] = []  # (name, status, cost, pass_rate)
    for report in all_reports:
        cost_str = ""
        pass_rate_str = ""
        for key, value in report.user_properties:
            if key == "unitai_cost":
                try:
                    cost_val = float(str(value).lstrip("$"))
                    total_cost += cost_val
                    cost_str = f"${cost_val:.4f}"
                except (ValueError, AttributeError):
                    pass
            elif key == "unitai_tokens":
                try:
                    total_tokens += int(value)
                except (ValueError, TypeError):
                    pass
            elif key == "unitai_pass_rate":
                pass_rate_str = str(value)

        passed_reports = terminalreporter.stats.get("passed", [])
        status = "PASS" if report in passed_reports else "FAIL"
        test_rows.append((report.nodeid, status, cost_str, pass_rate_str))

    if total_cost > 0 or total_tokens > 0:
        terminalreporter.write_sep("=", "UnitAI Summary")
        terminalreporter.write_line(f"  Total cost:   ${total_cost:.4f}")
        if total_tokens:
            terminalreporter.write_line(f"  Total tokens: {total_tokens}")

    # Write GitHub Actions step summary
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        _write_github_step_summary(
            step_summary_path, test_rows, total_cost, total_tokens
        )


def _write_github_step_summary(
    path: str,
    test_rows: List[tuple[str, str, str, str]],
    total_cost: float,
    total_tokens: int,
) -> None:
    """Write a Markdown cost summary to the GitHub Actions step summary file."""
    try:
        lines: List[str] = []
        lines.append("## UnitAI Test Summary\n")

        if test_rows:
            lines.append("| Test | Status | Cost | Pass Rate |")
            lines.append("|------|--------|------|-----------|")
            for nodeid, status, cost_str, pass_rate_str in test_rows:
                # Shorten long nodeids for readability
                short_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
                status_icon = "✅" if status == "PASS" else "❌"
                lines.append(
                    f"| `{short_name}` | {status_icon} {status} "
                    f"| {cost_str or '—'} | {pass_rate_str or '—'} |"
                )
            lines.append("")

        passed = sum(1 for _, s, _, _ in test_rows if s == "PASS")
        failed = sum(1 for _, s, _, _ in test_rows if s == "FAIL")
        total_str = (
            f"**Total:** {len(test_rows)} tests"
            f" — {passed} passed, {failed} failed"
        )
        lines.append(total_str)
        if total_cost > 0:
            lines.append(f"**Total LLM cost:** ${total_cost:.4f}")
        if total_tokens > 0:
            lines.append(f"**Total tokens:** {total_tokens}")
        lines.append("")

        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        pass
