"""Gemini-backed concrete `VoiceProvider`.

Real STT + TTS calls land in this file (E04-S02, E04-S03) with a shared
retry + timeout wrapper (E04-S04). The Gemini client is created lazily
and cached — first call decides whether the API key is present, later
calls reuse the same `google.genai.Client` instance.

Bytes stay in memory only (project-context R9). Nothing is logged that
could leak audio content or user text.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING

import httpx
from google import genai
from google.genai import types as genai_types
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from django.conf import settings

from apps.voice.exceptions import SynthesisError, TranscriptionError, VoiceError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

_STT_MODEL = "gemini-2.0-flash"
_TTS_MODEL = "gemini-2.0-flash"
# Retry only on network-layer failures. A 4xx content error (e.g. malformed
# audio) must NOT be retried — R9 rules out blind retry on content errors.
_RETRYABLE = retry_if_exception_type(httpx.HTTPError)


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Return the process-wide Gemini client. Cached to reuse HTTP pool."""
    if not settings.GEMINI_API_KEY:
        raise VoiceError("gemini not configured")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def _with_retry_and_timeout[T](
    op: Callable[[], Awaitable[T]],
    *,
    on_timeout: str,
) -> T:
    """Run `op` with 3x exp backoff on httpx errors, capped at settings.GEMINI_TIMEOUT_SECONDS."""

    async def _retrying() -> T:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
            retry=_RETRYABLE,
            reraise=True,
        ):
            with attempt:
                return await op()
        raise RuntimeError("unreachable")  # pragma: no cover

    try:
        return await asyncio.wait_for(_retrying(), timeout=settings.GEMINI_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        raise TimeoutError(on_timeout) from exc


class GeminiVoiceProvider:
    """Gemini implementation of the `VoiceProvider` Protocol.

    No constructor argument — the client is resolved lazily via `_client()`.
    Tests patch `apps.voice.gemini._client` (or its result) to avoid the
    network (project-context R11: mock external only).
    """

    async def transcribe(self, audio: bytes, language: str) -> str:
        """Convert speech audio bytes to plain text using Gemini STT."""
        client = _client()

        async def _call() -> str:
            response = await client.aio.models.generate_content(
                model=_STT_MODEL,
                contents=[
                    genai_types.Part.from_bytes(data=audio, mime_type="audio/ogg"),
                    f"Transcribe this audio in {language}. Return plain text only.",
                ],
            )
            return (response.text or "").strip()

        try:
            return await _with_retry_and_timeout(_call, on_timeout="stt timeout")
        except TimeoutError as exc:
            raise TranscriptionError(
                f"stt timeout after {settings.GEMINI_TIMEOUT_SECONDS}s"
            ) from exc
        except (RetryError, httpx.HTTPError) as exc:
            raise TranscriptionError("stt failed after 3 attempts") from exc

    async def synthesize(self, text: str, language: str) -> bytes:
        """Render text as speech audio bytes using Gemini TTS."""
        client = _client()

        async def _call() -> bytes:
            response = await client.aio.models.generate_content(
                model=_TTS_MODEL,
                contents=[f"[lang={language}] {text}"],
                config=genai_types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                ),
            )
            audio = _extract_audio_bytes(response)
            if not audio:
                raise SynthesisError("tts returned no audio")
            return audio

        try:
            return await _with_retry_and_timeout(_call, on_timeout="tts timeout")
        except TimeoutError as exc:
            raise SynthesisError(f"tts timeout after {settings.GEMINI_TIMEOUT_SECONDS}s") from exc
        except (RetryError, httpx.HTTPError) as exc:
            raise SynthesisError("tts failed after 3 attempts") from exc


def _extract_audio_bytes(response: object) -> bytes:
    """Pull the first inline audio blob out of a Gemini response, or b''."""
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        parts = getattr(getattr(candidate, "content", None), "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None)
            if data:
                return bytes(data)
    return b""
