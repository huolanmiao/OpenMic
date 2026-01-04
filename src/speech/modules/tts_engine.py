import ChatTTS
import numpy as np
from typing import List, Optional, Dict, Any


class TTSEngine:
    """Wrapper around ChatTTS inference with safe defaults."""

    def __init__(
        self,
        chat: ChatTTS.Chat,
        spk_emb,
        speed_prompt: str = "[speed_4]",
        oral_prompt: str = "[oral_2][laugh_1][break_4]",
        max_new_token: int = 4096,
    ) -> None:
        self.chat = chat
        self.spk_emb = spk_emb
        self.speed_prompt = speed_prompt
        self.oral_prompt = oral_prompt
        self.max_new_token = max_new_token

    def synthesize(
        self,
        text_list: List[str],
        temperature: float = 0.3,
        top_k: int = 20,
        top_p: float = 0.7,
        return_segments: bool = False,
        controls: Optional[List[Dict[str, Any]]] = None,
    ):
        valid_pairs = [
            (idx, t.strip())
            for idx, t in enumerate(text_list)
            if t and t.strip()
        ]
        if not valid_pairs:
            print("TTSEngine: No valid text to synthesize.")
            return [] if return_segments else np.zeros(0)

        def map_speed(level: int) -> str:
            # Map 1-5 -> speed_2..speed_5 (clamp)
            lv = max(1, min(5, level))
            if lv <= 2:
                return "[speed_2]"
            if lv == 3:
                return "[speed_3]"
            if lv == 4:
                return "[speed_4]"
            return "[speed_5]"

        def map_laugh(level: int) -> str:
            lv = max(0, min(2, level))
            return f"[laugh_{lv}]"

        def map_pause(level: int) -> str:
            lv = max(0, min(5, level))
            return f"[break_{lv}]"

        segments = []
        concat_audio = []

        for idx, seg_text in valid_pairs:
            ctrl = controls[idx] if controls and idx < len(controls) else {}
            speed_prompt = map_speed(int(ctrl.get("speed_level", 4)))
            laugh_prompt = map_laugh(int(ctrl.get("laugh_level", 0)))
            pause_prompt = map_pause(int(ctrl.get("pause_level", 3)))

            params_infer_code = ChatTTS.Chat.InferCodeParams(
                prompt=speed_prompt,
                top_K=top_k,
                top_P=top_p,
                temperature=temperature,
                spk_emb=self.spk_emb,
                max_new_token=self.max_new_token,
            )
            params_refine_text = ChatTTS.Chat.RefineTextParams(
                prompt=f"[oral_2]{laugh_prompt}{pause_prompt}",
                max_new_token=self.max_new_token // 2,
            )

            seg_wavs = self.chat.infer(
                [seg_text],
                params_refine_text=params_refine_text,
                params_infer_code=params_infer_code,
            )
            if seg_wavs and len(seg_wavs) > 0:
                segments.append(seg_wavs[0])
                concat_audio.append(seg_wavs[0])

        if return_segments:
            return segments
        if not concat_audio:
            return np.zeros(0)
        return np.concatenate(concat_audio)
