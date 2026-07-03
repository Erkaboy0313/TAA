"""Smoke tests for the voice provider abstraction.

The Gemini concrete implementation is exercised in `test_gemini.py`;
here we only pin the structural contract (Protocol + exception hierarchy)
so a refactor of gemini.py can't silently break the shape other apps
rely on.
"""

from apps.core.exceptions import DomainError
from apps.voice.exceptions import SynthesisError, TranscriptionError, VoiceError
from apps.voice.gemini import GeminiVoiceProvider
from apps.voice.providers import VoiceProvider


def test_gemini_voice_provider_satisfies_protocol_structural_check() -> None:
    provider = GeminiVoiceProvider()
    assert isinstance(provider, VoiceProvider)
    assert callable(provider.transcribe)
    assert callable(provider.synthesize)


def test_voice_exception_hierarchy_roots_at_domain_error() -> None:
    assert issubclass(VoiceError, DomainError)
    assert issubclass(TranscriptionError, VoiceError)
    assert issubclass(SynthesisError, VoiceError)
