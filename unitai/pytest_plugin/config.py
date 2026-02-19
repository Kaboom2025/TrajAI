from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class UnitAIConfig:
    default_n: int = 10
    default_threshold: float = 0.95
    max_workers: int = 5
    cost_budget_per_test: float = 1.00
    cost_budget_per_suite: float = 10.00
    strict_mocks: bool = True
    junit_xml: str = "test-results/unitai.xml"
    verbose: bool = False


def _read_toml_section(path: Path) -> Dict[str, Any]:
    """Read [tool.unitai] section from a TOML file."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError:
        return {}

    if path.name == "pyproject.toml":
        return data.get("tool", {}).get("unitai", {})
    # unitai.toml — top-level keys
    return data


def _apply_env_overrides(config: UnitAIConfig) -> UnitAIConfig:
    """Override config fields from UNITAI_* environment variables."""
    env_map = {
        "UNITAI_DEFAULT_N": ("default_n", int),
        "UNITAI_DEFAULT_THRESHOLD": ("default_threshold", float),
        "UNITAI_MAX_WORKERS": ("max_workers", int),
        "UNITAI_COST_BUDGET_PER_TEST": ("cost_budget_per_test", float),
        "UNITAI_COST_BUDGET_PER_SUITE": ("cost_budget_per_suite", float),
        "UNITAI_STRICT_MOCKS": (
            "strict_mocks",
            lambda v: v.lower() in ("1", "true", "yes"),
        ),
        "UNITAI_JUNIT_XML": ("junit_xml", str),
        "UNITAI_VERBOSE": (
            "verbose",
            lambda v: v.lower() in ("1", "true", "yes"),
        ),
    }

    updates: Dict[str, Any] = {}
    for env_var, (attr, converter) in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                updates[attr] = converter(value)
            except (ValueError, TypeError):
                pass

    if not updates:
        return config

    # Create new config with overrides (dataclass is mutable)
    import dataclasses
    return dataclasses.replace(config, **updates)


def _apply_dict(config: UnitAIConfig, data: Dict[str, Any]) -> UnitAIConfig:
    """Apply a dict of config values onto a UnitAIConfig."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(UnitAIConfig)}
    updates: Dict[str, Any] = {}

    type_map: Dict[str, Any] = {
        "default_n": int,
        "default_threshold": float,
        "max_workers": int,
        "cost_budget_per_test": float,
        "cost_budget_per_suite": float,
        "strict_mocks": bool,
        "junit_xml": str,
        "verbose": bool,
    }

    for key, value in data.items():
        if key in field_names:
            expected_type = type_map.get(key)
            if expected_type is not None:
                try:
                    updates[key] = expected_type(value)
                except (ValueError, TypeError):
                    pass
            else:
                updates[key] = value

    if not updates:
        return config
    return dataclasses.replace(config, **updates)


def load_unitai_config(root: Optional[Path] = None) -> UnitAIConfig:
    """Load UnitAIConfig from pyproject.toml, unitai.toml, and UNITAI_* env vars.

    Priority (highest last): defaults → pyproject.toml → unitai.toml → env vars.
    """
    if root is None:
        root = Path.cwd()

    config = UnitAIConfig()

    # 1. pyproject.toml [tool.unitai]
    pyproject_data = _read_toml_section(root / "pyproject.toml")
    config = _apply_dict(config, pyproject_data)

    # 2. unitai.toml (overrides pyproject.toml)
    unitai_toml_data = _read_toml_section(root / "unitai.toml")
    config = _apply_dict(config, unitai_toml_data)

    # 3. UNITAI_* env vars (highest priority)
    config = _apply_env_overrides(config)

    return config
