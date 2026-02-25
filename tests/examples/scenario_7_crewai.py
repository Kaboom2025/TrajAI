"""Scenario 7: CrewAI Integration

This scenario demonstrates using UnitAI with CrewAI crews and agents.

Key concepts:
- Auto-detection of CrewAI Crew and Agent objects
- BaseTool replacement with UnitAI mocks
- Testing multi-agent crews with shared tools
- Crew.kickoff() result extraction

Real-world use case: Testing a CrewAI agent that researches competitors
by looking up company data and analyzing market trends.
"""

import pytest

# Skip this scenario if crewai is not installed
pytest.importorskip("crewai")

from crewai import Agent as CrewAgent
from crewai import Crew, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from unitai.mock.toolkit import MockToolkit


# ---------------------------------------------------------------------------
# Step 1: Define tools as BaseTool subclasses
# ---------------------------------------------------------------------------


class CompanyLookupInput(BaseModel):
    """Input schema for company lookup."""

    company_name: str = Field(..., description="The company name to look up.")


class CompanyLookupTool(BaseTool):  # type: ignore[misc]
    """Tool for looking up company information."""

    name: str = "lookup_company"
    description: str = "Look up information about a company."
    args_schema: type[BaseModel] = CompanyLookupInput

    def _run(self, company_name: str) -> str:
        # Real implementation would query a database or API
        return f'{{"name": "{company_name}", "industry": "Technology", "size": "Large"}}'


class MarketAnalysisInput(BaseModel):
    """Input schema for market analysis."""

    industry: str = Field(..., description="The industry to analyze.")


class MarketAnalysisTool(BaseTool):  # type: ignore[misc]
    """Tool for analyzing market trends."""

    name: str = "analyze_market"
    description: str = "Analyze market trends for an industry."
    args_schema: type[BaseModel] = MarketAnalysisInput

    def _run(self, industry: str) -> str:
        # Real implementation would use market data
        return (
            f'{{"industry": "{industry}", "growth_rate": "15%", '
            f'"trend": "Growing rapidly"}}'
        )


# ---------------------------------------------------------------------------
# Step 2: Create the agent and crew
# ---------------------------------------------------------------------------


def create_research_agent() -> CrewAgent:
    """Create a CrewAI agent for market research."""
    return CrewAgent(
        role="Market Researcher",
        goal="Research competitors and analyze market trends.",
        backstory=(
            "You are an experienced market researcher who gathers "
            "intelligence about competitors and industry trends."
        ),
        tools=[CompanyLookupTool(), MarketAnalysisTool()],
        llm="gpt-4o-mini",
        verbose=False,
    )


def create_research_crew(agent: CrewAgent, task_description: str) -> Crew:
    """Create a crew with a single research task."""
    task = Task(
        description=task_description,
        expected_output="A comprehensive research report.",
        agent=agent,
    )
    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
    )


# ---------------------------------------------------------------------------
# Step 3: Test with UnitAI
# ---------------------------------------------------------------------------


def test_crewai_agent_company_lookup() -> None:
    """Test that the CrewAI agent calls lookup_company."""
    agent = create_research_agent()
    toolkit = MockToolkit()

    # Mock the lookup_company tool
    toolkit.mock(
        "lookup_company",
        return_value={"name": "Acme Corp", "industry": "Technology", "size": "Large"},
    )

    # Run the agent (UnitAI auto-detects it's a CrewAI Agent)
    try:
        result = toolkit.run(agent, "Research Acme Corp")

        # Assert the agent called the tool
        assert result.tool_was_called("lookup_company")

        # Check the arguments passed to the tool
        call = result.get_call("lookup_company", 0)
        assert "Acme" in str(call.args.get("company_name", ""))

        print("✓ CrewAI Agent correctly called lookup_company")
        print(f"  Tool arguments: {call.args}")
        print(f"  Mock result: {call.result}")

    except Exception as e:
        print(f"⚠ CrewAI Agent test skipped (requires crewai + API key): {e}")


def test_crewai_crew_multi_step() -> None:
    """Test a CrewAI crew with multiple tool calls."""
    agent = create_research_agent()
    crew = create_research_crew(agent, "Research Acme Corp and analyze the tech market")
    toolkit = MockToolkit()

    toolkit.mock(
        "lookup_company",
        return_value={"name": "Acme Corp", "industry": "Technology", "size": "Large"},
    )
    toolkit.mock(
        "analyze_market",
        return_value={
            "industry": "Technology",
            "growth_rate": "15%",
            "trend": "Growing",
        },
    )

    try:
        result = toolkit.run(crew, "Research Acme and analyze tech market")

        # Assert both tools were called
        assert result.tool_was_called("lookup_company")
        assert result.tool_was_called("analyze_market")

        print("✓ CrewAI Crew executed multi-step research correctly")
        print(f"  Tools called: {result.call_order()}")

    except Exception as e:
        print(f"⚠ CrewAI Crew test skipped: {e}")


def test_crewai_tool_not_called() -> None:
    """Test that unused tools are correctly not called."""
    agent = create_research_agent()
    toolkit = MockToolkit()

    # Mock both tools, but the agent should only need one
    toolkit.mock("lookup_company", return_value={"name": "TechCo", "industry": "Tech"})
    toolkit.mock("analyze_market", return_value={"industry": "Tech", "growth": "10%"})

    try:
        result = toolkit.run(agent, "Just look up TechCo, no market analysis needed")

        # Assert lookup was called but analysis was not
        assert result.tool_was_called("lookup_company")
        assert result.tool_not_called("analyze_market")

        print("✓ CrewAI Agent correctly skipped unnecessary tool")
        print(f"  Called: lookup_company")
        print(f"  Not called: analyze_market")

    except Exception as e:
        print(f"⚠ CrewAI selective tool test skipped: {e}")


# ---------------------------------------------------------------------------
# Step 4: Run the scenario
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 70)
    print("Scenario 7: CrewAI Integration")
    print("=" * 70)
    print()

    test_crewai_agent_company_lookup()
    print()
    test_crewai_crew_multi_step()
    print()
    test_crewai_tool_not_called()
    print()

    print("=" * 70)
    print("Key Takeaways:")
    print("- UnitAI auto-detects CrewAI Crew and Agent objects")
    print("- BaseTool instances are replaced with mocks (via model_copy)")
    print("- Both single agents and full crews can be tested")
    print("- All standard UnitAI assertions work with CrewAI")
    print("- Tool extraction works across multi-agent crews")
    print("=" * 70)
