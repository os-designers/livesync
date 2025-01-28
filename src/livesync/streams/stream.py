from __future__ import annotations

import asyncio
from typing import Any, Literal, Callable, Sequence, Awaitable, AsyncIterator
from collections import deque

from ..layers.layer import Layer
from .._utils.naming import generate_name
from .._utils.graph_visualizer import GraphVisualizer


class Stream:
    """
    A stream representing a data flow that can depend on other streams.

    Parameters
    ----------
    name : str
        A unique identifier for the stream.
    dtype : type
        The expected data type of values flowing through the stream.
    dependencies : Sequence[Stream], optional
        Other streams that this stream depends on for input.
    dependency_strategy : {'all', 'any'}, default='all'
        How to handle multiple dependencies:
        - 'any': Triggers on any single dependency update
        - 'all': Waits for all dependencies to update before triggering
    generator : AsyncIterator[Any], optional
        An async generator that produces source values (mutually exclusive with dependencies)
    operator : Callable[..., Awaitable[Any]], optional
        An async function to transform incoming values
    layer : Layer, optional
        A layer to apply to the stream
    """

    def __init__(
        self,
        dtype: type,
        name: str = "unnamed",
        dependencies: Sequence[Stream] = (),
        dependency_strategy: Literal["all", "any"] = "all",
        generator: AsyncIterator[Any] | None = None,
        operator: Callable[..., Awaitable[Any]] | None = None,
        layer: Layer | None = None,
    ) -> None:
        self.name = generate_name(name)
        self.dtype = dtype
        self.dependencies = dependencies
        self.dependency_strategy = dependency_strategy

        self._consumers: list[Stream] = []
        self._queue: asyncio.Queue[Any] = asyncio.Queue()
        self._generator: AsyncIterator[Any] | None = generator
        self._operator: Callable[..., Awaitable[Any]] | None = operator
        self._layer: Layer | None = layer

        if self._generator and len(dependencies) > 0:
            raise ValueError("Cannot use generator with dependencies")

        if self._generator and self._operator:
            raise ValueError("Cannot use generator and operator together")

        # Register this stream as a consumer for all dependencies
        for dep in dependencies:
            dep.add_consumer(self)

        # Initialize pending values storage for 'all' strategy
        self._pending_values: dict[str, deque[Any]] = {}
        if dependencies and dependency_strategy == "all":
            for dep in dependencies:
                self._pending_values[dep.name] = deque()

    async def push(self, value: Any | None, source: Stream | None = None) -> None:
        """
        Processes and queues a new value from an upstream dependency.

        Parameters
        ----------
        value : Any | None
            The value to be processed.
        source : Stream | None, optional
            The upstream stream that produced this value.
        """
        if value is None:
            return

        if self._operator:
            value = await self._operator(value)

        if len(self.dependencies) < 2:
            await self._queue.put(value)
            await self.propagate_to_consumers(value)

        else:
            if source is None:
                raise ValueError(f"Stream {self.name} received a value without a source")

            value = {source.name: value}
            if self.dependency_strategy != "all":
                await self._queue.put(value)
                await self.propagate_to_consumers(value)

            else:
                self._pending_values[source.name].append(value)

                while all(q for q in self._pending_values.values()):
                    merged_dict = {
                        dep.name: self._pending_values[dep.name].popleft()[dep.name] for dep in self.dependencies
                    }
                    await self._queue.put(merged_dict)
                    await self.propagate_to_consumers(merged_dict)

    async def propagate_to_consumers(self, value: Any) -> None:
        """
        Propagates a value dictionary to all dependent (downstream) streams.

        Parameters
        ----------
        value : Any
            The value to be added to the stream.
        """
        for consumer in self._consumers:
            asyncio.create_task(consumer.push(value, source=self))

    @property
    def ready(self) -> bool:
        """Check if the stream is ready to produce a value based on its dependency strategy."""
        if not self.dependencies:
            return True
        if self.dependency_strategy == "any":
            return len(self._pending_values) > 0
        return len(self._pending_values) == len(self.dependencies)

    def add_consumer(self, consumer: Stream) -> None:
        """Add a downstream consumer to this stream."""
        self._consumers.append(consumer)

    def reset(self) -> None:
        """Resets the stream's internal state, clearing pending values and queue."""
        for q in self._pending_values.values():
            q.clear()
        while not self._queue.empty():
            self._queue.get_nowait()

    async def pop(self) -> dict[int, Any]:
        """Pops a value dictionary from the stream."""
        return await self._queue.get()  # type: ignore[no-any-return]

    @property
    def depth(self) -> int:
        """Computes the depth of this stream in the dependency graph."""

        def get_depth(stream: Stream, visited: set[str]) -> int:
            if stream.name in visited:
                return 0
            visited.add(stream.name)
            if not stream.dependencies:
                return 0
            return 1 + max(get_depth(dep, visited) for dep in stream.dependencies)

        return get_depth(self, visited=set())

    @property
    def graph(self) -> str:
        """Get a formatted summary of the stream graph starting from this node in a git-log style format."""

        def get_name(stream: Stream) -> str:
            return stream.name

        def get_dependencies(stream: Stream) -> Sequence[Stream]:
            return stream.dependencies

        def get_node_type(stream: Stream) -> str:
            if not stream.dependencies:  # Input stream
                return "input"
            elif len(stream.dependencies) > 1:  # Merge stream
                return "merge"
            return "normal"

        rows = GraphVisualizer.create_ascii_graph(
            self, get_name=get_name, get_dependencies=get_dependencies, get_node_type=get_node_type
        )

        return "\n".join(rows)

    @property
    def consumers(self) -> list[Stream]:
        """Get the list of consumers of this stream."""
        return self._consumers

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Allows the stream to be used in an async iterator."""
        if self._generator:
            async for value in self._generator:
                yield value
                await self.propagate_to_consumers(value)
        else:
            while True:
                value = await self._queue.get()
                yield value

    def __len__(self) -> int:
        """Get the number of pending values in the stream."""
        return self._queue.qsize()

    def __repr__(self) -> str:
        """
        Returns a string representation of the stream.

        Returns
        -------
        str
            A string describing the stream and its dependencies.
        """
        dtype_name = self.dtype.__name__ if hasattr(self.dtype, "__name__") else str(self.dtype)
        return f"Stream(name={self.name}, dtype={dtype_name})"
