from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from unitai.core.trajectory import Trajectory
    from unitai.mock.toolkit import MockToolkit

class BaseAdapter(ABC):
    """Abstract base class for all framework adapters."""

    @abstractmethod
    def can_handle(self, agent: Any) -> bool:
        """Return True if this adapter can handle the given agent."""
        pass

    @abstractmethod
    def inject_mocks(self, agent: Any, toolkit: MockToolkit) -> Any:
        """Return a copy of the agent with real tools replaced by mocks."""
        pass

    @abstractmethod
    def execute(self, wrapped_agent: Any, input: str, timeout: float) -> Trajectory:
        """Execute the agent and return the collected trajectory."""
        pass

    @abstractmethod
    def extract_tools(self, agent: Any) -> list[str]:
        """Extract the names of tools registered on the agent."""
        pass
