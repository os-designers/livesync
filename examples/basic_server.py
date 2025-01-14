import sys
import signal
import asyncio
import logging
import traceback
from typing import Any
from concurrent import futures

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
        self._is_ready = False

    # -------------------------------------------------------------------------
    # HealthCheck
    # -------------------------------------------------------------------------
    async def HealthCheck(
        self, request: remote_node_pb2.HealthCheckRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> remote_node_pb2.HealthCheckResponse:
        return remote_node_pb2.HealthCheckResponse(
            is_healthy=self._is_ready,
            status_message="Service is ready" if self._is_ready else "Service is not configured yet",
        )

    # -------------------------------------------------------------------------
    # ConfigureProcessors
    # -------------------------------------------------------------------------
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
            self._is_ready = len(self._processor_chain) > 0

            logger.info(f"Configured {len(self._processor_chain)} processors successfully.")
            return remote_node_pb2.ConfigProcessorsResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to configure processors: {e}")
            logger.error(traceback.format_exc())
            return remote_node_pb2.ConfigProcessorsResponse(success=False, error_message=str(e))

    # -------------------------------------------------------------------------
    # ProcessFrame
    # -------------------------------------------------------------------------
    async def ProcessFrame(
        self, request: remote_node_pb2.ProcessFrameRequest, context: grpc.aio.ServicerContext[Any, Any]
    ) -> remote_node_pb2.ProcessFrameResponse:
        if not self._is_ready:
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


async def main() -> None:
    try:
        logger.info("Initializing server...")

        # Server setup
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ("grpc.max_receive_message_length", 10 * 1024 * 1024),  # 10MB
                ("grpc.max_send_message_length", 10 * 1024 * 1024),  # 10MB
                ("grpc.max_metadata_size", 10 * 1024 * 1024),  # 10MB
            ],
        )

        # Add service and port
        remote_node_pb2_grpc.add_RemoteNodeServicer_to_server(RemoteNodeServicer(), server)  # type: ignore
        server.add_insecure_port("[::]:50051")

        # Start server
        await server.start()
        logger.info("Server started on port 50051")

        # Handle termination signals
        shutdown_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        async def stop_server():
            logger.info("Stopping server...")
            await server.stop(grace=5)
            logger.info("Server stopped")
            shutdown_event.set()

        loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(stop_server()))
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(stop_server()))

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
