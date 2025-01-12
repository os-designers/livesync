from abc import ABC, abstractmethod
from logging import getLogger
from dataclasses import dataclass
from typing_extensions import override

from .base_node import BaseNode

logger = getLogger(__name__)


@dataclass
class RemoteNode(BaseNode, ABC):
    """Abstract node that represents a remote endpoint connection."""

    endpoints: list[str]

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
