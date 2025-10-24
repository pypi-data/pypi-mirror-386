from typing import Callable, TypeVar

T = TypeVar("T")

def setup(fn: Callable[[], T]) -> T:
    """Marker for an operation that creates the state required for a test."""
    try:
        return fn()
    except Exception as e:
        message =\
            "Setup function failed: " +\
            f"{str(fn.__name__)} raises error -> "+\
            f"{e.__class__.__name__}: {e}"
        assert False, message

def invariant(fn: Callable[[], bool]) -> None:
    """Marker for an operation that checks an invariant condition."""
    try:
        fullfill = fn()
    except Exception as e:
        message =\
            "Invariant condition checker failed: " +\
            f"{str(fn.__name__)} raises error -> "+\
            f"{e.__class__.__name__}: {e}"
        assert False, message
    
    if not fullfill:
        assert False, "Invariant condition not established."

def before(fn: Callable[[], bool]) -> None:
    """Marker for an operation that checks a precondition."""
    try:
        fullfill = fn()
    except Exception as e:
        message =\
            "Before condition checker failed: " +\
            f"{str(fn.__name__)} raises error -> "+\
            f"{e.__class__.__name__}: {e}"
        assert False, message
    
    if not fullfill:
        assert False, "Before condition not established."

def after(fn: Callable[[], bool]) -> None:
    """Marker for an operation that checks a postcondition."""
    try:
        fullfill = fn()
    except Exception as e:
        message =\
            "After condition checker failed: " +\
            f"{str(fn.__name__)} raises error -> "+\
            f"{e.__class__.__name__}: {e}"
        assert False, message
    
    if not fullfill:
        assert False, "After condition not established."

