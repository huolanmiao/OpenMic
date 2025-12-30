from .types import EvalReport, ProsodyPlan


class SpeechEvaluator:
    """Rule-based proxy evaluator (placeholder)."""

    def evaluate(self, plan: ProsodyPlan, audio: bytes, sample_rate: int) -> EvalReport:
        # TODO: implement pause alignment, stress hit rate, tempo adherence, MOS proxy.
        return EvalReport(notes=["Evaluation not implemented; placeholder only."])
