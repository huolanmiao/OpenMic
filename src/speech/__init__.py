"""
OpenMic Speech Module (Task 3)
Effects professional-grade stand-up comedy speech synthesis with performance markers.

Core Components:
- StandupSpeechPipeline: End-to-end pipeline (Text -> Audio)
- TextRefiner: LLM-based text preprocessing for natural delivery
- EmotionRhythmController: Controls pacing, pauses, and laughter
- FillerInjector: Inserts natural filler words (e.g., "uh", "um")
- AudioPostProcessor: Audio normalization and enhancing

Usage:
    from src.speech import StandupSpeechPipeline
    
    pipeline = StandupSpeechPipeline()
    result = pipeline.run("Hello, world!", return_text=True)
    audio_data = result["audio"]
"""

from src.speech.pipeline import StandupSpeechPipeline
from src.speech.modules.text_refiner import TextRefiner
from src.speech.modules.filler_injector import FillerInjector
from src.speech.modules.emotion_rhythm_controller import EmotionRhythmController
from src.speech.modules.audio_post_processor import AudioPostProcessor
from src.speech.modules.tts_engine import TTSEngine

__all__ = [
    "StandupSpeechPipeline",
    "TextRefiner",
    "FillerInjector",
    "EmotionRhythmController",
    "AudioPostProcessor",
    "TTSEngine",
]
