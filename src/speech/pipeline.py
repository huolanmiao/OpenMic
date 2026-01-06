import os
import ChatTTS
import numpy as np
import torch
from typing import List, Any, Dict, Union, Optional

from src.speech.chattts_patch import apply_chattts_patch

from src.speech.modules.text_refiner import TextRefiner
from src.speech.modules.filler_injector import FillerInjector
from src.speech.modules.tts_engine import TTSEngine
from src.speech.modules.emotion_rhythm_controller import EmotionRhythmController
from src.speech.modules.audio_post_processor import AudioPostProcessor

# Apply ChatTTS runtime patch (cache-length guard) so users don't need to modify site-packages.
apply_chattts_patch()


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
        voice_bank_dir: str = "/root/OpenMic/voices",
        voice_name: Optional[str] = None,
        target_sample_rate: int = 16000,
        enable_resample: bool = True,
    ) -> None:
        self.device = device
        self.use_llm = use_llm
        self.enable_fillers = enable_fillers
        self.enable_controller = enable_controller
        self.enable_post_process = enable_post_process
        self.sample_rate = sample_rate
        self.target_sample_rate = target_sample_rate
        self.enable_resample = enable_resample

        if ChatTTS is None:
            raise ImportError(
                "ChatTTS is not installed. Install it with `pip install ChatTTS` and ensure it is on your PYTHONPATH."
            )
        # Load ChatTTS locally (per user constraint: no HF download)
        self.chat = ChatTTS.Chat()
        print(f"Loading ChatTTS from {model_path}...")
        self.chat.load(source="custom", custom_path=model_path, device=device)
        self.voice_bank_dir = voice_bank_dir
        self.voice_bank = self._load_voice_bank(voice_bank_dir)
        # Speaker embedding: choose by name if provided, otherwise random for variety
        self.spk_emb = self._select_speaker(voice_name)

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

    def list_voices(self) -> Dict[str, Dict[str, str]]:
        """Return available voices from the voice bank with comments."""
        return self.voice_bank

    def set_voice(self, voice_name: Optional[str] = None):
        """Switch current speaker embedding; None or 'random' will resample."""
        self.spk_emb = self._select_speaker(voice_name)
        self.tts_engine.set_speaker(self.spk_emb)
        return self.spk_emb

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
            if self.enable_resample and self.target_sample_rate != self.sample_rate:
                audio = [self.audio_processor.resample(seg, self.target_sample_rate) for seg in audio]
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
            if self.enable_resample and self.target_sample_rate != self.sample_rate:
                audio = self.audio_processor.resample(audio, self.target_sample_rate)
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

        
        return {
            "audio": audio,
            "text": refined_text if return_text else None,
            "controls": result["controls"] if return_control else None,
        }

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

    def _load_voice_bank(self, directory: str) -> Dict[str, Dict[str, str]]:
        if not directory or not os.path.isdir(directory):
            return {}
        bank: Dict[str, Dict[str, str]] = {}
        for fname in os.listdir(directory):
            if not fname.endswith(".pt"):
                continue
            stem = os.path.splitext(fname)[0]
            pt_path = os.path.join(directory, fname)
            txt_path = os.path.join(directory, f"{stem}.txt")
            comment = ""
            try:
                if os.path.isfile(txt_path):
                    with open(txt_path, "r", encoding="utf-8") as f:
                        comment = f.read().strip()
            except Exception:
                comment = ""
            bank[stem] = {"path": pt_path, "comment": comment}
        return bank

    def _select_speaker(self, voice_name: Optional[str]):
        # 'random' or None -> random speaker
        if voice_name is None or (isinstance(voice_name, str) and voice_name.lower() == "random"):
            return self.chat.sample_random_speaker()

        meta = self.voice_bank.get(voice_name) if hasattr(self, "voice_bank") else None
        if meta:
            try:
                spk = torch.load(meta["path"], map_location=self.device if torch.cuda.is_available() else "cpu")
                print(f"Loaded speaker: {voice_name} ({meta.get('comment', '')})")
                return spk
            except Exception as exc:
                print(f"Warning: failed to load speaker '{voice_name}', fallback random. Reason: {exc}")
        else:
            if voice_name:
                print(f"Voice '{voice_name}' not found in {self.voice_bank_dir}, fallback random.")
        return self.chat.sample_random_speaker()
