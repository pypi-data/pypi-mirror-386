"""
ORM Logger Extension for Django RPC Logging.

Extends RPCLogger to save all RPC calls to Django database.
"""

import os
import sys
from typing import Any, Dict, Optional
from uuid import UUID

from .logger import RPCLogger
from .config import LoggerConfig


class ORMRPCLogger(RPCLogger):
    """
    Extended RPC Logger that saves to Django ORM.

    Inherits all file/console logging from RPCLogger and adds Django database logging.

    Features:
    - Saves all RPC requests/responses to Django database
    - Automatically tracks user, duration, success/failure
    - Works independently - even if Django app not available, falls back to file logging
    - Thread-safe and async-safe

    Example:
        >>> from django_ipc.logger import ORMRPCLogger, LoggerConfig
        >>>
        >>> config = LoggerConfig(log_rpc_calls=True)
        >>> logger = ORMRPCLogger(config, name="websocket_server")
        >>>
        >>> # All RPC calls will be logged to both files AND Django ORM
        >>> logger.log_rpc_request("session.message", {"content": "hello"}, "abc-123")
        >>> logger.log_rpc_response("session.message", {"success": True}, "abc-123", 45.2, True)
    """

    def __init__(
        self,
        config: Optional[LoggerConfig] = None,
        name: str = "django_ipc",
        enable_orm_logging: bool = True,
    ):
        """
        Initialize ORM RPC Logger.

        Args:
            config: Logger configuration
            name: Logger name
            enable_orm_logging: Enable Django ORM logging (default: True)
        """
        # Initialize parent (file/console logging)
        super().__init__(config, name)

        self.enable_orm_logging = enable_orm_logging
        self._django_available = False
        self._rplog_model = None
        self._pending_logs = {}  # correlation_id -> log_entry

        # Try to import Django models
        if enable_orm_logging:
            self._init_django()

    def _init_django(self) -> None:
        """Initialize Django connection for ORM logging."""
        try:
            # Check if Django is available
            import django
            from django.conf import settings

            # Setup Django if not configured
            if not settings.configured:
                # Get Django settings module from environment
                django_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
                if django_settings:
                    django.setup()
                else:
                    self.warning("Django not configured, ORM logging disabled")
                    return

            # Import RPCLog model
            try:
                from django_cfg.apps.ipc.models import RPCLog
                self._rpc_log_model = RPCLog
                self._django_available = True
                self.info("✅ Django ORM logging enabled")
            except ImportError as e:
                self.warning(f"RPCLog model not found: {e}. ORM logging disabled.")

        except ImportError:
            self.debug("Django not available, using file logging only")
        except Exception as e:
            self.warning(f"Failed to initialize Django ORM logging: {e}")

    def log_rpc_request(
        self,
        method: str,
        params: Dict[str, Any],
        correlation_id: str,
        user_id: Optional[str] = None,
        connection_id: Optional[UUID] = None,
    ) -> None:
        """
        Log RPC request to files AND Django ORM.

        Args:
            method: RPC method name
            params: Request parameters
            correlation_id: Correlation ID
            user_id: User ID (optional)
            connection_id: Connection ID (optional)
        """
        # Always log to files/console (parent)
        super().log_rpc_request(method, params, correlation_id, user_id, connection_id)

        # Also log to Django ORM if available
        if self._django_available and self._rpc_log_model:
            try:
                self._create_orm_log(
                    method=method,
                    params=params,
                    correlation_id=correlation_id,
                    user_id=user_id,
                )
            except Exception as e:
                self.error(f"Failed to create ORM log entry: {e}", exc_info=True)

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
        Log RPC response to files AND Django ORM.

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

        # Also update Django ORM if available
        if self._django_available and self._rpc_log_model:
            try:
                self._update_orm_log(
                    correlation_id=correlation_id,
                    result=result,
                    duration_ms=duration_ms,
                    success=success,
                    error_code=error_code,
                )
            except Exception as e:
                self.error(f"Failed to update ORM log entry: {e}", exc_info=True)

    def _create_orm_log(
        self,
        method: str,
        params: Dict[str, Any],
        correlation_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Create ORM log entry for request.

        Args:
            method: RPC method name
            params: Request parameters
            correlation_id: Correlation ID
            user_id: User ID (optional)
        """
        try:
            from django.contrib.auth import get_user_model

            # Get user instance if user_id provided
            user = None
            if user_id:
                try:
                    User = get_user_model()
                    user = User.objects.get(pk=user_id)
                except Exception:
                    pass  # User not found, continue without user

            # Create log entry
            log_entry = self._rpc_log_model.objects.create(
                correlation_id=correlation_id,
                method=method,
                params=params,
                user=user,
                status='pending',
            )

            # Store in pending logs for later update
            self._pending_logs[correlation_id] = log_entry

        except Exception as e:
            self.warning(f"Failed to create ORM log: {e}")

    def _update_orm_log(
        self,
        correlation_id: str,
        result: Any,
        duration_ms: float,
        success: bool,
        error_code: Optional[str] = None,
    ) -> None:
        """
        Update ORM log entry with response.

        Args:
            correlation_id: Correlation ID
            result: Response result
            duration_ms: Duration in milliseconds
            success: Whether request succeeded
            error_code: Error code if failed
        """
        try:
            # Try to get from pending logs first (faster)
            log_entry = self._pending_logs.pop(correlation_id, None)

            # If not in pending, try database lookup
            if not log_entry:
                try:
                    log_entry = self._rpc_log_model.objects.get(correlation_id=correlation_id)
                except self._rpc_log_model.DoesNotExist:
                    self.warning(f"ORM log entry not found for correlation_id: {correlation_id}")
                    return

            # Update with response
            if success:
                log_entry.mark_success(
                    response_data=result,
                    duration_ms=int(duration_ms),
                )
            else:
                error_message = result if isinstance(result, str) else str(result)
                log_entry.mark_failed(
                    error_code=error_code or 'unknown',
                    error_message=error_message,
                    duration_ms=int(duration_ms),
                )

        except Exception as e:
            self.warning(f"Failed to update ORM log: {e}")


__all__ = [
    "ORMRPCLogger",
]
