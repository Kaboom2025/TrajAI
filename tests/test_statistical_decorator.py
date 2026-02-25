import pytest
from trajai.runner.statistical import statistical, TrajAIStatisticalError
from trajai.mock.toolkit import MockToolkit

def test_decorator_basic_pass():
    """Test that decorator passes when threshold is met."""
    @statistical(n=5, threshold=0.8)
    def test_fn():
        assert True
        
    # Should not raise
    test_fn()

def test_decorator_basic_fail():
    """Test that decorator fails when threshold is not met."""
    @statistical(n=5, threshold=0.8)
    def test_fn():
        # Fail 40% of the time (2/5) -> 60% pass rate < 80%
        state = getattr(test_fn, "_state", 0)
        state += 1
        setattr(test_fn, "_state", state)
        if state <= 2:
            assert False, "Forced failure"
            
    with pytest.raises(TrajAIStatisticalError) as excinfo:
        test_fn()
        
    assert "3/5 passed (60.0%)" in str(excinfo.value)
    assert "required: 80.0%" in str(excinfo.value)

def test_decorator_with_mock_toolkit():
    """Test that decorator injects mock_toolkit correctly."""
    @statistical(n=3)
    def test_fn(mock_toolkit: MockToolkit):
        assert isinstance(mock_toolkit, MockToolkit)
        mock_toolkit.record_llm_call(model="test", cost=0.01)
        
    test_fn()

def test_decorator_with_other_args():
    """Test that decorator passes through other arguments."""
    @statistical(n=2)
    def test_fn(other_arg, mock_toolkit: MockToolkit = None):
        assert other_arg == "hello"
        assert isinstance(mock_toolkit, MockToolkit)
        
    test_fn("hello")

def test_decorator_no_mock_toolkit_but_args():
    """Test decorator on function with args but no mock_toolkit."""
    @statistical(n=2)
    def test_fn(val):
        assert val == 42
        
    test_fn(42)
