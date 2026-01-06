import asyncio
import os
import random
import re
from typing import Iterable, List, Optional

import jieba
from openai import OpenAI

# Expanded filler lists based on common speech patterns
FILLERS = {
    "start": ["呃", "那个", "其实", "就是", "嗯", "哎", "说实话", "怎么说呢"],
    "middle": ["呃", "那个", "就是", "你知道吧", "然后", "就像", "那个什么"],
    "end": ["你知道吧", "就是说", "对吧", "嗯", "是吧", "行吧", "对不对"],
}


class FillerInjector:
    """Filler-word inserter with optional LLM post-adjustment."""

    def __init__(
        self,
        prob_start: float = 0.05,
        prob_middle: float = 0.015,
        prob_end: float = 0.01,
        seed: int = 42,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
    ) -> None:
        self.prob_start = prob_start
        self.prob_middle = prob_middle
        self.prob_end = prob_end
        self.rng = random.Random(seed)
        self.model = model

        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.llm_client: Optional[OpenAI] = OpenAI(api_key=key, base_url=url) if key else None

    def inject(self, lines: Iterable[str], use_llm: bool = True) -> List[str]:
        # Stage 1: heuristic insertion
        injected: List[str] = []
        for line in lines:
            if not line:
                continue
            injected.append(self._inject_into_line(line))

        # Stage 2: LLM adjustment for naturalness
        if use_llm and self.llm_client and injected:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    injected = self._adjust_with_llm_sync(injected)
                else:
                    injected = loop.run_until_complete(self._adjust_with_llm_async(injected))
            except Exception as exc:  # pragma: no cover
                print(f"FillerInjector: LLM adjust failed, using heuristic result. Reason: {exc}")

        # Final safety: remove markers and ensure control tokens are properly bracketed
        sanitized = [self._sanitize_tokens(line) for line in injected if line]
        return sanitized

    def _inject_into_line(self, line: str) -> str:
        # Split by punctuation to handle clauses
        # Keep delimiters to reconstruct the sentence later
        parts = re.split(r"([，。,\.?!！？])", line)
        out_parts: List[str] = []

        # Iterate over text parts. parts[0] is text, parts[1] is punc, parts[2] is text...
        for i in range(0, len(parts), 2):
            text = parts[i]
            punc = parts[i+1] if i+1 < len(parts) else ""

            if not text.strip():
                out_parts.append(text + punc)
                continue

            # 1. Start filler (beginning of clause)
            prefix = ""
            if self.rng.random() < self.prob_start:
                f = self.rng.choice(FILLERS["start"])
                prefix = f"<{f}>"

            # 2. Middle fillers (between words)
            tokens = list(jieba.cut(text))
            middle_text = ""
            for j, tok in enumerate(tokens):
                middle_text += tok
                # Insert filler between tokens (not after the last one)
                if j < len(tokens) - 1:
                    if self.rng.random() < self.prob_middle:
                        f = self.rng.choice(FILLERS["middle"])
                        middle_text += f"<{f}>"
            
            # 3. End filler (end of clause, before punctuation)
            suffix = ""
            if self.rng.random() < self.prob_end:
                f = self.rng.choice(FILLERS["end"])
                suffix = f"<{f}>"
            
            out_parts.append(prefix + middle_text + suffix + punc)

        return "".join(out_parts)

    async def _adjust_with_llm_async(self, lines: List[str]) -> List[str]:
        joined = "\n".join(lines)
        prompt = (
            "你是口语润色助手。请检查下面文本中用<>标记的语气词(如<嗯>、<那个>)在当前语境下是否自然。"
            "如果不自然，请调整位置、替换为更合适的语气词(仍需保留<>)或直接删除。"
            "如果自然，保留原样。你可以适当增删<>标记的语气词以增强口语感，但不要改动非语气词的文本内容。"
            "保持原有 [uv_break]、[lbreak]、[laugh] 等控制标记不变。"
            "只返回修改后的文本，分行返回，与输入行数一致。"
        )

        async def _call():
            resp = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": joined},
                ],
                stream=False,
            )
            content = resp.choices[0].message.content
            return [ln.strip() for ln in content.split("\n") if ln.strip()]

        # Using asyncio.to_thread to avoid blocking if event loop exists
        adjusted = await asyncio.to_thread(_call)
        return adjusted

    def _adjust_with_llm_sync(self, lines: List[str]) -> List[str]:
        joined = "\n".join(lines)
        prompt = (
            "你是口语润色助手。请检查下面文本中用<>标记的语气词(如<嗯>、<那个>)在当前语境下是否自然。"
            "如果不自然，请调整位置、替换为更合适的语气词(仍需保留<>)或直接删除。"
            "如果自然，保留原样。你可以适当增删<>标记的语气词以增强口语感，但不要改动非语气词的文本内容。"
            "保持原有 [uv_break]、[lbreak]、[laugh] 等控制标记不变。"
            "只返回修改后的文本，分行返回，与输入行数一致。"
        )
        resp = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": joined},
            ],
            stream=False,
        )
        content = resp.choices[0].message.content
        adjusted = [ln.strip() for ln in content.split("\n") if ln.strip()]
        return adjusted

    @staticmethod
    def _sanitize_tokens(text: str) -> str:
        # Remove filler markers
        text = text.replace("<", "").replace(">", "")

        # Normalize bracket spacing and ensure tokens are wrapped
        def wrap(match: re.Match[str]) -> str:
            token = match.group(1)
            return f"[{token}]"

        # Normalize punctuation to ASCII to avoid invalid-char warnings
        text = text.replace("！", "!").replace("？", "?").replace("”", "'").replace("“", "'")
        # Collapse multiple brackets [[[token]]] -> [token]
        text = re.sub(r"\[+\s*(uv_break|lbreak|laugh)\s*\]+", wrap, text)
        # Fix single brackets with spaces
        text = re.sub(r"\[\s*(uv_break|lbreak|laugh)\s*\]", wrap, text)
        # Wrap bare tokens
        text = re.sub(r"\b(uv_break|lbreak|laugh)\b", wrap, text)
        return text
