from typing import Iterable

from .types import StreamChunk


class AudioPostProcessor:
    """Lightweight audio post-processing (stubs)."""

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate

    def finalize(self, audio: bytes, sample_rate: int) -> bytes:
        """Normalize and resample if needed (stub)."""
        # TODO: add loudness normalization and resampling to target_sample_rate.
        return audio

    def concat_stream(self, chunks: Iterable[StreamChunk]) -> bytes:
        """Concatenate stream chunks into a single bytes buffer."""
        return b"".join(chunk.audio for chunk in chunks)
