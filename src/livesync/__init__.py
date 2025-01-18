from __future__ import annotations

from .version import __title__, __version__
from .utils.logs import SensitiveHeadersFilter, setup_logging as _setup_logging

__all__ = [
    "__title__",
    "__version__",
    "Node",
    "Graph",
    "Run",
    "Runner",
    "Field",
    "CallbackEvent",
    "NodeEvent",
    "GraphEvent",
    "CallbackProtocol",
    "SensitiveHeadersFilter",
    "AudioFrame",
    "VideoFrame",
]
from .core import (
    Run,
    Node,
    Field,
    Graph,
    Runner,
    NodeEvent,
    AudioFrame,
    GraphEvent,
    VideoFrame,
    CallbackEvent,
    CallbackProtocol,
)

_setup_logging()

# Update the __module__ attribute for exported symbols so that
# error messages point to this module instead of the module
# it was originally defined in, e.g.
# livesync._exceptions.NotFoundError -> livesync.NotFoundError
__locals = locals()
for __name in __all__:
    if not __name.startswith("__"):
        try:
            __locals[__name].__module__ = "livesync"
        except (TypeError, AttributeError):
            # Some of our exported symbols are builtins which we can't set attributes for.
            pass
