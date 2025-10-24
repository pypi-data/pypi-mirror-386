"""
IPC/RPC Models for logging and monitoring.

Models:
- RPCLog: Log of all RPC calls for debugging and analytics
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class RPCLogManager(models.Manager):
    """Custom manager for RPCLog model."""

    def recent(self, hours=24):
        """Get logs from last N hours."""
        since = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(created_at__gte=since)

    def failed(self):
        """Get failed RPC calls."""
        return self.filter(status=RPCLog.StatusChoices.FAILED)

    def by_method(self, method):
        """Get logs for specific RPC method."""
        return self.filter(method=method)

    def stats_by_method(self):
        """
        Get statistics grouped by method.

        Returns:
            QuerySet with aggregated data per method
        """
        from django.db.models import Count, Avg, Max, Min

        return self.values('method').annotate(
            total_calls=Count('id'),
            avg_duration_ms=Avg('duration_ms'),
            max_duration_ms=Max('duration_ms'),
            min_duration_ms=Min('duration_ms'),
            success_count=Count('id', filter=models.Q(status='success')),
            failed_count=Count('id', filter=models.Q(status='failed')),
        ).order_by('-total_calls')


class RPCLog(models.Model):
    """
    Log of RPC calls between Django and WebSocket server.

    Used for:
    - Debugging RPC communication
    - Performance monitoring
    - Analytics (most used methods, success rate)
    - Audit trail (who called what and when)
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        TIMEOUT = 'timeout', 'Timeout'

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Correlation ID (matches RPC correlation_id)
    correlation_id = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Correlation ID",
        help_text="UUID from RPC request"
    )

    # User who initiated the call (optional)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rpc_logs',
        verbose_name="User"
    )

    # RPC method name
    method = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="RPC Method",
        help_text="e.g., send_notification, workspace.file_changed"
    )

    # Request parameters (JSON)
    params = models.JSONField(
        verbose_name="Request Params",
        help_text="Parameters sent to RPC method"
    )

    # Response data (JSON, nullable if failed)
    response = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Response Data",
        help_text="Result from RPC call"
    )

    # Type: RPC call or server event
    is_event = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Is Event",
        help_text="True if this is a server-to-client event (not a request-response RPC call)"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
        verbose_name="Status"
    )

    # Error details (if failed)
    error_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Error Code"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Error Message"
    )

    # Performance metrics
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Duration (ms)",
        help_text="Time taken for RPC call in milliseconds"
    )

    # Metadata
    caller_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Caller IP"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent"
    )

    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Created At"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At"
    )

    # Custom manager
    objects = RPCLogManager()

    class Meta:
        app_label = 'django_cfg_ipc'
        verbose_name = "RPC Log"
        verbose_name_plural = "RPC Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['method', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.method} ({self.status}) - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def is_successful(self):
        """Check if RPC call was successful."""
        return self.status == self.StatusChoices.SUCCESS

    @property
    def is_failed(self):
        """Check if RPC call failed."""
        return self.status in [self.StatusChoices.FAILED, self.StatusChoices.TIMEOUT]

    def mark_success(self, response_data, duration_ms=None):
        """Mark RPC call as successful."""
        self.status = self.StatusChoices.SUCCESS
        self.response = response_data
        self.completed_at = timezone.now()
        if duration_ms is not None:
            self.duration_ms = duration_ms
        self.save()

    def mark_failed(self, error_code, error_message, duration_ms=None):
        """Mark RPC call as failed."""
        self.status = self.StatusChoices.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = timezone.now()
        if duration_ms is not None:
            self.duration_ms = duration_ms
        self.save()

    def mark_timeout(self, timeout_seconds):
        """Mark RPC call as timed out."""
        self.status = self.StatusChoices.TIMEOUT
        self.error_code = 'timeout'
        self.error_message = f'RPC call timed out after {timeout_seconds}s'
        self.completed_at = timezone.now()
        self.duration_ms = timeout_seconds * 1000
        self.save()
