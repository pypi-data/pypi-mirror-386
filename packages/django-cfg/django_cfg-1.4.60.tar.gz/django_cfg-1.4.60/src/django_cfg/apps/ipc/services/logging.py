"""
RPC Logging helper for tracking RPC calls.

Provides async-safe logging of RPC calls to database.
"""

import time
from typing import Any, Dict, Optional
from django.conf import settings
from django_cfg.modules.django_logging import get_logger

logger = get_logger("ipc.rpc")


class RPCLogger:
    """
    Helper class for logging RPC calls to database.

    Usage:
        >>> log_entry = RPCLogger.create_log(
        ...     correlation_id="abc123",
        ...     method="send_notification",
        ...     params={"user_id": "123"},
        ...     user=request.user if authenticated else None
        ... )
        >>> # ... make RPC call ...
        >>> RPCLogger.mark_success(log_entry, response_data, duration_ms=150)
    """

    @staticmethod
    def is_logging_enabled() -> bool:
        """
        Check if RPC logging is enabled in settings.

        Returns:
            bool: True if logging is enabled
        """
        # Check if IPC app is installed
        if 'django_cfg.apps.ipc' not in settings.INSTALLED_APPS:
            return False

        # Check if logging is explicitly disabled
        if hasattr(settings, 'DJANGO_CFG_RPC'):
            return settings.DJANGO_CFG_RPC.get('ENABLE_LOGGING', True)

        return True

    @staticmethod
    def create_log(
        correlation_id: str,
        method: str,
        params: Dict[str, Any],
        user: Optional[Any] = None,
        caller_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Create RPC log entry in pending state.

        Args:
            correlation_id: UUID correlation ID from RPC request
            method: RPC method name
            params: Parameters sent to RPC method
            user: Django User instance (optional)
            caller_ip: IP address of caller (optional)
            user_agent: User agent string (optional)

        Returns:
            RPCLog instance or None if logging disabled
        """
        if not RPCLogger.is_logging_enabled():
            return None

        try:
            from ..models import RPCLog

            log_entry = RPCLog.objects.create(
                correlation_id=correlation_id,
                method=method,
                params=params,
                user=user,
                caller_ip=caller_ip,
                user_agent=user_agent,
                status=RPCLog.StatusChoices.PENDING
            )
            return log_entry

        except Exception as e:
            logger.error(f"Failed to create RPC log: {e}", exc_info=True)
            return None

    @staticmethod
    def mark_success(log_entry, response_data: Dict[str, Any], duration_ms: Optional[int] = None):
        """
        Mark RPC log as successful.

        Args:
            log_entry: RPCLog instance
            response_data: Response data from RPC call
            duration_ms: Duration in milliseconds (optional)
        """
        if log_entry is None:
            return

        try:
            log_entry.mark_success(response_data, duration_ms)
        except Exception as e:
            logger.error(f"Failed to mark RPC log as success: {e}", exc_info=True)

    @staticmethod
    def mark_failed(log_entry, error_code: str, error_message: str, duration_ms: Optional[int] = None):
        """
        Mark RPC log as failed.

        Args:
            log_entry: RPCLog instance
            error_code: Error code
            error_message: Error message
            duration_ms: Duration in milliseconds (optional)
        """
        if log_entry is None:
            return

        try:
            log_entry.mark_failed(error_code, error_message, duration_ms)
        except Exception as e:
            logger.error(f"Failed to mark RPC log as failed: {e}", exc_info=True)

    @staticmethod
    def mark_timeout(log_entry, timeout_seconds: int):
        """
        Mark RPC log as timed out.

        Args:
            log_entry: RPCLog instance
            timeout_seconds: Timeout duration in seconds
        """
        if log_entry is None:
            return

        try:
            log_entry.mark_timeout(timeout_seconds)
        except Exception as e:
            logger.error(f"Failed to mark RPC log as timeout: {e}", exc_info=True)


class RPCLogContext:
    """
    Context manager for automatically logging RPC calls.

    Usage:
        >>> with RPCLogContext(
        ...     correlation_id="abc123",
        ...     method="send_notification",
        ...     params={"user_id": "123"}
        ... ) as log_ctx:
        ...     result = rpc.call(...)
        ...     log_ctx.set_response(result)
    """

    def __init__(
        self,
        correlation_id: str,
        method: str,
        params: Dict[str, Any],
        user: Optional[Any] = None,
        caller_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize RPC log context.

        Args:
            correlation_id: UUID correlation ID
            method: RPC method name
            params: Parameters for RPC call
            user: Django User instance (optional)
            caller_ip: IP address (optional)
            user_agent: User agent string (optional)
        """
        self.correlation_id = correlation_id
        self.method = method
        self.params = params
        self.user = user
        self.caller_ip = caller_ip
        self.user_agent = user_agent
        self.log_entry = None
        self.start_time = None
        self.response = None

    def __enter__(self):
        """Start timing and create log entry."""
        self.start_time = time.time()
        self.log_entry = RPCLogger.create_log(
            correlation_id=self.correlation_id,
            method=self.method,
            params=self.params,
            user=self.user,
            caller_ip=self.caller_ip,
            user_agent=self.user_agent,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Mark log as success or failed based on exception."""
        if self.log_entry is None:
            return False

        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None

        if exc_type is None:
            # Success - use response if set
            RPCLogger.mark_success(self.log_entry, self.response or {}, duration_ms)
        else:
            # Failed - extract error details
            error_code = exc_type.__name__ if exc_type else 'unknown'
            error_message = str(exc_val) if exc_val else 'Unknown error'

            # Check if it's a timeout
            if 'timeout' in error_code.lower():
                timeout_seconds = duration_ms // 1000 if duration_ms else 30
                RPCLogger.mark_timeout(self.log_entry, timeout_seconds)
            else:
                RPCLogger.mark_failed(self.log_entry, error_code, error_message, duration_ms)

        # Don't suppress exceptions
        return False

    def set_response(self, response: Dict[str, Any]):
        """
        Set response data for successful call.

        Args:
            response: Response data from RPC call
        """
        self.response = response


__all__ = ['RPCLogger', 'RPCLogContext']
