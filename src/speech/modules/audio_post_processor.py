import numpy as np
from typing import List, Dict, Any, Optional


class AudioPostProcessor:
    """Audio post-processing for ChatTTS outputs: denoise, loudness match, concat with pauses."""

    def __init__(
        self,
        sample_rate: int = 24000,
        target_dbfs: float = -18.0,
        cutoff_hz: float = 8000.0,
        fade_ms: float = 20.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.target_dbfs = target_dbfs
        self.cutoff_hz = cutoff_hz
        self.fade_ms = fade_ms

    def process_segments(self, segments: List[np.ndarray]) -> List[np.ndarray]:
        processed: List[np.ndarray] = []
        for seg in segments:
            if seg is None or len(seg) == 0:
                continue
            wav = np.asarray(seg, dtype=np.float32)
            wav = self._lowpass_fft(wav, self.cutoff_hz)
            wav = self._normalize_rms(wav, self.target_dbfs)
            wav = self._apply_fade(wav, self.fade_ms)
            processed.append(wav)
        return processed

    def concat_with_pauses(
        self,
        segments: List[np.ndarray],
        controls: Optional[List[Dict[str, Any]]],
        default_pause: float = 0.8,
    ) -> np.ndarray:
        if not segments:
            return np.zeros(0, dtype=np.float32)
        parts: List[np.ndarray] = []
        sr = self.sample_rate
        for idx, seg in enumerate(segments):
            parts.append(seg)
            pause_sec = default_pause
            if controls and idx < len(controls):
                try:
                    pause_sec = float(controls[idx].get("end_pause_sec", default_pause))
                except Exception:
                    pause_sec = default_pause
            pause_sec = max(0.0, min(5.0, pause_sec))
            if pause_sec > 0:
                silence = np.zeros(int(pause_sec * sr), dtype=np.float32)
                parts.append(self._apply_fade(silence, self.fade_ms))
        return np.concatenate(parts)

    def _lowpass_fft(self, wav: np.ndarray, cutoff_hz: float) -> np.ndarray:
        # Simple FFT low-pass: zero out bins above cutoff
        if len(wav) == 0:
            return wav
        sr = self.sample_rate
        freqs = np.fft.rfftfreq(len(wav), d=1.0 / sr)
        spectrum = np.fft.rfft(wav)
        mask = freqs <= cutoff_hz
        spectrum = spectrum * mask
        filtered = np.fft.irfft(spectrum, n=len(wav))
        return filtered.astype(np.float32)

    def _normalize_rms(self, wav: np.ndarray, target_dbfs: float) -> np.ndarray:
        eps = 1e-6
        rms = np.sqrt(np.mean(np.square(wav), dtype=np.float64) + eps)
        target_rms = 10 ** (target_dbfs / 20.0)
        gain = target_rms / max(rms, eps)
        out = wav * gain
        # Avoid clipping
        out = np.clip(out, -1.0, 1.0)
        return out.astype(np.float32)

    def _apply_fade(self, wav: np.ndarray, fade_ms: float) -> np.ndarray:
        if len(wav) == 0:
            return wav
        sr = self.sample_rate
        fade_len = int(sr * fade_ms / 1000.0)
        fade_len = max(1, min(len(wav) // 2, fade_len))
        fade = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        out = wav.astype(np.float32).copy()
        out[:fade_len] *= fade  # fade in
        out[-fade_len:] *= fade[::-1]  # fade out
        return out
