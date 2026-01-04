import json
import os
from typing import List, Optional, Dict, Any

from openai import OpenAI

DEFAULT_SPEED = 4  # maps to [speed_5]
DEFAULT_LAUGH = 0
DEFAULT_PAUSE = 3
DEFAULT_END_PAUSE = 0.8


class EmotionRhythmController:
    """Scores segments for laugh level, speed, pause density, and end pause via LLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model
        self.client: Optional[OpenAI] = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze(self, segments: List[str]) -> List[Dict[str, Any]]:
        if not segments:
            return []
        if not self.client:
            return [self._default_scores() for _ in segments]

        prompt = self._build_prompt(segments)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": self._format_segments(segments)},
                ],
                stream=False,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            if isinstance(data, list) and len(data) == len(segments):
                return [self._normalize_item(item) for item in data]
            else:
                print("EmotionRhythmController: unexpected LLM output, using defaults.")
        except Exception as exc:  # pragma: no cover
            print(f"EmotionRhythmController: LLM call failed, using defaults. Reason: {exc}")
        return [self._default_scores() for _ in segments]

    @staticmethod
    def _format_segments(segments: List[str]) -> str:
        numbered = [f"{i+1}. {seg}" for i, seg in enumerate(segments)]
        return "\n".join(numbered)

    @staticmethod
    def _build_prompt(segments: List[str]) -> str:
        return (
            "你是一名脱口秀语音导演。对下面每一段文本打分并返回 JSON 数组（长度与输入段数一致）。"
            "每个元素字段："
            "'laugh_level': 0=不加笑声（默认首选）, 1=轻微笑声, 2=大量笑声（仅在强笑点时使用）；"
            "'speed_level': 1=极慢,2=较慢,3=中,4=较快,5=极快；"
            "'pause_level': 1=连续,2=略停顿,3=正常停顿,4=较多停顿,5=大量停顿；"
            "'end_pause_sec': 段尾停顿秒数，范围0.5-2.0；若检测为笑点，才建议>=1.5，否则尽量 <1.2。"
            "返回格式示例: [{\"laugh_level\":0,\"speed_level\":4,\"pause_level\":3,\"end_pause_sec\":0.9}, ...]"
            "必须输出合法 JSON，仅输出数组本身，禁止额外说明。"
        )

    @staticmethod
    def _default_scores() -> Dict[str, Any]:
        return {
            "laugh_level": DEFAULT_LAUGH,
            "speed_level": DEFAULT_SPEED,
            "pause_level": DEFAULT_PAUSE,
            "end_pause_sec": DEFAULT_END_PAUSE,
        }

    @staticmethod
    def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
        def clamp(val, lo, hi, default):
            try:
                v = float(val)
            except Exception:
                return default
            return max(lo, min(hi, v))

        laugh = int(clamp(item.get("laugh_level", DEFAULT_LAUGH), 0, 2, DEFAULT_LAUGH))
        speed = int(clamp(item.get("speed_level", DEFAULT_SPEED), 1, 5, DEFAULT_SPEED))
        pause = int(clamp(item.get("pause_level", DEFAULT_PAUSE), 1, 5, DEFAULT_PAUSE))
        end_pause = clamp(item.get("end_pause_sec", DEFAULT_END_PAUSE), 0.5, 2.0, DEFAULT_END_PAUSE)
        return {
            "laugh_level": laugh,
            "speed_level": speed,
            "pause_level": pause,
            "end_pause_sec": end_pause,
        }
