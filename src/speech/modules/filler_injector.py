import asyncio
import os
import random
import re
from typing import Iterable, List, Optional

import jieba
from openai import OpenAI
import os

FILLERS = [
    "呃",
    "那个",
    "就是",
    "你知道吧",
    "嗯",
    "然后",
    "其实",
    "就是说",
]


class FillerInjector:
    """Filler-word inserter with optional LLM post-adjustment."""

    def __init__(
        self,
        probability: float = 0.02,
        word_probability: float = 0.05,
        seed: int = 42,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
    ) -> None:
        self.probability = probability  # after punctuation
        self.word_probability = word_probability  # between words
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

        # Final safety: ensure control tokens are properly bracketed
        sanitized = [self._sanitize_tokens(line) for line in injected if line]
        return sanitized

    def _inject_into_line(self, line: str) -> str:
        # Sentence-level punctuation injection
        parts = re.split(r"([，。,\.?!！？])", line)
        out: List[str] = []
        for part in parts:
            if not part:
                continue
            out.append(part)
            if part in "，。, .?!！？":
                continue
            if self.rng.random() < self.probability:
                filler = self.rng.choice(FILLERS)
                out.append(f"[uv_break]{filler}")

        # Word-level insertion using jieba
        line_after_punc = "".join(out)
        tokens = list(jieba.cut(line_after_punc))
        rebuilt: List[str] = []
        for tok in tokens:
            rebuilt.append(tok)
            if tok in "，。, .?!！？":
                continue
            if self.rng.random() < self.word_probability:
                filler = self.rng.choice(FILLERS)
                rebuilt.append(f"[uv_break]{filler}")
        return "".join(rebuilt)

    async def _adjust_with_llm_async(self, lines: List[str]) -> List[str]:
        joined = "\n".join(lines)
        prompt = (
            "你是口语润色助手。请检查下面文本中的语气词(如嗯、呃、那个、就是、就是说、你知道吧、然后、其实等)是否自然，"
            "如不自然请调整位置或替换为更自然的语气词。保持原有 [uv_break]、[lbreak]、[laugh] 标记，"
            "不要删除或新增其他控制标记。只返回修改后的文本，分行返回，与输入行数一致。"
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
        return [self._sanitize_tokens(ln) for ln in adjusted if ln]

    def _adjust_with_llm_sync(self, lines: List[str]) -> List[str]:
        joined = "\n".join(lines)
        prompt = (
            "你是口语润色助手。请检查下面文本中的语气词(如嗯、呃、那个、就是、就是说、你知道吧、然后、其实等)是否自然，"
            "如不自然请调整位置或替换为更自然的语气词。保持原有 [uv_break]、[lbreak]、[laugh] 标记，"
            "不要删除或新增其他控制标记。只返回修改后的文本，分行返回，与输入行数一致。"
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
        return [self._sanitize_tokens(ln) for ln in adjusted if ln]

    @staticmethod
    def _sanitize_tokens(text: str) -> str:
        # Normalize bracket spacing and ensure tokens are wrapped
        def wrap(match: re.Match[str]) -> str:
            token = match.group(1)
            return f"[{token}]"

        # Normalize punctuation to ASCII to avoid invalid-char warnings
        text = text.replace("！", "!").replace("？", "?")
        # Collapse multiple brackets [[[token]]] -> [token]
        text = re.sub(r"\[+\s*(uv_break|lbreak|laugh)\s*\]+", wrap, text)
        # Fix single brackets with spaces
        text = re.sub(r"\[\s*(uv_break|lbreak|laugh)\s*\]", wrap, text)
        # Wrap bare tokens
        text = re.sub(r"\b(uv_break|lbreak|laugh)\b", wrap, text)
        return text
