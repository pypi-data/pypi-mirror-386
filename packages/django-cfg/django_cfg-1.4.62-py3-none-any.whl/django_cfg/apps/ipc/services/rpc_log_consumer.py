"""
RPC Log Consumer - Redis Stream to Django ORM.

Consumes RPC events from Redis Stream (published by WebSocket server)
and saves them to Django database for monitoring and analytics.

Architecture:
- WebSocket Server -> Redis Stream (stream:rpc-logs)
- This Consumer <- Redis Stream -> Django ORM (RPCLog model)

This maintains service independence while enabling centralized logging.
"""

import asyncio
import json
import time
from typing import Dict, Optional, Any
from django.contrib.auth import get_user_model
from django_cfg.modules.django_logging import get_logger
import redis.asyncio as redis

logger = get_logger("ipc.consumer")
User = get_user_model()


class RPCLogConsumer:
    """
    Consumes RPC events from Redis Stream and saves to Django ORM.

    Features:
    - Async consumer for high throughput
    - Automatic reconnection on Redis errors
    - Batched processing for performance
    - Graceful shutdown
    - Error tolerance (continues on DB errors)

    Example:
        >>> consumer = RPCLogConsumer(
        ...     redis_url="redis://localhost:6379/2",
        ...     stream_name="stream:rpc-logs",
        ... )
        >>> await consumer.start()  # Runs in background
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/2",
        stream_name: str = "stream:rpc-logs",
        consumer_group: str = "django-rpc-loggers",
        consumer_name: str = "django-1",
        batch_size: int = 10,
        block_ms: int = 1000,
    ):
        """
        Initialize RPC Log Consumer.

        Args:
            redis_url: Redis connection URL
            stream_name: Redis Stream name to consume
            consumer_group: Consumer group name
            consumer_name: Unique consumer name
            batch_size: Number of messages to process per batch
            block_ms: Block time for XREADGROUP (milliseconds)
        """
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.batch_size = batch_size
        self.block_ms = block_ms

        self._redis: Optional[redis.Redis] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Pending requests (correlation_id -> log_entry)
        self._pending_requests: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize Redis connection and consumer group."""
        try:
            self._redis = await redis.from_url(
                self.redis_url,
                decode_responses=True,  # Decode Redis responses to strings
                socket_keepalive=True,
            )

            # Test connection
            await self._redis.ping()

            # Create consumer group if not exists
            try:
                await self._redis.xgroup_create(
                    name=self.stream_name,
                    groupname=self.consumer_group,
                    id="0",  # Start from beginning
                    mkstream=True,  # Create stream if not exists
                )
                logger.info(f"✅ Created consumer group: {self.consumer_group}")
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.debug(f"Consumer group already exists: {self.consumer_group}")
                else:
                    raise

            logger.info(f"✅ RPC Log Consumer initialized: {self.stream_name}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize RPC Log Consumer: {e}")
            raise

    async def start(self) -> None:
        """Start consuming RPC events from Redis Stream."""
        if self._running:
            logger.warning("RPC Log Consumer already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"🚀 RPC Log Consumer started: {self.consumer_name}")

    async def stop(self) -> None:
        """Stop consuming and cleanup."""
        if not self._running:
            return

        logger.info("⏹️  Stopping RPC Log Consumer...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()

        logger.info("✅ RPC Log Consumer stopped")

    async def _consume_loop(self) -> None:
        """Main consume loop - reads from Redis Stream and processes events."""
        last_id = ">"  # Read only new messages

        while self._running:
            try:
                # Read from stream
                messages = await self._redis.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: last_id},
                    count=self.batch_size,
                    block=self.block_ms,
                )

                if not messages:
                    continue  # No new messages, continue

                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            await self._process_event(message_id, message_data)

                            # Acknowledge message
                            await self._redis.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id,
                            )

                        except Exception as e:
                            logger.error(
                                f"Error processing RPC event {message_id}: {e}",
                                exc_info=True
                            )
                            # Continue processing other messages

            except asyncio.CancelledError:
                logger.info("RPC Log Consumer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in RPC Log Consumer loop: {e}", exc_info=True)
                # Wait before retrying
                await asyncio.sleep(5)

    async def _process_event(self, message_id: str, event_data: Dict[str, str]) -> None:
        """
        Process single RPC event from Redis Stream.

        Args:
            message_id: Redis message ID
            event_data: Event data from stream
        """
        event_type = event_data.get("event_type")
        correlation_id = event_data.get("correlation_id")

        if not correlation_id:
            logger.warning(f"Event missing correlation_id: {message_id}")
            return

        if event_type == "request":
            await self._handle_request(correlation_id, event_data)
        elif event_type == "response":
            await self._handle_response(correlation_id, event_data)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    async def _handle_request(self, correlation_id: str, event_data: Dict[str, str]) -> None:
        """
        Handle RPC request event - create RPCLog entry.

        Args:
            correlation_id: Correlation ID
            event_data: Event data from stream
        """
        try:
            from ..models import RPCLog

            method = event_data.get("method")
            params_json = event_data.get("params", "{}")
            user_id = event_data.get("user_id")

            # Parse params
            try:
                params = json.loads(params_json)
            except json.JSONDecodeError:
                params = {}

            # Get user if user_id provided
            user = None
            if user_id:
                try:
                    user = await asyncio.to_thread(User.objects.get, pk=user_id)
                except User.DoesNotExist:
                    pass

            # Create log entry in database (sync operation in thread)
            log_entry = await asyncio.to_thread(
                RPCLog.objects.create,
                correlation_id=correlation_id,
                method=method,
                params=params,
                user=user,
                status=RPCLog.StatusChoices.PENDING,
            )

            # Store in pending for later update
            self._pending_requests[correlation_id] = log_entry

            logger.debug(f"Created RPC log entry: {method} ({correlation_id})")

        except Exception as e:
            logger.error(f"Failed to handle RPC request: {e}", exc_info=True)

    async def _handle_response(self, correlation_id: str, event_data: Dict[str, str]) -> None:
        """
        Handle RPC response event - update RPCLog entry.

        Args:
            correlation_id: Correlation ID
            event_data: Event data from stream
        """
        try:
            from ..models import RPCLog

            # Get log entry from pending or database
            log_entry = self._pending_requests.pop(correlation_id, None)

            if not log_entry:
                # Try to find in database with retry (race condition with request handler)
                max_retries = 3
                retry_delay = 0.1  # 100ms

                for attempt in range(max_retries):
                    try:
                        log_entry = await asyncio.to_thread(
                            RPCLog.objects.get,
                            correlation_id=correlation_id
                        )
                        break  # Found it!
                    except RPCLog.DoesNotExist:
                        if attempt < max_retries - 1:
                            # Wait a bit and retry
                            await asyncio.sleep(retry_delay)
                        else:
                            # Give up after retries
                            logger.warning(f"RPCLog not found for correlation_id: {correlation_id} after {max_retries} retries")
                            return

            # Parse response data
            success = event_data.get("success") == "1"
            duration_ms = int(event_data.get("duration_ms", 0))

            if success:
                result_json = event_data.get("result", "{}")
                try:
                    result = json.loads(result_json)
                except json.JSONDecodeError:
                    result = {}

                # Mark as success (sync operation in thread)
                await asyncio.to_thread(
                    log_entry.mark_success,
                    result,
                    duration_ms
                )

                logger.debug(f"Marked RPC log as success: {correlation_id}")

            else:
                error_code = event_data.get("error_code", "unknown")
                error_message = event_data.get("error_message", "")

                # Mark as failed (sync operation in thread)
                await asyncio.to_thread(
                    log_entry.mark_failed,
                    error_code,
                    error_message,
                    duration_ms
                )

                logger.debug(f"Marked RPC log as failed: {correlation_id}")

        except Exception as e:
            logger.error(f"Failed to handle RPC response: {e}", exc_info=True)


__all__ = ["RPCLogConsumer"]
