"""Smoke tests for the voice provider abstraction and Gemini skeleton."""

import pytest

from apps.core.exceptions import DomainError
from apps.voice.exceptions import SynthesisError, TranscriptionError, VoiceError
from apps.voice.gemini import GeminiVoiceProvider
from apps.voice.providers import VoiceProvider


def test_gemini_voice_provider_satisfies_protocol_structural_check() -> None:
    provider = GeminiVoiceProvider(client=object())
    assert isinstance(provider, VoiceProvider)
    assert callable(provider.transcribe)
    assert callable(provider.synthesize)


async def test_transcribe_raises_not_implemented_until_e04_s02() -> None:
    provider = GeminiVoiceProvider(client=object())
    with pytest.raises(NotImplementedError, match="S02"):
        await provider.transcribe(b"", "uz-Latn")


async def test_synthesize_raises_not_implemented_until_e04_s03() -> None:
    provider = GeminiVoiceProvider(client=object())
    with pytest.raises(NotImplementedError, match="S03"):
        await provider.synthesize("salom", "uz-Latn")


def test_voice_exception_hierarchy_roots_at_domain_error() -> None:
    assert issubclass(VoiceError, DomainError)
    assert issubclass(TranscriptionError, VoiceError)
    assert issubclass(SynthesisError, VoiceError)
