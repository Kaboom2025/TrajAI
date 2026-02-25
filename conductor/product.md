# Initial Concept

TrajAI — The open-source testing framework for AI agents. "Write tests for your agents like you write tests for your code."
TrajAI is a Python testing framework that lets developers write deterministic assertions about AI agent behavior. It provides mock infrastructure for agent tools, captures the full trajectory of agent actions during a test run, and supports statistical pass/fail thresholds to handle LLM non-determinism.

# Product Definition

## Vision & Goals
TrajAI aims to bring the rigor of traditional software testing to the world of AI agents. By focusing on deterministic assertions of agent trajectories, it enables developers to move beyond "vibe checks" and build robust, reliable agentic systems.

**Primary Goals:**
- **Deterministic Assertions:** Provide a robust API for asserting on tool calls, their order, and their arguments.
- **Statistical Reliability:** Address LLM non-determinism by running tests multiple times and asserting on pass-rate thresholds.
- **Developer Experience:** Integrate seamlessly with existing tools like `pytest` and provide rich, actionable failure reports.
- **Framework Agnostic:** Support major agent frameworks (LangGraph, CrewAI, OpenAI Agents) via specialized adapters while offering a generic fallback.

## Target Audience
- **AI Engineers/Developers:** Those building complex agentic workflows who need to ensure their agents follow specific protocols and business logic.
- **QA Engineers:** Teams specialized in validating LLM-based applications who require structured, automated testing tools.
- **DevOps Engineers:** Professionals looking to integrate agent verification into CI/CD pipelines with standard outputs like JUnit XML.

## Core Features (v0.1)
- **MockToolkit:** A powerful mocking layer for agent tools with support for static, sequential, conditional, and error-based response strategies.
- **Trajectory Collection:** Automatic recording of every action an agent takes during a test run, including tool calls, LLM interactions, and state changes.
- **Assertion Library:** A comprehensive set of methods to verify tool usage, output content, cost, performance, and error states.
- **Statistical Runner:** A decorator-based runner that executes tests N times to calculate pass rates, ensuring stability across non-determinism LLM calls.
- **pytest Integration:** A native plugin providing fixtures, markers, and enhanced failure reporting within the standard Python testing ecosystem.
- **Cost & Performance Tracking:** Built-in monitoring of token usage and API costs per test run, with configurable budget gates.