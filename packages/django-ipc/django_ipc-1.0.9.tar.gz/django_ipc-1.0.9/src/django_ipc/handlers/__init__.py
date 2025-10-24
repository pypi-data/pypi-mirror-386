"""
Built-in WebSocket Handlers.

Provides ready-to-use handlers for common WebSocket operations.

Example:
    >>> from django_ipc.handlers import (
    ...     BaseHandler,
    ...     NotificationHandler,
    ...     BroadcastHandler,
    ...     SystemHandler,
    ... )
"""

from .base import BaseHandler
from .notification import NotificationHandler
from .broadcast import BroadcastHandler
from .system import SystemHandler

__all__ = [
    "BaseHandler",
    "NotificationHandler",
    "BroadcastHandler",
    "SystemHandler",
]
