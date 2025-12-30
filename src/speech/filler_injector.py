import dataclasses
from typing import List, Sequence

from .types import FillerPlan, Segment


class FillerInjector:
    """
    Inserts natural fillers based on pause positions or clause boundaries.
    This stub is deterministic-friendly for testing.
    """

    def __init__(self, fillers: Sequence[str] = ("呃", "那个", "就是"), max_fillers: int = 3):
        self.fillers = list(fillers)
        self.max_fillers = max_fillers

    def inject(self, parsed_segments: List[Segment], deterministic: bool = True) -> FillerPlan:
        """Return a new plan with fillers inserted.

        Args:
            parsed_segments: segments from parser.
            deterministic: if True, use fixed pattern; else allow randomness (to be added).
        """
        new_segments: List[Segment] = []
        used = 0
        filler_cycle = list(self.fillers)

        for idx, seg in enumerate(parsed_segments):
            new_seg = dataclasses.replace(seg)
            if used < self.max_fillers and self._should_insert(seg, idx, deterministic):
                filler = filler_cycle[used % len(filler_cycle)]
                new_seg.text = f"{filler}，{new_seg.text}"
                used += 1
            new_segments.append(new_seg)

        return FillerPlan(segments=new_segments)

    @staticmethod
    def _should_insert(segment: Segment, idx: int, deterministic: bool) -> bool:
        if not segment.text:
            return False
        if len(segment.text) > 25 and idx % 2 == 1:
            return True if deterministic else False
        return False
