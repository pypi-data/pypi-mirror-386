"""
Django-IPC Middleware.

Provides universal middleware for RPC call logging, monitoring, and analytics.
"""

from .orm_logger import ORMLoggingMiddleware

__all__ = [
    "ORMLoggingMiddleware",
]
