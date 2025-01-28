import os
import struct
import asyncio
from typing import Any

import grpc  # type: ignore
from google.protobuf.struct_pb2 import Struct

from ...types import BytesableType
from ..._utils.logs import logger
from ...frames.audio_frame import AudioFrame
from ...frames.video_frame import VideoFrame
from ..core.callable_layer import CallableLayer
from ..._utils.round_robin_selector import RoundRobinSelector
from ..._protos.remote_layer.remote_layer_pb2 import (
    DataType as ProtoDataType,
    CallRequest,
    InitRequest,
    CallResponse,
    InitResponse,
)
from ..._protos.remote_layer.remote_layer_pb2_grpc import RemoteLayerStub

_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", os.environ.get("GRPC_MAX_RECEIVE_MESSAGE_LENGTH", 10 * 1024 * 1024)),  # 10MB
    ("grpc.max_send_message_length", os.environ.get("GRPC_MAX_SEND_MESSAGE_LENGTH", 10 * 1024 * 1024)),  # 10MB
    ("grpc.max_metadata_size", os.environ.get("GRPC_MAX_METADATA_SIZE", 10 * 1024 * 1024)),  # 10MB
]


class RemoteLayer(CallableLayer[BytesableType, BytesableType | None]):
    """A layer that represents a GRPC remote endpoint connection.

    This layer is used to connect to a remote endpoint and process frames.

    Example:
    ```python
    import livesync as ls
    from livesync import layers

    # Basic usage
    x = ls.WebcamInput(device_id=1, fps=30)
    f1 = layers.RemoteLayer(endpoint="localhost:50051")
    y1 = f1(x)

    # With initialization settings
    f2 = layers.RemoteLayer(
        endpoint="localhost:50051",
        model_path="yolo.pt",  # This will be passed to server's on_init
        threshold=0.5,  # as {"model_path": "yolo.pt", "threshold": 0.5}
    )
    y2 = f2(y)
    ```

    Parameters
    ----------
    endpoint : str | list[str]
        The endpoint to connect to
    name : str | None, optional
        Name of the layer
    **kwargs : Any
        Additional keyword arguments that will be passed to the remote server's
        on_init function during initialization. If no kwargs are provided,
        an empty dictionary will be passed to on_init.
    """

    def __init__(self, endpoint: str | list[str], name: str | None = None, **kwargs: Any) -> None:
        super().__init__(name=name)
        self._settings = kwargs
        self._endpoints = [endpoint] if isinstance(endpoint, str) else endpoint
        self._selector = RoundRobinSelector(self._endpoints)
        self._channel: grpc.aio.Channel | None = None
        self._stubs: dict[str, RemoteLayerStub] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def init(self) -> None:
        """Ensures the remote layer is initialized."""
        try:
            logger.debug(f"Connecting to {len(self._endpoints)} endpoints")

            async def establish_connection(endpoint: str) -> None:
                """Establishes connection to a single endpoint with authentication"""
                try:
                    channel = grpc.aio.insecure_channel(endpoint, options=_GRPC_OPTIONS)
                    await channel.channel_ready()

                    stub = RemoteLayerStub(channel)  # type: ignore[no-untyped-call]
                    async with self._lock:
                        self._stubs[endpoint] = stub
                        logger.info(f"Successfully connected endpoint: {endpoint}")

                except Exception as e:
                    logger.error(f"Failed to connect to {endpoint}: {e}")
                    raise grpc.RpcError(f"Connection failed to {endpoint}: {str(e)}") from e

            # Establish connections to all endpoints
            connection_tasks = [establish_connection(endpoint) for endpoint in self._endpoints]
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            successful_connections = sum(1 for r in results if not isinstance(r, Exception))

            if successful_connections == 0:
                logger.error(f"Failed to connect to any endpoints")
                raise grpc.RpcError("Failed to connect to any endpoints")

            if self._settings:
                await self._initialize_server(self._settings)
            logger.info(f"Successfully connected to endpoints: {self._endpoints}")
        except Exception as e:
            logger.error(f"Error connecting to gRPC endpoints: {e}")
            raise e
        self._initialized = True

    async def _initialize_server(self, settings: dict[str, Any]) -> None:
        try:
            logger.info(f"Initializing server with settings: {settings}")
            struct = Struct()
            struct.update(settings)
            request = InitRequest(settings=struct)
            responses: list[InitResponse] = await asyncio.gather(
                *[stub.Init(request) for stub in self._stubs.values()]  # type: ignore[func-returns-value]
            )
            for endpoint, response in zip(self._stubs.keys(), responses, strict=False):
                if not response.success:
                    logger.error(f"Failed to initialize {endpoint}: {response.error_message}")
                else:
                    logger.info(f"Initialized {endpoint} successfully")
            self._initialized = True
        except grpc.RpcError as e:
            raise e

    async def call(self, x: BytesableType) -> BytesableType | None:
        try:
            endpoint = await self._selector.next()
            stub = self._stubs[endpoint]
            if not stub:
                logger.error(f"No active stub for endpoint {endpoint}")
                raise Exception(f"No active stub for endpoint {endpoint}")

            if isinstance(x, VideoFrame):
                request = CallRequest(x=bytes(x), type=ProtoDataType.VIDEO_FRAME)
            elif isinstance(x, AudioFrame):
                request = CallRequest(x=bytes(x), type=ProtoDataType.AUDIO_FRAME)
            elif isinstance(x, bytes):
                request = CallRequest(x=x, type=ProtoDataType.BYTES)
            elif isinstance(x, str):
                request = CallRequest(x=x.encode(), type=ProtoDataType.STRING)
            elif isinstance(x, float):
                request = CallRequest(x=struct.pack("d", x), type=ProtoDataType.FLOAT)
            elif isinstance(x, int):  # type: ignore[redundant-isinstance]
                request = CallRequest(x=struct.pack("q", x), type=ProtoDataType.INT)
            else:
                logger.error(f"Unsupported frame type: {type(x)}")  # type: ignore[unreachable]
                raise ValueError(f"Unsupported frame type: {type(x)}")

            response: CallResponse | None = await stub.Call(request)  # type: ignore

            if not response or not response.success:  # type: ignore
                logger.error(f"Error processing frame on gRPC: {response.error_message}")  # type: ignore
                return None

            # Convert response based on type
            if len(response.y) == 0 or response.y is None:  # type: ignore
                return None
            elif response.type == ProtoDataType.VIDEO_FRAME:  # type: ignore
                return VideoFrame.frombytes(response.y)  # type: ignore
            elif response.type == ProtoDataType.AUDIO_FRAME:  # type: ignore
                return AudioFrame.frombytes(response.y)  # type: ignore
            elif response.type == ProtoDataType.BYTES:  # type: ignore
                return response.y  # type: ignore
            elif response.type == ProtoDataType.STRING:  # type: ignore
                return response.y.decode()  # type: ignore
            elif response.type == ProtoDataType.FLOAT:  # type: ignore
                return struct.unpack("d", response.y)[0]  # type: ignore
            elif response.type == ProtoDataType.INT:  # type: ignore
                return struct.unpack("q", response.y)[0]  # type: ignore
            elif response.type == ProtoDataType.BOOL:  # type: ignore
                return struct.unpack("?", response.y)[0]  # type: ignore
            else:
                raise ValueError(f"Unsupported response type: {response.type}")  # type: ignore

        except grpc.RpcError as e:
            logger.error(f"Call RPC failed: {e}")
            raise e

    async def cleanup(self) -> None:
        """Disconnect from the remote endpoints."""
        async with self._lock:

            async def close_connection(endpoint: str) -> None:
                """Closes connection to a single endpoint"""
                try:
                    if self._channel:
                        await self._channel.close()
                    logger.info(f"Disconnected from endpoint: {endpoint}")
                except Exception as e:
                    logger.error(f"Error disconnecting from {endpoint}: {e}")

            disconnect_tasks = [close_connection(endpoint) for endpoint in self._stubs.keys()]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            self._stubs.clear()
            self._initialized = False

    @property
    def endpoint(self) -> str | list[str]:
        if len(self._endpoints) == 1:
            return self._endpoints[0]
        return self._endpoints
