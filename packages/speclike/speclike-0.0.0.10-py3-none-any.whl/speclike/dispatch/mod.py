from __future__ import annotations

from abc import ABC, ABCMeta
from typing import Any, Callable

import pytest
import inspect

_MARK_FOR_DISPATCHING = "_speclike_dispatch"

_TEST_PREFIX = "test_"

def case(method):
    """Method decorator to mark a function to be executed as a test.

    Methods marked with this decorator are recognized and executed as tests.  
    The generated test name will appear as ``test_<method-name>``.

    Unlike ``pytest.mark.customtest``, this decorator allows the invocation
    signature of the test method to be customized not through pytest hooks,
    but by overriding :meth:`TestDispatcher.dispatch` or
    :meth:`TestDispatcher.dispatch_async`.

    Raises:
        TypeError: If the method name starts with ``test`` or ``_test``.  
        TypeError: If the method name is not a valid Python identifier.
    """
    method_name = str(method.__name__)
    if not method_name.isidentifier():
        raise TypeError(
            f"Method name must be valid python identifier." +
            f"but recieves -> {method_name}"
        )
    if method_name.startswith("test") or method_name.startswith("_test"):
        raise TypeError(
            f"Method name must not start \"test\" or \"_test\"." +
            f"but recieves -> {method_name}"
        )
    setattr(method, _MARK_FOR_DISPATCHING, 0)
    return method


class _DispatcherMeta(ABCMeta):

    _CASE_ACT_CACHE: dict[type[TestCase], set[Callable]] = {}

    def __new__(mcls, name, bases, namespace: dict[str, Any]):
        bridges = {}
        for k, v in namespace.items():
            if callable(v):
                is_act = False
                for case_type, acts in mcls._CASE_ACT_CACHE.items():
                    if v in acts:
                        casename, test, pymark = case_type.get_case_unit()
                        test_name = _TEST_PREFIX + casename
                        bridges[test_name] = mcls._make_act_bridge(test, v, pymark)
                        is_act = True
                        break
                
                if is_act and (hasattr(v, _MARK_FOR_DISPATCHING)):
                    raise TypeError
                elif hasattr(v, _MARK_FOR_DISPATCHING):
                    test_name = _TEST_PREFIX + k
                    if not inspect.iscoroutinefunction(v):
                        bridges[test_name] = mcls._make_bridge(k)
                    else:
                        bridges[test_name] = pytest.mark.asyncio(
                            mcls._make_async_bridge(k)
                        )
        namespace.update(bridges)

        return super().__new__(mcls, name, bases, namespace)

    @classmethod
    def register_case(mcls, case: type[TestCase], act: Callable):
        if not issubclass(case, TestCase):
            raise TypeError(
                f"case must be a \"{TestCase.__name__}\". " +
                f"but recieves -> \"{type(case)}\"."
            )
        if case not in mcls._CASE_ACT_CACHE:
            mcls._CASE_ACT_CACHE[case] = set()
        mcls._CASE_ACT_CACHE[case].add(act)
    
    @staticmethod
    def _make_bridge(k):
        def bridge(self):
            bound_method = getattr(self, k)
            self.dispatch(k, bound_method)
        return bridge

    @staticmethod
    def _make_async_bridge(k):
        async def bridge(self):
            bound_method = getattr(self, k)
            await self.dispatch_async(k, bound_method)
        return bridge

    @staticmethod
    def _make_act_bridge(test, act, pymark):
        def bridge(*args, **kwargs):
            test(act, *args, **kwargs)
        bridge.pymark = pymark
        return bridge


class TestDispatcher(ABC, metaclass = _DispatcherMeta):

    def dispatch(self, method_name: str, method: Callable) -> None:
        """Invoke a method representing a test.

        Override this method to customize how test methods are invoked,
        such as adjusting their call signatures.  
        Test skipping must **not** be performed within this method.
        """
        method()
    
    async def dispatch_async(self, method_name: str, method: Callable) -> None:
        """Invoke an asynchronous method representing a test.

        Asynchronous test methods should be awaited within this dispatcher.

        Override this method to customize how asynchronous test methods
        are invoked, such as adjusting their call signatures.  
        Test skipping must **not** be performed within this method.
        """
        await method()

class TestCase:

    @classmethod
    def register(cls, act: Callable):
        _DispatcherMeta.register_case(cls, act)

    @classmethod
    def get_case_unit(cls) -> tuple[str, Callable, list[pytest.Mark] | None]:
        for k, v in cls.__dict__.items():
            if k.startswith("test"):
                if not callable(v):
                    raise TypeError(
                        f"{cls.__name__}.{k} is not callable."
                    )
                name = k.replace("test", cls.__name__, 1)
                pymark = v.pytestmark if hasattr(v, "pytestmark") else None
                return name, v, pymark
        raise RuntimeError(
            ".test* method is missing."
        )
    
    def __init__(self, dummy):
        raise RuntimeError(
            "Unexpected call. __new__ may have returned a non-None value."
        )
