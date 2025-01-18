import asyncio
import inspect
from typing import Any, Generator, AsyncGenerator


def is_generator(obj: Any) -> bool:
    return isinstance(obj, Generator)


def is_async_generator(obj: Any) -> bool:
    return isinstance(obj, AsyncGenerator)


def is_coroutine(obj: Any) -> bool:
    return asyncio.iscoroutine(obj)


def is_async_function(obj: Any) -> bool:
    return inspect.iscoroutinefunction(obj)


def is_sync_function(obj: Any) -> bool:
    return not inspect.iscoroutinefunction(obj)


def is_bound_method(obj: Any) -> bool:
    return inspect.ismethod(obj)
