"""Tests for the research agent, including statistical testing."""
from trajai.core.assertions import cost_under, tokens_under
from trajai.mock import MockToolkit
from trajai.runner.statistical import StatisticalRunner

from agent import quick_search_agent, research_agent

MOCK_SOURCES = [
    {"url": "https://example.com/1", "title": "Source 1", "snippet": "First result"},
    {"url": "https://example.com/2", "title": "Source 2", "snippet": "Second result"},
    {"url": "https://example.com/3", "title": "Source 3", "snippet": "Third result"},
]


def _setup_research_toolkit() -> MockToolkit:
    """Create a toolkit with all research tools mocked."""
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": MOCK_SOURCES})
    toolkit.mock("fetch_content", sequence=[
        {"text": "Content from source 1 about machine learning."},
        {"text": "Content from source 2 about neural networks."},
        {"text": "Content from source 3 about deep learning."},
    ])
    toolkit.mock("summarize", return_value={
        "summary": "Machine learning encompasses neural networks and deep learning approaches."
    })
    toolkit.mock("generate_citations", return_value={
        "formatted": ["Source 1 (2024)", "Source 2 (2024)", "Source 3 (2024)"]
    })
    toolkit.mock("export_report", return_value={
        "path": "/tmp/report.pdf", "success": True
    })
    return toolkit


def test_research_tool_order():
    """Agent must follow the search -> fetch -> summarize -> cite -> export pipeline."""
    toolkit = _setup_research_toolkit()

    result = toolkit.run_callable(research_agent, "machine learning trends")

    expected_order = ["search", "summarize", "generate_citations", "export_report"]
    assert result.call_order_contains(expected_order)


def test_research_fetches_multiple_sources():
    """Agent should fetch content from the top 3 sources."""
    toolkit = _setup_research_toolkit()

    result = toolkit.run_callable(research_agent, "machine learning trends")

    assert result.tool_call_count("fetch_content", 3)


def test_research_output_contains_report_path():
    """Agent output should mention where the report was saved."""
    toolkit = _setup_research_toolkit()

    result = toolkit.run_callable(research_agent, "machine learning trends")

    assert result.output_contains("report.pdf")
    assert result.output_contains("3 sources")


def test_research_passes_correct_search_query():
    """Agent should pass the user's input as the search query."""
    toolkit = _setup_research_toolkit()

    result = toolkit.run_callable(research_agent, "quantum computing advances")

    call = result.get_call("search", 0)
    assert call.args["query"] == "quantum computing advances"


def test_research_handles_no_results():
    """Agent should handle empty search results gracefully."""
    toolkit = MockToolkit()
    toolkit.mock("search", return_value={"results": []})
    toolkit.mock("fetch_content", return_value={"text": ""})
    toolkit.mock("summarize", return_value={"summary": ""})
    toolkit.mock("generate_citations", return_value={"formatted": []})
    toolkit.mock("export_report", return_value={"path": "", "success": False})

    result = toolkit.run_callable(research_agent, "nonexistent topic")

    assert result.tool_was_called("search")
    assert result.tool_not_called("fetch_content")
    assert result.output_contains("No sources found")


def test_quick_search_statistical():
    """Quick search agent should reliably search and summarize (statistical test)."""

    def _single_run():
        toolkit = MockToolkit()
        toolkit.mock("search", return_value={"results": MOCK_SOURCES})
        toolkit.mock("summarize", return_value={"summary": "A concise answer about the topic."})

        result = toolkit.run_callable(quick_search_agent, "What is AI?")
        assert result.tool_was_called("search")
        assert result.tool_was_called("summarize")
        assert result.tool_called_before("search", "summarize")

    runner = StatisticalRunner(n=5, threshold=1.0, budget=10.0)
    stat_result = runner.run(_single_run)
    assert stat_result.pass_rate >= 1.0
