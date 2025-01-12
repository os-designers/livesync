import asyncio
from typing import Type, Generic, TypeVar, Protocol
from logging import getLogger
from datetime import datetime
from dataclasses import dataclass

import grpc  # type: ignore


class GrpcStub(Protocol):
    def __init__(self, channel: grpc.aio.Channel) -> None: ...


logger = getLogger(__name__)
StubT = TypeVar("StubT", bound=GrpcStub)


@dataclass
class GrpcConnection(Generic[StubT]):
    """Holds connection details for a single gRPC endpoint"""

    channel: grpc.aio.Channel
    stub: StubT
    last_error_time: datetime | None = None
    error_count: int = 0


class GrpcConnectionManager(Generic[StubT]):
    """Manages gRPC connections to multiple endpoints with authentication"""

    def __init__(
        self,
        endpoints: list[str],
        stub_class: Type[StubT],
        max_message_size: int = 10 * 1024 * 1024,  # 10 MB
        max_metadata_size: int = 1 * 1024 * 1024,  # 1 MB
    ):
        self.endpoints = endpoints
        self.stub_class = stub_class
        self.connections: dict[str, GrpcConnection[StubT]] = {}
        self._lock = asyncio.Lock()

        self.channel_options = [
            ("grpc.max_receive_message_length", max_message_size),
            ("grpc.max_send_message_length", max_message_size),
            ("grpc.max_metadata_size", max_metadata_size),
        ]

    async def connect(self) -> None:
        """Establishes connections to all configured endpoints"""
        logger.debug(f"Connecting to {len(self.endpoints)} endpoints")

        connection_tasks = [self._establish_connection(endpoint) for endpoint in self.endpoints]
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        successful_connections = sum(1 for r in results if not isinstance(r, Exception))

        logger.debug(f"Successful connections: {successful_connections}")
        if successful_connections == 0:
            logger.error(f"Failed to connect to any endpoints")
            raise grpc.RpcError("Failed to connect to any endpoints")

    async def disconnect(self) -> None:
        """Closes all endpoint connections gracefully"""
        async with self._lock:
            disconnect_tasks = [self._close_connection(endpoint, conn) for endpoint, conn in self.connections.items()]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            self.connections.clear()

    async def _establish_connection(self, endpoint: str) -> None:
        """Establishes connection to a single endpoint with authentication"""
        try:
            channel = grpc.aio.insecure_channel(
                endpoint,
                options=self.channel_options,
            )
            await channel.channel_ready()

            stub = self.stub_class(channel)

            async with self._lock:
                self.connections[endpoint] = GrpcConnection[StubT](channel=channel, stub=stub)
                logger.info(f"Successfully connected endpoint: {endpoint}")

        except Exception as e:
            logger.error(f"Failed to connect to {endpoint}: {e}")
            raise grpc.RpcError(f"Connection failed to {endpoint}: {str(e)}") from e

    async def _close_connection(self, endpoint: str, conn: GrpcConnection[StubT]) -> None:
        """Closes connection to a single endpoint"""
        try:
            await conn.channel.close()
            logger.info(f"Disconnected from endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Error disconnecting from {endpoint}: {e}")

    def get_stub(self, endpoint: str) -> StubT | None:
        """Returns the stub for a specific endpoint if available"""
        connection = self.connections.get(endpoint)
        return connection.stub if connection else None

    def get_active_endpoints(self) -> list[str]:
        """Returns a list of currently active endpoint addresses"""
        return list(self.connections.keys())
