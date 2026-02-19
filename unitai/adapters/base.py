from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

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
    def execute(
        self, 
        wrapped_agent: Any, 
        input: str, 
        timeout: float,
        cache: Optional[Any] = None,  # ReplayCache instance
        cache_mode: str = "auto",  # "auto", "record", "replay", "no-cache"
    ) -> Trajectory:
        """Execute the agent and return the collected trajectory.
        
        Args:
            wrapped_agent: The agent with mocks injected.
            input: User input string.
            timeout: Maximum execution time in seconds.
            cache: Optional ReplayCache instance for LLM response caching.
            cache_mode: Cache mode - "auto" (use cache if enabled), 
                       "record" (force fresh calls and cache), 
                       "replay" (use cache only, fail on miss),
                       "no-cache" (ignore cache).
        """
        pass

    @abstractmethod
    def extract_tools(self, agent: Any) -> list[str]:
        """Extract the names of tools registered on the agent."""
        pass
