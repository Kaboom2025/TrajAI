# Implementation Plan: Statistical Runner

## Phase 1: StatisticalResult Data Model and Failure Mode Grouping
- [x] Task: Define `StatisticalResult` and formatting logic
    - [x] Write tests for `StatisticalResult` summary formatting and failure mode grouping
    - [x] Implement `StatisticalResult` dataclass in `unitai/runner/statistical.py`
    - [x] Implement `summary()` method with exact-match grouping for assertion errors
- [x] Task: Conductor - User Manual Verification 'Phase 1: StatisticalResult Data Model' (Protocol in workflow.md) [checkpoint: Phase 1 Done]

## Phase 2: Core StatisticalRunner (Serial Execution & Cost Tracking Foundation)
- [x] Task: Implement basic `StatisticalRunner` with serial execution and cost accumulation
    - [x] Write tests for deterministic always-pass and always-fail scenarios
    - [x] Write tests for stochastic failure scenarios (e.g., fails 30% of the time)
    - [x] Implement `StatisticalRunner.run()` with `try/except` for `AssertionError` and `TrajAIAssertionError`
    - [x] Implement loop to execute N times, collecting trajectories and accumulating `total_cost` from RunResults
    - [x] Ensure non-assertion exceptions propagate immediately
- [x] Task: Conductor - User Manual Verification 'Phase 2: Core StatisticalRunner' (Protocol in workflow.md) [checkpoint: Phase 2 Done]

## Phase 3: Cost Safety and Budgeting Logic
- [x] Task: Implement Calibration and Budget Enforcement
    - [x] Write tests for cost-based aborts (budget exceeded on first run, estimated total over budget, cumulative cost over budget)
    - [x] Implement calibration check after Run #1 (estimated total calculation and pre-emptive abort)
    - [x] Implement `CostLimitExceeded` exception with helpful error message and `--budget` suggestion
    - [x] Implement mid-run abort logic when cumulative cost exceeds budget during remaining runs
- [x] Task: Conductor - User Manual Verification 'Phase 3: Cost Safety' (Protocol in workflow.md) [checkpoint: Phase 3 Done]

## Phase 4: Parallel Execution
- [x] Task: Implement Parallel Execution via `ThreadPoolExecutor`
    - [x] Write tests verifying execution speed improvements (I/O-bound simulation)
    - [x] Write tests verifying thread isolation (no cross-contamination of `MockToolkit` or `Trajectory`)
    - [x] Implement `ThreadPoolExecutor` logic in `StatisticalRunner.run()`
    - [x] Ensure `max_workers` defaults to `min(n, 5)`
- [x] Task: Conductor - User Manual Verification 'Phase 4: Parallel Execution' (Protocol in workflow.md) [checkpoint: Phase 4 Done]

## Phase 5: @statistical Decorator
- [x] Task: Implement ` @statistical` decorator and parameter injection
    - [x] Write tests for decorator threshold enforcement (pass/fail based on pass rate)
    - [x] Write tests for `mock_toolkit` parameter detection and per-run instantiation
    - [x] Write tests for non-`mock_toolkit` parameter passthrough (ensuring other args/fixtures are untouched)
    - [x] Implement ` @statistical` using `functools.wraps` and `inspect.signature`
    - [x] Implement `TrajAIStatisticalError` for implicit assertions when pass rate < threshold
- [x] Task: Conductor - User Manual Verification 'Phase 5: @statistical Decorator' (Protocol in workflow.md) [checkpoint: Phase 5 Done]
