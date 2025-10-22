"""
Settings generation orchestrator.

Coordinates all specialized generators to produce complete Django settings.
Size: ~200 lines (orchestration logic)
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from django_cfg.core.exceptions import ConfigurationError

if TYPE_CHECKING:
    from ..base.config_model import DjangoConfig

logger = logging.getLogger(__name__)


class SettingsOrchestrator:
    """
    Orchestrates Django settings generation from DjangoConfig.

    Responsibilities:
    - Coordinate all specialized generators
    - Merge settings in correct order
    - Apply additional settings
    - Validate generated settings
    - Handle errors gracefully

    Example:
        ```python
        orchestrator = SettingsOrchestrator(config)
        settings = orchestrator.generate()
        ```
    """

    def __init__(self, config: "DjangoConfig"):
        """
        Initialize orchestrator with configuration.

        Args:
            config: DjangoConfig instance
        """
        self.config = config

    def generate(self) -> Dict[str, Any]:
        """
        Generate complete Django settings dictionary.

        Returns:
            Complete Django settings dictionary

        Raises:
            ConfigurationError: If settings generation fails

        Example:
            >>> orchestrator = SettingsOrchestrator(config)
            >>> settings = orchestrator.generate()
            >>> "SECRET_KEY" in settings
            True
        """
        try:
            settings = {}

            # Generate settings in dependency order
            settings.update(self._generate_core_settings())
            settings.update(self._generate_template_settings())
            settings.update(self._generate_static_settings())
            settings.update(self._generate_database_settings())
            settings.update(self._generate_cache_settings())
            settings.update(self._generate_security_settings())
            settings.update(self._generate_email_settings())
            settings.update(self._generate_logging_settings())
            settings.update(self._generate_i18n_settings())
            settings.update(self._generate_limits_settings())
            settings.update(self._generate_session_settings())
            settings.update(self._generate_third_party_settings())
            settings.update(self._generate_api_settings())
            settings.update(self._generate_tasks_settings())
            settings.update(self._generate_tailwind_settings())

            # Apply additional settings (user overrides)
            settings.update(self._get_additional_settings())

            return settings

        except Exception as e:
            raise ConfigurationError(f"Failed to generate settings: {e}") from e

    def _generate_core_settings(self) -> Dict[str, Any]:
        """Generate core Django settings."""
        try:
            from .core_generators.settings import CoreSettingsGenerator
            generator = CoreSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate core settings: {e}") from e

    def _generate_template_settings(self) -> Dict[str, Any]:
        """Generate template settings."""
        try:
            from .core_generators.templates import TemplateSettingsGenerator
            generator = TemplateSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate template settings: {e}") from e

    def _generate_static_settings(self) -> Dict[str, Any]:
        """Generate static files settings."""
        try:
            from .core_generators.static import StaticFilesGenerator
            generator = StaticFilesGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate static settings: {e}") from e

    def _generate_database_settings(self) -> Dict[str, Any]:
        """Generate database settings."""
        try:
            from .data_generators.database import DatabaseSettingsGenerator
            generator = DatabaseSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate database settings: {e}") from e

    def _generate_cache_settings(self) -> Dict[str, Any]:
        """Generate cache settings."""
        try:
            from .data_generators.cache import CacheSettingsGenerator
            generator = CacheSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate cache settings: {e}") from e

    def _generate_security_settings(self) -> Dict[str, Any]:
        """Generate security settings."""
        try:
            from .utility_generators.security import SecuritySettingsGenerator
            generator = SecuritySettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate security settings: {e}") from e

    def _generate_email_settings(self) -> Dict[str, Any]:
        """Generate email settings."""
        try:
            from .utility_generators.email import EmailSettingsGenerator
            generator = EmailSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate email settings: {e}") from e

    def _generate_logging_settings(self) -> Dict[str, Any]:
        """Generate logging settings."""
        try:
            from .utility_generators.logging import LoggingSettingsGenerator
            generator = LoggingSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate logging settings: {e}") from e

    def _generate_i18n_settings(self) -> Dict[str, Any]:
        """Generate i18n settings."""
        try:
            from .utility_generators.i18n import I18nSettingsGenerator
            generator = I18nSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate i18n settings: {e}") from e

    def _generate_limits_settings(self) -> Dict[str, Any]:
        """Generate limits settings."""
        try:
            from .utility_generators.limits import LimitsSettingsGenerator
            generator = LimitsSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate limits settings: {e}") from e

    def _generate_session_settings(self) -> Dict[str, Any]:
        """Generate session settings."""
        try:
            from .integration_generators.sessions import SessionSettingsGenerator
            generator = SessionSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate session settings: {e}") from e

    def _generate_third_party_settings(self) -> Dict[str, Any]:
        """Generate third-party integration settings."""
        try:
            from .integration_generators.third_party import ThirdPartyIntegrationsGenerator
            generator = ThirdPartyIntegrationsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate third-party settings: {e}") from e

    def _generate_api_settings(self) -> Dict[str, Any]:
        """Generate API framework settings."""
        try:
            from .integration_generators.api import APIFrameworksGenerator
            generator = APIFrameworksGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate API settings: {e}") from e

    def _generate_tasks_settings(self) -> Dict[str, Any]:
        """Generate background tasks settings."""
        try:
            from .integration_generators.tasks import TasksSettingsGenerator
            generator = TasksSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate tasks settings: {e}") from e

    def _generate_tailwind_settings(self) -> Dict[str, Any]:
        """Generate Tailwind CSS settings."""
        try:
            from .integration_generators.tailwind import TailwindSettingsGenerator
            generator = TailwindSettingsGenerator(self.config)
            return generator.generate()
        except Exception as e:
            raise ConfigurationError(f"Failed to generate Tailwind settings: {e}") from e

    def _get_additional_settings(self) -> Dict[str, Any]:
        """
        Get additional settings from config (user overrides).

        Returns:
            Dictionary with additional settings
        """
        if hasattr(self.config, "get_additional_settings"):
            return self.config.get_additional_settings()
        return {}

    @staticmethod
    def validate_settings(settings: Dict[str, Any]) -> List[str]:
        """
        Validate generated Django settings.

        Args:
            settings: Generated Django settings

        Returns:
            List of validation errors (empty if valid)

        Example:
            >>> errors = SettingsOrchestrator.validate_settings(settings)
            >>> if errors:
            ...     print("Validation errors:", errors)
        """
        errors = []

        # Required settings validation
        required_settings = [
            "SECRET_KEY",
            "DEBUG",
            "ALLOWED_HOSTS",
            "INSTALLED_APPS",
            "MIDDLEWARE",
            "DATABASES"
        ]

        for setting in required_settings:
            if setting not in settings:
                errors.append(f"Missing required setting: {setting}")

        # SECRET_KEY validation
        if "SECRET_KEY" in settings:
            secret_key = settings["SECRET_KEY"]
            if not secret_key or len(secret_key) < 50:
                errors.append("SECRET_KEY must be at least 50 characters long")

        # DATABASES validation
        if "DATABASES" in settings:
            databases = settings["DATABASES"]
            if not databases:
                errors.append("DATABASES cannot be empty")
            elif "default" not in databases:
                errors.append("DATABASES must contain a 'default' database")

        return errors


__all__ = ["SettingsOrchestrator"]
