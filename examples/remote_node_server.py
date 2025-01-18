import asyncio

from livesync.prebuilt.nodes import ResolutionNode, RemoteNodeServer

if __name__ == "__main__":
    server = RemoteNodeServer(supported_nodes={"resolution_node": ResolutionNode}, port=50051, max_workers=10)
    asyncio.run(server.start())
