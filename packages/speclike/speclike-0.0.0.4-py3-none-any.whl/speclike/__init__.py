"""Partial support library for structured testing

Dependencies:
    Currently, the only supported testing framework is pytest.
    The pytest-dependent components are defined in `speclike.pytest`.

```
The markers are framework-independent and can be imported directly from `speclike`.
```

This library is not intended for contract testing, but it borrows some of its concepts.

0: Motivation and Use Case

While experimenting with structuring tests using diamond inheritance, 
I found it useful to create test case definitions and executions without relying on inheritance.
This library was created to support that approach.

```
from speclike import after
from speclike.pytest import TestDispatcher

class TestBase(TestDispatcher):
    # This is equivalent to the default implementation, but shown here for clarity.
    def dispatched(self, method_name: str) -> bool:
        # You can customize which methods should be executed.
        return method_name.startswith("case_happy_path")

    # Same as above
    def dispatch(self, method_name: str, method: Callable) -> None:
        # You can customize how methods are invoked (e.g., passing arguments)
        method()
        
    ... # Other details omitted

# Example of a reusable individual test case (unrelated to this library itself)
class TestEnableUndefinedKey(TestBase):
    def test_method_can_handle_undefined_key(self):
        obj = self.create_with_defaults()
        ukey = self.UNDEFINED_KEY1
        self.case_for_handling_undefined_key(obj, ukey)
    
    @abstractmethod
    def case_for_handling_undefined_key(self, obj, undefined_key: str):
        ...

# Same as above
class TestRefuseUndefinedKey(TestBase):
    def test_raises_UndefinedError(self):
        obj = self.create_with_defaults()
        ukey = self.UNDEFINED_KEY1
        with pytest.raises(UndefinedError):
            self.case_UndefinedError_with_undefined_key(obj, ukey)
    
    @abstractmethod
    def case_UndefinedError_with_undefined_key(self, obj, undefined_key: str):
        ...

... # Remaining test cases omitted

class TestInstantiation(
    TestEnableUndefinedKey,
    TestRefuseInvalidKey,
    TestAcceptValidKey,
    TestAcceptNoneAsValue,
):
    # The following part can be automatically executed using this library.
    # It is not inherited from any of the above test cases.
    def case_happy_path_with_not_none_value(self):
        
        obj = Message({"key": "value"})

        after(lambda: isinstance(obj, Message))
        after(lambda: obj.exists("key"))
        after(lambda: obj.initialized_unsafe("key"))
        after(lambda: not obj.consumed_unsafe("key"))

    # Same as above
    def case_happy_path_with_none_value(self):

        obj = Message({"key": None})

        after(lambda: isinstance(obj, Message))
        after(lambda: obj.exists("key"))
        after(lambda: not obj.initialized_unsafe("key"))
        after(lambda: not obj.consumed_unsafe("key"))

    # The following are individual test cases, not related to this library’s functionality.
    def case_for_handling_undefined_key(self, obj, undefined_key):
        Message({undefined_key: 0})

    def case_KeyTypeError_with_invalid_key(self, obj: Message, invalid_key):
        Message({invalid_key: 0})

    def case_accepts_key_as_str_enumsub_enum_member(self, obj: Message, valid_key):
        Message({valid_key: 0})
    
    def case_accepts_none_as_value(self, obj: Message, none):
        Message({"key": none})
```

1: Markers

Based on the concept of contract testing, the following markers are provided:
- setup: Setup phase
- invariant: Invariant condition
- before: Precondition
- after: Postcondition

These markers allow you to express the purpose of each step in your tests directly in the code.
Each marker raises an AssertionError when its condition fails (either through an exception or a False result),
which will terminate the test at that point.

Example:

```
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
```

Note:
Logical inconsistencies (e.g., calling `after` before `before`) are not detected.
Each marker is simply an assertion wrapper.

2: TestDispatcher (currently for pytest only: speclike.pytest.TestDispatcher)

By inheriting from this class, you can define any number of test methods whose execution is controlled
by the `.dispatched()` method.
This allows you to define and execute context-specific test cases such as happy-path tests
without needing to make them reusable across tests. See the example below.

```
from speclike import setup, before, after
from speclike.pytest import TestDispatcher

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

    def case_happy_path_define_with_int(self):
        # Happy path: define() with an int value
        msg = setup(lambda: Message())

        before(lambda: True)  # Precondition (no specific restriction in this case)
        result = msg.define("id", int, 0)
        after(lambda: result is True)

    def case_happy_path_define_with_none(self):
        # Happy path: define() with None as the initial value
        msg = setup(lambda: Message())

        before(lambda: True)
        result = msg.define("name", str, None)
        after(lambda: result is True)
```

"""


from speclike.marker import setup, invariant, before, after

__all__ = ("setup", "invariant", "before", "after")

