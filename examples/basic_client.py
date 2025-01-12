import signal
import asyncio
from logging import getLogger

from livesync import Graph
from livesync.nodes import WebcamNode
from livesync.nodes.presets.livesync import ProcessorConfig, LivesyncRemoteNode

logger = getLogger(__name__)


async def main():
    shutdown_event = asyncio.Event()

    graph = Graph()

    # Add a webcam node
    webcam_node = WebcamNode(id="webcam", concurrent=True)
    graph.add_node(webcam_node)

    # Add a frame rate node
    frame_rate_node = LivesyncRemoteNode(
        endpoints=["localhost:50051"],
        configs=[ProcessorConfig(name="frame_rate", settings={"target_fps": "5"})],
    )
    graph.add_node(frame_rate_node)

    # Connect the nodes
    graph.add_edge(webcam_node, frame_rate_node)

    await graph.start()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown_event.set()))  # type: ignore
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown_event.set()))  # type: ignore

    await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
    print("Done")
