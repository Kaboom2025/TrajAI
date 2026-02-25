"""Tests for the chatbot agent."""
from unitai.mock import MockToolkit

from agent import chatbot_agent


def test_chatbot_answers_question():
    """Agent should use the knowledge base to answer factual questions."""
    toolkit = MockToolkit()
    toolkit.mock("knowledge_base", return_value={
        "found": True,
        "answer": "Python was created by Guido van Rossum in 1991.",
    })

    result = toolkit.run_callable(chatbot_agent, "What is Python?")

    assert result.tool_was_called("knowledge_base")
    assert result.output_contains("Guido van Rossum")


def test_chatbot_handles_not_found():
    """Agent should gracefully handle missing knowledge base entries."""
    toolkit = MockToolkit()
    toolkit.mock("knowledge_base", return_value={"found": False, "answer": None})

    result = toolkit.run_callable(chatbot_agent, "What is the meaning of life?")

    assert result.tool_was_called("knowledge_base")
    assert result.output_contains("couldn't find")


def test_chatbot_skips_tool_for_greetings():
    """Agent should respond to greetings without calling the knowledge base."""
    toolkit = MockToolkit()
    toolkit.mock("knowledge_base", return_value={"found": True, "answer": "unused"})

    result = toolkit.run_callable(chatbot_agent, "Hello!")

    assert result.tool_not_called("knowledge_base")
    assert result.output_contains("Hello")
