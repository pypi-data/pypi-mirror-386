"""
Django app configuration for IPC/RPC module.

Provides RPC client and monitoring dashboard.
"""

import asyncio
from django.apps import AppConfig
from django.conf import settings


class IPCConfig(AppConfig):
    """
    IPC/RPC application configuration.

    Provides:
    - RPC client for inter-service communication
    - Monitoring dashboard with real-time stats
    - DRF API endpoints for dashboard
    - RPC log consumer (Redis Stream -> ORM)
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_cfg.apps.ipc'
    label = 'django_cfg_ipc'
    verbose_name = 'IPC/RPC System'

    def ready(self):
        """Initialize app when Django starts."""
        # Import monitor to ensure Redis connection is initialized
        from .services import monitor  # noqa: F401

        # Start RPC Log Consumer in background (if enabled)
        self._start_rpc_log_consumer()

    def _start_rpc_log_consumer(self):
        """Start RPC Log Consumer to capture logs from WebSocket server."""
        # Check if RPC logging consumer is enabled
        enable_consumer = getattr(settings, 'DJANGO_CFG_RPC_LOG_CONSUMER_ENABLED', True)

        if not enable_consumer:
            return

        # Check if we have RPC configuration
        if not hasattr(settings, 'DJANGO_CFG_RPC'):
            return

        # Check if RPC is enabled (case-insensitive)
        rpc_enabled = settings.DJANGO_CFG_RPC.get('ENABLED') or settings.DJANGO_CFG_RPC.get('enabled')
        if not rpc_enabled:
            return

        try:
            import threading
            from .services.rpc_log_consumer import RPCLogConsumer

            # Get Redis URL (case-insensitive)
            redis_url = settings.DJANGO_CFG_RPC.get('REDIS_URL') or settings.DJANGO_CFG_RPC.get('redis_url', 'redis://localhost:6379/2')

            consumer = RPCLogConsumer(
                redis_url=redis_url,
                stream_name="stream:rpc-logs",
                consumer_group="django-rpc-loggers",
                consumer_name="django-1",
            )

            # Run consumer in background thread with its own event loop
            def run_consumer():
                """Run consumer in background thread."""
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Initialize and start consumer
                    loop.run_until_complete(consumer.initialize())
                    loop.run_until_complete(consumer.start())

                    # Keep running
                    loop.run_forever()

                except Exception as e:
                    from django_cfg.modules.django_logging import get_logger
                    logger = get_logger("ipc.consumer")
                    logger.error(f"RPC Log Consumer error: {e}", exc_info=True)

            # Start in daemon thread (won't block Django shutdown)
            thread = threading.Thread(target=run_consumer, daemon=True, name="rpc-log-consumer")
            thread.start()

            from django_cfg.modules.django_logging import get_logger
            logger = get_logger("ipc.apps")
            logger.info("✅ RPC Log Consumer started in background thread")

        except Exception as e:
            from django_cfg.modules.django_logging import get_logger
            logger = get_logger("ipc.apps")
            logger.warning(f"Failed to start RPC Log Consumer: {e}")
