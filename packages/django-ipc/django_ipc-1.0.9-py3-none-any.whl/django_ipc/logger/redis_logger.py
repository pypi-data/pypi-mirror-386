"""
Redis Stream Logger for RPC calls.

Publishes RPC events to Redis Stream for independent consumers.
This allows WebSocket server to remain independent from Django.
"""

from typing import Any, Dict, Optional
from uuid import UUID
import json
import time

from .logger import RPCLogger
from .config import LoggerConfig


class RedisStreamRPCLogger(RPCLogger):
    """
    RPC Logger that publishes to Redis Stream.

    WebSocket server publishes RPC events to Redis Stream.
    Django (or any other service) can consume these events independently.

    Architecture:
    - WebSocket Server -> Redis Stream (stream:rpc-logs)
    - Django Consumer <- Redis Stream -> Django ORM

    This maintains service independence while enabling centralized logging.

    Example:
        >>> import redis.asyncio as redis
        >>>
        >>> redis_client = redis.from_url("redis://localhost:6379/2")
        >>> logger = RedisStreamRPCLogger(
        ...     config=LoggerConfig(),
        ...     redis_client=redis_client,
        ...     stream_name="stream:rpc-logs"
        ... )
        >>>
        >>> # All RPC calls will be logged to Redis Stream
        >>> await logger.log_rpc_request_async("session.message", {...}, "abc-123")
        >>> await logger.log_rpc_response_async("session.message", {...}, "abc-123", 45.2, True)
    """

    def __init__(
        self,
        config: Optional[LoggerConfig] = None,
        name: str = "django_ipc",
        redis_client = None,  # redis.asyncio.Redis
        stream_name: str = "stream:rpc-logs",
        max_stream_length: int = 10000,
    ):
        """
        Initialize Redis Stream RPC Logger.

        Args:
            config: Logger configuration
            name: Logger name
            redis_client: Redis async client (redis.asyncio.Redis)
            stream_name: Redis Stream name for RPC logs
            max_stream_length: Maximum stream length (MAXLEN ~)
        """
        # Initialize parent (file/console logging)
        super().__init__(config, name)

        self.redis_client = redis_client
        self.stream_name = stream_name
        self.max_stream_length = max_stream_length
        self._redis_available = redis_client is not None

        if self._redis_available:
            self.info(f"✅ Redis Stream logging enabled: {stream_name}")
        else:
            self.warning("⚠️  Redis client not provided, stream logging disabled")

    def log_rpc_request(
        self,
        method: str,
        params: Dict[str, Any],
        correlation_id: str,
        user_id: Optional[str] = None,
        connection_id: Optional[UUID] = None,
    ) -> None:
        """
        Log RPC request to files AND Redis Stream (sync wrapper).

        Args:
            method: RPC method name
            params: Request parameters
            correlation_id: Correlation ID
            user_id: User ID (optional)
            connection_id: Connection ID (optional)
        """
        # Always log to files/console (parent)
        super().log_rpc_request(method, params, correlation_id, user_id, connection_id)

        # Also publish to Redis Stream (async)
        if self._redis_available:
            try:
                # Get current event loop or create new one
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create task in running loop
                        asyncio.create_task(self._publish_rpc_request(
                            method, params, correlation_id, user_id, connection_id
                        ))
                    else:
                        # Run in existing but not running loop
                        loop.run_until_complete(self._publish_rpc_request(
                            method, params, correlation_id, user_id, connection_id
                        ))
                except RuntimeError:
                    # No event loop - create new one
                    asyncio.run(self._publish_rpc_request(
                        method, params, correlation_id, user_id, connection_id
                    ))
            except Exception as e:
                self.error(f"Failed to publish RPC request to Redis: {e}")

    def log_rpc_response(
        self,
        method: str,
        result: Any,
        correlation_id: str,
        duration_ms: float,
        success: bool = True,
        error_code: Optional[str] = None,
    ) -> None:
        """
        Log RPC response to files AND Redis Stream (sync wrapper).

        Args:
            method: RPC method name
            result: Response result
            correlation_id: Correlation ID
            duration_ms: Duration in milliseconds
            success: Whether request succeeded
            error_code: Error code if failed
        """
        # Always log to files/console (parent)
        super().log_rpc_response(method, result, correlation_id, duration_ms, success, error_code)

        # Also publish to Redis Stream (async)
        if self._redis_available:
            try:
                # Get current event loop or create new one
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create task in running loop
                        asyncio.create_task(self._publish_rpc_response(
                            method, result, correlation_id, duration_ms, success, error_code
                        ))
                    else:
                        # Run in existing but not running loop
                        loop.run_until_complete(self._publish_rpc_response(
                            method, result, correlation_id, duration_ms, success, error_code
                        ))
                except RuntimeError:
                    # No event loop - create new one
                    asyncio.run(self._publish_rpc_response(
                        method, result, correlation_id, duration_ms, success, error_code
                    ))
            except Exception as e:
                self.error(f"Failed to publish RPC response to Redis: {e}")

    async def _publish_rpc_request(
        self,
        method: str,
        params: Dict[str, Any],
        correlation_id: str,
        user_id: Optional[str],
        connection_id: Optional[UUID],
    ) -> None:
        """Async helper to publish RPC request."""
        await self._publish_rpc_event(
            event_type="request",
            method=method,
            params=params,
            correlation_id=correlation_id,
            user_id=user_id,
            connection_id=str(connection_id) if connection_id else None,
        )

    async def _publish_rpc_response(
        self,
        method: str,
        result: Any,
        correlation_id: str,
        duration_ms: float,
        success: bool,
        error_code: Optional[str],
    ) -> None:
        """Async helper to publish RPC response."""
        await self._publish_rpc_event(
            event_type="response",
            method=method,
            result=result,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            success=success,
            error_code=error_code,
        )

    async def _publish_rpc_event(
        self,
        event_type: str,
        method: str,
        correlation_id: str,
        params: Optional[Dict] = None,
        result: Optional[Any] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
        error_code: Optional[str] = None,
        user_id: Optional[str] = None,
        connection_id: Optional[str] = None,
    ) -> None:
        """
        Publish RPC event to Redis Stream.

        Args:
            event_type: "request" or "response"
            method: RPC method name
            correlation_id: Correlation ID
            params: Request parameters (for request events)
            result: Response result (for response events)
            duration_ms: Duration in milliseconds (for response events)
            success: Success flag (for response events)
            error_code: Error code (for failed response events)
            user_id: User ID
            connection_id: Connection ID
        """
        try:
            # Build event data
            event_data = {
                "event_type": event_type,
                "method": method,
                "correlation_id": correlation_id,
                "timestamp": int(time.time() * 1000),  # milliseconds
            }

            # Add request-specific fields
            if event_type == "request":
                event_data["params"] = json.dumps(params) if params else "{}"
                if user_id:
                    event_data["user_id"] = user_id
                if connection_id:
                    event_data["connection_id"] = connection_id

            # Add response-specific fields
            elif event_type == "response":
                event_data["success"] = "1" if success else "0"
                if duration_ms is not None:
                    event_data["duration_ms"] = str(int(duration_ms))
                if success:
                    event_data["result"] = json.dumps(result) if result else "{}"
                else:
                    event_data["error_code"] = error_code or "unknown"
                    event_data["error_message"] = str(result) if result else ""

            # Publish to Redis Stream with MAXLEN
            await self.redis_client.xadd(
                name=self.stream_name,
                fields=event_data,
                maxlen=self.max_stream_length,  # Limit stream size
                approximate=True,  # ~MAXLEN for performance
            )

        except Exception as e:
            # Don't crash if Redis fails, just log it
            self.warning(f"Failed to publish RPC event to Redis: {e}")


__all__ = [
    "RedisStreamRPCLogger",
]
