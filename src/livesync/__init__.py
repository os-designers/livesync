from __future__ import annotations

from ._logs import SensitiveHeadersFilter, setup_logging as _setup_logging
from ._version import __title__, __version__

__all__ = [
    "__title__",
    "__version__",
    "SensitiveHeadersFilter",
    "AudioFrame",
    "VideoFrame",
    "Graph",
    "BaseNode",
    "NodeCallbackHandler",
    "SourceNode",
    "FrameRateNode",
    "ResolutionNode",
    "WebcamNode",
    "LiveKitAudioPublisherNode",
    "LiveKitAudioSourceNode",
    "LiveKitVideoPublisherNode",
    "LiveKitVideoSourceNode",
    "LivesyncRemoteNode",
]

from .nodes import (
    BaseNode,
    SourceNode,
    WebcamNode,
    FrameRateNode,
    ResolutionNode,
    LivesyncRemoteNode,
    NodeCallbackHandler,
    LiveKitAudioSourceNode,
    LiveKitVideoSourceNode,
    LiveKitAudioPublisherNode,
    LiveKitVideoPublisherNode,
)
from .frames import AudioFrame, VideoFrame
from .graphs import Graph
from .version import VERSION as VERSION

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
