from __future__ import annotations

from typing import Generator

import pytest

from trajai.mock.toolkit import MockToolkit
from trajai.pytest_plugin.config import TrajAIConfig

# Stash key for TrajAIConfig
_TRAJAI_CONFIG_KEY = pytest.StashKey[TrajAIConfig]()


@pytest.fixture
def mock_toolkit() -> Generator[MockToolkit, None, None]:
    """Provides a fresh MockToolkit instance. Resets on teardown."""
    toolkit = MockToolkit()
    yield toolkit
    toolkit.reset()


@pytest.fixture
def trajai_config(request: pytest.FixtureRequest) -> TrajAIConfig:
    """Returns the TrajAIConfig loaded during pytest_configure."""
    return request.config.stash[_TRAJAI_CONFIG_KEY]
