import asyncio
from abc import ABC
from logging import getLogger
from dataclasses import field, dataclass
from typing_extensions import override

import grpc  # type: ignore

from ...remote_node import RemoteNode
from ....frames.base_frame import BaseFrame
from ....frames.audio_frame import AudioFrame
from ....frames.video_frame import VideoFrame
from ...._protos.remote_node import remote_node_pb2_grpc
from ...._lib.grpc_connection_manager import GrpcConnectionManager
from ...._protos.remote_node.remote_node_pb2 import (
    ProcessorConfig,
    HealthCheckRequest,
    HealthCheckResponse,
    ProcessFrameRequest,
    ProcessFrameResponse,
    ConfigProcessorsRequest,
    ConfigProcessorsResponse,
)

logger = getLogger(__name__)


@dataclass
class LivesyncRemoteNode(RemoteNode, ABC):
    """Concrete node implementation that uses gRPC to process frames."""

    configs: list[ProcessorConfig] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self._connection_manager = GrpcConnectionManager(self.endpoints, remote_node_pb2_grpc.RemoteNodeStub)

    @override
    async def _connect(self):
        if not self.configs:
            raise ValueError("Configs are required")

        try:
            await self._connection_manager.connect()
            await self.health_check()
            await self.configure_processors(self.configs)
            logger.debug(f"[{self.__class__.__name__}] Successfully connected to endpoints: {self.endpoints}")
        except Exception as e:
            logger.error(f"Error connecting to gRPC endpoints: {e}")
            raise e

    async def health_check(self) -> None:
        try:
            request = HealthCheckRequest()
            responses: list[HealthCheckResponse] = await asyncio.gather(
                *[
                    self._connection_manager.get_stub(ep).HealthCheck(request)  # type: ignore[func-returns-value]
                    for ep in self._connection_manager.endpoints
                ]
            )

            for endpoint, response in zip(self._connection_manager.endpoints, responses):
                logger.info(
                    f"HealthCheck for {endpoint}:"
                    f"  is_healthy = {response.is_healthy}"
                    f"  status_message = {response.status_message}"
                )

        except grpc.RpcError as e:
            logger.error("HealthCheck RPC failed:", e)
            raise e

    @override
    async def _disconnect(self):
        try:
            await self._connection_manager.disconnect()
            logger.debug(f"[{self.__class__.__name__}] Successfully disconnected from endpoints: {self.endpoints}")
        except Exception as e:
            logger.error(f"Error disconnecting from gRPC endpoints: {e}")
            raise e

    async def configure_processors(self, configs: list[ProcessorConfig]) -> None:
        try:
            request = ConfigProcessorsRequest(processors=configs)
            responses: list[ConfigProcessorsResponse] = await asyncio.gather(
                *[
                    self._connection_manager.get_stub(ep).ConfigureProcessors(request)  # type: ignore[func-returns-value]
                    for ep in self._connection_manager.endpoints
                ]
            )
            for endpoint, response in zip(self._connection_manager.endpoints, responses):
                logger.info(
                    f"ConfigureProcessors response for {endpoint}: "
                    f"  success = {response.success} "
                    f"  error_message = {response.error_message}"
                )

        except grpc.RpcError as e:
            raise e

    @override
    async def process_frame(self, frame: BaseFrame) -> BaseFrame | None:
        """Send frame to remote gRPC service and receive processed frame."""
        try:
            endpoint = await self._selector.next()
            stub = self._connection_manager.get_stub(endpoint)
            if not stub:
                raise Exception(f"No active stub for endpoint {endpoint}")

            request = ProcessFrameRequest(target_frame=frame.tobytes())
            response: ProcessFrameResponse = await stub.ProcessFrame(request)  # type: ignore

            if not response.success:  # type: ignore
                logger.error(f"Error processing frame on gRPC: {response.error_message}")  # type: ignore
                return None

            if len(response.processed_frame) == 0:  # type: ignore[arg-type]
                return None
            elif isinstance(frame, VideoFrame):
                return VideoFrame.frombytes(response.processed_frame)  # type: ignore
            elif isinstance(frame, AudioFrame):
                return AudioFrame.frombytes(response.processed_frame)  # type: ignore

            return None
        except grpc.RpcError as e:
            logger.error(f"ProcessFrame RPC failed: {e}")
            raise e
