"""
Scenario 5: Error Handling - Adapter Not Found
===============================================

What it simulates:
    Attempting to use TrajAI with an agent framework that isn't supported yet.
    TrajAI provides clear, actionable error messages when it can't auto-detect
    an agent type.

Use case:
    Understanding how TrajAI handles unsupported agent types and what to do about it.
    This teaches:
    - How to catch and handle AdapterNotFoundError
    - What frameworks are currently supported
    - How to write tests that expect exceptions
    - Error handling patterns in TrajAI

Key concepts demonstrated:
    - AdapterNotFoundError exception
    - try/except pattern for expected failures
    - Error message interpretation
    - Graceful degradation when framework isn't supported

Real-world example:
    Developer tries to test an agent using a custom framework or a framework
    that TrajAI hasn't added an adapter for yet. TrajAI provides a clear error
    instead of silently failing.
"""

import warnings

warnings.filterwarnings("ignore")

from trajai.mock.toolkit import AdapterNotFoundError, MockToolkit  # noqa: E402

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"

def print_header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")

def print_ok(label: str, value: object) -> None:
    print(f"  {GREEN}✓{RESET}  {label}: {BOLD}{value}{RESET}")

def print_section(text: str) -> None:
    print(f"\n  {YELLOW}▶ {text}{RESET}")

def print_error(label: str, value: object) -> None:
    print(f"  {RED}✓{RESET}  {label}: {BOLD}{value}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Setup: Create a toolkit and try to run an unsupported agent type
# ─────────────────────────────────────────────────────────────────────────────
print_header("Scenario 5 — Error Handling (AdapterNotFoundError)")

toolkit = MockToolkit()

# Define a custom, unsupported agent type
class CustomUnsupportedAgent:
    """A hypothetical agent type that TrajAI doesn't have an adapter for yet."""
    def __init__(self):
        self.name = "CustomUnsupportedAgent"

    def __repr__(self):
        return f"<{self.name}>"


# ─────────────────────────────────────────────────────────────────────────────
# Try to run the unsupported agent (this will fail)
# ─────────────────────────────────────────────────────────────────────────────
print_section("Attempting to run unsupported agent type")

unsupported_agent = CustomUnsupportedAgent()
print(f"  Agent type: {unsupported_agent}")

try:
    print("  Calling toolkit.run()...")
    result = toolkit.run(unsupported_agent, "Hello, what is 2+2?")
    print(f"  {RED}✗ Expected AdapterNotFoundError but nothing was raised!{RESET}")
except AdapterNotFoundError as e:
    print_error("AdapterNotFoundError raised as expected", True)
    print("\n  Error message:")
    print(f"    {BOLD}{e}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Understanding the error
# ─────────────────────────────────────────────────────────────────────────────
print_section("What This Error Means")
print("  TrajAI tried to run an agent but couldn't identify its framework.")
print("  This happens when:")
print("    ✗ The agent framework isn't supported yet")
print("    ✗ The adapter for that framework isn't installed")
print("    ✗ The agent object is the wrong type entirely")
print()
print("  Solutions:")
print("    → Check if your framework has an installed adapter")
print("    → Use GenericAdapter and manually wire tools (Phase 2)")
print("    → Request support for your framework in GitHub issues")


# ─────────────────────────────────────────────────────────────────────────────
# Currently supported frameworks
# ─────────────────────────────────────────────────────────────────────────────
print_section("Currently Supported Frameworks")
print("  ✓ LangGraph")
print("  ✓ Generic (manual tool wiring)")
print("  ")
print("  Planned for future phases:")
print("    • CrewAI")
print("    • OpenAI Agents")
print("    • Semantic Kernel")


# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Fallback with try/except
# ─────────────────────────────────────────────────────────────────────────────
print_section("Pattern: Safe Error Handling")
print("  def test_with_fallback():")
print("      toolkit = MockToolkit()")
print("      toolkit.mock('my_tool', return_value={'result': 'ok'})")
print("      try:")
print("          result = toolkit.run(my_agent, 'prompt')")
print("      except AdapterNotFoundError as e:")
print("          print(f'Framework not supported: {e}')")
print("          # Use fallback approach or skip test")
print("          pytest.skip(f'Adapter not found: {e}')")


# ─────────────────────────────────────────────────────────────────────────────
# Pattern: Testing for expected exceptions
# ─────────────────────────────────────────────────────────────────────────────
print_section("Pattern: pytest.raises() (in actual tests)")
print("  import pytest")
print("  from trajai.mock.toolkit import AdapterNotFoundError")
print("  ")
print("  def test_unsupported_agent():")
print("      toolkit = MockToolkit()")
print("      with pytest.raises(AdapterNotFoundError):")
print("          toolkit.run(UnsupportedAgent(), 'test')")


# ─────────────────────────────────────────────────────────────────────────────
# Why error handling matters
# ─────────────────────────────────────────────────────────────────────────────
print_section("Why This Matters")
print("  ✓ Clear feedback when something isn't supported")
print("  ✓ Prevents silent failures or cryptic errors")
print("  ✓ Guides developers to the right solution")
print("  ✓ Tests can gracefully skip or fail with context")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{GREEN}✓ Scenario 5 complete!{RESET}")
print("  This example showed how to:")
print("    1. Handle AdapterNotFoundError with try/except")
print("    2. Interpret error messages")
print("    3. Use pytest.raises() to test for exceptions")
print("    4. Understand framework support status")
print("    5. Plan fallback strategies")
print()
