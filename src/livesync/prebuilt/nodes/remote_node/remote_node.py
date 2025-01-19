import os
import asyncio
from typing import Any, TypeVar

import grpc  # type: ignore
from google.protobuf.struct_pb2 import Struct

from ....core.nodes import Node
from ....utils.logs import logger
from ....core.fields import Field
from ....core.frames import AudioFrame, VideoFrame
from ....utils.round_robin_selector import RoundRobinSelector
from ...._protos.remote_node.remote_node_pb2 import StepRequest, StepResponse, ConfigureRequest, ConfigureResponse
from ...._protos.remote_node.remote_node_pb2_grpc import RemoteNodeStub

T = TypeVar("T")


class RemoteNode(Node):
    """A node that represents a GRPC remote endpoint connection.

    This node is used to connect to a remote endpoint and process frames.

    Example:
    ```python
    node = GrpcRemoteNode(
        endpoints=["localhost:50051", "localhost:50052"],
        config={
            "face_swap": {
                "face_swap_model": "face_swap_model.onnx",
                "face_swap_model_type": "onnx",
            }
        },
    )
    ```
    """

    endpoints: list[str] = Field(default=..., description="The endpoints to connect to")
    settings: dict[str, Any] = Field(default=..., description="The configuration for the remote node")

    async def bootstrap(self) -> None:
        """Connect to the remote endpoints."""
        if len(self.parents) != 1:
            raise ValueError("ResolutionNode must have a single parent")
        self._parent_node = self.parents[0]
        self._selector = RoundRobinSelector(self.endpoints)
        self._channel: grpc.aio.Channel | None = None
        self._stubs: dict[str, RemoteNodeStub] = {}
        self._lock = asyncio.Lock()

        if not self.settings:
            raise ValueError("Configs are required")

        try:
            await self._connect()
            await self._configure(self.settings)
            logger.debug(f"[{self.__class__.__name__}] Successfully connected to endpoints: {self.endpoints}")
        except Exception as e:
            logger.error(f"Error connecting to gRPC endpoints: {e}")
            raise e

    async def _connect(self) -> None:
        """Establishes connections to all configured endpoints"""
        logger.debug(f"Connecting to {len(self.endpoints)} endpoints")

        connection_tasks = [self._establish_connection(endpoint) for endpoint in self.endpoints]
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        successful_connections = sum(1 for r in results if not isinstance(r, Exception))

        logger.debug(f"Successful connections: {successful_connections}")
        if successful_connections == 0:
            logger.error(f"Failed to connect to any endpoints")
            raise grpc.RpcError("Failed to connect to any endpoints")

    async def _establish_connection(self, endpoint: str) -> None:
        """Establishes connection to a single endpoint with authentication"""
        try:
            channel = grpc.aio.insecure_channel(
                endpoint,
                options=[
                    (
                        "grpc.max_receive_message_length",
                        os.environ.get("GRPC_MAX_RECEIVE_MESSAGE_LENGTH", 10 * 1024 * 1024),  # 10 MB
                    ),
                    (
                        "grpc.max_send_message_length",
                        os.environ.get("GRPC_MAX_SEND_MESSAGE_LENGTH", 10 * 1024 * 1024),  # 10 MB
                    ),
                    (
                        "grpc.max_metadata_size",
                        os.environ.get("GRPC_MAX_METADATA_SIZE", 1 * 1024 * 1024),  # 1 MB
                    ),
                ],
            )
            await channel.channel_ready()

            stub = RemoteNodeStub(channel)
            async with self._lock:
                self._stubs[endpoint] = stub
                logger.info(f"Successfully connected endpoint: {endpoint}")

        except Exception as e:
            logger.error(f"Failed to connect to {endpoint}: {e}")
            raise grpc.RpcError(f"Connection failed to {endpoint}: {str(e)}") from e

    async def _configure(self, settings: dict[str, Any]) -> None:
        try:
            struct = Struct()
            struct.update(settings)
            request = ConfigureRequest(settings=struct)
            responses: list[ConfigureResponse] = await asyncio.gather(
                *[stub.Configure(request) for stub in self._stubs.values()]  # type: ignore[func-returns-value]
            )
            for endpoint, response in zip(self._stubs.keys(), responses):
                logger.info(
                    f"ConfigureProcessors response for {endpoint}: "
                    f"  success = {response.success} "
                    f"  error_message = {response.error_message}"
                )

        except grpc.RpcError as e:
            raise e

    async def step(self) -> VideoFrame | AudioFrame | None:
        try:
            endpoint = await self._selector.next()
            stub = self._stubs[endpoint]
            if not stub:
                raise Exception(f"No active stub for endpoint {endpoint}")

            frame: VideoFrame | AudioFrame = await self.get_input(self._parent_node.name)
            request = StepRequest(target_frame=frame.tobytes())
            response: StepResponse = await stub.Step(request)  # type: ignore

            if not response.success:  # type: ignore
                logger.error(f"Error processing frame on gRPC: {response.error_message}")  # type: ignore
                return None

            if len(response.processed_frame) == 0:  # type: ignore[arg-type]
                return None
            elif isinstance(frame, VideoFrame):
                return VideoFrame.frombytes(response.processed_frame)  # type: ignore
            return AudioFrame.frombytes(response.processed_frame)  # type: ignore

        except grpc.RpcError as e:
            logger.error(f"ProcessFrame RPC failed: {e}")
            raise e

    async def shutdown(self):
        """Disconnect from the remote endpoints."""
        async with self._lock:
            disconnect_tasks = [self._close_connection(endpoint) for endpoint in self._stubs.keys()]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            self._stubs.clear()

    async def _close_connection(self, endpoint: str) -> None:
        """Closes connection to a single endpoint"""
        try:
            if self._channel:
                await self._channel.close()
            logger.info(f"Disconnected from endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Error disconnecting from {endpoint}: {e}")
