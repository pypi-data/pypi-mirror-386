"""Partial support library for structured testing.

Dependencies:
    Currently, this library supports only pytest as its underlying test framework.  
    Pytest-dependent components are defined in ``speclike.pytest``.

    The markers themselves are framework-independent and can be imported
    directly from ``speclike``.

This library is not intended for contract testing, but it borrows and adapts
some of its core concepts.


0: Motivation and Use Case

While structuring tests using diamond inheritance, I found it useful to have
a mechanism for defining and executing test cases *without* relying on inheritance.  
This library was created to support that workflow.

Example:

    from speclike import after
    from speclike.pytest import TestDispatcher

    class TestBase(TestDispatcher):
        # This implementation is equivalent to the default one,
        # but shown here for explanation purposes.
        def dispatch(self, method_name: str, method: Callable) -> None:
            # Customize how arguments are passed to the test method.
            method()
            
        ...  # Omitted for brevity

    # These classes are reusable base test cases (unrelated to this library).
    class TestEnableUndefinedKey(TestBase):
        def test_method_can_handle_undefined_key(self):
            obj = self.create_with_defaults()
            ukey = self.UNDEFINED_KEY1
            self.case_for_handling_undefined_key(obj, ukey)
        
        @abstractmethod
        def case_for_handling_undefined_key(self, obj, undefined_key: str):
            ...

    class TestRefuseUndefinedKey(TestBase):
        def test_raises_UndefinedError(self):
            obj = self.create_with_defaults()
            ukey = self.UNDEFINED_KEY1
            with pytest.raises(UndefinedError):
                self.case_UndefinedError_with_undefined_key(obj, ukey)
        
        @abstractmethod
        def case_UndefinedError_with_undefined_key(self, obj, undefined_key: str):
            ...
    
    ...  # Other test cases omitted for clarity

    class TestInstantiation(
        TestEnableUndefinedKey,
        TestRefuseInvalidKey,
        TestAcceptValidKey,
        TestAcceptNoneAsValue,
    ):
        # The functionality provided by this library automatically executes
        # the following as pytest test cases.
        # These methods are not inherited from any of the above base classes.
        @case
        def happy_path_with_not_none_value(self):
            obj = Message({"key": "value"})

            after(lambda: isinstance(obj, Message))
            after(lambda: obj.exists("key"))
            after(lambda: obj.initialized_unsafe("key"))
            after(lambda: not obj.consumed_unsafe("key"))

        @case
        def happy_path_with_none_value(self):
            obj = Message({"key": None})

            after(lambda: isinstance(obj, Message))
            after(lambda: obj.exists("key"))
            after(lambda: not obj.initialized_unsafe("key"))
            after(lambda: not obj.consumed_unsafe("key"))

        # The following are ordinary test cases, not related to this library.
        def case_for_handling_undefined_key(self, obj, undefined_key):
            Message({undefined_key: 0})

        def case_KeyTypeError_with_invalid_key(self, obj: Message, invalid_key):
            Message({invalid_key: 0})

        def case_accepts_key_as_str_enumsub_enum_member(self, obj: Message, valid_key):
            Message({valid_key: 0})
        
        def case_accepts_none_as_value(self, obj: Message, none):
            Message({"key": none})


1: Markers

Based on the concept of contract testing, this library provides the following markers:
    - setup: for initialization
    - invariant: for invariants
    - before: for preconditions
    - after: for postconditions

These markers make it possible to express the *intent* of each operation
within a test case. Each marker raises an AssertionError when the
lambda expression raises an exception or evaluates to False,
immediately stopping the test at that point.

Example:

    from speclike import setup, invariant, before, after

    class Calculator:
        def __init__(self):
            self.value = 0

        def add(self, n: int):
            if not isinstance(n, int):
                raise TypeError("n must be int")
            self.value += n

    def test_happy_path_add():
        calc = setup(lambda: Calculator())
        before(lambda: calc.value == 0)

        calc.add(10)

        invariant(lambda: isinstance(calc.value, int))
        after(lambda: calc.value == 10)

Note:
    Logical contradictions—such as calling ``after`` before ``before``—are not detected.
    Each marker is simply a lightweight assertion wrapper.


2: TestDispatcher (currently pytest only: speclike.pytest.TestDispatcher)

This class automatically generates pytest-recognized test methods
(named ``test_<method-name>``) from methods marked with the ``@case`` decorator.

By using this mechanism, you can define and execute test cases that are specific
to the target’s intended "happy path" behavior—those that don’t need to be
reused across other test modules.

Example:

    from speclike import setup, before, after
    from speclike.pytest import TestDispatcher, case

    class Message:
        # Target under test: Example message API

        def define(self, key: str, typ: type, init):
            if not isinstance(key, str):
                raise TypeError("key must be str")
            if not isinstance(init, (typ, type(None))):
                raise TypeError(f"init must be {typ.__name__} or None")
            return True

    class TestMessage(TestDispatcher):
        # Happy-path tests for each method of the Message class
        @case
        def happy_path_define_with_int(self):
            # Happy path: define() with an int value
            msg = setup(lambda: Message())

            before(lambda: True)  # Precondition (no specific restriction in this case)
            result = msg.define("id", int, 0)
            after(lambda: result is True)

        @case
        def happy_path_define_with_none(self):
            # Happy path: define() with None as the initial value
            msg = setup(lambda: Message())

            before(lambda: True)
            result = msg.define("name", str, None)
            after(lambda: result is True)

Note:
    The test abstraction provided by the ``@case`` decorator is similar to
    ``pytest.mark.customtest``.  
    However, the invocation style of the test methods would otherwise require
    customizing pytest’s hook mechanism, which is relatively complex.  
    Instead, ``@case`` allows you to simply override
    :meth:`TestDispatcher.dispatch` to modify the invocation behavior.
"""
from speclike.mark import setup, invariant, before, after
from speclike.dispatch import TestDispatcher, TestCase, case

__all__ = [
    "setup", "invariant", "before", "after",
    "TestDispatcher", "TestCase", "case",
]

