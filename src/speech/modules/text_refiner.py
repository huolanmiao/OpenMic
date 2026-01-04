import os
import re
from typing import List, Optional
from openai import OpenAI

# Mapping of common stage cues to ChatTTS tokens
CUE_TO_TOKEN = {
    "笑": "[laugh]",
    "笑声": "[laugh]",
    "停顿": "[uv_break]",
    "短停顿": "[uv_break]",
    "长停顿": "[lbreak]",
    "长时间停顿": "[lbreak]",
}


class TextRefiner:
    """
    Text refinement helper. Prefers LLM rewriting; falls back to a rule-based cleaner.
    """

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

    def refine(self, raw_text: str, use_llm: bool = True) -> List[str]:
        lines: List[str]
        if use_llm and self.client:
            try:
                lines = self._refine_with_llm(raw_text)
            except Exception as exc:  # pragma: no cover - best effort fallback
                print(f"TextRefiner: LLM rewrite failed, falling back. Reason: {exc}")
                lines = self._fallback_clean(raw_text)
        else:
            lines = self._fallback_clean(raw_text)

        # Post-process to ensure control tokens are bracketed (avoid literal reading like "uv_break")
        normalized: List[str] = []
        for ln in lines:
            if not ln:
                continue
            ln = self._normalize_punct(ln)
            ln = self._ensure_bracketed_tokens(ln)
            normalized.append(ln)
        return normalized

    def _refine_with_llm(self, raw_text: str) -> List[str]:
        prompt = (
            "你是一名脱口秀语音导演，帮忙把稿子改写为 ChatTTS 可读文本。"
            "要求："
            "1) 去掉与发音无关的符号/标注；"
            "2) 标点符号只保留 , . ? ! ， 。 （感叹号和问号是英文版的）， 并保持句读自然；"
            "3) 将表演标注中需要停顿或者转为指令，你只能使用以下三种指令：[laugh] 笑声，[uv_break] 短停顿，[lbreak] 长停顿；"
            "4) 读法标记：中英混排时，注意将容易读混的词语，比如2025转换成中文，如二零二五；此外，由于[laugh]是标记，为了避免混淆原文的“laugh”，请将其替换为“Laugh”；"
            "5) 用换行符号分段：每段尽量不超过5句，并且爆出笑点后需要分段；"
            "6) 输出只包含改写后的文本，不要解释。"
            "示例："
            """原文：大家好！~~欢迎来到我的脱口秀节目。（笑）今天我们来聊聊**编程**。（走下台）编程真有趣，对吧？
            改写后：大家好! 欢迎来到我的脱口秀节目。[laugh]\n今天我们来聊聊[uv_break]编程。[lbreak]\n编程真有趣，对吧？"""
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": raw_text},
            ],
            stream=False,
        )
        content = response.choices[0].message.content
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        return lines

    def _fallback_clean(self, raw_text: str) -> List[str]:
        # Remove Markdown bold/italic markers
        text = raw_text.replace("**", "").replace("*", "")
        # Replace stage cues in parentheses or brackets
        def replace_cues(match: re.Match[str]) -> str:
            inner = match.group(1)
            for cue, token in CUE_TO_TOKEN.items():
                if cue in inner:
                    return token
            return ""

        text = re.sub(r"[\(（]([^\)）]{0,30})[\)）]", replace_cues, text)
        # Normalize whitespace and split
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        cleaned: List[str] = []
        for ln in lines:
            # Collapse multiple spaces
            ln = re.sub(r"\s+", " ", ln)
            # Remove stray brackets that can break ChatTTS
            ln = ln.replace("[", " ").replace("]", " ")
            ln = ln.strip()
            if not ln:
                continue
            cleaned.append(ln)
        return cleaned

    @staticmethod
    def _normalize_punct(text: str) -> str:
        # Convert full-width Chinese ! ? to ASCII to avoid ChatTTS complaints
        return text.replace("！", "!").replace("？", "?")

    @staticmethod
    def _ensure_bracketed_tokens(text: str) -> str:
        # If tokens appear without brackets, wrap them; if already bracketed, keep as-is.
        def repl(match: re.Match[str]) -> str:
            token = match.group(1)
            return f"[{token}]"

        # Collapse repeated brackets like [[[uv_break]]] -> [uv_break]
        text = re.sub(r"\[+\s*(uv_break|lbreak|laugh)\s*\]+", repl, text)
        # Wrap bare tokens
        text = re.sub(r"\b(uv_break|lbreak|laugh)\b", repl, text)
        return text
