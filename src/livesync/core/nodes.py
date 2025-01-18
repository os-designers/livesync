from __future__ import annotations

import asyncio
from uuid import uuid4
from typing import Any, Callable
from typing_extensions import override

from .fields import Field, FieldMeta


class Node(metaclass=FieldMeta):
    """
    A unified node implementation that can be used in both DAG and streaming pipelines.

    Parameters
    ----------
    name : str
        Unique identifier for the node
    bootstrap_func : Callable[..., Any]
        The bootstrap function (can be sync/async)
    step_func : Callable[..., Any]
        The step function (can be sync/async/generator/async generator)
    shutdown_func : Callable[..., Any]
        The shutdown function (can be sync/async)

    Attributes
    ----------
    parents : list[Node]
        List of parent nodes that feed into this node
    children : list[Node]
        List of child nodes that this node feeds into
    input_queues : dict[Node, asyncio.Queue[Any]]
        Queues for receiving data from parent nodes (used in streaming mode)
    output_queues : dict[Node, asyncio.Queue[Any]]
        Queues for sending data to child nodes (used in streaming mode)
    """

    name: str = Field(default_factory=lambda: uuid4().hex)
    bootstrap_func: Callable[..., Any] | None = Field(default=None, init=False)
    step_func: Callable[..., Any] | None = Field(default=None)
    shutdown_func: Callable[..., Any] | None = Field(default=None, init=False)

    def __post_init__(self) -> None:
        self._bootstrap_func = self.bootstrap_func or getattr(self, "bootstrap", None)
        self._step_func = self.step_func or getattr(self, "step", None)
        self._shutdown_func = self.shutdown_func or getattr(self, "shutdown", None)

        if self._step_func is None:
            raise ValueError("step_func is required")

        self.parents: list[Node] = []
        self.children: list[Node] = []
        self.input_queues: dict[str, asyncio.Queue[Any]] = {}
        self.output_queues: dict[str, asyncio.Queue[Any]] = {}

    async def get_inputs(self) -> dict[str, Any]:
        """Collect inputs from all parent nodes in a dictionary."""
        inputs: dict[str, Any] = {}
        for parent in self.parents:
            inputs[parent.name] = await self.input_queues[parent.name].get()
        return inputs

    async def get_input(self, parent_name: str) -> Any:
        """Get input from a specific parent node by name."""
        for parent in self.parents:
            if parent.name == parent_name:
                return await self.input_queues[parent.name].get()
        raise ValueError(f"No parent node found with name '{parent_name}'")

    def is_input_empty(self, parent_name: str) -> bool:
        """Check if the input queue from a specific parent node is empty.

        Parameters
        ----------
        parent_name : str
            Name of the parent node to check

        Returns
        -------
        bool
            True if the queue is empty, False otherwise

        Raises
        ------
        ValueError
            If no parent node exists with the given name
        """
        for parent in self.parents:
            if parent.name == parent_name:
                return self.input_queues[parent.name].empty()
        raise ValueError(f"No parent node found with name '{parent_name}'")

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
