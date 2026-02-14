# Tech Stack

This document outlines the core technologies and tools used to build and maintain the UnitAI framework.

## 1. Core Language & Runtime
*   **Language:** Python 3.12+
*   **Rationale:** Python is the primary language for the AI and LLM ecosystem. Version 3.12 provides the latest performance improvements and modern typing features essential for a robust testing framework.

## 2. Testing & Quality Assurance
*   **Framework:** `pytest`
*   **Rationale:** `pytest` offers a rich ecosystem of plugins and a simple, expressive syntax. UnitAI will leverage its plugin architecture to provide custom markers, fixtures, and failure reporting.
*   **Linting:** `ruff`
*   **Type Checking:** `mypy`

## 3. Core Libraries (No Required External Dependencies for Core)
*   **Standard Library:** `dataclasses`, `asyncio`, `threading`, `json`, `argparse`.
*   **Rationale:** Keeping the core framework dependency-free (standard library only) ensures maximum compatibility and minimal overhead for users.

## 4. Optional Adapter Dependencies
*   **LangGraph:** `langgraph`
*   **CrewAI:** `crewai`
*   **OpenAI Agents:** `openai`
*   **Semantic Kernel:** `semantic-kernel`

## 5. Development & CI/CD
*   **Build System:** `hatch` or `poetry` (Standard Python packaging)
*   **CI:** GitHub Actions
*   **Documentation:** `mkdocs` with `mkdocstrings`
