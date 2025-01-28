import inspect
from typing import Any, Callable, Awaitable

from .callable_layer import Layer
from ...streams.stream import Stream


class Lambda(Layer):
    """A layer that applies a custom async function to stream data.

    This layer allows you to create a stream transformation using any async function.
    The function must accept a single input and return a processed output.

    Parameters
    ----------
    function : Callable[..., Awaitable[Any]]
        The async function to apply to the stream data
    name : str | None, optional
        Name of the layer, by default None

    Examples
    --------
    >>> async def process(x):
    ...     return x * 2
    >>> f = Lambda(process)
    >>> y = f(x)

    Raises
    ------
    ValueError
        If the provided function is not async or if parameter count mismatches
    TypeError
        If the input is not a Stream object
    """

    def __init__(self, function: Callable[..., Awaitable[Any]], name: str | None = None):
        super().__init__(name=name)
        if not inspect.iscoroutinefunction(function):
            raise ValueError("Lambda layer only accepts async functions")
        self._function = function

    def __call__(self, x: Stream, name: str | None = None) -> Stream:
        """Create a new stream by applying this layer to an input stream.

        Parameters
        ----------
        x : Stream
            Input stream to process
        name : str | None, optional
            Name for the output stream, by default None

        Returns
        -------
        Stream
            New stream containing the processed data
        """
        new_stream = Stream(
            dtype=x.dtype,
            name=name or self.name,
            dependencies=[x],
            operator=self._function,
            layer=self,
        )
        return new_stream

    def __repr__(self) -> str:
        return f"Lambda(function={self._function.__name__}, name={self.name})"
