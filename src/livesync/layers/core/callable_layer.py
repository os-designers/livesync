from abc import abstractmethod
from typing import Generic, TypeVar

from ..layer import Layer
from ...types import StreamDataType
from ...streams.stream import Stream

T = TypeVar("T", bound=StreamDataType)
U = TypeVar("U", bound=StreamDataType | None)


class CallableLayer(Layer, Generic[T, U]):
    """A base class for layers that can be called as functions on streams.

    This layer acts as a callable function that transforms stream data of type T to type U.
    Can be used either by calling the layer directly on a stream or through the call() method.

    Parameters
    ----------
    name : str | None, optional
        Name of the layer, by default None
    """

    def __init__(self, name: str | None = None):
        super().__init__(name=name)

    @abstractmethod
    async def call(self, x: T) -> U:
        """Process a single data element from the stream.

        Parameters
        ----------
        x : T
            Input data of type T to process

        Returns
        -------
        U
            Processed output data of type U
        """
        pass

    def __call__(self, x: Stream, name: str | None = None) -> Stream:
        """Create a new stream by applying this layer to a stream.

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
            operator=self.call,
            layer=self,
        )
        return new_stream
