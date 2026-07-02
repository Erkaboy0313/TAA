"""Enumerations used across the accounts app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.TextChoices):
    """Supported UI languages. Latin script is the default until Cyrillic
    translations land; Russian is a first-class parallel language.
    """

    UZ_LATIN = "uz-Latn", _("O'zbekcha (Latin)")
    UZ_CYRILLIC = "uz-Cyrl", _("Ўзбекча (Кирилл)")
    RUSSIAN = "ru", _("Русский")
