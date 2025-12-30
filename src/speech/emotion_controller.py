from typing import Dict, List, Optional

from .types import EmotionPlan, EmotionProfile, ParsedScript, Segment


DEFAULT_PROFILES: Dict[str, EmotionProfile] = {
    "平稳": EmotionProfile(name="平稳", speed_scale=1.0, f0_shift_semitones=0.0, energy_scale=1.0, temperature=0.6),
    "吐槽": EmotionProfile(name="吐槽", speed_scale=0.95, f0_shift_semitones=-0.5, energy_scale=0.9, temperature=0.55),
    "兴奋": EmotionProfile(name="兴奋", speed_scale=1.05, f0_shift_semitones=1.0, energy_scale=1.1, temperature=0.75),
    "无语": EmotionProfile(name="无语", speed_scale=0.9, f0_shift_semitones=-1.0, energy_scale=0.85, temperature=0.5),
}


class EmotionController:
    """Assigns emotion profiles to segments based on roles and hints."""

    def __init__(self, profiles: Optional[Dict[str, EmotionProfile]] = None):
        self.profiles = profiles or DEFAULT_PROFILES

    def plan(self, parsed: ParsedScript, preferred: Optional[str] = None) -> EmotionPlan:
        default_profile = self._select_default(preferred)
        segment_profiles: List[EmotionProfile] = []
        for segment in parsed.segments:
            profile = self._profile_for_segment(segment, default_profile)
            segment_profiles.append(profile)
        return EmotionPlan(default_profile=default_profile, segment_profiles=segment_profiles)

    def _select_default(self, preferred: Optional[str]) -> EmotionProfile:
        if preferred and preferred in self.profiles:
            return self.profiles[preferred]
        return self.profiles["平稳"]

    def _profile_for_segment(self, segment: Segment, default_profile: EmotionProfile) -> EmotionProfile:
        if segment.tone_hint and segment.tone_hint in self.profiles:
            return self.profiles[segment.tone_hint]
        if segment.role == "setup":
            return EmotionProfile(
                name=f"{default_profile.name}-setup",
                speed_scale=default_profile.speed_scale * 0.95,
                f0_shift_semitones=default_profile.f0_shift_semitones - 0.2,
                energy_scale=default_profile.energy_scale * 0.95,
                temperature=default_profile.temperature,
            )
        if segment.role == "punch":
            return EmotionProfile(
                name=f"{default_profile.name}-punch",
                speed_scale=default_profile.speed_scale * 1.02,
                f0_shift_semitones=default_profile.f0_shift_semitones + 0.3,
                energy_scale=default_profile.energy_scale * 1.05,
                temperature=default_profile.temperature + 0.05,
            )
        return default_profile
