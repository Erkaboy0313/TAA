"""Domain exceptions for the voice app.

Rooted at `DomainError` so bot-layer handlers can `except DomainError`
at the boundary and translate any voice failure into a user-friendly
apology (project-context R4).
"""

from apps.core.exceptions import DomainError


class VoiceError(DomainError):
    """Base class for expected voice-pipeline failures (STT + TTS)."""


class TranscriptionError(VoiceError):
    """Raised when speech-to-text fails (Gemini error, timeout, empty audio)."""


class SynthesisError(VoiceError):
    """Raised when text-to-speech fails (Gemini error, timeout, empty text)."""
