"""
Service integrations registry.
"""

SERVICES_REGISTRY = {
    # Email services
    "EmailConfig": ("django_cfg.models.services", "EmailConfig"),
    "DjangoEmailService": ("django_cfg.modules.django_email", "DjangoEmailService"),
    "send_email": ("django_cfg.modules.django_email", "send_email"),
    "SendGridConfig": ("django_cfg.modules.django_twilio.models", "SendGridConfig"),

    # Telegram services
    "TelegramConfig": ("django_cfg.models.services", "TelegramConfig"),
    "DjangoTelegram": ("django_cfg.modules.django_telegram", "DjangoTelegram"),
    "send_telegram_message": ("django_cfg.modules.django_telegram", "send_telegram_message"),
    "send_telegram_photo": ("django_cfg.modules.django_telegram", "send_telegram_photo"),

    # Twilio services
    "TwilioConfig": ("django_cfg.modules.django_twilio.models", "TwilioConfig"),
    "TwilioVerifyConfig": ("django_cfg.modules.django_twilio.models", "TwilioVerifyConfig"),
    "TwilioChannelType": ("django_cfg.modules.django_twilio.models", "TwilioChannelType"),

    # Ngrok services (simplified flat config)
    "NgrokConfig": ("django_cfg.models.ngrok", "NgrokConfig"),
    "DjangoNgrok": ("django_cfg.modules.django_ngrok", "DjangoNgrok"),
    "NgrokManager": ("django_cfg.modules.django_ngrok", "NgrokManager"),
    "NgrokError": ("django_cfg.modules.django_ngrok", "NgrokError"),
    "get_ngrok_service": ("django_cfg.modules.django_ngrok", "get_ngrok_service"),
    "start_tunnel": ("django_cfg.modules.django_ngrok", "start_tunnel"),
    "stop_tunnel": ("django_cfg.modules.django_ngrok", "stop_tunnel"),
    "get_tunnel_url": ("django_cfg.modules.django_ngrok", "get_tunnel_url"),
    "get_webhook_url": ("django_cfg.modules.django_ngrok", "get_webhook_url"),
    "get_api_url": ("django_cfg.modules.django_ngrok", "get_api_url"),
    "get_tunnel_url_from_env": ("django_cfg.modules.django_ngrok", "get_tunnel_url_from_env"),
    "get_ngrok_host_from_env": ("django_cfg.modules.django_ngrok", "get_ngrok_host_from_env"),
    "is_ngrok_available_from_env": ("django_cfg.modules.django_ngrok", "is_ngrok_available_from_env"),
    "is_tunnel_active": ("django_cfg.modules.django_ngrok", "is_tunnel_active"),
    "get_effective_tunnel_url": ("django_cfg.modules.django_ngrok", "get_effective_tunnel_url"),

    # Logging services
    "DjangoLogger": ("django_cfg.modules.django_logging", "DjangoLogger"),
    "get_logger": ("django_cfg.modules.django_logging", "get_logger"),
}
