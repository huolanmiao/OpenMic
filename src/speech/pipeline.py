import os
import ChatTTS
import numpy as np
from typing import List, Any, Dict, Union

from src.speech.modules.text_refiner import TextRefiner
from src.speech.modules.filler_injector import FillerInjector
from src.speech.modules.tts_engine import TTSEngine
from src.speech.modules.emotion_rhythm_controller import EmotionRhythmController
from src.speech.modules.audio_post_processor import AudioPostProcessor


class StandupSpeechPipeline:
    """
    Modular stand-up speech pipeline:
    1) LLM/ref-rule text rewrite -> ChatTTS-friendly segments
    2) Optional filler insertion
    3) ChatTTS synthesis with safe defaults
    """

    def __init__(
        self,
        model_path: str = "/home/zhuran/ran/OpenMic/models",
        device: str = "cuda",
        use_llm: bool = True,
        enable_fillers: bool = True,
        enable_controller: bool = True,
        enable_post_process: bool = True,
        sample_rate: int = 24000,
    ) -> None:
        self.device = device
        self.use_llm = use_llm
        self.enable_fillers = enable_fillers
        self.enable_controller = enable_controller
        self.enable_post_process = enable_post_process
        self.sample_rate = sample_rate

        # Load ChatTTS locally (per user constraint: no HF download)
        self.chat = ChatTTS.Chat()
        print(f"Loading ChatTTS from {model_path}...")
        self.chat.load (source="custom", custom_path=model_path, device=device)

        # Speaker embedding: keep stable for consistency; allow override via env seed later if needed
        self.spk_emb = self.chat.sample_random_speaker()

        # Modules
        self.text_refiner = TextRefiner()
        self.filler_injector = FillerInjector()
        self.tts_engine = TTSEngine(self.chat, self.spk_emb)
        self.controller = EmotionRhythmController()
        self.audio_processor = AudioPostProcessor(sample_rate=sample_rate)

    def refine_text(self, raw_text: str) -> List[str]:
        refined = self.text_refiner.refine(raw_text, use_llm=self.use_llm)
        if self.enable_fillers:
            refined = self.filler_injector.inject(refined)
        # Final guard: drop empty strings
        refined = [t.strip() for t in refined if t and t.strip()]
        return refined

    def synthesize(
        self,
        text_list: List[str],
        temperature: float = 0.3,
        return_segments: bool = False,
    ) -> Dict[str, Any]:
        controls = None
        if self.enable_controller:
            print(f"EmotionRhythmController: analyzing controls for {len(text_list)} segments.")
            controls = self.controller.analyze(text_list)
        raw_segments = self.tts_engine.synthesize(
            text_list,
            temperature=temperature,
            return_segments=True,
            controls=controls,
        )
        processed_segments = (
            self.audio_processor.process_segments(raw_segments)
            if self.enable_post_process
            else raw_segments
        )
        if return_segments:
            audio = processed_segments
        else:
            audio = (
                self.audio_processor.concat_with_pauses(
                    processed_segments,
                    controls,
                    default_pause=0.8,
                )
                if self.enable_post_process
                else self._simple_concat(processed_segments)
            )
        return {"audio": audio, "controls": controls}

    @staticmethod
    def _simple_concat(wavs: List[Any]):
        if not wavs:
            return []
        try:
            import numpy as np

            return np.concatenate(wavs)
        except Exception:
            return wavs

    def run(
        self,
        raw_text: str,
        return_text: bool = False,
        return_control: bool = False,
        temperature: float = 0.3,
    ) -> Union[np.ndarray, Dict[str, Any]]:
        print("Refining text...")
        refined_text = self.refine_text(raw_text)
        print(f"Refined text segments: {len(refined_text)}")

        print("Synthesizing audio...")
        result = self.synthesize(refined_text, temperature=temperature)
        audio = result["audio"]
        print(f"Audio generated, shape: {audio.shape if hasattr(audio, 'shape') else 'segments'}")

        if return_text or return_control:
            return {
                "audio": audio,
                "text": refined_text if return_text else None,
                "controls": result["controls"] if return_control else None,
            }
        return audio

    def run_segments(
        self,
        raw_text: str,
        return_text: bool = False,
        return_control: bool = False,
        temperature: float = 0.3,
    ) -> Union[List[np.ndarray], Dict[str, Any]]:
        """Return list of audio segments (no concatenation)."""
        print("Refining text...")
        refined_text = self.refine_text(raw_text)
        print(f"Refined text segments: {len(refined_text)}")

        print("Synthesizing audio (segmented)...")
        result = self.synthesize(refined_text, temperature=temperature, return_segments=True)
        wavs = result["audio"]
        if isinstance(wavs, list):
            print(f"Segments generated: {len(wavs)}")
        else:
            print("No segments generated.")

        if return_text or return_control:
            return {
                "audio": wavs,
                "text": refined_text if return_text else None,
                "controls": result["controls"] if return_control else None,
            }
        return wavs
