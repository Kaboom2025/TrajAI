from __future__ import annotations

from unitai.adapters.base import BaseAdapter
from unitai.adapters.generic import GenericAdapter

__all__ = ["BaseAdapter", "GenericAdapter"]

try:
    from unitai.adapters.langgraph import LangGraphAdapter

    __all__ = [*__all__, "LangGraphAdapter"]
except ImportError:
    pass

try:
    from unitai.adapters.openai_agents import OpenAIAgentsAdapter

    __all__ = [*__all__, "OpenAIAgentsAdapter"]
except ImportError:
    pass

try:
    from unitai.adapters.crewai import CrewAIAdapter

    __all__ = [*__all__, "CrewAIAdapter"]
except ImportError:
    pass
