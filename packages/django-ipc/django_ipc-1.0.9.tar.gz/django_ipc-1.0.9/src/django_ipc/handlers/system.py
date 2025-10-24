"""
System Handler for RPC Bridge Testing and Diagnostics.

Provides built-in test methods to verify RPC bridge functionality.
"""

import time
import asyncio
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .base import BaseHandler
from ..server.connection_manager import ActiveConnection
from ..server.message_router import MessageRouter


# =============================================================================
# Pydantic Models
# =============================================================================


class PingParams(BaseModel):
    """Ping test parameters."""

    message: str = Field(default="ping", description="Message to echo back")
    delay_ms: int = Field(default=0, ge=0, le=5000, description="Response delay in milliseconds (0-5000)")


class EchoParams(BaseModel):
    """Echo test parameters."""

    data: Dict[str, Any] = Field(..., description="Data to echo back")


class LatencyTestParams(BaseModel):
    """Latency test parameters."""

    iterations: int = Field(default=10, ge=1, le=100, description="Number of iterations (1-100)")


# =============================================================================
# System Handler
# =============================================================================


class SystemHandler(BaseHandler):
    """
    System diagnostic handler for RPC bridge testing.

    RPC Methods:
        - system.ping: Simple ping/pong test
        - system.echo: Echo back any data structure
        - system.latency: Measure round-trip latency
        - system.health: Get server health status
        - system.info: Get server information

    Example:
        >>> from django_ipc.handlers import SystemHandler
        >>> handler = SystemHandler(connection_manager)
        >>> # Methods are automatically available via RPC
    """

    async def initialize(self) -> None:
        """Initialize system handler."""
        self._log_info("System diagnostic handler initialized")

    def register(self, router: MessageRouter) -> None:
        """Register system methods with router."""
        if not self.enabled:
            self._log_info("System handler disabled, skipping registration")
            return

        @router.register("system.ping")
        async def handle_ping(conn: ActiveConnection, params: PingParams):
            return await self.ping(conn, params.model_dump())

        @router.register("system.echo")
        async def handle_echo(conn: ActiveConnection, params: EchoParams):
            return await self.echo(conn, params.model_dump())

        @router.register("system.latency")
        async def handle_latency(conn: ActiveConnection, params: LatencyTestParams):
            return await self.latency_test(conn, params.model_dump())

        @router.register("system.health")
        async def handle_health(conn: ActiveConnection, params: Dict[str, Any]):
            return await self.health(conn, params)

        @router.register("system.info")
        async def handle_info(conn: ActiveConnection, params: Dict[str, Any]):
            return await self.info(conn, params)

        self._log_info("Registered system diagnostic methods")

    async def ping(self, conn: ActiveConnection, params: dict) -> dict:
        """
        Simple ping/pong test with optional delay.

        Args:
            conn: Active connection
            params: Ping parameters (message, delay_ms)

        Returns:
            Pong response with timing

        Example:
            >>> await client.system_ping({"message": "hello", "delay_ms": 100})
            {"pong": "hello", "timestamp": "2025-10-24T...", "delay_ms": 100}
        """
        validated = PingParams.model_validate(params)

        # Optional delay for latency testing
        if validated.delay_ms > 0:
            await asyncio.sleep(validated.delay_ms / 1000.0)

        return {
            "pong": validated.message,
            "timestamp": time.time(),
            "delay_ms": validated.delay_ms,
            "server_time": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        }

    async def echo(self, conn: ActiveConnection, params: dict) -> dict:
        """
        Echo back any data structure.

        Args:
            conn: Active connection
            params: Echo parameters (data)

        Returns:
            Echo response with metadata

        Example:
            >>> data = {"foo": "bar", "nested": {"value": 123}}
            >>> await client.system_echo({"data": data})
            {"echo": {...}, "size": 123, "timestamp": ...}
        """
        validated = EchoParams.model_validate(params)

        import json

        serialized = json.dumps(validated.data)

        return {
            "echo": validated.data,
            "size": len(serialized),
            "timestamp": time.time(),
            "type": type(validated.data).__name__,
        }

    async def latency_test(self, conn: ActiveConnection, params: dict) -> dict:
        """
        Measure server processing latency.

        Args:
            conn: Active connection
            params: Latency test parameters (iterations)

        Returns:
            Latency statistics

        Example:
            >>> await client.system_latency({"iterations": 10})
            {"iterations": 10, "min_ms": 0.1, "max_ms": 0.5, "avg_ms": 0.3}
        """
        validated = LatencyTestParams.model_validate(params)

        latencies = []
        for _ in range(validated.iterations):
            start = time.perf_counter()
            # Simulate minimal work
            await asyncio.sleep(0.001)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        return {
            "iterations": validated.iterations,
            "min_ms": round(min(latencies), 3),
            "max_ms": round(max(latencies), 3),
            "avg_ms": round(sum(latencies) / len(latencies), 3),
            "p50_ms": round(sorted(latencies)[len(latencies) // 2], 3),
            "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 3),
            "p99_ms": round(sorted(latencies)[int(len(latencies) * 0.99)], 3),
        }

    async def health(self, conn: ActiveConnection, params: dict) -> dict:
        """
        Get server health status.

        Args:
            conn: Active connection
            params: Empty params

        Returns:
            Health status

        Example:
            >>> await client.system_health({})
            {"status": "ok", "uptime_seconds": 3600, "connections": 5}
        """
        if not self.connection_manager:
            return {
                "status": "ok",
                "message": "Health check passed (no connection manager)",
            }

        stats = await self.connection_manager.get_stats()

        return {
            "status": "ok",
            "timestamp": time.time(),
            "connections": {
                "total": stats.total_connections,
                "authenticated": stats.authenticated_connections,
                "unique_users": stats.unique_users,
            },
            "rooms": len(stats.rooms),
        }

    async def info(self, conn: ActiveConnection, params: dict) -> dict:
        """
        Get server information.

        Args:
            conn: Active connection
            params: Empty params

        Returns:
            Server info

        Example:
            >>> await client.system_info({})
            {"version": "1.0.8", "protocol": "websocket", ...}
        """
        try:
            from ..utils.version_checker import get_server_version
            version = get_server_version()
        except:
            version = "unknown"

        return {
            "version": version,
            "protocol": "websocket",
            "rpc": {
                "timeout": 30,
                "max_message_size": 1024 * 1024,  # 1MB
            },
            "features": [
                "ping",
                "echo",
                "latency_test",
                "health_check",
                "notifications",
                "broadcasts",
                "rooms",
            ],
        }


__all__ = ["SystemHandler"]
