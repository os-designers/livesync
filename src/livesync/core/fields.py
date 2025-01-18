from __future__ import annotations

from typing import Any
from dataclasses import field as _field, dataclass
from typing_extensions import dataclass_transform


@dataclass_transform(field_specifiers=(lambda *args, **kwargs: _field(*args, **kwargs),))  # type: ignore
def Field(*, description: str = "", init: bool = True, **kwargs: Any) -> Any:
    metadata = kwargs.get("metadata", {})
    metadata["description"] = description
    kwargs["metadata"] = metadata
    return _field(init=init, **kwargs)


@dataclass_transform(field_specifiers=(Field,))
class FieldMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        if not hasattr(attrs.get("__dataclass_fields__", None), "items"):
            new_cls = super().__new__(cls, name, bases, attrs)
            return dataclass(new_cls, unsafe_hash=True)  # type: ignore
        return super().__new__(cls, name, bases, attrs)


__all__ = ["Field", "FieldMeta"]
