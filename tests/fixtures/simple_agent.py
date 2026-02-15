from typing import Any, Callable

def simple_tool_agent(input_str: str, tools: dict[str, Callable[[dict[str, Any]], Any]]) -> str:
    """
    A simple agent that calls tools based on the input.
    """
    if input_str.startswith("search:"):
        query = input_str.split(":", 1)[1].strip()
        # Direct access will trigger UnmockedToolError in strict mode
        tool = tools["search"]
        result = tool({"q": query})
        return f"Found: {result}"
    
    if input_str.startswith("calc:"):
        expr = input_str.split(":", 1)[1].strip()
        tool = tools["calculator"]
        result = tool({"expression": expr})
        return f"Result is {result}"
        
    return "I don't know how to do that."

def metadata_agent(input_str: str, toolkit: Any) -> str:
    """An agent that manually records LLM metadata."""
    toolkit.record_llm_call(model="gpt-4o", prompt_tokens=100, completion_tokens=50, cost=0.002)
    return f"Processed {input_str}"
