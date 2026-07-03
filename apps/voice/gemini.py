"""Gemini-backed concrete `VoiceProvider`.

Skeleton only in E04-S01: the class shape, constructor, and method
signatures are in place so downstream code (bot integration, retry
wrapper) can be written against the real type. Real Gemini calls
land in E04-S02 (transcribe) and E04-S03 (synthesize).

The Gemini client is typed as `Any` on purpose — the `google-genai`
SDK is NOT a dependency yet (project-context R6: no library until a
real call needs it). E04-S02 adds `google-genai` to requirements.txt
and tightens the type at the same time.
"""

from typing import Any


class GeminiVoiceProvider:
    """Gemini implementation of the `VoiceProvider` Protocol.

    The `client` is injected so tests can pass a fake without hitting
    the network (project-context R11: mock external only).
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def transcribe(self, audio: bytes, language: str) -> str:
        raise NotImplementedError("wired in E04-S02/S03")

    async def synthesize(self, text: str, language: str) -> bytes:
        raise NotImplementedError("wired in E04-S02/S03")
