import sys
import signal
import asyncio
import logging
import traceback
from typing import Any
from concurrent import futures
from typing_extensions import override

import grpc  # type: ignore

from livesync import VideoFrame
from livesync.nodes import BaseNode, FrameRateNode, ResolutionNode
from livesync._protos.remote_node import remote_node_pb2, remote_node_pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


logger = logging.getLogger(__name__)


def create_processor(name: str, config: dict[str, Any]) -> BaseNode:
    """
    Factory function that returns a processor instance for the given name/config.
    Raise ValueError if the processor name is unknown.
    """
    if name == "frame_rate":
        return FrameRateNode(target_fps=int(config["target_fps"]))
    elif name == "resolution":
        return ResolutionNode(target_height=int(config["target_height"]))
    else:
        raise ValueError(f"Unknown processor: {name}")


class RemoteNodeServicer(remote_node_pb2_grpc.RemoteNodeServicer):
    def __init__(self):
        self._processor_chain: list[BaseNode] = []
        self._is_service_ready = False

    # -------------------------------------------------------------------------
    # HealthCheck
    # -------------------------------------------------------------------------
    @override
    async def HealthCheck(
        self, request: remote_node_pb2.HealthCheckRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> remote_node_pb2.HealthCheckResponse:
        return remote_node_pb2.HealthCheckResponse(
            is_healthy=self._is_service_ready,
            status_message="Service is ready" if self._is_service_ready else "Service is not configured yet",
        )

    # -------------------------------------------------------------------------
    # ConfigureProcessors
    # -------------------------------------------------------------------------
    @override
    async def ConfigureProcessors(
        self, request: remote_node_pb2.ConfigProcessorsRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> remote_node_pb2.ConfigProcessorsResponse:
        """
        Configure the server with a set of processors (and their settings).
        This replaces any previously existing chain of processors.
        """
        try:
            logger.info("Configuring processors...")

            # Build a new chain from the request
            new_chain: list[BaseNode] = []
            for proc_conf in request.processors:
                # Convert the proto map<string,string> to a regular dict
                config_dict = dict(proc_conf.settings)
                logger.info(f"Configuring processor: {proc_conf.name} with settings: {config_dict}")
                processor_instance = create_processor(proc_conf.name, config_dict)
                new_chain.append(processor_instance)

            # Only assign to our chain if everything succeeds
            self._processor_chain = new_chain
            self._is_service_ready = len(self._processor_chain) > 0

            logger.info(f"Configured {len(self._processor_chain)} processors successfully.")
            return remote_node_pb2.ConfigProcessorsResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to configure processors: {e}")
            logger.error(traceback.format_exc())
            return remote_node_pb2.ConfigProcessorsResponse(success=False, error_message=str(e))

    # -------------------------------------------------------------------------
    # ProcessFrame
    # -------------------------------------------------------------------------
    @override
    async def ProcessFrame(
        self, request: remote_node_pb2.ProcessFrameRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> remote_node_pb2.ProcessFrameResponse:
        if not self._is_service_ready:
            return remote_node_pb2.ProcessFrameResponse(
                success=False, error_message="Service not configured. Call ConfigureProcessors first."
            )

        try:
            # Parse the incoming frame
            frame = VideoFrame.frombytes(request.target_frame)

            # Apply each processor in sequence
            for processor in self._processor_chain:
                if frame:
                    frame = await processor.process_frame(frame)  # type: ignore

            # Serialize the transformed frame
            return remote_node_pb2.ProcessFrameResponse(
                success=True, processed_frame=frame.tobytes() if frame else None
            )
        except Exception as e:
            logging.error(f"Error during ProcessFrame: {e}")
            logging.error(traceback.format_exc())
            return remote_node_pb2.ProcessFrameResponse(success=False, error_message=str(e))

    # async def UpdateSourceImage(
    #     self, request: media_transformation_pb2.UpdateSourceImageRequest, context: grpc.aio.ServicerContext
    # ) -> media_transformation_pb2.UpdateSourceImageResponse:
    #     try:
    #         source_image = np.frombuffer(request.source_image, dtype=np.uint8)
    #         if source_image.size == 0:
    #             self.source_face = None
    #             return media_transformation_pb2.UpdateSourceImageResponse(success=True)

    #         decoded_image = cv2.imdecode(source_image, cv2.IMREAD_COLOR)

    #         faces = get_many_faces([decoded_image])
    #         self.source_face = faces[0] if faces else None

    #         if not self.source_face:
    #             return media_transformation_pb2.UpdateSourceImageResponse(
    #                 success=False, error_message="No faces detected in source image"
    #             )

    #         return media_transformation_pb2.UpdateSourceImageResponse(success=True)

    #     except Exception as e:
    #         logger.error(f"Error during UpdateSourceImage: {str(e)}")
    #         logger.error(traceback.format_exc())
    #         return media_transformation_pb2.UpdateSourceImageResponse(
    #             success=False, error_message=f"Processing error: {str(e)}"
    #         )

    # async def UpdateSourceVoice(
    #     self, request: media_transformation_pb2.UpdateSourceVoiceRequest, context: grpc.aio.ServicerContext
    # ) -> media_transformation_pb2.UpdateSourceVoiceResponse:
    #     raise NotImplementedError("UpdateSourceVoice is not implemented")


class GRPCServer:
    def __init__(self, port: int = 50051, max_workers: int = 10, options: list[tuple[str, Any]] = []):
        self._servicer = RemoteNodeServicer()
        self._server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=max_workers), options=options)
        self._port = port
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        try:
            remote_node_pb2_grpc.add_RemoteNodeServicer_to_server(self._servicer, self._server)  # type: ignore
            self._server.add_insecure_port(f"[::]:{self._port}")
            await self._server.start()
            logger.info(f"Server started on port {self._port}")

            # Wait for termination signals (SIGTERM or SIGINT)
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.stop()))
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.stop()))

            await self._shutdown_event.wait()
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            sys.exit(1)

    async def stop(self) -> None:
        if self._server:
            logger.info("Stopping server...")
            await self._server.stop(grace=5)
            logger.info("Server stopped")

        self._shutdown_event.set()


async def main() -> None:
    try:
        logger.info("Initializing server...")
        server = GRPCServer(
            port=50051,
            max_workers=10,
            options=[
                ("grpc.max_receive_message_length", 10 * 1024 * 1024),  # 10MB
                ("grpc.max_send_message_length", 10 * 1024 * 1024),  # 10MB
                ("grpc.max_metadata_size", 10 * 1024 * 1024),  # 10MB
            ],
        )
        logger.info("Starting server...")
        await server.start()
        logger.info("Server started")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
