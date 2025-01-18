from __future__ import annotations

import time
import asyncio
from typing import TYPE_CHECKING, Any, Literal
from typing_extensions import override

from ..utils.logs import logger

if TYPE_CHECKING:
    from .runner import Runner


class Run:
    """
    A handle to a runner that is currently executing or has executed.

    - Use `.wait()` (async) to await completion with an optional timeout.
    - You can also `.cancel()` if the runner supports cancellation.
    - This class can serve as a context manager for automatic cleanup.
    """

    def __init__(self, runner: Runner, task: asyncio.Task[Any]) -> None:
        self.runner = runner
        self.task: asyncio.Task[Any] = task
        self.status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"

        self._start_time: float | None = None
        self._end_time: float | None = None

    def __enter__(self) -> "Run":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.runner.__exit__(exc_type, exc_value, traceback)

    async def wait(self, timeout: float | None = None) -> "Run":
        """
        Wait for this run to finish, optionally with a timeout.
        """
        if self.status == "pending":
            self.status = "running"
            self._start_time = time.monotonic()

        try:
            await asyncio.wait_for(self.task, timeout=timeout)
            if self.status == "running":
                self.status = "completed"
                self._end_time = time.monotonic()
        except asyncio.TimeoutError:
            self.cancel()
            self.status = "cancelled"
            self._end_time = time.monotonic()
            logger.debug("Timed out waiting for tasks; all tasks cancelled.")
        except Exception:
            self.status = "failed"
            self._end_time = time.monotonic()
            raise
        return self

    def cancel(self) -> None:
        """
        Cancel all tasks immediately.
        """
        self.task.cancel()

        if self.status in ("pending", "running"):
            self.status = "cancelled"
            self._end_time = time.monotonic()

    @property
    def runtime(self) -> float | None:
        """
        Return the total runtime in seconds, or None if not started/completed.
        """
        if self._start_time is None or self._end_time is None:
            return None
        return self._end_time - self._start_time

    @override
    def __repr__(self) -> str:
        runtime_str = f"{self.runtime:.3f}s" if self.runtime else "N/A"
        return f"Run(status={self.status}, runtime={runtime_str})"
