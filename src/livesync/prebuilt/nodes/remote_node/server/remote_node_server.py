import sys
import signal
import asyncio
from typing import Type
from concurrent import futures

import grpc  # type: ignore

from .....core.nodes import Node
from .....utils.logs import logger
from .remote_node_pb2_grpc import add_RemoteNodeServicer_to_server  # type: ignore
from .remote_node_servicer import RemoteNodeServicer


class RemoteNodeServer:
    """
    gRPC server for remote node operations.

    This server is used to connect to a remote endpoint and process frames.

    Example:
    ```python
    server = RemoteNodeServer(supported_nodes={"resolution_node": ResolutionNode}, port=50051, max_workers=10)
    asyncio.run(server.start())
    ```

    Parameters
    ----------
    supported_nodes : dict[str, Type[Node]]
        Dictionary mapping node names to their corresponding Node classes.
    port : int, optional
        Port number to listen on, by default 50051.
    max_workers : int, optional
        Maximum number of worker threads, by default 10.
    """

    def __init__(self, supported_nodes: dict[str, Type[Node]], port: int = 50051, max_workers: int = 10):
        self.supported_nodes = supported_nodes
        self.port = port
        self.max_workers = max_workers
        self.server: grpc.aio.Server | None = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the gRPC server and wait for shutdown."""
        try:
            logger.debug("Initializing server...")

            self.server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers),
                options=[
                    ("grpc.max_receive_message_length", 10 * 1024 * 1024),  # 10MB
                    ("grpc.max_send_message_length", 10 * 1024 * 1024),  # 10MB
                    ("grpc.max_metadata_size", 10 * 1024 * 1024),  # 10MB
                ],
            )

            # Add service and port
            servicer = RemoteNodeServicer(self.supported_nodes)
            add_RemoteNodeServicer_to_server(servicer, self.server)  # type: ignore
            self.server.add_insecure_port(f"[::]:{self.port}")

            # Start server
            await self.server.start()
            logger.debug(f"Server started on port {self.port}")

            # Handle termination signals
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            sys.exit(1)

    async def stop(self) -> None:
        """Stop the gRPC server gracefully."""
        if self.server:
            logger.debug("Stopping server...")
            await self.server.stop(grace=5)
            logger.debug("Server stopped")
            self._shutdown_event.set()
