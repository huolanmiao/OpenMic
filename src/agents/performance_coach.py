"""
PerformanceCoach (表演教练) 智能体
设计语音表达策略和表演标记，为语音合成提供指导
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseComedyAgent

# PerformanceCoach 系统提示词
PERFORMANCE_COACH_SYSTEM_MESSAGE = """你是OpenMic系统的【表演教练（PerformanceCoach）】，专注于设计语音表达策略和表演标记。

## ⚠️ 最重要的规则：你必须添加表演标记！
当轮到你发言时，你必须立即为脱口秀脚本添加表演标记！不要：
- 不要说"请等待其他智能体"
- 不要说"这不是我的职责"
- 不要推诿给其他智能体
- 不要只输出模板或说明

你的职责就是【添加表演标记】，收到脚本后直接开始标注！

## ⚠️ 职责边界（你不做的事）
- 不要创作脱口秀段子内容（这是JokeWriter的职责）
- 不要制定创作策略（这是ComedyDirector的职责）
- 不要分析受众（这是AudienceAnalyzer的职责）
- 不要评估质量打分（这是QualityController的职责）

## 核心职责
1. **语速控制**：设计不同段落的语速策略（正常/加快/放慢）
2. **停顿设计**：在关键位置标记停顿（包袱前停顿、笑点后停顿）
3. **重音标记**：标记需要强调的关键词和短语
4. **情感标注**：标注不同段落的情感基调
5. **语气词插入**：设计自然的语气词位置

## 你的输出格式
当你被要求添加表演标记时，直接输出带标记的脚本。例如：

【表演指导方案】

（*表演者状态：放松，面带微笑*）

朋友们，（*停顿*）又到了每年最刺激的环节——（*重音*）**Final季**！

（*语速放慢*）你们有没有发现...（*停顿，制造悬念*）

...

## 表演标记格式（使用括号和星号）
- （*停顿*）- 短停顿
- （*长停顿*）- 长停顿，用于笑点后
- （*重音*）- 强调下一个词
- （*语速加快*）- 加快语速
- （*语速放慢*）- 放慢语速
- （*自嘲语气*）- 情感标注
- （*模仿XX*）- 模仿某人
- **加粗文字** - 需要重读的关键词

记住：你是表演教练，你的工作就是添加表演标记！收到脚本后立即开始标注！"""


class PerformanceCoachAgent(BaseComedyAgent):
    """
    表演教练智能体
    
    核心职责：
    - 语速控制策略
    - 停顿设计
    - 重音标记
    - 情感标注
    - 语气词插入
    """
    
    def __init__(
        self,
        llm_config: Dict[str, Any],
        name: str = "PerformanceCoach",
        **kwargs
    ):
        """
        初始化表演教练智能体
        
        Args:
            llm_config: LLM配置
            name: 智能体名称
        """
        description = (
            "表演教练，负责设计语音表达策略，添加表演标记（停顿、重音、情感、语气词）。"
            "当内容创作完成后需要添加表演指导，或需要优化表演效果时，应该让PerformanceCoach发言。"
        )
        
        super().__init__(
            name=name,
            system_message=PERFORMANCE_COACH_SYSTEM_MESSAGE,
            llm_config=llm_config,
            description=description,
            **kwargs
        )
    
    def get_timing_params(self) -> Dict[str, float]:
        """
        获取时间控制参数
        
        Returns:
            时间参数字典（单位：秒）
        """
        return {
            "pause_short": 0.3,
            "pause_medium": 0.8,
            "pause_long": 2.0,
            "pause_beat": 0.5,
        }
    
    def get_emotion_list(self) -> List[str]:
        """
        获取支持的情感类型列表
        
        Returns:
            情感类型列表
        """
        return [
            "neutral",      # 平静
            "excited",      # 兴奋
            "sarcastic",    # 讽刺
            "self-deprecating",  # 自嘲
            "surprised",    # 惊讶
            "frustrated",   # 沮丧
            "happy",        # 开心
            "confused",     # 困惑
        ]
    
    def get_filler_words(self) -> List[str]:
        """
        获取支持的语气词列表
        
        Returns:
            语气词列表
        """
        return [
            "呃",
            "那个",
            "就是",
            "然后",
            "所以说",
            "你知道吧",
            "我跟你说",
            "真的是",
        ]
    
    def parse_performance_markers(self, marked_content: str) -> Dict[str, Any]:
        """
        解析带有表演标记的内容
        
        Args:
            marked_content: 带标记的文本内容
            
        Returns:
            解析后的结构化数据
        """
        import re
        
        result = {
            "pauses": [],
            "emotions": [],
            "emphases": [],
            "fillers": [],
            "speeds": []
        }
        
        # 解析停顿标记
        pause_pattern = r'<pause:(\w+)/>'
        for match in re.finditer(pause_pattern, marked_content):
            result["pauses"].append({
                "type": match.group(1),
                "position": match.start()
            })
        
        # 解析情感标记
        emotion_pattern = r'<emotion:(\w+)>(.*?)</emotion>'
        for match in re.finditer(emotion_pattern, marked_content, re.DOTALL):
            result["emotions"].append({
                "emotion": match.group(1),
                "content": match.group(2),
                "position": match.start()
            })
        
        # 解析重音标记
        emphasis_pattern = r'<emphasis>(.*?)</emphasis>'
        for match in re.finditer(emphasis_pattern, marked_content):
            result["emphases"].append({
                "content": match.group(1),
                "position": match.start()
            })
        
        # 解析语气词
        filler_pattern = r'<filler:([^/]+)/>'
        for match in re.finditer(filler_pattern, marked_content):
            result["fillers"].append({
                "word": match.group(1),
                "position": match.start()
            })
        
        self.log_action("解析表演标记", {
            "pause_count": len(result["pauses"]),
            "emotion_count": len(result["emotions"]),
            "emphasis_count": len(result["emphases"]),
            "filler_count": len(result["fillers"])
        })
        
        return result
