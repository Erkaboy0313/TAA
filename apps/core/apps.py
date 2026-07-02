"""AppConfig for apps.core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared utilities, base models, base exceptions.

    Concrete `TimestampedModel` and `DomainError` land in E00-S07.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
