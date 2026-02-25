"""A simple chatbot agent that looks up answers from a knowledge base."""


def chatbot_agent(input: str, tools: dict) -> str:
    """Answer user questions using a knowledge base tool.

    If the question is about a factual topic, look it up.
    If it's casual conversation, respond directly.
    """
    greetings = ["hello", "hi", "hey", "good morning", "good evening"]
    if any(g in input.lower() for g in greetings):
        return "Hello! How can I help you today?"

    if "?" in input or any(kw in input.lower() for kw in ["what", "how", "when", "where", "who", "why"]):
        result = tools["knowledge_base"]({"query": input})
        if result.get("found"):
            return f"Here's what I found: {result['answer']}"
        return "I'm sorry, I couldn't find an answer to that question."

    return "I'm here to help! Feel free to ask me a question."
