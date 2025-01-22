import asyncio
from typing import Generic, TypeVar

T = TypeVar("T")


class RoundRobinSelector(Generic[T]):
    """Round robin index selector for a given list of items."""

    def __init__(self, items: list[T]):
        self._items: list[T] = items
        self._index: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def next(self) -> T:
        async with self._lock:
            item = self._items[self._index]
            self._index = (self._index + 1) % len(self._items)
            return item
