"""AppConfig for apps.bot."""

from django.apps import AppConfig


class BotConfig(AppConfig):
    """Telegram bot layer for TAA.

    Owns the webhook view, dispatcher, handlers, middleware and response
    templates (architecture §3). No persistent models of its own — user
    identity lives in `apps.accounts`.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bot"
    label = "bot"
