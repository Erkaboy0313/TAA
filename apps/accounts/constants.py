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


class Regime(models.TextChoices):
    """Soliq rejim options presented by the simulator (PRD F3)."""

    SAMOZANYATOS = "samozanyatos", _("Samozanyatos")
    YTT_4 = "ytt_4", _("YTT 4% aylanma")
    YTT_25M = "ytt_25m", _("YTT 25M soddalashtirilgan")
    MCHJ_SIMPLIFIED = "mchj_simplified", _("MChJ soddalashtirilgan")
    MCHJ_GENERAL = "mchj_general", _("MChJ umumiy rejim")
    MCHJ_IT_PARK = "mchj_it_park", _("MChJ IT Park rezident")


class CurrentStatus(models.TextChoices):
    """Where the entrepreneur is today, captured during onboarding."""

    NOT_STARTED = "not_started", _("Firma yo'q, boshlashni o'ylayapman")
    PLANNING = "planning", _("Rejalashtiryapman, tayyorgarlik ko'ryapman")
    ACTIVE_LT_6MO = "active_lt_6mo", _("6 oydan kam ochilgan firma")
    ACTIVE_GE_6MO = "active_ge_6mo", _("6 oydan ko'p ishlab turgan firma")


class OnboardingStep(models.TextChoices):
    """State machine for the onboarding conversation (E08)."""

    NOT_STARTED = "not_started", _("Boshlanmagan")
    ASK_PROFESSION = "ask_profession", _("Kasb so'ralmoqda")
    ASK_REVENUE = "ask_revenue", _("Yillik daromad so'ralmoqda")
    ASK_EMPLOYEES = "ask_employees", _("Xodim soni so'ralmoqda")
    ASK_FOREIGN_CLIENTS = "ask_foreign_clients", _("Chet el mijozlar so'ralmoqda")
    ASK_IT_SECTOR = "ask_it_sector", _("IT sohasi so'ralmoqda")
    ASK_CURRENT_STATUS = "ask_current_status", _("Joriy holat so'ralmoqda")
    GENERATE_BRIEFING = "generate_briefing", _("Briefing generatsiya bosqichi")
    COMPLETE = "complete", _("Wizard yakunlangan")
