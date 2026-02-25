# Specification: Statistical Runner

## Overview
The Statistical Runner is the core execution layer of UnitAI designed to handle the inherent non-determinism of LLM-based agents. It allows developers to execute a test function multiple times and assert on a success threshold (pass rate), providing aggregated failure reports and cost-safety guards.

## Functional Requirements

### 1. StatisticalRunner Class
- **Constructor:** `StatisticalRunner(n=10, threshold=0.95, max_workers=5, budget=5.00)`
- **Core Method:** `run(test_fn, *args, **kwargs) -> StatisticalResult`
    - Executes `test_fn` N times.
    - Each execution is wrapped in a `try/except` block to capture `AssertionError` and `TrajAIAssertionError`.
    - Other exceptions (e.g., `TypeError`, `ConnectionError`) should propagate immediately and halt execution.
    - Collects trajectories and results from every run.
    - Uses `concurrent.futures.ThreadPoolExecutor` for parallel execution.

### 2. Parallel Execution & State Management
- `max_workers` defaults to `min(n, 5)` to prevent overwhelming LLM APIs.
- **Isolation:** Each thread must receive its own `MockToolkit` instance to prevent state contamination between parallel runs.

### 3. Cost Safety Protocol
- **Calibration Run:** Run #1 of N is executed serially first.
- **Pre-emptive Check:** After Run #1, calculate `estimated_total = first_run_cost * N`.
- **Strict Abort:** If `estimated_total > budget`, raise `CostLimitExceeded` with a helpful message including the required `--budget` flag to allow the run.
- **Mid-run Tracking:** Continuously track cumulative cost during the remaining N-1 runs and abort if the budget is exceeded.

### 4. Failure Mode Grouping
- Group failures based on **exact match** of the assertion error message.
- Reporting should include the count of occurrences for each unique failure message.

### 5. `@statistical` Decorator
- Transforms a standard test function into a statistical test.
- Automatically handles the instantiation and execution of the `StatisticalRunner`.
- **Parameter Detection:** The decorator inspects the wrapped function's signature (via `inspect.signature`). If it contains a `mock_toolkit` parameter, the decorator MUST instantiate a fresh `MockToolkit()` for each of the N runs and pass it as that argument.
- **Implicit Assertion:** Fails the test (raises `TrajAIStatisticalError`) if the pass rate is below the `threshold`.
- Integrates with `pytest` by providing a structured failure summary in the output.

## Non-Functional Requirements
- **Standard Library Only:** Implementation must not introduce new required dependencies.
- **Thread Safety:** Ensure trajectory collection and mock state are isolated per thread.

## Acceptance Criteria
- [ ] `StatisticalRunner.run()` executes exactly N times and returns a `StatisticalResult`.
- [ ] Pass rate is calculated correctly for both deterministic and stochastic test functions.
- [ ] Cost safety aborts execution BEFORE the budget is heavily exceeded, using the first run as a calibration.
- [ ] Parallel execution completes significantly faster than serial execution for I/O-bound tests.
- [ ] The `@statistical` decorator successfully fails a test when the threshold is not met and passes otherwise.
- [ ] The decorator correctly identifies and injects fresh `MockToolkit` instances for each run when the `mock_toolkit` parameter is present.
- [ ] Failure modes are grouped by exact message match in the summary output.

## Out of Scope
- Support for `ProcessPoolExecutor` or other non-thread-based parallelization.
- Advanced failure normalization or "fuzzy" grouping of error messages.
- Persistent caching of statistical results (to be handled in a later phase).
