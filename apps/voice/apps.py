"""AppConfig for apps.voice."""

from django.apps import AppConfig


class VoiceConfig(AppConfig):
    """Gemini-backed voice pipeline (STT + TTS) for TAA.

    Owns the provider abstraction (`VoiceProvider` Protocol) and its
    concrete `GeminiVoiceProvider` implementation (architecture §5).
    No persistent models — audio bytes stay in memory only (R9).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.voice"
    label = "voice"
