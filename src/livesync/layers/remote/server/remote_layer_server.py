import os
from typing import Any, Callable, Awaitable
from concurrent import futures

import grpc  # type: ignore

from ...._utils.logs import logger
from .remote_layer_servicer import RemoteLayerServicer
from ...._protos.remote_layer.remote_layer_pb2_grpc import add_RemoteLayerServicer_to_server  # type: ignore

_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", os.environ.get("GRPC_MAX_RECEIVE_MESSAGE_LENGTH", 10 * 1024 * 1024)),  # 10MB
    ("grpc.max_send_message_length", os.environ.get("GRPC_MAX_SEND_MESSAGE_LENGTH", 10 * 1024 * 1024)),  # 10MB
    ("grpc.max_metadata_size", os.environ.get("GRPC_MAX_METADATA_SIZE", 10 * 1024 * 1024)),  # 10MB
]


class RemoteLayerServer:
    """
    A gRPC server implementation for handling remote layer operations.

    This server establishes a gRPC endpoint that processes frames and handles remote
    layer communications. It supports custom callback functions for initialization
    and request handling.

    Example:
    ```python
    async def on_init(ctx: ls.RemoteLayerServicer, **settings):
        print(f"Initializing with settings: {settings}")


    async def on_call(ctx: ls.RemoteLayerServicer, x: bytes) -> bytes:
        print(x)
        return x


    server = RemoteLayerServer(on_call=on_call, on_init=on_init)
    await server.start()
    await server.wait()
    ```

    Parameters
    ----------
    on_call : Callable[..., Awaitable[Any]]
        The function to be called when a call is made.
    on_init : Callable[..., Awaitable[Any]] | None, optional
        The function to be called when the layer is initialized.
        Will receive any kwargs passed to RemoteLayer as a dictionary.
    port : int, optional
        Port number to listen on, by default 50051.
    max_workers : int, optional
        Maximum number of worker threads, by default 10.
    """

    def __init__(
        self,
        on_call: Callable[..., Awaitable[Any]],
        on_init: Callable[..., Awaitable[Any]] | None = None,
        port: int = 50051,
        max_workers: int = 10,
    ):
        self.on_call = on_call
        self.on_init = on_init
        self.port = port
        self.max_workers = max_workers
        self.server: grpc.aio.Server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            options=_GRPC_OPTIONS,
        )
        # Add service and port
        servicer = RemoteLayerServicer(on_call=self.on_call, on_init=self.on_init)
        add_RemoteLayerServicer_to_server(servicer, self.server)  # type: ignore
        self.server.add_insecure_port(f"[::]:{self.port}")

    async def async_run(self) -> None:
        """Starts the gRPC server and begins accepting connections."""
        await self.server.start()
        logger.info(f"Server started on port {self.port}")

    async def wait(self) -> None:
        """Blocks until the server receives a shutdown signal."""
        logger.info("Waiting for server to stop: Ctrl+C to stop")
        await self.server.wait_for_termination()

    async def stop(self, grace: int = 0) -> None:
        """Stop the gRPC server."""
        await self.server.stop(grace)
        logger.info("Server stopped")
