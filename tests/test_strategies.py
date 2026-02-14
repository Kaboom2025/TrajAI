import pytest
from unitai.mock.strategies import (
    StaticStrategy,
    SequenceStrategy,
    ConditionalStrategy,
    ErrorStrategy,
    CallableStrategy,
    MockExhaustedError,
    NoMatchingConditionError
)

def test_static_strategy() -> None:
    strategy = StaticStrategy(value="static-val")
    assert strategy.execute({}) == "static-val"
    assert strategy.execute({"any": "args"}) == "static-val"

def test_sequence_strategy() -> None:
    strategy = SequenceStrategy(values=["a", "b"])
    assert strategy.execute({}) == "a"
    assert strategy.execute({}) == "b"
    with pytest.raises(MockExhaustedError, match="exhausted after 2 calls"):
        strategy.execute({})

def test_conditional_strategy() -> None:
    conditions = {
        lambda args: args.get("q") == "1": "one",
        lambda args: args.get("q") == "2": "two"
    }
    strategy = ConditionalStrategy(conditions=conditions)
    assert strategy.execute({"q": "1"}) == "one"
    assert strategy.execute({"q": "2"}) == "two"
    with pytest.raises(NoMatchingConditionError):
        strategy.execute({"q": "3"})

def test_error_strategy() -> None:
    strategy = ErrorStrategy(exception=ValueError("oops"))
    with pytest.raises(ValueError, match="oops"):
        strategy.execute({})

def test_callable_strategy() -> None:
    def my_fn(args):
        return args["x"] * 2
    
    strategy = CallableStrategy(fn=my_fn)
    assert strategy.execute({"x": 5}) == 10
