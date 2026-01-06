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
        model: Optional[str] = None,
    ) -> None:
        # Load from centralized config if not provided
        try:
            from src.config.settings import config_manager
            llm_config = config_manager.llm_config
            default_api_key = llm_config.api_key
            default_base_url = llm_config.base_url
            default_model = llm_config.model
        except ImportError:
            # Fallback for standalone usage
            default_api_key = os.getenv("DEEPSEEK_API_KEY")
            default_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            default_model = "deepseek-chat"

        self.api_key = api_key or default_api_key
        self.base_url = base_url or default_base_url
        self.model = model or default_model
        
        self.client: Optional[OpenAI] = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def refine(self, raw_text: str, use_llm: bool = True) -> List[str]:
        lines: List[str]
        
        if use_llm:
            if not self.client:
                msg = (
                    "⚠ TEXT REFINER WARNING ⚠\n"
                    "LLM refinement enabled but no API Client configured (Check API Key/Base URL).\n"
                    "Falling back to rule-based processing (Performance markers might be missing)."
                )
                try:
                    from rich import print as rprint
                    rprint(f"[bold yellow]{msg}[/bold yellow]")
                except ImportError:
                    print(f"\n{'!'*40}\n{msg}\n{'!'*40}\n")
                
                lines = self._fallback_clean(raw_text)
            else:
                try:
                    lines = self._refine_with_llm_two_step(raw_text)
                except Exception as exc:  # pragma: no cover - best effort fallback
                    msg = (
                        "❌ TEXT REFINER ERROR ❌\n"
                        f"LLM call failed: {exc}\n"
                        "Falling back to rule-based processing."
                    )
                    try:
                        from rich import print as rprint
                        rprint(f"[bold red]{msg}[/bold red]")
                    except ImportError:
                        print(f"\n{'!'*40}\n{msg}\n{'!'*40}\n")

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

    def _refine_with_llm_two_step(self, raw_text: str) -> List[str]:
        """Two-pass LLM pipeline: rewrite first, then add laugh/pause marks."""
        # Pass 1: rewrite & clean
        prompt_rewrite = (
            "你是一名脱口秀稿件改写助手，先完成【内容改写与清洗】。\n"
            "要求：\n"
            "1) 去掉与发音无关的符号/标注（如表情、Markdown、舞台动作）。\n"
            "2) 标点只保留逗号、句号、问号、感叹号（中英文均可），保持语义自然。\n"
            "3) 中英混排时，将容易读混的数字或英文改写为容易朗读的形式，例如 2025 -> 二零二五，Laugh（作为单词）改写为大写 L 开头的单词。\n"
            "4) 按语义分段，每段 4-5 句左右；爆笑点或话题切换后必须分段。\n"
            "5) 输出只包含改写文本，多段用换行分隔，不要任何解释。\n"
            "示例 1：\n"
            "原文：大家好！~~欢迎来到我的脱口秀节目。（笑）今天我们来聊聊**编程**。（走下台）编程真有趣，对吧？\n"
            "改写后：\n"
            "大家好[uv_break]! 欢迎来到我的脱口秀节目。\n今天我们来聊聊编程。编程真有趣，对吧？\n"
            "示例 2：\n"
            "原文：2025 年我想去美国旅行，然后学点 jazz，顺便练练 laugh 的发音。还有，我想在旅途中试试即兴表演。\n"
            "改写后：\n"
            "二零二五年我想去美国旅行，然后学点爵士，顺便练练 Laugh 这个词的发音。[lbreak]还有，在旅途中我还想试试即兴表演。\n"
        )

        resp1 = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_rewrite},
                {"role": "user", "content": raw_text},
            ],
            stream=False,
        )
        text_stage1 = resp1.choices[0].message.content
        stage1_lines = [ln.strip() for ln in text_stage1.split("\n") if ln.strip()]

        # Pass 2: add performance marks (laugh / short pause / long pause)
        prompt_marks = (
            "你现在是一名表演节奏导演，对已改写好的文本增加【笑声/停顿】指令。\n"
            "仅使用三种指令：\n"
            "- [laugh] 笑声\n"
            "- [uv_break] 短停顿\n"
            "- [lbreak] 长停顿\n"
            "规则：\n"
            "1) 爆点/包袱后按语境可加入 [laugh] 或长停顿；\n"
            "2) 情绪转折、提问前可加 [uv_break]；铺垫到 punchline 前可用 [lbreak]；\n"            
            "3) 不要在一句话里反复插太多标记，适度即可；\n"
            "4) 输出仍按行分段，只在需要的位置插入上述指令，不要新增其他标记。\n"
            "示例：\n"
            "输入：今天我们来聊聊编程。编程真有趣，对吧？\n"
            "输出：今天我们来聊聊编程。[uv_break]编程真有趣，对吧？[laugh]\n"
            "输入：二零二五年我想去美国旅行，然后学点爵士。顺便练练 Laugh 这个词的发音。\n"
            "输出：二零二五年我想去美国旅行。[uv_break]然后学点爵士。[uv_break]顺便练练 Laugh 这个词的发音。\n"
        )

        joined = "\n".join(stage1_lines)
        resp2 = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_marks},
                {"role": "user", "content": joined},
            ],
            stream=False,
            temperature=0.2, 
        )
        text_stage2 = resp2.choices[0].message.content
        lines = [ln.strip() for ln in text_stage2.split("\n") if ln.strip()]
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
        # Wrap bare tokens that are NOT already bracketed
        # Use negative lookbehind (?<!\[) and lookahead (?!\])
        text = re.sub(r"(?<!\[)\b(uv_break|lbreak|laugh)\b(?!\])", repl, text)
        return text
