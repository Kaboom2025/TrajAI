from __future__ import annotations

from trajai.adapters.base import BaseAdapter
from trajai.adapters.generic import GenericAdapter

__all__ = ["BaseAdapter", "GenericAdapter"]

try:
    from trajai.adapters.langgraph import LangGraphAdapter

    __all__ = [*__all__, "LangGraphAdapter"]
except ImportError:
    pass

try:
    from trajai.adapters.openai_agents import OpenAIAgentsAdapter

    __all__ = [*__all__, "OpenAIAgentsAdapter"]
except ImportError:
    pass

try:
    from trajai.adapters.crewai import CrewAIAdapter

    __all__ = [*__all__, "CrewAIAdapter"]
except ImportError:
    pass
