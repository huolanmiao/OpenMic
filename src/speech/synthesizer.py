from typing import Optional, Tuple

from .audio_post_processor import AudioPostProcessor
from .chattts_backend import ChatTTSBackend
from .emotion_controller import EmotionController
from .filler_injector import FillerInjector
from .performance_marker_parser import PerformanceMarkerParser
from .prosody_controller import ProsodyController
from .evaluator import SpeechEvaluator
from .types import BackendResponse, EvalReport, SynthesisRequest, SynthesisResult


class SpeechSynthesizer:
    """Facade for the speech pipeline. This is the public entry point."""

    def __init__(
        self,
        backend: Optional[ChatTTSBackend] = None,
        parser: Optional[PerformanceMarkerParser] = None,
        filler_injector: Optional[FillerInjector] = None,
        emotion_controller: Optional[EmotionController] = None,
        prosody_controller: Optional[ProsodyController] = None,
        post_processor: Optional[AudioPostProcessor] = None,
        evaluator: Optional[SpeechEvaluator] = None,
    ):
        self.backend = backend or ChatTTSBackend()
        self.parser = parser or PerformanceMarkerParser()
        self.filler_injector = filler_injector or FillerInjector()
        self.emotion_controller = emotion_controller or EmotionController()
        self.prosody_controller = prosody_controller or ProsodyController()
        self.post_processor = post_processor or AudioPostProcessor()
        self.evaluator = evaluator or SpeechEvaluator()

    def synthesize(self, request: SynthesisRequest) -> Tuple[SynthesisResult, Optional[EvalReport]]:
        parsed = self.parser.parse(request.script)
        filler_plan = self.filler_injector.inject(parsed.segments, deterministic=True)
        emotion_plan = self.emotion_controller.plan(parsed, preferred=request.emotion_profile)
        prosody_plan = self.prosody_controller.build_plan(filler_plan.segments, emotion_plan)

        backend_response: BackendResponse = self.backend.synthesize(prosody_plan, stream=request.stream)
        audio_bytes = backend_response.audio

        if request.stream and backend_response.chunks is not None:
            audio_bytes = self.post_processor.concat_stream(backend_response.chunks)

        audio_bytes = self.post_processor.finalize(audio_bytes, backend_response.sample_rate)

        eval_report: Optional[EvalReport] = None
        if request.evaluate:
            eval_report = self.evaluator.evaluate(prosody_plan, audio_bytes, self.post_processor.target_sample_rate)

        result = SynthesisResult(audio=audio_bytes, sample_rate=self.post_processor.target_sample_rate, report=eval_report)
        return result, eval_report
