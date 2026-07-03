"""Voice provider abstraction.

`VoiceProvider` is the structural contract every concrete engine
(Gemini today, possibly Vertex/OpenAI later — architecture §12) must
satisfy. Consumers depend on this Protocol, not on a concrete class,
which keeps swap-out cheap (project-context R3 dependency inversion).

Audio is always raw bytes in-memory — never a file path, never disk
(project-context R9).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class VoiceProvider(Protocol):
    """Structural contract for a voice engine.

    `runtime_checkable` lets tests assert `isinstance(x, VoiceProvider)` —
    only the presence of the two methods is checked (not signatures),
    which is enough as a smoke check that a class advertises the shape.
    """

    async def transcribe(self, audio: bytes, language: str) -> str:
        """Convert speech audio bytes to plain text in the given language."""
        ...

    async def synthesize(self, text: str, language: str) -> bytes:
        """Render text as speech audio bytes in the given language."""
        ...
