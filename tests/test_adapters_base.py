import pytest
from typing import Any, TYPE_CHECKING
from unitai.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from unitai.core.trajectory import Trajectory
    from unitai.mock.toolkit import MockToolkit

def test_base_adapter_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseAdapter() # type: ignore

class MyAdapter(BaseAdapter):
    def can_handle(self, agent: Any) -> bool:
        return True
    def inject_mocks(self, agent: Any, toolkit: MockToolkit) -> Any:
        return agent
    def execute(self, wrapped_agent: Any, input: str, timeout: float) -> Trajectory:
        return None # type: ignore
    def extract_tools(self, agent: Any) -> list[str]:
        return []

def test_concrete_adapter_creation() -> None:
    adapter = MyAdapter()
    assert adapter.can_handle(None) is True
