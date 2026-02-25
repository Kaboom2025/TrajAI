import time
import pytest
from trajai.runner.statistical import StatisticalRunner
from trajai.mock.toolkit import MockToolkit

def test_parallel_execution_speed():
    """Test that parallel execution is faster than serial for I/O bound tasks."""
    def test_fn():
        time.sleep(0.1)
        
    # Serial: 1 + 9 runs * 0.1s = 1.0s
    # Parallel (max_workers=5): 
    # Run 1 (serial): 0.1s
    # Remaining 9 runs in batches of 5: ~2 batches * 0.1s = 0.2s
    # Total: ~0.3s
    
    runner = StatisticalRunner(n=10, max_workers=5)
    
    start = time.time()
    runner.run(test_fn)
    duration = time.time() - start
    
    # It should definitely be faster than 0.7s (generous threshold)
    assert duration < 0.7

def test_thread_isolation():
    """Test that parallel runs do not share MockToolkit state."""
    toolkits = []
    import threading
    lock = threading.Lock()
    
    def test_fn(mock_toolkit: MockToolkit):
        # Verify this toolkit is fresh
        assert len(mock_toolkit._recorded_llm_calls) == 0
        
        with lock:
            toolkits.append(mock_toolkit)
            
        mock_toolkit.record_llm_call(model="test", cost=0.01)
        
        # Verify this toolkit only has ONE call
        assert len(mock_toolkit._recorded_llm_calls) == 1
        
    runner = StatisticalRunner(n=10, max_workers=5)
    runner.run(test_fn)
    
    # Should have seen 10 unique toolkit instances
    assert len(toolkits) == 10
    assert len(set(id(t) for t in toolkits)) == 10

def test_parallel_failure_collection():
    """Test that failures from parallel runs are correctly collected and grouped."""
    def test_fn():
        # Fail 50% of the time with different messages
        import threading
        tid = threading.get_ident()
        if tid % 2 == 0:
            assert False, "Even TID failure"
        else:
            assert True
            
    # We can't guarantee TID distribution, so let's use a counter
    from dataclasses import dataclass
    @dataclass
    class Counter:
        val: int = 0
        import threading
        lock = threading.Lock()
        def inc(self):
            with self.lock:
                self.val += 1
                return self.val
                
    c = Counter()
    def test_fn_deterministic_split():
        val = c.inc()
        if val <= 5:
            assert False, "First five fail"
            
    runner = StatisticalRunner(n=10, max_workers=5)
    result = runner.run(test_fn_deterministic_split)
    
    assert result.failed_runs == 5
    assert result.failure_modes == {"AssertionError: First five fail": 5}
