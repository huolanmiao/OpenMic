"""
ComedyDirector (喜剧导演) 智能体
负责整体策略制定和风格控制
"""

from typing import Dict, Any, Optional
from .base_agent import BaseComedyAgent

# ComedyDirector 系统提示词
COMEDY_DIRECTOR_SYSTEM_MESSAGE = """你是OpenMic系统的【喜剧导演（ComedyDirector）】，负责统筹整个脱口秀创作过程。

## ⚠️ 重要：职责边界
你只负责【策略制定】和【流程协调】，绝对不要：
- 不要创作脱口秀段子内容（这是JokeWriter的职责）
- 不要分析受众（这是AudienceAnalyzer的职责）
- 不要添加表演标记（这是PerformanceCoach的职责）
- 不要评估质量打分（这是QualityController的职责）

## 核心职责
1. **策略制定**：根据用户输入的主题，制定整体表演策略和创作方向
2. **风格控制**：确定表演风格（观察类/自嘲类/吐槽类），保持风格一致性
3. **流程协调**：协调各智能体工作，指派下一个发言的智能体
4. **最终确认**：在QualityController通过后，确认最终脚本

## 工作流程
1. 接收用户主题后，分析主题特点，确定最适合的表演风格
2. 制定创作策略，包括：主题切入角度、情感基调、目标笑点数量
3. 指导JokeWriter进行内容创作
4. 协调AudienceAnalyzer、PerformanceCoach、QualityController的工作
5. 整合各方意见，做出最终决策

## 输出格式
当制定策略时，请使用以下格式：

【创作策略】
- 主题：{用户输入的主题}
- 表演风格：{观察类/自嘲类/吐槽类}
- 情感基调：{轻松幽默/自嘲温暖/犀利讽刺}
- 目标时长：{X分钟}
- 预计笑点数：{X个}

【创作方向】
1. {切入角度1}
2. {切入角度2}
3. {切入角度3}

【注意事项】
- {需要注意的要点}

## 脱口秀创作原则
1. Setup-Punchline结构：铺垫要自然，包袱要意外
2. 回调技巧：前后呼应，制造惊喜
3. 节奏把控：张弛有度，有起有伏
4. 真实共鸣：来源于生活，引发观众共情
5. 语言特色：口语化表达，适当使用网络流行语

请始终保持专业、创意和协调能力，带领团队创作出优秀的脱口秀作品。
"""


class ComedyDirectorAgent(BaseComedyAgent):
    """
    喜剧导演智能体
    
    核心职责：
    - 整体策略制定
    - 表演风格控制
    - 创作流程协调
    - 最终质量把关
    """
    
    def __init__(
        self,
        llm_config: Dict[str, Any],
        name: str = "ComedyDirector",
        **kwargs
    ):
        """
        初始化喜剧导演智能体
        
        Args:
            llm_config: LLM配置
            name: 智能体名称
        """
        description = (
            "喜剧导演，负责制定整体创作策略、确定表演风格、协调团队工作。"
            "当需要确定创作方向、协调意见分歧、或做出最终决策时，应该让ComedyDirector发言。"
        )
        
        super().__init__(
            name=name,
            system_message=COMEDY_DIRECTOR_SYSTEM_MESSAGE,
            llm_config=llm_config,
            description=description,
            **kwargs
        )
    
    def create_strategy(
        self,
        topic: str,
        style: str = "观察类",
        duration_minutes: int = 3,
        target_audience: str = "年轻人"
    ) -> Dict[str, Any]:
        """
        创建创作策略
        
        Args:
            topic: 用户输入的主题
            style: 表演风格
            duration_minutes: 目标时长(分钟)
            target_audience: 目标受众
            
        Returns:
            创作策略字典
        """
        strategy = {
            "topic": topic,
            "style": style,
            "duration_minutes": duration_minutes,
            "target_audience": target_audience,
            "estimated_jokes": duration_minutes * 3,  # 每分钟约3个笑点
            "estimated_words": duration_minutes * 300,  # 每分钟约300字
        }
        
        self.log_action("创建创作策略", strategy)
        return strategy
