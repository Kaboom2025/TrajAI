"""Tests for Phase 9: Configuration System."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from trajai.config import TrajAIConfig, get_config, reload_config


def test_config_defaults() -> None:
    """Test that config has sensible defaults."""
    config = TrajAIConfig()

    assert config.default_n == 10
    assert config.default_threshold == 0.95
    assert config.max_workers == 5
    assert config.cost_budget_per_test == 1.00
    assert config.strict_mocks is True
    assert config.cache_enabled is False


def test_config_env_override() -> None:
    """Test environment variable overrides."""
    os.environ["TRAJAI_DEFAULT_N"] = "20"
    os.environ["TRAJAI_DEFAULT_THRESHOLD"] = "0.90"
    os.environ["TRAJAI_STRICT_MOCKS"] = "false"

    try:
        config = reload_config()
        assert config.default_n == 20
        assert config.default_threshold == 0.90
        assert config.strict_mocks is False
    finally:
        # Cleanup
        os.environ.pop("TRAJAI_DEFAULT_N", None)
        os.environ.pop("TRAJAI_DEFAULT_THRESHOLD", None)
        os.environ.pop("TRAJAI_STRICT_MOCKS", None)
        reload_config()


def test_config_load_from_trajai_toml() -> None:
    """Test loading config from trajai.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "trajai.toml"
        toml_path.write_text("""\
default_n = 15
default_threshold = 0.85
strict_mocks = false
cache_enabled = true
""")

        # Change to tmpdir to load config
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = reload_config()

            assert config.default_n == 15
            assert config.default_threshold == 0.85
            assert config.strict_mocks is False
            assert config.cache_enabled is True
        finally:
            os.chdir(old_cwd)
            reload_config()


def test_config_load_from_pyproject_toml() -> None:
    """Test loading config from pyproject.toml [tool.trajai] section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject_path = Path(tmpdir) / "pyproject.toml"
        pyproject_path.write_text("""\
[project]
name = "test"

[tool.trajai]
default_n = 25
cost_budget_per_test = 2.50
""")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = reload_config()

            assert config.default_n == 25
            assert config.cost_budget_per_test == 2.50
        finally:
            os.chdir(old_cwd)
            reload_config()


def test_config_env_overrides_file() -> None:
    """Test that environment variables override file config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "trajai.toml"
        toml_path.write_text("""\
[tool.trajai]
default_n = 10
""")

        os.environ["TRAJAI_DEFAULT_N"] = "30"

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = reload_config()

            # Env var should override file
            assert config.default_n == 30
        finally:
            os.chdir(old_cwd)
            os.environ.pop("TRAJAI_DEFAULT_N", None)
            reload_config()


def test_config_bool_parsing() -> None:
    """Test boolean environment variable parsing."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
    ]

    for value, expected in test_cases:
        os.environ["TRAJAI_STRICT_MOCKS"] = value
        try:
            config = reload_config()
            assert config.strict_mocks == expected, f"Failed for value: {value}"
        finally:
            os.environ.pop("TRAJAI_STRICT_MOCKS", None)
            reload_config()


def test_config_get_config_singleton() -> None:
    """Test that get_config returns a singleton."""
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_config_model_override_alias() -> None:
    """Test that TRAJAI_MODEL is an alias for TRAJAI_MODEL_OVERRIDE."""
    os.environ["TRAJAI_MODEL"] = "gpt-4o-mini"

    try:
        config = reload_config()
        assert config.model_override == "gpt-4o-mini"
    finally:
        os.environ.pop("TRAJAI_MODEL", None)
        reload_config()
