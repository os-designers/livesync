import struct
import traceback
from typing import Any, Callable, Awaitable

import grpc  # type: ignore
from google.protobuf.json_format import MessageToDict

from ....types import BytesableType
from ...._utils.logs import logger
from ....frames.audio_frame import AudioFrame
from ....frames.video_frame import VideoFrame
from ...._protos.remote_layer.remote_layer_pb2 import (
    DataType,
    CallRequest,
    InitRequest,
    CallResponse,
    InitResponse,
)
from ...._protos.remote_layer.remote_layer_pb2_grpc import RemoteLayerServicer as _RemoteLayerServicer  # type: ignore


class RemoteLayerServicer(_RemoteLayerServicer):
    """
    gRPC servicer for remote callable layer operations.

    Parameters
    ----------
    on_call : Callable[..., Awaitable[BytesableType | None]]
        The lambda layer to be used for the remote callable layer.
    on_init : Callable[..., Awaitable[None]] | None, optional
        The lambda layer to be used for the remote callable layer.
    """

    def __init__(
        self,
        on_call: Callable[..., Awaitable[BytesableType | None]],
        on_init: Callable[..., Awaitable[None]] | None = None,
    ):
        self._on_call = on_call
        self._on_init = on_init
        self._initialized = False if on_init else True

    async def Init(
        self,
        request: InitRequest,
        context: grpc.aio.ServicerContext[Any, Any],  # noqa: ARG002
    ) -> InitResponse:
        """
        Initialize the server with settings.

        Parameters
        ----------
        request : remote_layer_pb2.InitRequest
            Configuration request containing node settings.
        context : grpc.aio.ServicerContext
            gRPC service context.

        Returns
        -------
        remote_node_pb2.ConfigureResponse
            Response indicating success or failure of configuration.
        """
        try:
            settings = MessageToDict(request.settings)
            if self._on_init:
                await self._on_init(self, **settings)
            self._initialized = True
            return InitResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            logger.error(traceback.format_exc())
            return InitResponse(success=False, error_message=str(e))

    async def Call(
        self,
        request: CallRequest,
        context: grpc.aio.ServicerContext[Any, Any],  # noqa: ARG002
    ) -> CallResponse:
        """
        Process a single step with the configured node.

        Parameters
        ----------
        request : remote_node_pb2.StepRequest
            Request containing the target frame to process.
        context : grpc.aio.ServicerContext
            gRPC service context.

        Returns
        -------
        remote_node_pb2.StepResponse
            Response containing the processed frame or error message.
        """
        if not self._initialized:
            logger.error("Layer not initialized. Call Init first.")
            return CallResponse(success=False, error_message="Layer not initialized. Call Init first.")

        try:
            x: BytesableType

            if request.type == DataType.VIDEO_FRAME:
                x = VideoFrame.frombytes(request.x)
            elif request.type == DataType.AUDIO_FRAME:
                x = AudioFrame.frombytes(request.x)
            elif request.type == DataType.BYTES:
                x = request.x
            elif request.type == DataType.STRING:
                x = request.x.decode()
            elif request.type == DataType.FLOAT:
                x = struct.unpack("d", request.x)[0]
            elif request.type == DataType.INT:
                x = struct.unpack("q", request.x)[0]
            elif request.type == DataType.BOOL:
                x = struct.unpack("?", request.x)[0]
            else:
                raise ValueError(f"Unsupported type: {request.type}")

            # Call handler with converted input
            y: BytesableType | None = await self._on_call(self, x)

            # Prepare response based on output type
            if y is None:
                return CallResponse(success=True, y=None, type=DataType.NONE)
            elif isinstance(y, VideoFrame):
                return CallResponse(success=True, y=bytes(y), type=DataType.VIDEO_FRAME)
            elif isinstance(y, AudioFrame):
                return CallResponse(success=True, y=bytes(y), type=DataType.AUDIO_FRAME)
            elif isinstance(y, bytes):
                return CallResponse(success=True, y=y, type=DataType.BYTES)
            elif isinstance(y, str):
                return CallResponse(success=True, y=y.encode(), type=DataType.STRING)
            elif isinstance(y, float):
                return CallResponse(success=True, y=struct.pack("d", y), type=DataType.FLOAT)
            elif isinstance(y, bool):
                return CallResponse(success=True, y=struct.pack("?", y), type=DataType.BOOL)
            elif isinstance(y, int):  # type: ignore[redundant-isinstance]
                return CallResponse(success=True, y=struct.pack("q", y), type=DataType.INT)
            else:
                return CallResponse(  # type: ignore[unreachable]
                    success=False, y=y, type=DataType.UNKNOWN, error_message=f"Unsupported return type: {type(y)}"
                )

        except Exception as e:
            logger.error(f"Error during Call: {e}")
            logger.error(traceback.format_exc())
            return CallResponse(success=False, type=DataType.NONE, error_message=str(e))

    @property
    def initialized(self) -> bool:
        return self._initialized
