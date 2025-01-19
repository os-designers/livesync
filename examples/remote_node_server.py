import asyncio
import logging

from livesync.prebuilt.nodes import ResolutionNode, RemoteNodeServer


async def serve() -> None:
    server = RemoteNodeServer(supported_nodes={"resolution_node": ResolutionNode}, port=50051, max_workers=10)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
