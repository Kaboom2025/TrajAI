"""Tests for Phase 10: CI integration features.

Covers:
- GitHub Actions step summary writing
- Cost summary format correctness
- JUnit XML parseability
"""
from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_rows(
    *entries: tuple[str, str, str, str],
) -> list[tuple[str, str, str, str]]:
    """Build (nodeid, status, cost, pass_rate) test rows."""
    return list(entries)


# ---------------------------------------------------------------------------
# Tests for _write_github_step_summary
# ---------------------------------------------------------------------------


class TestWriteGithubStepSummary:
    def _summary(self, path: str) -> str:
        from trajai.pytest_plugin.plugin import _write_github_step_summary

        rows = _make_test_rows(
            ("tests/test_foo.py::test_bar", "PASS", "$0.0023", ""),
            ("tests/test_foo.py::test_baz", "FAIL", "$0.0010", "80.0%"),
        )
        _write_github_step_summary(path, rows, total_cost=0.0033, total_tokens=0)
        return Path(path).read_text(encoding="utf-8")

    def test_creates_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            from trajai.pytest_plugin.plugin import _write_github_step_summary

            _write_github_step_summary(path, [], total_cost=0.0, total_tokens=0)
            assert Path(path).exists()
        finally:
            os.unlink(path)

    def test_contains_header(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "## TrajAI Test Summary" in content
        finally:
            os.unlink(path)

    def test_contains_table_rows(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "test_bar" in content
            assert "test_baz" in content
        finally:
            os.unlink(path)

    def test_pass_shows_checkmark(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "✅" in content
        finally:
            os.unlink(path)

    def test_fail_shows_cross(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "❌" in content
        finally:
            os.unlink(path)

    def test_cost_shown(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "$0.0033" in content
        finally:
            os.unlink(path)

    def test_pass_rate_shown(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            content = self._summary(path)
            assert "80.0%" in content
        finally:
            os.unlink(path)

    def test_empty_rows_produces_summary(self) -> None:
        """Even with no test rows, the summary line should be present."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            from trajai.pytest_plugin.plugin import _write_github_step_summary

            _write_github_step_summary(path, [], total_cost=0.0, total_tokens=0)
            content = Path(path).read_text(encoding="utf-8")
            assert "0 tests" in content
        finally:
            os.unlink(path)

    def test_tokens_shown_when_nonzero(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            from trajai.pytest_plugin.plugin import _write_github_step_summary

            _write_github_step_summary(path, [], total_cost=0.0, total_tokens=1234)
            content = Path(path).read_text(encoding="utf-8")
            assert "1234" in content
        finally:
            os.unlink(path)

    def test_appends_to_existing_file(self) -> None:
        """The summary should append to an existing file (GitHub Actions pattern)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Existing content\n")
            path = f.name
        try:
            from trajai.pytest_plugin.plugin import _write_github_step_summary

            _write_github_step_summary(path, [], total_cost=0.0, total_tokens=0)
            content = Path(path).read_text(encoding="utf-8")
            assert "# Existing content" in content
            assert "## TrajAI Test Summary" in content
        finally:
            os.unlink(path)

    def test_invalid_path_does_not_raise(self) -> None:
        """OSError on unwritable path should be silently swallowed."""
        from trajai.pytest_plugin.plugin import _write_github_step_summary

        _write_github_step_summary("/dev/null/cannot/write/here", [], 0.0, 0)


# ---------------------------------------------------------------------------
# Tests for JUnit XML format
# ---------------------------------------------------------------------------


class TestJUnitXMLFormat:
    def _make_junit_xml(self, tmp_path: Path) -> Path:
        """Produce a minimal valid JUnit XML file similar to what pytest emits."""
        xml_content = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="trajai" tests="2" errors="0" failures="1" skipped="0">
    <testcase classname="tests.test_foo" name="test_pass" time="1.23">
      <properties>
        <property name="trajai_cost" value="$0.0023"/>
      </properties>
    </testcase>
    <testcase classname="tests.test_foo" name="test_fail" time="0.45">
      <failure message="AssertionError">tool not called</failure>
      <properties>
        <property name="trajai_cost" value="$0.0010"/>
        <property name="trajai_pass_rate" value="70.0%"/>
      </properties>
    </testcase>
  </testsuite>
</testsuites>
"""
        xml_path = tmp_path / "trajai.xml"
        xml_path.write_text(xml_content)
        return xml_path

    def test_xml_is_parseable(self, tmp_path: Path) -> None:
        xml_path = self._make_junit_xml(tmp_path)
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
        assert root.tag in ("testsuites", "testsuite")

    def test_xml_contains_testcases(self, tmp_path: Path) -> None:
        xml_path = self._make_junit_xml(tmp_path)
        tree = ET.parse(str(xml_path))
        testcases = list(tree.getroot().iter("testcase"))
        assert len(testcases) == 2

    def test_xml_trajai_properties_readable(self, tmp_path: Path) -> None:
        xml_path = self._make_junit_xml(tmp_path)
        tree = ET.parse(str(xml_path))
        props: dict[str, str] = {}
        for prop in tree.getroot().iter("property"):
            name = prop.get("name", "")
            if name.startswith("trajai_"):
                props[name] = prop.get("value", "")
        assert "trajai_cost" in props
        assert "trajai_pass_rate" in props

    def test_xml_display_results_parses_correctly(self, tmp_path: Path) -> None:
        """display_results should parse our JUnit XML without error."""
        from trajai.cli.results import display_results

        xml_path = self._make_junit_xml(tmp_path)
        # Should not raise
        display_results(str(xml_path))
