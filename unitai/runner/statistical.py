import inspect
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type
from unitai.core.assertions import UnitAIAssertionError
from unitai.mock.toolkit import MockToolkit

class CostLimitExceeded(Exception):
    """Raised when the LLM API cost exceeds the configured budget."""
    pass

class UnitAIStatisticalError(AssertionError):
    """Raised when a statistical test fails to meet the pass rate threshold."""
    pass

@dataclass
class StatisticalResult:
    total_runs: int
    passed_runs: int
    failed_runs: int
    total_cost: float
    failure_modes: Dict[str, int] = field(default_factory=dict)
    
    @property
    def pass_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.passed_runs / self.total_runs
    
    def summary(self) -> str:
        lines = []
        lines.append(f"Statistical Result: {self.passed_runs}/{self.total_runs} passed ({self.pass_rate*100:.1f}%)")
        lines.append(f"Total Cost: ${self.total_cost:.4f}")
        
        if self.failure_modes:
            lines.append("Failure Modes:")
            for error_msg, count in self.failure_modes.items():
                lines.append(f"  {count}x — {error_msg}")
                
        return "\n".join(lines)

class StatisticalRunner:
    def __init__(
        self, 
        n: int = 10, 
        threshold: float = 0.95, 
        max_workers: Optional[int] = None, 
        budget: float = 5.00
    ):
        self.n = n
        self.threshold = threshold
        self.max_workers = max_workers if max_workers is not None else min(n, 5)
        self.budget = budget
        self._stop_event = threading.Event()

    def _execute_run(
        self, 
        test_fn: Callable[..., Any], 
        args: Any, 
        kwargs: Any, 
        has_mock_toolkit: bool
    ) -> Optional[tuple[bool, float, Optional[str]]]:
        if self._stop_event.is_set():
            return None
            
        run_kwargs = kwargs.copy()
        toolkit = None
        if has_mock_toolkit:
            toolkit = MockToolkit()
            run_kwargs["mock_toolkit"] = toolkit
        
        passed = False
        error_msg = None
        try:
            test_fn(*args, **run_kwargs)
            passed = True
        except (AssertionError, UnitAIAssertionError) as e:
            error_msg = f"{type(e).__name__}: {str(e).splitlines()[0]}"
        except Exception:
            self._stop_event.set()
            raise
        
        run_cost = 0.0
        if toolkit:
            run_cost = sum(call.cost or 0.0 for call in toolkit._recorded_llm_calls)
            
        return passed, run_cost, error_msg

    def run(self, test_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> StatisticalResult:
        self._stop_event.clear()
        passed_runs = 0
        failed_runs = 0
        total_cost = 0.0
        failure_modes: Dict[str, int] = {}
        
        sig = inspect.signature(test_fn)
        has_mock_toolkit = "mock_toolkit" in sig.parameters

        # Run 1: Calibration Run (always serial)
        result = self._execute_run(test_fn, args, kwargs, has_mock_toolkit)
        if result is None: # Should not happen for Run 1
             return StatisticalResult(0, 0, 0, 0.0)
             
        passed, run_cost, error_msg = result
        
        total_cost += run_cost
        if passed:
            passed_runs += 1
        else:
            failed_runs += 1
            if error_msg:
                failure_modes[error_msg] = failure_modes.get(error_msg, 0) + 1
        
        # Calibration check
        estimated_total = run_cost * self.n
        if estimated_total > self.budget:
            self._stop_event.set()
            raise CostLimitExceeded(
                f"First run cost ${run_cost:.4f}. "
                f"Estimated total for {self.n} runs: ${estimated_total:.4f}. "
                f"Budget: ${self.budget:.2f}. "
                f"Run with --budget={estimated_total:.2f} to allow this."
            )

        if self.n > 1:
            # Remaining runs in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._execute_run, test_fn, args, kwargs, has_mock_toolkit) 
                    for _ in range(self.n - 1)
                ]
                
                try:
                    for future in as_completed(futures):
                        # If a thread set the stop event due to unhandled exception, 
                        # future.result() will raise it here.
                        res = future.result()
                        if res is None:
                            continue
                            
                        passed, run_cost, error_msg = res
                        total_cost += run_cost
                        
                        if total_cost > self.budget:
                            self._stop_event.set()
                            for f in futures:
                                f.cancel()
                            raise CostLimitExceeded(
                                f"Budget exceeded mid-run. Cumulative cost: ${total_cost:.4f}. "
                                f"Budget: ${self.budget:.2f}."
                            )

                        if passed:
                            passed_runs += 1
                        else:
                            failed_runs += 1
                            if error_msg:
                                failure_modes[error_msg] = failure_modes.get(error_msg, 0) + 1
                except Exception:
                    self._stop_event.set()
                    for f in futures:
                        f.cancel()
                    raise

        return StatisticalResult(
            total_runs=self.n,
            passed_runs=passed_runs,
            failed_runs=failed_runs,
            total_cost=total_cost,
            failure_modes=failure_modes
        )

def statistical(
    n: int = 10, 
    threshold: float = 0.95, 
    max_workers: Optional[int] = None, 
    budget: float = 5.00
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to run a test function multiple times and assert on pass rate."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> StatisticalResult:
            runner = StatisticalRunner(
                n=n, 
                threshold=threshold, 
                max_workers=max_workers, 
                budget=budget
            )
            result = runner.run(func, *args, **kwargs)
            
            if result.pass_rate < threshold:
                raise UnitAIStatisticalError(
                    f"Statistical failure: {result.passed_runs}/{result.total_runs} passed "
                    f"({result.pass_rate*100:.1f}%) — required: {threshold*100:.1f}%\n\n"
                    f"{result.summary()}"
                )
            return result
        return wrapper
    return decorator
