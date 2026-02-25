"""Configuration loading for TrajAI.

Loads configuration from pyproject.toml [tool.trajai] section or trajai.toml,
with environment variable overrides.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TrajAIConfig:
    """TrajAI configuration settings."""

    # Statistical runner defaults
    default_n: int = 10
    default_threshold: float = 0.95
    max_workers: int = 5

    # Cost controls
    cost_budget_per_test: float = 1.00
    cost_budget_per_suite: float = 10.00
    model_override: str = ""

    # Mock behavior
    strict_mocks: bool = True

    # Cache settings
    cache_enabled: bool = False
    cache_directory: str = ".trajai/cache"
    cache_ttl_hours: float = 168.0  # 7 days

    # Output
    junit_xml: str = "test-results/trajai.xml"
    verbose: bool = False

    # Adapter (for future use)
    adapter: str = ""

    @classmethod
    def load(cls) -> TrajAIConfig:
        """Load configuration from files and environment variables.

        Priority order (highest to lowest):
        1. Environment variables (TRAJAI_*)
        2. trajai.toml
        3. pyproject.toml [tool.trajai]
        4. Defaults
        """
        config = cls()

        # Try to load from pyproject.toml or trajai.toml
        cwd = Path.cwd()
        trajai_toml = cwd / "trajai.toml"
        pyproject_toml = cwd / "pyproject.toml"

        # Load from trajai.toml first (if exists)
        if trajai_toml.exists():
            try:
                config._load_from_toml(trajai_toml)
            except Exception:
                pass  # Ignore parse errors, fall back to defaults

        # Load from pyproject.toml [tool.trajai] section (if exists)
        if pyproject_toml.exists():
            try:
                config._load_from_pyproject_toml(pyproject_toml)
            except Exception:
                pass  # Ignore parse errors

        # Apply environment variable overrides
        config._apply_env_overrides()

        return config

    def _load_from_toml(self, toml_path: Path) -> None:
        """Load configuration from a TOML file."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import]
            except ImportError:
                # No TOML parser available - skip file loading
                return

        with open(toml_path, "rb") as f:
            data = tomllib.load(f)

        trajai_section = data.get("tool", {}).get("trajai", {})
        if not trajai_section and "trajai" in data:
            trajai_section = data["trajai"]

        self._apply_dict(trajai_section)

    def _load_from_pyproject_toml(self, pyproject_path: Path) -> None:
        """Load configuration from pyproject.toml [tool.trajai] section."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import]
            except ImportError:
                # No TOML parser available - skip file loading
                return

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        trajai_section = data.get("tool", {}).get("trajai", {})
        self._apply_dict(trajai_section)

    def _apply_dict(self, data: dict) -> None:
        """Apply configuration from a dictionary."""
        if "default_n" in data:
            self.default_n = int(data["default_n"])
        if "default_threshold" in data:
            self.default_threshold = float(data["default_threshold"])
        if "max_workers" in data:
            self.max_workers = int(data["max_workers"])
        if "cost_budget_per_test" in data:
            self.cost_budget_per_test = float(data["cost_budget_per_test"])
        if "cost_budget_per_suite" in data:
            self.cost_budget_per_suite = float(data["cost_budget_per_suite"])
        if "model_override" in data:
            self.model_override = str(data["model_override"])
        if "strict_mocks" in data:
            self.strict_mocks = bool(data["strict_mocks"])
        if "cache_enabled" in data:
            self.cache_enabled = bool(data["cache_enabled"])
        if "cache_directory" in data:
            self.cache_directory = str(data["cache_directory"])
        if "cache_ttl_hours" in data:
            self.cache_ttl_hours = float(data["cache_ttl_hours"])
        if "junit_xml" in data:
            self.junit_xml = str(data["junit_xml"])
        if "verbose" in data:
            self.verbose = bool(data["verbose"])
        if "adapter" in data:
            self.adapter = str(data["adapter"])

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_map = {
            "TRAJAI_DEFAULT_N": ("default_n", int),
            "TRAJAI_DEFAULT_THRESHOLD": ("default_threshold", float),
            "TRAJAI_MAX_WORKERS": ("max_workers", int),
            "TRAJAI_COST_BUDGET_PER_TEST": ("cost_budget_per_test", float),
            "TRAJAI_COST_BUDGET_PER_SUITE": ("cost_budget_per_suite", float),
            "TRAJAI_MODEL_OVERRIDE": ("model_override", str),
            "TRAJAI_MODEL": ("model_override", str),  # Alias
            "TRAJAI_STRICT_MOCKS": (
                "strict_mocks", lambda x: x.lower() in ("true", "1", "yes")
            ),
            "TRAJAI_CACHE_ENABLED": (
                "cache_enabled", lambda x: x.lower() in ("true", "1", "yes")
            ),
            "TRAJAI_CACHE_DIRECTORY": ("cache_directory", str),
            "TRAJAI_CACHE_TTL_HOURS": ("cache_ttl_hours", float),
            "TRAJAI_JUNIT_XML": ("junit_xml", str),
            "TRAJAI_VERBOSE": ("verbose", lambda x: x.lower() in ("true", "1", "yes")),
            "TRAJAI_ADAPTER": ("adapter", str),
        }

        for env_var, (attr_name, converter) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    if callable(converter) and converter.__name__ == "<lambda>":
                        setattr(self, attr_name, converter(value))
                    else:
                        setattr(self, attr_name, converter(value))
                except (ValueError, TypeError):
                    # Invalid value - skip this override
                    pass


# Global config instance (lazy-loaded)
_config: Optional[TrajAIConfig] = None


def get_config() -> TrajAIConfig:
    """Get the global TrajAI configuration instance."""
    global _config
    if _config is None:
        _config = TrajAIConfig.load()
    return _config


def reload_config() -> TrajAIConfig:
    """Reload configuration from files and environment."""
    global _config
    _config = TrajAIConfig.load()
    return _config
