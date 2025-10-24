from abc import ABC
from typing import Callable
import importlib.util

import pytest
import inspect

_ENABLE_ASYNCIO = importlib.util.find_spec("pytest_asyncio") is not None

class TestDispatcher(ABC):

    def dispatched(self, method_name: str) -> bool:
        """Determine whether a method should be executed as a test.
        
        This method can be overridden to customize which methods
        are selected and executed as tests.
        The `method_name` argument is the name of a class attribute
        whose `callable` check returns True.
        """
        return method_name.startswith("case_happy_path")

    def dispatch(self, method_name: str, method: Callable) -> None:
        """Invoke a method that represents a test.
        
        This method can be overridden to customize how a test method
        is invoked (e.g., to modify its call signature).
        Test skipping must **not** be performed within this method.
        """
        method()
    
    async def dispatch_async(self, method_name: str, method: Callable) -> None:
        """Invoke an asynchronous method that represents a test.
        
        Asynchronous methods should be awaited within this dispatcher.

        This method can be overridden to customize how an async test method
        is invoked (e.g., to modify its call signature).
        Test skipping must **not** be performed within this method.
        """
        await method()

    
    def test_by_dispatched(self):
        cases = []
        for k, v in self.__class__.__dict__.items():
            if callable(v) and not inspect.iscoroutinefunction(v) and (
                self.dispatched(k)
            ):
                cases.append(k)
        failed = {}
        for method_name in cases:
            method = getattr(self, method_name)
            try:
                self.dispatch(method_name, method)
            except Exception as e:
                failed[method_name] = e

        if failed:
            messages = ["Following test cases failed:"]
            for name, e in failed.items():
                messages.append(f"  - {name}: {type(e).__name__}({e})")
            pytest.fail("\n".join(messages))
    
    @pytest.mark.skipif(not _ENABLE_ASYNCIO, reason="pytest-asyncio not installed")
    @pytest.mark.asyncio
    async def test_by_dispatched_async(self):
        cases = []
        for k, v in self.__class__.__dict__.items():
            if callable(v) and inspect.iscoroutinefunction(v) and (
                self.dispatched(k)
            ):
                cases.append(k)
        failed = {}
        for method_name in cases:
            method = getattr(self, method_name)
            try:
                await self.dispatch_async(method_name, method)
            except Exception as e:
                failed[method_name] = e
        
        if failed:
            messages = ["Following async test cases failed:"]
            for name, e in failed.items():
                messages.append(f"  - {name}: {type(e).__name__}({e})")
            pytest.fail("\n".join(messages))
