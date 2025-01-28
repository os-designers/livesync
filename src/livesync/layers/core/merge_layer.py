from typing import Any, Literal, Sequence

from ..layer import Layer
from ...streams.stream import Stream


class Merge(Layer):
    """A layer that combines multiple input streams into a single output stream.

    Creates a new stream that yields tuples containing values from all input streams.
    The merge behavior can be controlled using the 'how' parameter.

    Parameters
    ----------
    inputs : Sequence[Stream]
        List of input streams to merge
    how : Literal["outer", "inner"], optional
        Merge strategy:
        - "outer": Yields when any input has new data (default)
        - "inner": Yields only when all inputs have new data
    name : str | None, optional
        Name of the merged stream, by default None

    Examples
    --------
    >>> u = ls.layers.Merge([x1, x2], how="outer")

    Raises
    ------
    ValueError
        If inputs is not a list/tuple of streams
    """

    def __init__(self, inputs: Sequence[Stream], how: Literal["outer", "inner"] = "outer", name: str | None = None):
        super().__init__(name=name)
        self.inputs = inputs
        self.how: Literal["outer", "inner"] = how

    def __call__(self, *args: Any, **kwargs: Any) -> Stream:
        return self.__new__(*args, **kwargs)

    def __new__(  # type: ignore[misc]
        cls, inputs: Sequence[Stream], how: Literal["outer", "inner"] = "outer", name: str | None = None
    ) -> Stream:
        """Create a new stream by applying this layer to an input stream.

        Parameters
        ----------
        inputs : Sequence[Stream]
            List of input streams to merge
        how : Literal["outer", "inner"], optional
            Merge strategy:
            - "outer": Yields when any input has new data (default)
            - "inner": Yields only when all inputs have new data
        name : str | None, optional
            Name of the merged stream, by default None

        Returns
        -------
        Stream
            New stream containing the processed data
        """
        # Create the layer instance first
        obj = super().__new__(cls)
        obj.__init__(inputs, how, name)  # type: ignore[misc]

        if not inputs or not isinstance(inputs, (list, tuple)):
            raise ValueError("Merge layer input must be a list/tuple of streams")

        # Create new stream with proper typing
        new_stream = Stream(
            dtype=tuple,
            name=name or obj.name,
            dependencies=inputs,
            dependency_strategy="all" if obj.how == "inner" else "any",
            layer=obj,
        )

        return new_stream

    def __repr__(self) -> str:
        return f"Merge({', '.join(input.name for input in self.inputs)}, name={self.name})"
