"""Tests for the UnitAI CLI (Phase 7)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from unitai.cli.main import main

# ---------------------------------------------------------------------------
# Help output
# ---------------------------------------------------------------------------


def test_help_output(capsys: pytest.CaptureFixture[str]) -> None:
    """main(['--help']) prints usage and returns 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "unitai" in out.lower()


def test_test_help(capsys: pytest.CaptureFixture[str]) -> None:
    """`unitai test --help` prints test subcommand usage."""
    with pytest.raises(SystemExit) as exc_info:
        main(["test", "--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "test" in out.lower()


# ---------------------------------------------------------------------------
# `unitai test` env var mapping
# ---------------------------------------------------------------------------


def test_test_sets_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """--n, --threshold, --budget flags set the corresponding UNITAI_* env vars."""
    called_with: List[List[str]] = []

    def mock_pytest_main(args: List[str]) -> int:
        called_with.append(args)
        return 0

    monkeypatch.delenv("UNITAI_DEFAULT_N", raising=False)
    monkeypatch.delenv("UNITAI_DEFAULT_THRESHOLD", raising=False)
    monkeypatch.delenv("UNITAI_COST_BUDGET_PER_TEST", raising=False)

    with patch("pytest.main", side_effect=mock_pytest_main):
        main(["test", "--n", "5", "--threshold", "0.8", "--budget", "2.50"])

    assert os.environ.get("UNITAI_DEFAULT_N") == "5"
    assert os.environ.get("UNITAI_DEFAULT_THRESHOLD") == "0.8"
    assert os.environ.get("UNITAI_COST_BUDGET_PER_TEST") == "2.5"


def test_test_passes_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Path argument is forwarded to pytest.main."""
    captured: List[List[str]] = []

    def mock_pytest_main(args: List[str]) -> int:
        captured.append(args)
        return 0

    with patch("pytest.main", side_effect=mock_pytest_main):
        main(["test", "tests/test_foo.py"])

    assert len(captured) == 1
    assert "tests/test_foo.py" in captured[0]


def test_test_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """pytest exit code is propagated by `unitai test`."""
    with patch("pytest.main", return_value=1):
        code = main(["test"])
    assert code == 1


# ---------------------------------------------------------------------------
# `unitai init`
# ---------------------------------------------------------------------------


def test_init_creates_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`unitai init` creates unitai.toml in the current directory."""
    monkeypatch.chdir(tmp_path)
    main(["init"])
    toml_path = tmp_path / "unitai.toml"
    assert toml_path.exists()
    content = toml_path.read_text()
    assert "default_n" in content


def test_init_creates_example_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`unitai init` creates tests/test_agent_example.py."""
    monkeypatch.chdir(tmp_path)
    main(["init"])
    example = tmp_path / "tests" / "test_agent_example.py"
    assert example.exists()
    content = example.read_text()
    assert "mock_toolkit" in content


def test_init_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`unitai init` doesn't overwrite existing files."""
    monkeypatch.chdir(tmp_path)

    # Create files with sentinel content
    toml_path = tmp_path / "unitai.toml"
    toml_path.write_text("sentinel_content_toml")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    example = tests_dir / "test_agent_example.py"
    example.write_text("sentinel_content_example")

    main(["init"])

    assert toml_path.read_text() == "sentinel_content_toml"
    assert example.read_text() == "sentinel_content_example"


def test_init_updates_gitignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`unitai init` appends .unitai/ to existing .gitignore."""
    monkeypatch.chdir(tmp_path)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n")

    main(["init"])

    content = gitignore.read_text()
    assert ".unitai/" in content


# ---------------------------------------------------------------------------
# `unitai results`
# ---------------------------------------------------------------------------


def test_results_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Graceful message when no JUnit XML file exists."""
    monkeypatch.chdir(tmp_path)
    # Use a non-existent path
    main(["results", "--xml", str(tmp_path / "nonexistent.xml")])
    out = capsys.readouterr().out
    assert "No results file found" in out


# ---------------------------------------------------------------------------
# `unitai cache`
# ---------------------------------------------------------------------------


def test_cache_placeholder(capsys: pytest.CaptureFixture[str]) -> None:
    """Cache commands print placeholder message."""
    main(["cache", "clear"])
    out = capsys.readouterr().out
    assert "Phase 8" in out

    main(["cache", "stats"])
    out = capsys.readouterr().out
    assert "Phase 8" in out
