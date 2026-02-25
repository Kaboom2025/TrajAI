"""Parse and display JUnit XML results produced by pytest + TrajAI plugin."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List


def display_results(junit_xml_path: str) -> None:
    """Parse JUnit XML and print a formatted results table."""
    path = Path(junit_xml_path)
    if not path.exists():
        print(f"[TrajAI] No results file found at: {junit_xml_path}")
        return

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        print(f"[TrajAI] Failed to parse results file: {exc}")
        return

    root = tree.getroot()

    # Handle both <testsuite> and <testsuites> root elements
    suites: List[ET.Element] = []
    if root.tag == "testsuites":
        suites = list(root)
    elif root.tag == "testsuite":
        suites = [root]
    else:
        print(f"[TrajAI] Unexpected XML root element: {root.tag}")
        return

    print("\n" + "=" * 70)
    print("  TrajAI Test Results")
    print("=" * 70)

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    for suite in suites:
        for testcase in suite.iter("testcase"):
            total_tests += 1
            name = testcase.get("name", "<unknown>")
            classname = testcase.get("classname", "")
            time_str = testcase.get("time", "")
            full_name = f"{classname}.{name}" if classname else name

            # Determine status
            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped = testcase.find("skipped")

            if failure is not None:
                status = "FAIL"
                total_failures += 1
            elif error is not None:
                status = "ERROR"
                total_errors += 1
            elif skipped is not None:
                status = "SKIP"
                total_skipped += 1
            else:
                status = "PASS"

            # Extract TrajAI properties
            props: dict[str, str] = {}
            for prop_elem in testcase.iter("property"):
                prop_name = prop_elem.get("name", "")
                prop_value = prop_elem.get("value", "")
                if prop_name.startswith("trajai_"):
                    props[prop_name[7:]] = prop_value  # strip "trajai_" prefix

            # Format row
            time_part = f" ({time_str}s)" if time_str else ""
            prop_parts: List[str] = []
            if "cost" in props:
                prop_parts.append(f"cost={props['cost']}")
            if "tokens" in props:
                prop_parts.append(f"tokens={props['tokens']}")
            if "pass_rate" in props:
                prop_parts.append(f"pass_rate={props['pass_rate']}")
            prop_str = "  [" + ", ".join(prop_parts) + "]" if prop_parts else ""

            _labels = {
                "PASS": "✓ PASS",
                "FAIL": "✗ FAIL",
                "ERROR": "! ERROR",
                "SKIP": "- SKIP",
            }
            status_label = _labels.get(status, status)
            print(f"  {status_label:10s}  {full_name}{time_part}{prop_str}")

    print("-" * 70)
    passed = total_tests - total_failures - total_errors - total_skipped
    print(
        f"  {total_tests} tests: "
        f"{passed} passed, "
        f"{total_failures} failed, "
        f"{total_errors} errors, "
        f"{total_skipped} skipped"
    )
    print("=" * 70 + "\n")
