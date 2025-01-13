import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from logging import getLogger
from dataclasses import dataclass
from typing_extensions import override

from .base_node import BaseNode

logger = getLogger(__name__)


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


@dataclass
class RemoteNode(BaseNode, ABC):
    """Abstract node that represents a remote endpoint connection."""

    endpoints: list[str]

    def __post_init__(self):
        super().__post_init__()
        self._selector = RoundRobinSelector(self.endpoints)

    @override
    async def _before_run(self):
        """Hook for setup logic before run."""
        await self._connect()

    @abstractmethod
    async def _connect(self):
        """Connect to the remote endpoints."""
        pass

    @override
    async def _before_cleanup(self):
        """Hook for cleanup logic after run."""
        await self._disconnect()

    @abstractmethod
    async def _disconnect(self):
        """Disconnect from the remote endpoints."""
        pass
