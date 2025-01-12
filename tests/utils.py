from __future__ import annotations

import io
from typing import Any, ForwardRef

import rich


def evaluate_forwardref(forwardref: ForwardRef, globalns: dict[str, Any]) -> type:
    return eval(str(forwardref), globalns)  # type: ignore[no-any-return]


def rich_print_str(obj: object) -> str:
    """Like `rich.print()` but returns the string instead"""
    buf = io.StringIO()

    console = rich.console.Console(file=buf, width=120)
    console.print(obj)

    return buf.getvalue()
