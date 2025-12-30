from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Literal, Optional, Sequence, Tuple


# Core data structures used across the speech module. Keep dependency-free.

SegmentRole = Literal["setup", "punch", "outro", "generic"]


@dataclass
class Pause:
    duration_s: float
    reason: Literal["setup", "punch", "post_punch", "comma", "period", "custom"] = "custom"


@dataclass
class Stress:
    token: str
    strength: float = 1.0  # 1.0 = default, >1.0 = stronger emphasis


@dataclass
class Segment:
    text: str
    role: SegmentRole = "generic"
    pauses_before: List[Pause] = field(default_factory=list)
    pauses_after: List[Pause] = field(default_factory=list)
    stresses: List[Stress] = field(default_factory=list)
    tone_hint: Optional[str] = None  # e.g., "吐槽", "兴奋", "无语"
    speed_scale: Optional[float] = None  # tempo multiplier suggestion


@dataclass
class EmotionProfile:
    name: str
    speed_scale: float = 1.0
    f0_shift_semitones: float = 0.0
    energy_scale: float = 1.0
    temperature: float = 0.7


@dataclass
class EmotionPlan:
    default_profile: EmotionProfile
    segment_profiles: List[EmotionProfile] = field(default_factory=list)


@dataclass
class ProsodyInstruction:
    text: str
    speed_scale: float
    f0_shift_semitones: float
    energy_scale: float
    pauses_before: List[Pause] = field(default_factory=list)
    pauses_after: List[Pause] = field(default_factory=list)
    stresses: List[Stress] = field(default_factory=list)
    temperature: float = 0.7


@dataclass
class SynthesisRequest:
    script: str
    style: Optional[str] = None
    emotion_profile: Optional[str] = None  # identifier
    seed: Optional[int] = None
    max_len_s: Optional[float] = None
    stream: bool = False
    evaluate: bool = False


@dataclass
class EvalReport:
    pause_alignment_score: Optional[float] = None
    stress_hit_rate: Optional[float] = None
    tempo_adherence: Optional[float] = None
    mos_proxy: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class SynthesisResult:
    audio: bytes  # 16 kHz PCM mono
    sample_rate: int = 16000
    report: Optional[EvalReport] = None


@dataclass
class StreamChunk:
    audio: bytes
    sample_rate: int


AudioStream = Iterator[StreamChunk]


@dataclass
class ProsodyPlan:
    instructions: List[ProsodyInstruction]


@dataclass
class ParsedScript:
    segments: List[Segment]


@dataclass
class FillerPlan:
    segments: List[Segment]


@dataclass
class ProsodyContext:
    parsed: ParsedScript
    emotion: EmotionPlan
    prosody: ProsodyPlan


@dataclass
class BackendResponse:
    audio: bytes
    sample_rate: int
    chunks: Optional[Iterable[StreamChunk]] = None
