"""Django settings for TAA.

Single-file, env-driven (project-context R6). No base/dev/prod split.
Toggle behaviour via `.env` variables (see `.env.example`).
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# No default — fail loudly if unset (project-context R10 §9).
SECRET_KEY: str = config("SECRET_KEY")
DEBUG: bool = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", default="", cast=Csv())

# Admin gate — off in prod by default. Ops can force-enable via env for
# short-lived investigation. Architecture §9 spells out the IP-allowlist
# layer that lands with prod deploy (Faza 3).
ADMIN_ENABLED: bool = config("ADMIN_ENABLED", default=DEBUG, cast=bool)

# Telegram bot (E05-S01). Empty defaults let tests import Django without
# bot credentials in the env; `apps.bot.telegram.get_bot()` raises
# BotNotConfiguredError at first real use if the token is unset.
# TELEGRAM_WEBHOOK_SECRET is embedded in the webhook URL path (architecture
# §9) so an attacker cannot POST fake updates without guessing the secret.
TELEGRAM_BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_WEBHOOK_SECRET: str = config("TELEGRAM_WEBHOOK_SECRET", default="")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.bot",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "taa.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "taa.wsgi.application"
ASGI_APPLICATION = "taa.asgi.application"

# ---------------------------------------------------------------------------
# Database (project-context R8 — Postgres in prod; dj-database-url parses URL)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),
        conn_max_age=60,
        conn_health_checks=True,
    ),
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization (project-context R8 — UTC store, Asia/Tashkent display)
# ---------------------------------------------------------------------------
LANGUAGE_CODE: str = config("LANGUAGE_CODE", default="uz")
TIME_ZONE: str = config("TIME_ZONE", default="Asia/Tashkent")
USE_I18N = True
USE_TZ = True

# i18n — Uzbek (Latin script default; Cyrillic added as separate locale once
# translations land) and Russian. UI text lives in per-app `locale/` dirs.
# NOTE: no `LocaleMiddleware` — per-user language lives on `User.language`
# (bot context), not request headers, so middleware would fight the bot flow.
LANGUAGES: list[tuple[str, str]] = [
    ("uz", "O'zbekcha"),
    ("ru", "Русский"),
]
LOCALE_PATHS: list[Path] = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Celery (E00-S02). Broker + result backend read from REDIS_URL so local dev
# (docker-compose network hostname `redis`) and prod (managed Redis URL)
# share the same code path. `django-celery-beat`/`django-celery-results`
# deliberately NOT installed — v2 optimisation (project-context R6).
# ---------------------------------------------------------------------------
CELERY_BROKER_URL: str = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND: str = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_TIMEZONE: str = TIME_ZONE
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 30 * 60

# ---------------------------------------------------------------------------
# Cache — Redis via the same URL Celery uses. Uses Django 4.0+ built-in
# Redis backend (no `django-redis` dep — R6). DB index /1 keeps cache
# flushes from ever nuking Celery's queued tasks on /0.
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/1"),
        "TIMEOUT": 60 * 60,
    },
}

# ---------------------------------------------------------------------------
# Production hardening (project-context R10 §9). Baked in from day one so
# `if not DEBUG` deploys automatically enforce HTTPS + secure cookies.
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Logging — pure stdlib dictConfig. Docker captures stdout so no filehandlers.
# See architecture.md §10: structured JSON logs + Sentry are Faza 3 additions
# that layer on top of this baseline (python-json-logger formatter swap).
# PII-redaction filter lives in apps.bot.logging_filter and is attached to
# the console handler below.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "pii_redaction": {"()": "apps.bot.logging_filter.PiiRedactionFilter"},
    },
    "formatters": {
        "compact": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "compact",
            "filters": ["pii_redaction"],
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": False,
        },
        # Never INFO — floods logs with every SQL statement.
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "WARNING",
    },
}
