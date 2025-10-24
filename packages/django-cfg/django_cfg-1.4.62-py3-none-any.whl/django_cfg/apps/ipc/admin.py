"""
Django Admin for IPC/RPC models.

Uses PydanticAdmin with declarative configuration.
"""

import json

from django.contrib import admin
from django_cfg.modules.django_admin import (
    AdminConfig,
    BadgeField,
    DateTimeField,
    Icons,
    UserField,
    computed_field,
)
from django_cfg.modules.django_admin.base import PydanticAdmin

from .models import RPCLog


# Declarative configuration for RPCLog
rpclog_config = AdminConfig(
    model=RPCLog,

    # Performance optimization
    select_related=["user"],

    # List display
    list_display=[
        "method",
        "type_badge",  # NEW: Show RPC vs Event
        "status",
        "user",
        "duration_ms",
        "created_at",
        "completed_at"
    ],

    # Auto-generated display methods
    display_fields=[
        BadgeField(
            name="method",
            title="RPC Method",
            variant="info",
            icon=Icons.API
        ),
        BadgeField(
            name="status",
            title="Status",
            label_map={
                "pending": "warning",
                "success": "success",
                "failed": "danger",
                "timeout": "danger"
            }
        ),
        UserField(
            name="user",
            title="User",
            header=True  # Show with avatar
        ),
        DateTimeField(
            name="created_at",
            title="Created",
            ordering="created_at"
        ),
        DateTimeField(
            name="completed_at",
            title="Completed",
            ordering="completed_at"
        ),
    ],

    # Filters
    list_filter=["status", "is_event", "method", "created_at"],
    search_fields=["method", "correlation_id", "user__username", "user__email", "error_message"],

    # Autocomplete for user field
    autocomplete_fields=["user"],

    # Readonly fields (custom methods below)
    readonly_fields=[
        "id",
        "correlation_id",
        "created_at",
        "completed_at",
        "params_display",
        "response_display",
        "error_details_display"
    ],

    # Date hierarchy
    date_hierarchy="created_at",

    # Per page
    list_per_page=50,
)


@admin.register(RPCLog)
class RPCLogAdmin(PydanticAdmin):
    """
    RPC log admin with analytics and filtering.

    Features:
    - Color-coded status badges
    - Duration display with performance indicators
    - Formatted JSON for params/response
    - Error details with highlighted display
    """
    config = rpclog_config

    @computed_field("Type", ordering="is_event")
    def type_badge(self, obj):
        """Display badge showing if this is an RPC call or server event."""
        if obj.is_event:
            return self.html.badge(
                "EVENT",
                variant="info",
                icon=Icons.NOTIFICATION  # or Icons.BROADCAST
            )
        else:
            return self.html.badge(
                "RPC",
                variant="primary",
                icon=Icons.API
            )

    @computed_field("Duration", ordering="duration_ms")
    def duration_display(self, obj):
        """Display duration with color coding based on speed."""
        if obj.duration_ms is None:
            return self.html.empty()

        # Color code based on duration
        if obj.duration_ms < 100:
            variant = "success"  # Fast
            icon = Icons.SPEED
        elif obj.duration_ms < 500:
            variant = "warning"  # Moderate
            icon = Icons.TIMER
        else:
            variant = "danger"  # Slow
            icon = Icons.ERROR

        return self.html.badge(
            f"{obj.duration_ms}ms",
            variant=variant,
            icon=icon
        )

    def params_display(self, obj):
        """Display formatted JSON params."""
        if not obj.params:
            return self.html.empty("No parameters")

        try:
            formatted = json.dumps(obj.params, indent=2)
            return f'<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; max-height: 400px; overflow: auto; font-size: 12px; line-height: 1.5;">{formatted}</pre>'
        except Exception:
            return str(obj.params)

    params_display.short_description = "Request Parameters"

    def response_display(self, obj):
        """Display formatted JSON response."""
        if not obj.response:
            return self.html.empty("No response")

        try:
            formatted = json.dumps(obj.response, indent=2)
            return f'<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; max-height: 400px; overflow: auto; font-size: 12px; line-height: 1.5;">{formatted}</pre>'
        except Exception:
            return str(obj.response)

    response_display.short_description = "Response Data"

    def error_details_display(self, obj):
        """Display error information if call failed."""
        if not obj.is_failed:
            return self.html.inline([
                self.html.icon(Icons.CHECK_CIRCLE, size="sm"),
                self.html.span("No errors", "text-green-600")
            ])

        details = []

        if obj.error_code:
            details.append(self.html.inline([
                self.html.span("Error Code:", "font-semibold"),
                self.html.badge(obj.error_code, variant="danger", icon=Icons.ERROR)
            ], separator=" "))

        if obj.error_message:
            details.append(self.html.inline([
                self.html.span("Message:", "font-semibold"),
                self.html.span(obj.error_message, "text-red-600")
            ], separator=" "))

        return "<br>".join(details) if details else self.html.empty()

    error_details_display.short_description = "Error Details"

    # Fieldsets for detail view
    def get_fieldsets(self, request, obj=None):
        """Dynamic fieldsets based on object state."""
        fieldsets = [
            ("RPC Call Information", {
                'fields': ('id', 'correlation_id', 'method', 'user', 'status')
            }),
            ("Request & Response", {
                'fields': ('params_display', 'response_display'),
                'classes': ('collapse',)
            }),
            ("Performance", {
                'fields': ('duration_ms', 'created_at', 'completed_at')
            }),
            ("Metadata", {
                'fields': ('caller_ip', 'user_agent'),
                'classes': ('collapse',)
            }),
        ]

        # Add error section only if failed
        if obj and obj.is_failed:
            fieldsets.insert(2, ("Error Details", {
                'fields': ('error_details_display', 'error_code', 'error_message')
            }))

        return fieldsets
