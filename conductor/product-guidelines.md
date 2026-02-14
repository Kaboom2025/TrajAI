# Product Guidelines

These guidelines define the standards for documentation, development, and user experience for the UnitAI framework.

## 1. Documentation & Prose Style
*   **Tone:** Professional, precise, and technical. UnitAI is a tool for engineers; the documentation should respect their time and expertise.
*   **Clarity over Cleverness:** Avoid jargon or overly complex metaphors. Use straightforward language to explain technical concepts.
*   **Action-Oriented:** Documentation should focus on "How to" and "Why," providing clear examples for every feature.

## 2. Code Example Standards
*   **Idiomatic Python:** All code snippets must follow modern Python (3.10+) best practices and PEP 8.
*   **Runnable Snippets:** Examples in the documentation should be as close to "copy-paste and run" as possible.
*   **Type Hinting:** Use explicit type hints in all examples to demonstrate clear API usage and improve discoverability.

## 3. Testing Philosophy
*   **Determinism First:** Prioritize tests that assert on specific, observable actions (tool calls) rather than fuzzy text output.
*   **Embrace Non-Determinism:** Use statistical runners to provide high confidence in agent behavior while acknowledging the inherent variability of LLMs.
*   **Cost Efficiency:** Encourage development patterns that minimize unnecessary LLM API calls, such as using the record/replay cache.

## 4. User Experience (UX) & CLI
*   **CLI-First:** The `unitai` command should be the primary interface for running tests, providing a clean wrapper over `pytest`.
*   **Actionable Errors:** When a test fails, provide rich, structured output showing exactly what happened in the trajectory versus what was expected.
*   **Zero Configuration:** UnitAI should work out of the box with sensible defaults, while allowing deep customization via `pyproject.toml`.

## 5. Architectural Principles
*   **Minimal Core:** Keep the core framework lightweight and free of heavy dependencies.
*   **Adapter Pattern:** Use adapters to bridge the gap between UnitAI and specific agent frameworks (LangGraph, CrewAI, etc.), keeping the core logic decoupled.
*   **Transparency:** Every step the agent takes should be visible and queryable in the resulting trajectory.
