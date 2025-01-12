from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from dataclasses import dataclass
from typing_extensions import override

from .base_node import BaseNode
from ..frames.base_frame import BaseFrame


@dataclass
class SourceNode(BaseNode, ABC):
    """Abstract node that represents a source of frames."""

    @override
    def __post_init__(self):
        """Initializes tasks and locks from the base node."""
        super().__post_init__()
        self._source_task: asyncio.Task[Any] | None = None

    @override
    async def process_frame(self, frame: BaseFrame) -> BaseFrame | None:
        """Forwards the frame without modification."""
        return frame

    @override
    async def _before_run(self):
        """Starts the frame capture task before running."""
        if not self._source_task:
            self._source_task = asyncio.create_task(self._process_source_frames())

    async def _process_source_frames(self) -> None:
        """Process frames from the capture iterator and put them into the queue."""
        generator = self._source_frames()
        async for frame in generator:  # type: ignore
            await self._input_queue.put((self.id, frame))  # type: ignore

    @abstractmethod
    async def _source_frames(self) -> AsyncIterator[BaseFrame]:
        """Continuously capture frames from the source."""
        pass

    @override
    async def _before_cleanup(self):
        """Cancels the capture task if active."""
        await self._stop_source()
        if self._source_task:
            if not self._source_task.done():
                self._source_task.cancel()
                try:
                    await self._source_task
                except (asyncio.CancelledError, RuntimeError):
                    pass
            self._source_task = None

    @abstractmethod
    async def _stop_source(self) -> None:
        """Stops the frame capture task."""
        pass
