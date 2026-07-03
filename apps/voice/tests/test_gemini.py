"""Tests for `apps.voice.gemini` — STT + TTS with retry + timeout.

Every test patches `apps.voice.gemini._client` so no real network call
leaves the process (project-context R11). Audio bytes never touch disk
and never appear in log assertions (R10).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from apps.voice.exceptions import SynthesisError, TranscriptionError, VoiceError
from apps.voice.gemini import GeminiVoiceProvider, _client

_MAX_ATTEMPTS = 3
_SECOND_ATTEMPT = 2


def _fake_client(*, generate: AsyncMock) -> SimpleNamespace:
    """Build a stand-in for `google.genai.Client` with the shape the code uses."""
    return SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))


def _stt_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, candidates=[])


def _tts_response(audio: bytes) -> SimpleNamespace:
    part = SimpleNamespace(inline_data=SimpleNamespace(data=audio))
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
    return SimpleNamespace(text=None, candidates=[candidate])


async def _instant_timeout(awaitable: object, *_args: object, **_kwargs: object) -> object:
    """Close the wrapped coroutine, then raise TimeoutError.

    Without close(), the retry coroutine created by `_with_retry_and_timeout`
    stays pending and pytest raises PytestUnraisableExceptionWarning in the
    NEXT test — a nasty cross-test leak.
    """
    if hasattr(awaitable, "close"):
        awaitable.close()
    raise TimeoutError


@pytest.fixture(autouse=True)
def _reset_client_cache() -> None:
    """Clear the lru_cache between tests so patched settings take effect."""
    _client.cache_clear()
    yield
    _client.cache_clear()


async def test_transcribe_returns_text_from_gemini_response() -> None:
    generate = AsyncMock(return_value=_stt_response("salom dunyo"))
    with patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)):
        provider = GeminiVoiceProvider()
        result = await provider.transcribe(b"\x00\x01", "uz-Latn")
    assert result == "salom dunyo"
    assert generate.await_count == 1


async def test_synthesize_returns_bytes_from_gemini_response() -> None:
    audio_out = b"OGGS\x00fake-tts-bytes"
    generate = AsyncMock(return_value=_tts_response(audio_out))
    with patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)):
        provider = GeminiVoiceProvider()
        result = await provider.synthesize("Salom dunyo", "uz-Latn")
    assert result == audio_out
    assert generate.await_count == 1


async def test_transcribe_retries_on_transient_http_error_then_succeeds() -> None:
    generate = AsyncMock(
        side_effect=[
            httpx.ConnectError("boom"),
            _stt_response("second try wins"),
        ]
    )
    with patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)):
        provider = GeminiVoiceProvider()
        result = await provider.transcribe(b"\x00\x01", "uz-Latn")
    assert result == "second try wins"
    assert generate.await_count == _SECOND_ATTEMPT


async def test_transcribe_gives_up_after_three_attempts_and_raises_transcription_error() -> None:
    generate = AsyncMock(side_effect=httpx.ConnectError("still down"))
    with (
        patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)),
        pytest.raises(TranscriptionError, match="3 attempts"),
    ):
        provider = GeminiVoiceProvider()
        await provider.transcribe(b"\x00\x01", "uz-Latn")
    assert generate.await_count == _MAX_ATTEMPTS


async def test_transcribe_wraps_asyncio_timeout_as_transcription_error() -> None:
    generate = AsyncMock(return_value=_stt_response("never returned"))
    with (
        patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)),
        patch("apps.voice.gemini.asyncio.wait_for", side_effect=_instant_timeout),
        pytest.raises(TranscriptionError, match="timeout"),
    ):
        provider = GeminiVoiceProvider()
        await provider.transcribe(b"\x00\x01", "uz-Latn")


async def test_synthesize_retries_and_gives_up_with_synthesis_error() -> None:
    generate = AsyncMock(side_effect=httpx.ReadTimeout("slow"))
    with (
        patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)),
        pytest.raises(SynthesisError, match="3 attempts"),
    ):
        provider = GeminiVoiceProvider()
        await provider.synthesize("Salom", "uz-Latn")
    assert generate.await_count == _MAX_ATTEMPTS


async def test_synthesize_wraps_asyncio_timeout_as_synthesis_error() -> None:
    generate = AsyncMock(return_value=_tts_response(b"unused"))
    with (
        patch("apps.voice.gemini._client", return_value=_fake_client(generate=generate)),
        patch("apps.voice.gemini.asyncio.wait_for", side_effect=_instant_timeout),
        pytest.raises(SynthesisError, match="timeout"),
    ):
        provider = GeminiVoiceProvider()
        await provider.synthesize("Salom", "uz-Latn")


async def test_transcribe_raises_voice_error_when_api_key_missing(settings) -> None:
    settings.GEMINI_API_KEY = ""
    provider = GeminiVoiceProvider()
    with pytest.raises(VoiceError, match="gemini not configured"):
        await provider.transcribe(b"\x00\x01", "uz-Latn")


async def test_synthesize_raises_voice_error_when_api_key_missing(settings) -> None:
    settings.GEMINI_API_KEY = ""
    provider = GeminiVoiceProvider()
    with pytest.raises(VoiceError, match="gemini not configured"):
        await provider.synthesize("Salom", "uz-Latn")
