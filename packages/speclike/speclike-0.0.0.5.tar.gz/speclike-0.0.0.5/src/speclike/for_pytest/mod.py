from abc import ABC, ABCMeta
from typing import Any, Callable

import pytest
import inspect

_MARK_FOR_DISPATCHING = "_speclike_dispatch"

_BRIDGE_PREFIX = "test_"

def _make_bridge(k):
    def bridge(self):
        bound_method = getattr(self, k)
        self.dispatch(k, bound_method)
    return bridge

def _make_async_bridge(k):
    async def bridge(self):
        bound_method = getattr(self, k)
        await self.dispatch_async(k, bound_method)
    return bridge


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

class DispatcherMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace: dict[str, Any]):
        bridges = {}
        for k, v in namespace.items():
            if hasattr(v, _MARK_FOR_DISPATCHING):
                bridge_name = _BRIDGE_PREFIX + k
                if not inspect.iscoroutinefunction(v):
                    bridges[bridge_name] = _make_bridge(k)
                else:
                    bridges[bridge_name] = pytest.mark.asyncio(
                        _make_async_bridge(k)
                    )
        namespace.update(bridges)

        return super().__new__(mcls, name, bases, namespace)



class TestDispatcher(ABC, metaclass = DispatcherMeta):

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
