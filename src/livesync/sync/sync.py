from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ..layers.layer import Layer
from ..streams.stream import Stream
from .._utils.graph_visualizer import GraphVisualizer

if TYPE_CHECKING:
    from .runner import Runner


class Sync:
    """
    A sync implementation that can be used in both DAG and streaming pipelines.

    Attributes
    ----------
    inputs : list[Stream]
        List of input streams
    outputs : list[Stream]
        List of output streams
    """

    def __init__(self, inputs: list[Stream], outputs: list[Stream]) -> None:
        self._inputs = inputs
        self._outputs = outputs
        self._validate_graph()

    def _validate_graph(self) -> None:
        """Validate the computational graph for cycles and reachability."""
        # Validate input streams have no dependencies
        for input_stream in self._inputs:
            if input_stream.dependencies:
                raise ValueError(f"Input stream {input_stream.name} should not have any dependencies")

        # Check for cycles in the graph
        self._check_cycles()

        # For each output, check if it's reachable from at least one input
        for output in self._outputs:
            reachable = False
            for input_stream in self._inputs:
                if self._is_reachable(input_stream, output):
                    reachable = True
                    break
            if not reachable:
                raise ValueError(f"Output stream {output} is not reachable from any input")

        # Verify consumer-dependency relationships
        self._validate_relationships()

    def _check_cycles(self) -> None:
        """Check for cycles in the graph using DFS."""
        visited: set[Stream] = set()
        path: set[Stream] = set()

        def dfs(stream: Stream) -> None:
            if stream in path:
                raise ValueError(f"Cycle detected in graph involving stream {stream.name}")
            if stream in visited:
                return

            visited.add(stream)
            path.add(stream)

            for dep in stream.dependencies:
                dfs(dep)

            path.remove(stream)

        for input_stream in self._inputs:
            dfs(input_stream)

    def _validate_relationships(self) -> None:
        """Validate that consumer-dependency relationships are bidirectional."""
        for stream in self.get_all_streams():
            # Check if all dependencies list this stream as a consumer
            for dep in stream.dependencies:
                if stream not in dep.consumers:
                    raise ValueError(
                        f"Inconsistent relationship: {stream.name} lists {dep.name} as dependency "
                        f"but {dep.name} doesn't list {stream.name} as consumer"
                    )
            # Check if all consumers list this stream as a dependency
            for consumer in stream.consumers:
                if stream not in consumer.dependencies:
                    raise ValueError(
                        f"Inconsistent relationship: {stream.name} lists {consumer.name} as consumer "
                        f"but {consumer.name} doesn't list {stream.name} as dependency"
                    )

    def get_all_streams(self) -> set[Stream]:
        """Get all streams in the graph."""
        all_streams: set[Stream] = set()

        def collect_streams(stream: Stream) -> None:
            if stream in all_streams:
                return
            all_streams.add(stream)
            for dep in stream.dependencies:
                collect_streams(dep)
            for consumer in stream.consumers:
                collect_streams(consumer)

        for input_stream in self._inputs:
            collect_streams(input_stream)
        return all_streams

    def get_all_layers(self) -> set[Layer]:
        """Get all layers in the graph."""
        return {stream._layer for stream in self.get_all_streams() if stream._layer is not None}

    def _is_reachable(self, start: Stream, target: Stream) -> bool:
        """Check if target stream is reachable from start stream using BFS."""
        visited: set[Stream] = set()
        queue = [start]

        while queue:
            node = queue.pop(0)
            if node == target:
                return True
            if node not in visited:
                visited.add(node)
                queue.extend(node.consumers)

        return False

    def compile(self) -> Runner:
        """
        Return a runner associated with this graph.
        Each graph type should return its corresponding runner.
        """
        from .runner import Runner

        return Runner(self)

    @property
    def inputs(self) -> list[Stream]:
        return self._inputs

    @property
    def outputs(self) -> list[Stream]:
        return self._outputs

    @property
    def paths(self) -> dict[Stream, list[list[Stream]]]:
        """Get all possible paths from inputs to each output.

        Returns a dictionary where:
            - key: output stream
            - value: list of paths, where each path is a list of streams from input to output
        """
        paths: dict[Stream, list[list[Stream]]] = {}

        def build_paths(stream: Stream, current_path: list[Stream]) -> list[list[Stream]]:
            """Recursively build all possible paths to inputs."""
            if not stream.dependencies:  # If it's an input stream
                return [current_path + [stream]]

            all_paths: list[list[Stream]] = []
            for input_stream in stream.dependencies:
                paths_from_input = build_paths(input_stream, current_path + [stream])
                all_paths.extend(paths_from_input)

            return all_paths

        # Get paths for each output separately
        for output in self._outputs:
            paths[output] = build_paths(output, [])

        return paths

    def summary(self) -> str:
        """Returns a string summary of the sync graph."""

        summary: list[str] = []

        for output in self._outputs:
            summary.append(f"\nPath to output: {output}")
            summary.append("-" * 100)

            def get_name(stream: Stream) -> str:
                name = stream.name
                if stream in self._outputs:
                    name += " (output)"
                return name

            def get_dependencies(stream: Stream) -> Sequence[Stream]:
                return stream.dependencies

            def get_node_type(stream: Stream) -> str:
                if not stream.dependencies:
                    return "input"
                elif len(stream.dependencies) > 1:
                    return "merge"
                return "normal"

            rows = GraphVisualizer.create_ascii_graph(
                output,
                get_name=get_name,
                get_dependencies=get_dependencies,
                get_node_type=get_node_type,
            )
            summary.extend(rows)

        return "\n".join(summary)
