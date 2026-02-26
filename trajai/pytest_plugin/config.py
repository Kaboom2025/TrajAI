from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional


@dataclass
class TrajAIConfig:
    default_n: int = 10
    default_threshold: float = 0.95
    max_workers: int = 5
    cost_budget_per_test: float = 1.00
    cost_budget_per_suite: float = 10.00
    strict_mocks: bool = True
    junit_xml: str = "test-results/trajai.xml"
    verbose: bool = False


def _read_toml_section(path: Path) -> Dict[str, Any]:
    """Read [tool.trajai] section from a TOML file."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError:
        return {}

    if path.name == "pyproject.toml":
        result: Dict[str, Any] = data.get("tool", {}).get("trajai", {})
        return result
    # trajai.toml — top-level keys
    return dict(data)


def _apply_env_overrides(config: TrajAIConfig) -> TrajAIConfig:
    """Override config fields from TRAJAI_* environment variables."""
    def _bool(v: str) -> bool:
        return v.lower() in ("1", "true", "yes")

    env_map: Dict[str, tuple[str, Callable[[str], Any]]] = {
        "TRAJAI_DEFAULT_N": ("default_n", int),
        "TRAJAI_DEFAULT_THRESHOLD": ("default_threshold", float),
        "TRAJAI_MAX_WORKERS": ("max_workers", int),
        "TRAJAI_COST_BUDGET_PER_TEST": ("cost_budget_per_test", float),
        "TRAJAI_COST_BUDGET_PER_SUITE": ("cost_budget_per_suite", float),
        "TRAJAI_STRICT_MOCKS": ("strict_mocks", _bool),
        "TRAJAI_JUNIT_XML": ("junit_xml", str),
        "TRAJAI_VERBOSE": ("verbose", _bool),
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


def _apply_dict(config: TrajAIConfig, data: Dict[str, Any]) -> TrajAIConfig:
    """Apply a dict of config values onto a TrajAIConfig."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(TrajAIConfig)}
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


def load_trajai_config(root: Optional[Path] = None) -> TrajAIConfig:
    """Load TrajAIConfig from pyproject.toml, trajai.toml, and TRAJAI_* env vars.

    Priority (highest last): defaults → pyproject.toml → trajai.toml → env vars.
    """
    if root is None:
        root = Path.cwd()

    config = TrajAIConfig()

    # 1. pyproject.toml [tool.trajai]
    pyproject_data = _read_toml_section(root / "pyproject.toml")
    config = _apply_dict(config, pyproject_data)

    # 2. trajai.toml (overrides pyproject.toml)
    trajai_toml_data = _read_toml_section(root / "trajai.toml")
    config = _apply_dict(config, trajai_toml_data)

    # 3. TRAJAI_* env vars (highest priority)
    config = _apply_env_overrides(config)

    return config
