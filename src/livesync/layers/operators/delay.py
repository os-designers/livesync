import asyncio
from typing import Any

from ..core.callable_layer import CallableLayer


class DelayLayer(CallableLayer[Any, Any]):
    """Layer that delays the input by a specified time interval.

    Parameters
    ----------
    interval : int or float
        The time interval to delay in seconds.
    name : str or None, optional
        Name of the layer, by default None.
    """

    def __init__(self, interval: int | float, name: str | None = None) -> None:
        super().__init__(name=name)
        self.interval = interval

    async def call(self, x: Any) -> Any:
        """Delays the input by the specified time interval.

        Parameters
        ----------
        x : Any
            Input value to be delayed.

        Returns
        -------
        Any
            The original input value after the delay.
        """
        await asyncio.sleep(self.interval)
        return x
