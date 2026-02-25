from typing import Any, Callable

from trajai.mock.toolkit import MockToolDict, UnmockedToolError


def test_mock_tool_dict_strict_mode() -> None:
    tools: dict[str, Callable[[dict[str, Any]], Any]] = {
        "tool1": lambda x: "res1"
    }
    mock_dict = MockToolDict(tools, strict=True)

    assert mock_dict["tool1"]({}) == "res1"

    import pytest
    with pytest.raises(UnmockedToolError, match="tool2"):
        _ = mock_dict["tool2"]

def test_mock_tool_dict_non_strict_mode() -> None:
    tools: dict[str, Callable[[dict[str, Any]], Any]] = {
        "tool1": lambda x: "res1"
    }
    mock_dict = MockToolDict(tools, strict=False)

    assert mock_dict["tool1"]({}) == "res1"
    # Should not raise
    assert "tool2" not in mock_dict
    import pytest
    with pytest.raises(KeyError):
        _ = mock_dict["tool2"]
