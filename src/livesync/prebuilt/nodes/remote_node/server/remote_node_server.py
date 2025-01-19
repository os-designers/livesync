import sys
from typing import Type
from concurrent import futures

import grpc  # type: ignore

from .....core.nodes import Node
from .....utils.logs import logger
from .remote_node_servicer import RemoteNodeServicer
from ....._protos.remote_node.remote_node_pb2_grpc import add_RemoteNodeServicer_to_server  # type: ignore


class RemoteNodeServer:
    """
    gRPC server for remote node operations.

    This server is used to connect to a remote endpoint and process frames.

    Example:
    ```python
    server = RemoteNodeServer(supported_nodes={"resolution_node": ResolutionNode}, port=50051, max_workers=10)
    await server.start()
    await server.wait_for_termination()
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
        self.server: grpc.aio.Server = grpc.aio.server(
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

    async def start(self) -> None:
        """Start the gRPC server and wait for shutdown."""
        try:
            await self.server.start()
            logger.debug(f"Server started on port {self.port}")

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            sys.exit(1)

    async def wait_for_termination(self) -> None:
        """Stop the gRPC server gracefully."""
        await self.server.wait_for_termination()
