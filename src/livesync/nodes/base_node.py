from __future__ import annotations

import uuid
import asyncio
from abc import ABC, abstractmethod
from typing import Any
from logging import getLogger
from dataclasses import field, dataclass

from ..frames.base_frame import BaseFrame

logger = getLogger(__name__)


class NodeCallbackHandler(ABC):
    """Callback methods for node events."""

    @abstractmethod
    async def on_frame_received(self, node: BaseNode, frame: BaseFrame):
        """Called when a frame is received."""
        pass

    @abstractmethod
    async def on_frame_processed(self, node: BaseNode, frame: BaseFrame):
        """Called after a frame is processed."""
        pass


@dataclass(kw_only=True)
class BaseNode(ABC):
    """Base class for all pipeline nodes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concurrent: bool = field(default=False)
    callback_handler: NodeCallbackHandler | None = field(default=None)

    def __post_init__(self):
        """Sets up queues, tasks, and locks."""
        self._input_queue: asyncio.Queue[tuple[str, BaseFrame]] = asyncio.Queue()
        self._is_running: bool = False
        self._tasks: list[asyncio.Task[Any]] = []

    async def start(self, loop: asyncio.AbstractEventLoop | None = None, successors: list[BaseNode] = []):
        """Starts the node loop until a stop signal is received."""
        if self._is_running:
            raise RuntimeError("Node is already running")

        try:
            self._is_running = True
            current_loop = loop or asyncio.get_running_loop()
            self._tasks.append(current_loop.create_task(self._try_run(successors)))
        except asyncio.CancelledError:
            logger.debug("Graph execution cancelled")
        except Exception as e:
            logger.error(f"Error during graph execution: {e}")
            raise

    async def _before_run(self):  # noqa: B027
        """Hook for setup logic before run."""
        pass

    async def _try_run(self, successors: list[BaseNode] = []):
        """Consumes frames from the queue and processes them."""
        try:
            await self._before_run()

            while self._is_running:
                source_id, frame = await self._input_queue.get()

                if self.callback_handler:
                    await self.callback_handler.on_frame_received(self, frame)

                try:
                    if self.concurrent:
                        task = asyncio.create_task(self._process_and_propagate(source_id, frame, successors))
                        self._tasks.append(task)
                        task.add_done_callback(self._tasks.remove)
                    else:
                        await self._process_and_propagate(source_id, frame, successors)
                except Exception as e:
                    logger.exception(f"Error processing frame in node {self.id} " f"({self.__class__.__name__}): {e}")
                finally:
                    self._input_queue.task_done()

        except asyncio.CancelledError:
            logger.info(f"Node {self.id} processing cancelled")
        except Exception as e:
            logger.exception(f"Unexpected error in node {self.id}: {e}")
            raise

    async def _process_and_propagate(self, source_id: str, frame: BaseFrame, successors: list[BaseNode]):
        """Processes the frame and propagates it to successors."""
        processed_frame: BaseFrame | None = await self.process_frame(frame)

        if processed_frame is not None:
            # Propagate the frame to connected nodes
            await asyncio.gather(
                *(node._input_queue.put((source_id, processed_frame)) for node in successors), return_exceptions=True
            )
            if self.callback_handler:
                await self.callback_handler.on_frame_processed(self, processed_frame)

    async def _before_cleanup(self):  # noqa: B027
        """Hook for cleanup logic before cleanup."""
        pass

    @abstractmethod
    async def process_frame(self, frame: BaseFrame) -> BaseFrame | None:
        """Processes a frame and returns a (possibly modified) frame or None."""
        pass

    async def stop(self):
        """Stops the node and triggers cleanup."""
        if not self._is_running:
            return

        try:
            await self._before_cleanup()
            await self._drain_input_queue()
        finally:
            await self._cancel_tasks()
            self._is_running = False
            self._tasks.clear()

    async def _drain_input_queue(self) -> None:
        """Drains the queue."""
        while not self._input_queue.empty():
            try:
                _ = self._input_queue.get_nowait()
                self._input_queue.task_done()
            except asyncio.QueueEmpty:
                break

    async def _cancel_tasks(self) -> None:
        """Cancel remaining tasks."""
        if not self._tasks:
            return

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task  # Wait for task to complete cancellation
                except (asyncio.CancelledError, Exception) as e:
                    logger.debug(f"Task cancellation: {e}")
