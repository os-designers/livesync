from __future__ import annotations

import time
import asyncio
from typing import Any, AsyncGenerator

from ..core.nodes import Node
from ..utils.logs import logger
from ..core.graphs import Graph
from ..core.callbacks import NodeEvent, GraphEvent, CallbackProtocol
from ..core.run_handle import Run
from ..utils.type_checkers import is_generator, is_bound_method, is_sync_function, is_async_function, is_async_generator
from ..utils.topological_sort import topological_sort_levels


class Runner:
    """
    A runner class for a pipeline runner.

    A runner class that manages the lifecycle and execution flow of computational
    graphs, supporting both synchronous and asynchronous operations.


    Parameters
    ----------
    graph : Graph
        The computational graph to execute

    Attributes
    ----------
    _graph : Graph
        The computational graph to execute
    _callback : CallbackProtocol | None
        Callback for monitoring execution events
    _running : bool
        Flag indicating whether the runner is currently executing
    _tasks : list[asyncio.Task]
        List of currently running async tasks.
    """

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self._callback: CallbackProtocol | None = None
        self._running = False
        self._tasks: list[asyncio.Task[Any]] = []

    def run(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> Run:
        """Execute the graph synchronously.

        Parameters
        ----------
        continuous : bool, optional
            If True, runs nodes in continuous loop mode, by default True
        callback : CallbackProtocol | None, optional
            Callback for monitoring execution events, by default None

        Returns
        -------
        Run
            Handle to monitor and control the execution
        """
        return asyncio.run(self._execute_sync(continuous=continuous, callback=callback))

    async def _execute_sync(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> Run:
        run = await self.async_run(continuous=continuous, callback=callback)
        try:
            await run.wait()
        except Exception:
            raise
        return run

    def resume(self) -> Run:
        """
        Resume the runner from a previous execution.
        """
        raise NotImplementedError("Please implement in a subclass.")

    async def async_run(self, continuous: bool = True, callback: CallbackProtocol | None = None) -> Run:
        """Execute the graph asynchronously.

        Parameters
        ----------
        continuous : bool, optional
            If True, runs nodes in continuous loop mode, by default True
        callback : CallbackProtocol | None, optional
            Callback for monitoring execution events, by default None

        Returns
        -------
        Run
            Handle to monitor and control the execution

        Raises
        ------
        RuntimeError
            If the runner is already running
        """
        if self._running:
            raise RuntimeError("Runner is already running.")

        self._running = True
        self._callback = callback

        # Validate nodes
        for node in self.graph.nodes:
            self._validate_node(node)

        # Notify that the graph has started
        if callback:
            callback.on_graph_start(GraphEvent(node_count=len(self.graph.nodes), event_type="start"))

        try:
            main_task = asyncio.create_task(self._run_nodes_topological(self.graph.nodes, continuous))
            self._tasks.append(main_task)

            run = Run(self, main_task)
            run.status = "running"
            run._start_time = time.monotonic()
            return run

        except Exception as e:
            if callback:
                callback.on_graph_error(GraphEvent(node_count=len(self.graph.nodes), event_type="error", error=e))
            raise

    def _validate_node(self, node: Node) -> None:
        if not node._step_func:
            raise ValueError(f"Node {node.name} has no step function.")

    async def _run_nodes_topological(self, nodes: list[Node], continuous: bool = False) -> None:
        """Execute nodes in topological order with optional continuous execution.

        This method orchestrates the execution flow of nodes in a directed acyclic graph (DAG).

        Execution Flow:
        1. Nodes are grouped into levels based on dependencies
        2. Bootstrap phase runs for all nodes
        3. Source nodes (Level 0) start executing
        4. Dependent nodes (Level 1+) wait for parent data and process

        Visual Example of Levels:
        ```
        Level 0 (Sources):    [A]       [B]
                               ↓         ↓
        Level 1:              [C]       [D]
                                 ↘     ↙
        Level 2:                   [E]
        ```

        Data Flow Example:
        1. Node A and B run independently and produce data
        2. Node C processes A's data, D processes B's data
        3. Node E waits for both C and D before processing

        Parameters
        ----------
        nodes : list[Node]
            List of nodes to execute
        continuous : bool, optional
            If True, executes nodes in an infinite loop. If False, executes once.
        """
        levels = topological_sort_levels(nodes)

        # Run bootstrap for all nodes
        bootstrap_tasks = [asyncio.create_task(self._maybe_run_bootstrap(node)) for node in nodes]
        await asyncio.gather(*bootstrap_tasks)

        # Track completion of source nodes
        source_completed = {node.name: False for node in levels[0]}

        async def run_source_node(node: Node):
            try:
                step_index = 0
                while True:
                    if not self._running:
                        break
                    step_index += 1
                    results = await self._run_node_once(node, step_index)
                    # Propagate results to children
                    for r in results:
                        for child in node.children:
                            await child.input_queues[node.name].put(r)
                    if not continuous:
                        # Mark this source as completed
                        source_completed[node.name] = True
                        break
            except asyncio.CancelledError:
                pass
            except Exception as e:
                if self._callback:
                    self._callback.on_node_error(NodeEvent(node_name=node.name, event_type="error", error=e))
                raise
            finally:
                # Ensure source is marked as completed even if error occurs
                if not continuous:
                    source_completed[node.name] = True

        async def run_dependent_node(node: Node):
            try:
                step_index = 0
                while True:
                    if not self._running:
                        break

                    # Check if we should stop processing in non-continuous mode
                    if not continuous:
                        # Check if all parent sources are done and queues are empty
                        all_parents_done = True
                        for parent in node.parents:
                            # If parent is a source node, check its completion
                            if parent.name in source_completed:
                                if not source_completed[parent.name]:
                                    all_parents_done = False
                                    break
                            # If parent is not a source, check if it's still running
                            parent_task = next(
                                (t for t in self._tasks if t.get_name() == f"dependent_{parent.name}"), None
                            )
                            if parent_task and not parent_task.done():
                                all_parents_done = False
                                break

                        # If all parents are done and no more data in queues, we can stop
                        if all_parents_done and all(node.input_queues[parent.name].empty() for parent in node.parents):
                            break

                    # Process available data
                    if all(not node.input_queues[parent.name].empty() for parent in node.parents):
                        step_index += 1
                        results = await self._run_node_once(node, step_index)
                        # Propagate results to children
                        for r in results:
                            for child in node.children:
                                await child.input_queues[node.name].put(r)
                    else:
                        await asyncio.sleep(0.001)

            except asyncio.CancelledError:
                pass
            except Exception as e:
                if self._callback:
                    self._callback.on_node_error(NodeEvent(node_name=node.name, event_type="error", error=e))
                raise

        # Create tasks for source nodes (level 0)
        source_tasks = [asyncio.create_task(run_source_node(node), name=f"source_{node.name}") for node in levels[0]]

        # Create tasks for dependent nodes (levels 1+)
        dependent_tasks = [
            asyncio.create_task(run_dependent_node(node), name=f"dependent_{node.name}")
            for level in levels[1:]
            for node in level
        ]

        # Add all tasks to the runner's task list
        self._tasks.extend(source_tasks)
        self._tasks.extend(dependent_tasks)

        # Wait for all tasks to complete
        await asyncio.gather(*source_tasks, *dependent_tasks, return_exceptions=True)

    async def _run_node_once(self, node: Node, step_index: int) -> list[Any]:
        """Execute a single step of the node and collect all yielded results.

        Parameters
        ----------
        node : Node
            The node to execute
        step_index : int
            The index of the step to execute

        Returns
        -------
        list[Any]
            List of all values yielded during the node's step execution
        """
        try:
            if self._callback:
                self._callback.on_node_step_start(
                    NodeEvent(node_name=node.name, step_index=step_index, event_type="step_start")
                )

            results: list[Any] = []
            async for r in self._execute_step_function(node):
                if self._callback:
                    self._callback.on_node_step_end(
                        NodeEvent(
                            node_name=node.name,
                            step_index=step_index,
                            output=r,
                            event_type="step_end",
                        )
                    )

                # Skip None results for propagation
                if r is not None:
                    results.append(r)

            return results
        except Exception as e:
            if self._callback:
                self._callback.on_node_error(NodeEvent(node_name=node.name, event_type="error", error=e))
            raise

    async def _maybe_run_bootstrap(self, node: Node) -> None:
        """Run the bootstrap function of a node if it exists."""
        bootstrap_func = node._bootstrap_func
        if bootstrap_func:
            if is_async_function(bootstrap_func):
                await bootstrap_func()
            else:
                bootstrap_func()

            if self._callback:
                event = NodeEvent(node_name=node.name, event_type="bootstrap")
                self._callback.on_node_bootstrap(event)

    async def _execute_step_function(self, node: Node) -> AsyncGenerator[Any, None]:
        """Execute the step function of a node and yield the results."""
        step_func = node._step_func
        if not step_func:
            raise ValueError(f"Node {node.name} has no step function.")

        is_method = is_bound_method(step_func)
        func_args = () if is_method else (node,)
        loop = asyncio.get_event_loop()

        if is_async_generator(step_func):
            async for val in step_func(*func_args):
                yield val

        elif is_async_function(step_func):
            val = await step_func(*func_args)
            yield val

        elif is_generator(step_func):

            def run_generator():
                return list(step_func(*func_args))

            values = await loop.run_in_executor(None, run_generator)
            for val in values:
                yield val

        elif is_sync_function(step_func):
            val = await loop.run_in_executor(None, step_func, *func_args)  # type: ignore[func-returns-value]
            yield val

        else:
            raise TypeError(f"Node {node.name} step function type not supported.")

    async def async_resume(self) -> None:
        """Async entry point to resume the runner from a previous execution."""
        raise NotImplementedError("Please implement in a subclass.")

    def cleanup(self) -> None:
        """Cleanup resources after execution (if needed)."""
        # Create and run an event loop if there isn't one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Handle shutdown functions
        shutdown_tasks: list[asyncio.Task[Any]] = []
        for node in self.graph.nodes:
            shutdown_func = node._shutdown_func
            if shutdown_func:
                if is_async_function(shutdown_func):
                    # Create task for async shutdown
                    shutdown_tasks.append(shutdown_func())
                else:
                    # Run sync shutdown directly
                    shutdown_func()

        # Run async shutdown tasks if any exist
        if shutdown_tasks:
            loop.run_until_complete(asyncio.gather(*shutdown_tasks))

        for t in self._tasks:
            t.cancel()

        self._running = False
        self._tasks.clear()
        logger.debug("Runner stopped and cleaned up.")

        if self._callback:
            self._callback.on_graph_end(GraphEvent(node_count=len(self.graph.nodes), event_type="end"))
            self._callback = None

    def __enter__(self) -> Runner:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.cleanup()

    async def __aenter__(self) -> Runner:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.cleanup()
