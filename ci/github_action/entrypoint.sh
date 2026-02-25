#!/usr/bin/env bash
# TrajAI GitHub Action entrypoint script.
# Usage: entrypoint.sh [test-path] [budget] [model-override] [junit-xml] [extra-args]
set -euo pipefail

TEST_PATH="${1:-}"
BUDGET="${2:-}"
MODEL_OVERRIDE="${3:-}"
JUNIT_XML="${4:-test-results/trajai.xml}"
EXTRA_ARGS="${5:-}"

# Build the trajai test command
CMD="trajai test"

if [ -n "$TEST_PATH" ]; then
    CMD="$CMD $TEST_PATH"
fi

if [ -n "$BUDGET" ]; then
    CMD="$CMD --budget $BUDGET"
fi

if [ -n "$MODEL_OVERRIDE" ]; then
    CMD="$CMD --model $MODEL_OVERRIDE"
fi

CMD="$CMD --xml $JUNIT_XML"

if [ -n "$EXTRA_ARGS" ]; then
    CMD="$CMD $EXTRA_ARGS"
fi

echo "[TrajAI] Running: $CMD"
set +e
eval "$CMD"
EXIT_CODE=$?
set -e

# Parse JUnit XML to extract pass/fail counts and total cost for action outputs
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COST="0.0000"

if [ -f "$JUNIT_XML" ]; then
    # Extract tests, failures, errors counts using Python (available since we installed trajai)
    COUNTS=$(python3 - <<'PYEOF'
import sys
import xml.etree.ElementTree as ET
import os

xml_path = os.environ.get("TRAJAI_JUNIT_XML", "test-results/trajai.xml")
try:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    suites = []
    if root.tag == "testsuites":
        suites = list(root)
    elif root.tag == "testsuite":
        suites = [root]

    total = 0
    failures = 0
    errors = 0
    total_cost = 0.0

    for suite in suites:
        for testcase in suite.iter("testcase"):
            total += 1
            if testcase.find("failure") is not None or testcase.find("error") is not None:
                failures += 1
            # Extract cost from properties
            for prop in testcase.iter("property"):
                if prop.get("name") == "trajai_cost":
                    try:
                        total_cost += float(str(prop.get("value", "0")).lstrip("$"))
                    except (ValueError, AttributeError):
                        pass

    passed = total - failures
    print(f"pass={passed}")
    print(f"fail={failures}")
    print(f"cost={total_cost:.4f}")
except Exception as e:
    print(f"pass=0")
    print(f"fail=0")
    print(f"cost=0.0000")
PYEOF
)

    PASS_COUNT=$(echo "$COUNTS" | grep "^pass=" | cut -d= -f2)
    FAIL_COUNT=$(echo "$COUNTS" | grep "^fail=" | cut -d= -f2)
    TOTAL_COST=$(echo "$COUNTS" | grep "^cost=" | cut -d= -f2)
fi

# Set GitHub Actions outputs
if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "pass-count=${PASS_COUNT}" >> "$GITHUB_OUTPUT"
    echo "fail-count=${FAIL_COUNT}" >> "$GITHUB_OUTPUT"
    echo "total-cost=${TOTAL_COST}" >> "$GITHUB_OUTPUT"
fi

echo "[TrajAI] Results: ${PASS_COUNT} passed, ${FAIL_COUNT} failed, cost=\$${TOTAL_COST}"

exit $EXIT_CODE
