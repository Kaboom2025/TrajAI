"""A research agent that searches, fetches, summarizes, and exports findings."""


def research_agent(input: str, tools: dict) -> str:
    """Conduct research on a topic using multiple tools.

    Workflow:
    1. Search for relevant sources
    2. Fetch content from top results
    3. Summarize the findings
    4. Generate citations
    5. Export the report
    """
    search_results = tools["search"]({"query": input, "limit": 5})
    sources = search_results.get("results", [])

    if not sources:
        return f"No sources found for: {input}"

    contents = []
    for source in sources[:3]:
        content = tools["fetch_content"]({"url": source["url"]})
        contents.append(content.get("text", ""))

    combined = "\n\n".join(contents)
    summary = tools["summarize"]({"text": combined, "max_length": 500})

    citations = tools["generate_citations"](
        {"sources": sources[:3], "format": "APA"}
    )

    report = tools["export_report"]({
        "title": f"Research: {input}",
        "summary": summary.get("summary", ""),
        "citations": citations.get("formatted", []),
    })

    return (
        f"Research complete. Report saved to {report['path']}. "
        f"Found {len(sources)} sources, summarized top {len(contents)}."
    )


def quick_search_agent(input: str, tools: dict) -> str:
    """A simpler agent that just searches and summarizes."""
    results = tools["search"]({"query": input})
    sources = results.get("results", [])

    if not sources:
        return "No results found."

    summary = tools["summarize"](
        {"text": sources[0].get("snippet", ""), "max_length": 100}
    )
    return f"Quick answer: {summary.get('summary', 'No summary available.')}"
