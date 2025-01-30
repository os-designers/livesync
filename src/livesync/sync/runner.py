from __future__ import annotations

import time
import asyncio
from typing import Any

from .sync import Sync
from .run_handle import Run
from .._utils.logs import logger
from ..streams.stream import Stream
from ..callbacks.events import RunEvent, StreamEvent
from ..callbacks.protocol import CallbackProtocol
from ..callbacks.callbacks import LoggingCallback


class Runner:
    """
    A runner class for a pipeline runner.

    A runner class that manages the lifecycle and execution flow of computational
    graphs, supporting both synchronous and asynchronous operations.


    Parameters
    ----------
    sync : Sync
        The sync to execute

    Attributes
    ----------
    _sync : Sync
        The sync to execute
    _callback : CallbackProtocol | None
        Callback for monitoring execution events
    _running : bool
        Flag indicating whether the runner is currently executing
    _tasks : list[asyncio.Task]
        List of currently running async tasks.
    """

    def __init__(self, sync: Sync) -> None:
        self._sync = sync
        self._callback: CallbackProtocol | None = None
        self._running = False
        self._tasks: list[asyncio.Task[Any]] = []
        self._step_counts: dict[str, int] = {}

    def run(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> None:
        """Execute the graph synchronously.

        Parameters
        ----------
        continuous : bool, optional
            If True, runs nodes in continuous loop mode, by default True
        callback : CallbackProtocol | None, optional
            Callback for monitoring execution events, by default None
        """
        if callback is None:
            callback = LoggingCallback(log_level="debug")
        try:
            asyncio.run(self._execute_sync(continuous=continuous, callback=callback))
        except KeyboardInterrupt:
            return None

    async def _execute_sync(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> Run:
        run = await self.async_run(continuous=continuous, callback=callback)
        try:
            await run.wait()
        except Exception:
            raise
        return run

    async def async_run(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> Run:
        """Execute the sync asynchronously.

        Parameters
        ----------
        continuous : bool, optional
            If True, runs nodes in continuous loop mode, by default True
        callback : CallbackProtocol | None, optional
            Callback for monitoring execution events, by default None

        Returns
        -------
        Run
            Handle to monitor and control the execution

        Raises
        ------
        RuntimeError
            If the runner is already running
        """
        if self._running:
            raise RuntimeError("Runner is already running.")

        unique_layers = self._sync.get_all_layers()
        for layer in unique_layers:
            await layer.init()

        self._running = True
        self._callback = callback

        # Notify that the graph has started
        if callback:
            callback.on_run_start(RunEvent(event_type="start"))

        try:
            tasks = [asyncio.create_task(self._run_input_stream(input, continuous)) for input in self._sync.inputs]
            self._tasks.extend(tasks)

            run = Run(self, tasks)
            run.status = "running"
            run._start_time = time.monotonic()
            return run

        except Exception as e:
            if callback:
                callback.on_run_error(RunEvent(event_type="error", error=e))
            raise

    async def _run_input_stream(self, stream: Stream, continuous: bool) -> None:
        """Execute stream in parallel while respecting its topological dependencies."""
        self._step_counts[stream.name] = 0
        consumer_tasks: list[asyncio.Task[Any]] = []

        async_iterator = stream.__aiter__()

        async def process_consumers(stream: Stream, value: Any) -> None:
            """Recursively processes and propagates values to all dependent (downstream) streams."""
            if stream.name not in self._step_counts:
                self._step_counts[stream.name] = 0
            self._step_counts[stream.name] += 1
            current_step = self._step_counts[stream.name]

            for consumer in stream.consumers:
                if self._callback:
                    self._callback.on_stream_start(
                        StreamEvent(
                            event_type="start",
                            stream_name=consumer.name,
                            input=value,
                            step=current_step,
                            queue_size=len(consumer),
                        )
                    )

                try:
                    value = await consumer.__aiter__().__anext__()

                    if self._callback:
                        self._callback.on_stream_end(
                            StreamEvent(
                                event_type="end",
                                stream_name=consumer.name,
                                step=current_step,
                                output=value,
                                queue_size=len(consumer),
                            )
                        )

                    if value:
                        task = asyncio.create_task(process_consumers(consumer, value))
                        consumer_tasks.append(task)

                except Exception as e:
                    logger.error(f"Error processing consumer {consumer.name}: {e}")

                    if self._callback:
                        self._callback.on_stream_error(
                            StreamEvent(
                                event_type="error",
                                stream_name=consumer.name,
                                step=current_step,
                                error=e,
                            )
                        )

        try:
            while self._running:
                self._step_counts[stream.name] += 1
                current_step = self._step_counts[stream.name]

                if self._callback:
                    self._callback.on_stream_start(
                        StreamEvent(
                            event_type="start",
                            stream_name=stream.name,
                            input=None,
                            step=current_step,
                            queue_size=len(stream),
                        )
                    )

                try:
                    value = await async_iterator.__anext__()

                    if value:
                        asyncio.create_task(process_consumers(stream, value))

                    if self._callback:
                        self._callback.on_stream_end(
                            StreamEvent(
                                stream_name=stream.name,
                                step=current_step,
                                output=value,
                                event_type="end",
                                queue_size=len(stream),
                            )
                        )

                    if not continuous:
                        self._running = False
                        break
                except asyncio.CancelledError:
                    break

                except StopAsyncIteration:
                    break
        finally:
            for t in consumer_tasks:
                if not t.done():
                    t.cancel()

            if consumer_tasks:
                await asyncio.gather(*consumer_tasks, return_exceptions=True)
                logger.info(f"Consumer tasks for stream '{stream.name}' cancelled.")

            self._running = False

    def cleanup(self) -> None:
        """Cleanup resources after execution (if needed)."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._async_cleanup())
        except RuntimeError:
            # No running loop, run cleanup synchronously
            asyncio.run(self._async_cleanup())

    async def _async_cleanup(self) -> None:
        """Asynchronous cleanup implementation."""
        try:
            # Cleanup all layers
            unique_layers = self._sync.get_all_layers()
            await asyncio.gather(*(layer.cleanup() for layer in unique_layers))

            # Cancel all tasks
            for t in self._tasks:
                if not t.done():
                    t.cancel()

            self._running = False
            self._tasks.clear()
            logger.debug("Runner stopped and cleaned up.")

            if self._callback:
                self._callback.on_run_end(RunEvent(event_type="end"))

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise

    def __enter__(self) -> Runner:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.cleanup()

    async def __aenter__(self) -> Runner:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.cleanup()
