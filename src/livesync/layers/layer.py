from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .._utils.naming import generate_name
from .._utils.string_transformers import to_snake_case


class Layer(ABC):
    """Base class for all layers in the processing pipeline.

    This abstract class serves as the foundation for all layer types in the system.
    Layers are the building blocks of the processing pipeline, each performing
    specific operations on data streams.

    Parameters
    ----------
    name : str | None, optional
        Name of the layer. If None, generates a name based on the class name
        in snake_case format.
    """

    def __init__(self, name: str | None = None):
        if name is None:
            name = to_snake_case(self.__class__.__name__)
        self.name = generate_name(name)

    async def init(self) -> None:  # noqa: B027
        pass

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass

    async def cleanup(self) -> None:  # noqa: B027
        pass

    def __repr__(self) -> str:
        # Get the class name
        class_name = self.__class__.__name__

        # Get all instance attributes that don't start with underscore
        params = {k: v for k, v in self.__dict__.items() if not k.startswith("_") and k != "name"}

        # Format parameters as key=value pairs
        param_parts: list[str] = []
        if params:  # Only add parameters if there are any
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            param_parts.append(param_str)
        param_parts.append(f"name={self.name}")

        # Combine class name and all parts with comma separation
        return f"{class_name}({', '.join(param_parts)})"
