from typing import Any, Type
from typing_extensions import override

import grpc  # type: ignore
from google.protobuf.json_format import MessageToDict

from .....core.nodes import Node
from .....utils.logs import logger
from .....core.frames import VideoFrame
from ....._protos.remote_node.remote_node_pb2 import StepRequest, StepResponse, ConfigureRequest, ConfigureResponse
from ....._protos.remote_node.remote_node_pb2_grpc import RemoteNodeServicer as _RemoteNodeServicer  # type: ignore


class RemoteNodeServicer(_RemoteNodeServicer):
    """
    gRPC servicer for remote node operations.

    Parameters
    ----------
    supported_nodes : dict[str, Type[Node]]
        Dictionary mapping node names to their corresponding Node classes.
    """

    def __init__(self, supported_nodes: dict[str, Type[Node]]):
        self._node: Node | None = None
        self._supported_nodes = supported_nodes

    @override
    async def Configure(
        self, request: ConfigureRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> ConfigureResponse:
        """
        Configure the server with settings.

        Parameters
        ----------
        request : remote_node_pb2.ConfigureRequest
            Configuration request containing node settings.
        context : grpc.aio.ServicerContext
            gRPC service context.

        Returns
        -------
        remote_node_pb2.ConfigureResponse
            Response indicating success or failure of configuration.
        """
        try:
            logger.info("Configuring node...")

            settings = MessageToDict(request.settings)

            if len(settings.keys()) != 1:
                raise ValueError("Only one node is supported at a time")

            node_name = list(settings.keys())[0]
            self._node = self._supported_nodes[node_name](**settings[node_name])

            logger.info(f"Configured {node_name} successfully.")
            return ConfigureResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to configure processors: {e}")
            return ConfigureResponse(success=False, error_message=str(e))

    @override
    async def Step(self, request: StepRequest, context: grpc.aio.ServicerContext[Any, Any]) -> StepResponse:
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
        if not self._node:
            return StepResponse(success=False, error_message="Node not configured. Call Configure first.")

        try:
            frame = VideoFrame.frombytes(request.target_frame)
            return StepResponse(success=True, processed_frame=frame.tobytes() if frame else None)
        except Exception as e:
            logger.error(f"Error during Step: {e}")
            return StepResponse(success=False, error_message=str(e))
