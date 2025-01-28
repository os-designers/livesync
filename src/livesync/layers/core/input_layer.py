from __future__ import annotations

from abc import abstractmethod
from typing import Any, Generic, TypeVar, AsyncIterator

from ..layer import Layer
from ...streams.stream import Stream

T = TypeVar("T")


class InputLayer(Layer, AsyncIterator[T], Generic[T]):
    """A base class for layers that generate input data as an asynchronous stream.

    This layer acts as a source of data by implementing an async iterator interface.
    When instantiated, it creates a Stream object that yields values of type T.

    Parameters
    ----------
    dtype : type
        The data type of values that will be generated
    name : str | None, optional
        Name of the layer, by default None

    Examples
    --------
    >>> class MyInput(InputLayer[int]):
    ...     async def aiter(self):
    ...         for i in range(10):
    ...             await asyncio.sleep(1)
    ...             yield i
    >>> input_stream = MyInput(dtype=int)

    Notes
    -----
    Subclasses must implement the aiter() method to define how values are generated.
    The layer automatically creates and returns a Stream object when instantiated.
    """

    def __init__(
        self,
        dtype: type,
        name: str | None = None,
    ):
        super().__init__(name=name)

        self._dtype = dtype
        self._generator: AsyncIterator[T] | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Stream:
        return self.__new__(*args, **kwargs)

    def __new__(cls, *args: Any, **kwargs: Any) -> Stream:  # type: ignore[misc]
        """Create a new stream by applying this layer to an input stream.

        Returns
        -------
        Stream
            New stream containing the processed data
        """
        # Create the layer instance first
        obj = super().__new__(cls)
        obj.__init__(*args, **kwargs)  # type: ignore[misc]
        stream = Stream(
            dtype=obj._dtype,
            name=obj.name,
            dependencies=[],
            generator=obj.aiter(),
            layer=obj,
        )
        return stream

    def __aiter__(self) -> AsyncIterator[T]:
        self._generator = self.aiter()
        return self

    @abstractmethod
    def aiter(self) -> AsyncIterator[T]:
        """Input layers should implement this method to generate values."""
        pass

    async def __anext__(self) -> T:
        if self._generator is None:
            raise StopAsyncIteration

        try:
            return await self._generator.__anext__()
        except StopAsyncIteration:
            raise
