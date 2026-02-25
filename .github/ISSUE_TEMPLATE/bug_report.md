---
name: Bug Report
about: Report a bug or unexpected behavior in TrajAI
title: "[BUG] "
labels: bug
assignees: ''
---

## Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Install TrajAI version `...`
2. Create an agent with `...`
3. Run test with `...`
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened. Include error messages and stack traces if applicable.

```
Paste error message or stack trace here
```

## Minimal Reproduction

Please provide a minimal code example that reproduces the issue:

```python
# Your minimal reproduction code here
from trajai.mock import MockToolkit

def my_agent(input: str, tools: dict) -> str:
    ...

def test_bug():
    toolkit = MockToolkit()
    ...
```

## Environment

- **TrajAI version:** [e.g., 0.1.0] (run `pip show trajai`)
- **Python version:** [e.g., 3.12.0] (run `python --version`)
- **Operating system:** [e.g., macOS 14.0, Ubuntu 22.04, Windows 11]
- **Framework:** [e.g., LangGraph, CrewAI, generic] and version if applicable
- **Install method:** [e.g., `pip install trajai`, `pip install trajai[langgraph]`]

## Additional Context

Add any other context about the problem here. Screenshots, logs, or relevant configuration files are helpful.
