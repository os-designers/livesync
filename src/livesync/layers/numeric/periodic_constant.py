import asyncio
from typing import AsyncIterator

from ...types import DataType
from ..core.input_layer import InputLayer
from ..._utils.type_utils import infer_dtype


class PeriodicConstantInput(InputLayer[DataType]):
    """A layer that periodically yields a constant value.

    This input layer repeatedly yields the same value at specified intervals
    for a given number of iterations or indefinitely.

    Parameters
    ----------
    value : Any
        The constant value to yield
    num_iter : int or None
        Maximum number of iterations. If None, yields indefinitely
    interval : float, default=0.0
        Time interval between yields in seconds
    name : str | None, default=None
        The name of the layer
    """

    def __init__(self, value: DataType, num_iter: int | None = None, interval: float = 0.0, name: str | None = None):
        super().__init__(dtype=infer_dtype(value), name=name)
        self._value = value
        self._current_iter = 0
        self._num_iter = num_iter
        self._interval = interval

    async def aiter(self) -> AsyncIterator[DataType]:
        """Asynchronously iterate over the constant value.

        Yields
        ------
        Any
            The constant value at specified intervals

        Raises
        ------
        StopAsyncIteration
            When the specified number of iterations is reached
        """
        while True:
            if self._num_iter is not None:
                if self._current_iter >= self._num_iter:
                    raise StopAsyncIteration
                self._current_iter += 1

            if self._interval > 0:
                await asyncio.sleep(self._interval)

            yield self._value
