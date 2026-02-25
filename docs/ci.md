# CI Integration Guide

TrajAI integrates with any CI system that can run pytest and process JUnit XML reports.

---

## GitHub Actions (Recommended)

Use the official TrajAI composite action for zero-config setup.

### Quick Start

```yaml
# .github/workflows/trajai.yml
name: Agent Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  agent-tests:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Run TrajAI Tests
        uses: trajai/trajai-action@v1   # or path: ./ci/github_action
        with:
          python-version: "3.12"
          junit-xml: test-results/trajai.xml
```

### With LangGraph and Budget Control

```yaml
      - name: Run TrajAI Tests
        uses: trajai/trajai-action@v1
        with:
          python-version: "3.12"
          install-extras: "langgraph"
          budget: "2.00"            # abort if per-test cost exceeds $2.00
          extra-args: "--n 10 --threshold 0.9"
          junit-xml: test-results/trajai.xml
```

### Using Action Outputs

```yaml
      - name: Run TrajAI Tests
        id: trajai
        uses: trajai/trajai-action@v1
        with:
          python-version: "3.12"

      - name: Report results
        run: |
          echo "Passed: ${{ steps.trajai.outputs.pass-count }}"
          echo "Failed: ${{ steps.trajai.outputs.fail-count }}"
          echo "Cost:   \$${{ steps.trajai.outputs.total-cost }}"
```

### GitHub Actions Step Summary

When running in GitHub Actions, TrajAI automatically writes a Markdown cost summary
to the job summary (visible in the **Summary** tab of each workflow run):

| Test | Status | Cost | Pass Rate |
|------|--------|------|-----------|
| `test_order_refund` | ✅ PASS | $0.0023 | — |
| `test_weather_lookup` | ✅ PASS | $0.0018 | — |

**Total LLM cost:** $0.0041

This summary is produced by the pytest plugin and written to `$GITHUB_STEP_SUMMARY`
automatically — no extra configuration needed.

### Manual Setup (Without the Composite Action)

If you prefer to manage the steps yourself:

```yaml
name: Agent Tests

on: [push, pull_request]

jobs:
  agent-tests:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install trajai[langgraph]
          pip install -r requirements.txt   # your project deps

      - name: Run tests
        run: trajai test --xml test-results/trajai.xml

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: trajai-test-results
          path: test-results/trajai.xml
```

---

## GitLab CI

```yaml
# .gitlab-ci.yml
agent-tests:
  image: python:3.12
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY   # set in GitLab CI/CD Settings → Variables
  script:
    - pip install trajai[langgraph]
    - pip install -r requirements.txt
    - trajai test --xml test-results/trajai.xml
  artifacts:
    when: always
    reports:
      junit: test-results/trajai.xml
    paths:
      - test-results/
    expire_in: 7 days
  # Optional: only run on merge requests and main branch
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

GitLab natively renders JUnit XML from the `reports: junit` key — test results appear
directly in the merge request UI.

### With statistical runner and budget:

```yaml
agent-tests:
  image: python:3.12
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
    TRAJAI_DEFAULT_N: "5"
    TRAJAI_DEFAULT_THRESHOLD: "0.9"
    TRAJAI_COST_BUDGET_PER_TEST: "1.00"
  script:
    - pip install trajai[langgraph]
    - trajai test --xml test-results/trajai.xml
  artifacts:
    reports:
      junit: test-results/trajai.xml
```

---

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  agent-tests:
    docker:
      - image: cimg/python:3.12
    environment:
      OPENAI_API_KEY: $OPENAI_API_KEY   # set in CircleCI Project Settings → Environment Variables
    steps:
      - checkout

      - run:
          name: Install TrajAI
          command: |
            pip install trajai[langgraph]
            pip install -r requirements.txt

      - run:
          name: Run agent tests
          command: |
            mkdir -p test-results
            trajai test --xml test-results/trajai.xml

      - store_test_results:
          path: test-results

      - store_artifacts:
          path: test-results
          destination: trajai-results

workflows:
  main:
    jobs:
      - agent-tests
```

CircleCI reads JUnit XML from `store_test_results` and displays pass/fail status,
duration, and flaky test detection in the **Tests** tab of each pipeline run.

---

## Generic CI (Any System)

For any CI system that runs shell commands:

```bash
# Install
pip install trajai

# Run tests and produce JUnit XML
trajai test --xml test-results/trajai.xml

# The exit code is non-zero if tests fail — standard CI behavior
```

TrajAI tests are standard pytest tests. Any CI integration that:
1. Runs `pytest` or `trajai test`
2. Reads JUnit XML (optional, for rich reporting)

...works out of the box.

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TRAJAI_DEFAULT_N` | Statistical runner: runs per test | `10` |
| `TRAJAI_DEFAULT_THRESHOLD` | Statistical runner: required pass rate | `0.9` |
| `TRAJAI_COST_BUDGET_PER_TEST` | Abort if per-test cost exceeds this | `1.00` |
| `TRAJAI_CACHE_ENABLED` | Enable LLM response cache | `true` |
| `TRAJAI_CACHE_MODE` | Cache mode: `auto`, `record`, `replay` | `replay` |
| `TRAJAI_JUNIT_XML` | JUnit XML output path | `test-results/trajai.xml` |

### Caching LLM Responses

For fast, deterministic CI runs (no real LLM calls needed):

```bash
# First run: record LLM responses
trajai test --record --xml test-results/trajai.xml

# Commit .trajai/cache/ to your repo (or save as CI artifact)

# Subsequent runs: replay from cache (fast, free)
trajai test --replay --xml test-results/trajai.xml
```

---

## Secrets Management

Never hardcode API keys. Use your CI platform's secret management:

| Platform | How to set secrets |
|----------|-------------------|
| GitHub Actions | Settings → Secrets and variables → Actions |
| GitLab CI | Settings → CI/CD → Variables |
| CircleCI | Project Settings → Environment Variables |

Then reference them in your CI config:
- GitHub: `${{ secrets.OPENAI_API_KEY }}`
- GitLab: `$OPENAI_API_KEY`
- CircleCI: `$OPENAI_API_KEY`
