"""
Speech module exports.
"""

from .types import (
    AudioStream,
    BackendResponse,
    EmotionPlan,
    EmotionProfile,
    EvalReport,
    FillerPlan,
    ParsedScript,
    Pause,
    ProsodyContext,
    ProsodyInstruction,
    ProsodyPlan,
    Segment,
    SynthesisRequest,
    SynthesisResult,
    StreamChunk,
)
from .synthesizer import SpeechSynthesizer
from .performance_marker_parser import PerformanceMarkerParser
from .filler_injector import FillerInjector
from .emotion_controller import EmotionController
from .prosody_controller import ProsodyController
from .chattts_backend import ChatTTSBackend
from .audio_post_processor import AudioPostProcessor
from .evaluator import SpeechEvaluator

__all__ = [
    "AudioStream",
    "BackendResponse",
    "EmotionPlan",
    "EmotionProfile",
    "EvalReport",
    "FillerPlan",
    "ParsedScript",
    "Pause",
    "ProsodyContext",
    "ProsodyInstruction",
    "ProsodyPlan",
    "Segment",
    "SynthesisRequest",
    "SynthesisResult",
    "StreamChunk",
    "SpeechSynthesizer",
    "PerformanceMarkerParser",
    "FillerInjector",
    "EmotionController",
    "ProsodyController",
    "ChatTTSBackend",
    "AudioPostProcessor",
    "SpeechEvaluator",
]
