"""
ExternalData creator for the mixin.
"""

import logging
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import transaction

from ..models.external_data import ExternalData, ExternalDataStatus
from .config import ExternalDataMetaConfig

logger = logging.getLogger(__name__)


class ExternalDataCreator:
    """
    Creator class for ExternalData objects with validation.
    """

    def __init__(self, user=None):
        if user is None:
            self.user = self._get_default_user()
        else:
            self.user = user

    def create_from_config(self, config: ExternalDataMetaConfig) -> Dict[str, Any]:
        """
        Create an ExternalData object from a Pydantic configuration.
        
        Args:
            config: An instance of ExternalDataMetaConfig.
            
        Returns:
            dict: Result with success status, external_data object, and message/error.
        """
        try:
            with transaction.atomic():
                external_data = ExternalData.objects.create(
                    user=self.user,
                    title=config.title,
                    description=config.description,
                    source_type=config.source_type,
                    source_identifier=config.source_identifier,
                    content=config.content,
                    similarity_threshold=config.similarity_threshold,
                    is_active=config.is_active,
                    is_public=config.is_public,
                    metadata=config.metadata,
                    source_config=config.source_config,
                    tags=config.tags,
                    status=ExternalDataStatus.PENDING,  # Always set to pending on creation
                    processed_at=None,
                    processing_error="",
                )

                logger.info(f"Created ExternalData: {external_data.title} (ID: {external_data.id})")
                return {
                    'success': True,
                    'message': f"ExternalData '{external_data.title}' created successfully.",
                    'external_data': external_data
                }
        except Exception as e:
            logger.error(f"Failed to create ExternalData from config: {e}")
            return {
                'success': False,
                'error': f"Failed to create ExternalData: {e}",
                'external_data': None
            }

    def _get_default_user(self):
        """Get default user for ExternalData ownership."""
        User = get_user_model()

        # Try to find a staff user (staff or superuser)
        staff_user = User.objects.filter(is_staff=True).first()
        if staff_user:
            return staff_user

        raise ValueError("No user provided and no staff user found for ExternalData ownership")
