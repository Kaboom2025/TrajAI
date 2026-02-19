from __future__ import annotations

from unitai.adapters.base import BaseAdapter
from unitai.adapters.generic import GenericAdapter

__all__ = ["BaseAdapter", "GenericAdapter"]

try:
    from unitai.adapters.langgraph import LangGraphAdapter

    __all__ = [*__all__, "LangGraphAdapter"]
except ImportError:
    pass
