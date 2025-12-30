from typing import List

from .types import EmotionPlan, ProsodyInstruction, ProsodyPlan, Segment


class ProsodyController:
    """Converts parsed segments + emotion plan into prosody instructions."""

    def build_plan(self, segments: List[Segment], emotion: EmotionPlan) -> ProsodyPlan:
        instructions: List[ProsodyInstruction] = []
        for idx, segment in enumerate(segments):
            profile = emotion.segment_profiles[idx] if idx < len(emotion.segment_profiles) else emotion.default_profile
            instruction = ProsodyInstruction(
                text=segment.text,
                speed_scale=segment.speed_scale or profile.speed_scale or 1.0,
                f0_shift_semitones=profile.f0_shift_semitones,
                energy_scale=profile.energy_scale,
                pauses_before=segment.pauses_before,
                pauses_after=segment.pauses_after,
                stresses=segment.stresses,
                temperature=profile.temperature,
            )
            instructions.append(instruction)
        return ProsodyPlan(instructions=instructions)
