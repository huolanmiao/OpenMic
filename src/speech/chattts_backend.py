from typing import Iterable, Optional

from .types import BackendResponse, ProsodyPlan, StreamChunk


class ChatTTSBackend:
    """
    Placeholder ChatTTS backend.
    Real implementation will load ChatTTS, apply prosody controls, and stream or return audio.
    """

    def __init__(self, model_name: str = "chattts", device: Optional[str] = None):
        self.model_name = model_name
        self.device = device
        # TODO: lazy-load ChatTTS model when implemented.

    def synthesize(self, plan: ProsodyPlan, stream: bool = False) -> BackendResponse:
        """Synthesize audio from a prosody plan.

        Args:
            plan: prosody instructions.
            stream: whether to yield streaming chunks.
        """
        # TODO: implement ChatTTS integration; return silence bytes placeholder for now.
        dummy_audio = b""
        dummy_chunks: Optional[Iterable[StreamChunk]] = None
        return BackendResponse(audio=dummy_audio, sample_rate=16000, chunks=dummy_chunks)
