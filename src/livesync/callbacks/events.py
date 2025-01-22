from __future__ import annotations

from typing import Any, Literal
from datetime import datetime


class CallbackEvent:
    """Base class for all callback events.

    Attributes
    ----------
    timestamp : datetime
        Time when the event was created.
    """

    def __init__(self, *, timestamp: datetime | None = None) -> None:
        self.timestamp = timestamp or datetime.now()


class StreamEvent(CallbackEvent):
    """Event data for stream-related callbacks.

    Parameters
    ----------
    event_type : {'start', 'end', 'error', 'cancelled'}
        Type of stream event.
    stream_name : str
        Name of the stream.
    step: int, optional
        Index of the current stream if applicable.
    queue_size: int, optional
        Size of the queue.
    input : Any, optional
        Input data to the stream.
    output : Any, optional
        Output data from the stream.
    error : Exception, optional
        Exception if an error occurred.
    timestamp : datetime, optional
        Event timestamp. Defaults to current time.
    """

    def __init__(
        self,
        event_type: Literal["start", "end", "error", "cancelled"],
        stream_name: str,
        step: int | None = None,
        queue_size: int | None = None,
        input: Any = None,
        output: Any = None,
        error: Exception | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__(timestamp=timestamp)
        self.event_type = event_type
        self.stream_name = stream_name
        self.step = step
        self.queue_size = queue_size
        self.input = input
        self.output = output
        self.error = error


class RunEvent(CallbackEvent):
    """Event data for run-related callbacks.

    Parameters
    ----------
    event_type : {'start', 'end', 'error'}
        Type of run event.
    error : Exception, optional
        Exception if an error occurred.
    timestamp : datetime, optional
        Event timestamp. Defaults to current time.
    """

    def __init__(
        self,
        event_type: Literal["start", "end", "error"],
        error: Exception | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__(timestamp=timestamp)
        self.event_type = event_type
        self.error = error
