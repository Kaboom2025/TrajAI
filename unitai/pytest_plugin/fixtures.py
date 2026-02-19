from __future__ import annotations

import pytest

from unitai.mock.toolkit import MockToolkit
from unitai.pytest_plugin.config import UnitAIConfig

# Stash key for UnitAIConfig
_UNITAI_CONFIG_KEY = pytest.StashKey[UnitAIConfig]()


@pytest.fixture
def mock_toolkit() -> MockToolkit:  # type: ignore[misc]
    """Provides a fresh MockToolkit instance. Resets on teardown."""
    toolkit = MockToolkit()
    yield toolkit  # type: ignore[misc]
    toolkit.reset()


@pytest.fixture
def unitai_config(request: pytest.FixtureRequest) -> UnitAIConfig:
    """Returns the UnitAIConfig loaded during pytest_configure."""
    return request.config.stash[_UNITAI_CONFIG_KEY]
