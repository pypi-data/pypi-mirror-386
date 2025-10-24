"""
Custom JWT Authentication for Django CFG.

Extends rest_framework_simplejwt.authentication.JWTAuthentication to automatically
update user's last_login field on successful authentication.
"""

import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

User = get_user_model()


class JWTAuthenticationWithLastLogin(JWTAuthentication):
    """
    JWT Authentication that updates last_login on successful authentication.

    Updates last_login field with intelligent throttling to avoid database spam.
    Only updates if last_login is None or older than the configured interval.

    Features:
    - Automatic last_login tracking for all JWT-authenticated requests
    - Built-in throttling (default: 5 minutes) to minimize database writes
    - In-memory cache for tracking last update times
    - Automatic cache cleanup to prevent memory leaks
    - Error handling to prevent authentication failures

    Usage:
        Add to REST_FRAMEWORK settings:
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'django_cfg.apps.accounts.authentication.JWTAuthenticationWithLastLogin',
        ]
    """

    # Class-level cache to track last update times (shared across all instances)
    _last_updates = {}

    # Update interval in seconds (5 minutes by default, same as UserActivityMiddleware)
    UPDATE_INTERVAL = 300

    # Maximum cache size before cleanup (prevents memory leaks)
    MAX_CACHE_SIZE = 1000
    CLEANUP_CACHE_SIZE = 500

    def authenticate(self, request):
        """
        Authenticate request and update last_login if needed.

        Args:
            request: Django HttpRequest object

        Returns:
            Tuple of (user, token) if authentication succeeds, None otherwise
        """
        # Perform standard JWT authentication
        result = super().authenticate(request)

        if result is not None:
            user, token = result
            # Update last_login with throttling
            self._update_last_login(user)

        return result

    def _update_last_login(self, user):
        """
        Update user's last_login field with intelligent throttling.

        Only updates if:
        - last_login is None (never logged in)
        - last_login is older than UPDATE_INTERVAL seconds

        Uses UPDATE query to avoid triggering signals and save() overhead.

        Args:
            user: User instance to update
        """
        now = timezone.now()
        user_id = user.pk

        # Check if we should update (avoid database spam)
        last_update = self._last_updates.get(user_id)
        if last_update and (now - last_update).total_seconds() < self.UPDATE_INTERVAL:
            # Skip update - too soon since last update
            return

        try:
            # Use update() to avoid triggering signals and save() overhead
            # This is more efficient than user.save(update_fields=['last_login'])
            updated_count = User.objects.filter(pk=user_id).update(last_login=now)

            if updated_count > 0:
                # Cache the update time
                self._last_updates[user_id] = now

                logger.debug(
                    f"Updated last_login for user {user.email} (ID: {user_id}) "
                    f"via JWT authentication"
                )

                # Clean up old cache entries to prevent memory leaks
                if len(self._last_updates) > self.MAX_CACHE_SIZE:
                    self._cleanup_cache()

        except Exception as e:
            # Log error but don't break authentication
            # Authentication should succeed even if last_login update fails
            logger.error(
                f"Failed to update last_login for user {user_id}: {e}",
                exc_info=True
            )

    def _cleanup_cache(self):
        """
        Clean up old cache entries to prevent memory leaks.

        Keeps only the most recent CLEANUP_CACHE_SIZE entries.
        Sorted by update time (newest first).
        """
        try:
            # Sort by update time (value), keep newest entries
            sorted_items = sorted(
                self._last_updates.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Keep only the most recent entries
            self._last_updates = dict(sorted_items[:self.CLEANUP_CACHE_SIZE])

            logger.debug(
                f"Cleaned up last_login cache: "
                f"kept {len(self._last_updates)} most recent entries"
            )

        except Exception as e:
            logger.error(f"Failed to cleanup last_login cache: {e}")

    @classmethod
    def get_cache_stats(cls):
        """
        Get cache statistics for monitoring/debugging.

        Returns:
            dict: Cache statistics including size and configuration
        """
        return {
            'cache_size': len(cls._last_updates),
            'max_cache_size': cls.MAX_CACHE_SIZE,
            'update_interval_seconds': cls.UPDATE_INTERVAL,
            'update_interval_minutes': cls.UPDATE_INTERVAL / 60,
        }
