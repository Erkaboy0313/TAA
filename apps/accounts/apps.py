"""AppConfig for apps.accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Telegram-native user identity for TAA.

    Owns the `User` model (telegram_id PK) and, in later stories, the
    `EntrepreneurProfile` and account services/selectors that every other
    app depends on (architecture §3).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
