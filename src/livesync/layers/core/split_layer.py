from typing import Any, Callable, Sequence

from ..layer import Layer
from ...streams.stream import Stream


class Split(Layer):
    """
    A layer that splits a stream containing multiple data values (e.g., a tuple, list, or
    dictionary from a merge operation) into multiple separate output streams.

    Parameters
    ----------
    keys : Sequence[str]
        If a sequence of strings, each string acts as a key to extract values from an incoming dictionary.
    name : str | None, optional
        The name of the split layer. If None, a name is automatically generated.

    Examples
    --------
    >>> split_layer = ls.layers.Split(["h1_name", "h2_name"])
    >>> stream_a, stream_b = split_layer(merged_stream)
    """

    def __init__(self, keys: Sequence[str], name: str | None = None) -> None:
        super().__init__(name=name)
        self.output_count = len(keys)
        self.keys = keys

    def _make_extractor(self, key: str) -> Callable[[dict[str, Any]], Any]:
        async def extractor(val: dict[str, Any]) -> Any:
            # If the key exists, return a dict with just that key/value.
            if key in val:
                return val[key]
            # Otherwise, return the original input.
            return None

        return extractor

    def __call__(self, input_stream: Stream) -> tuple[Stream, ...]:
        """
        Splits the input stream into multiple output streams.
        If the input is a dictionary and keys were provided during initialization, values will be extracted using these keys.
        Otherwise, extraction is based on index order.

        Parameters
        ----------
        input_stream : Stream
            A stream that outputs an indexable value or a dictionary.

        Returns
        -------
        tuple[Stream, ...]
            A tuple containing the split output streams.
        """
        outputs: list[Stream] = []
        for i in range(self.output_count):
            extractor = self._make_extractor(self.keys[i])
            new_stream = Stream(
                name=f"{input_stream.name}_split[{i}]",
                dependencies=[input_stream],
                operator=extractor,
                layer=self,
            )
            outputs.append(new_stream)
        return tuple(outputs)

    def __repr__(self) -> str:
        return f"Split(outputs={self.keys}, name={self.name})"
