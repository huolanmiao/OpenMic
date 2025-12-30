import re
from typing import List

from .types import ParsedScript, Pause, Segment, SegmentRole, Stress


class PerformanceMarkerParser:
    """
    Rule-based parser for performance markers and default pauses.
    This is a lightweight placeholder; LLM-powered parsing can be added later.
    """

    def __init__(self, default_setup_pause: float = 0.8, default_post_punch_pause: float = 2.0):
        self.default_setup_pause = default_setup_pause
        self.default_post_punch_pause = default_post_punch_pause

    def parse(self, script: str) -> ParsedScript:
        """Parse raw script text into structured segments and markers.

        Args:
            script: Input stand-up script text (may include inline markers).

        Returns:
            ParsedScript with segments, pauses, stresses, tone hints, and roles.
        """
        markers = list(self._extract_markers(script))
        clean_script = self._strip_markers(script)

        sentences = self._split_sentences(clean_script)
        segments: List[Segment] = []
        for idx, sentence in enumerate(sentences):
            role = self._role_for_index(idx, len(sentences))
            segment = Segment(
                text=sentence.strip(),
                role=role,
                pauses_before=[],
                pauses_after=self._punctuation_pauses(sentence),
                stresses=[],
                tone_hint=None,
                speed_scale=None,
            )
            segments.append(segment)

        # Apply inline markers (tone/role/stress/pause)
        self._apply_role_markers(markers, segments)
        self._apply_tone_markers(markers, segments)
        self._apply_pause_markers(markers, segments)
        self._apply_stress_markers(markers, segments)

        # Add default role-based pauses
        for segment in segments:
            if segment.role == "setup":
                segment.pauses_before.append(Pause(duration_s=self.default_setup_pause, reason="setup"))
            if segment.role == "punch":
                segment.pauses_before.append(Pause(duration_s=self.default_setup_pause, reason="punch"))
                segment.pauses_after.append(Pause(duration_s=self.default_post_punch_pause, reason="post_punch"))

        return ParsedScript(segments=segments)

    @staticmethod
    def default_pauses_for_role(role: SegmentRole) -> List[Pause]:
        if role == "setup":
            return [Pause(duration_s=0.8, reason="setup")]
        if role == "punch":
            return [Pause(duration_s=0.8, reason="punch")]
        if role == "outro":
            return []
        return []

    @staticmethod
    def default_post_punch_pause() -> Pause:
        return Pause(duration_s=2.0, reason="post_punch")

    @staticmethod
    def stress_for_token(token: str, strength: float = 1.1) -> Stress:
        return Stress(token=token, strength=strength)

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        sentences = re.findall(r"[^。！？!?]+[。！？!?]?", text)
        if not sentences:
            return [text]
        return [s for s in sentences if s.strip()]

    @staticmethod
    def _punctuation_pauses(sentence: str) -> List[Pause]:
        sentence = sentence.strip()
        pauses: List[Pause] = []
        if not sentence:
            return pauses
        tail = sentence[-1]
        if tail in {",", "，", ";", "；"}:
            pauses.append(Pause(duration_s=0.35, reason="comma"))
        if tail in {"。", ".", "!", "！", "?", "？"}:
            pauses.append(Pause(duration_s=0.6, reason="period"))
        return pauses

    @staticmethod
    def _role_for_index(idx: int, total: int) -> SegmentRole:
        if total <= 1:
            return "punch"
        if idx == 0:
            return "setup"
        if idx == total - 1:
            return "punch"
        return "generic"

    @staticmethod
    def _extract_markers(script: str):
        pattern = re.compile(r"\(\*(?P<kind>[a-zA-Z]+):?(?P<value>[^*]*)\*\)")
        for match in pattern.finditer(script):
            kind = match.group("kind").lower()
            value = match.group("value").strip()
            yield {"kind": kind, "value": value}

    @staticmethod
    def _strip_markers(script: str) -> str:
        return re.sub(r"\(\*[^*]*\*\)", "", script)

    def _apply_role_markers(self, markers, segments: List[Segment]) -> None:
        role_markers = [m for m in markers if m["kind"] == "role"]
        for idx, marker in enumerate(role_markers):
            if idx < len(segments):
                role_val = marker["value"] or "generic"
                if role_val in ("setup", "punch", "outro", "generic"):
                    segments[idx].role = role_val  # type: ignore

    def _apply_tone_markers(self, markers, segments: List[Segment]) -> None:
        tone_markers = [m for m in markers if m["kind"] == "tone"]
        for idx, marker in enumerate(tone_markers):
            if idx < len(segments):
                segments[idx].tone_hint = marker["value"] or None

    def _apply_pause_markers(self, markers, segments: List[Segment]) -> None:
        pause_markers = [m for m in markers if m["kind"] == "pause"]
        for idx, marker in enumerate(pause_markers):
            if idx < len(segments):
                try:
                    duration = float(marker["value"])
                except ValueError:
                    continue
                segments[idx].pauses_before.append(Pause(duration_s=duration, reason="custom"))

    def _apply_stress_markers(self, markers, segments: List[Segment]) -> None:
        stress_markers = [m for m in markers if m["kind"] == "stress"]
        for marker in stress_markers:
            token = marker["value"]
            if not token:
                continue
            for segment in segments:
                if token in segment.text:
                    segment.stresses.append(self.stress_for_token(token))
