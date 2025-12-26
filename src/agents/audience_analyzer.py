"""
AudienceAnalyzer (受众分析师) 智能体
进行受众适配分析，确保内容符合目标受众特点
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseComedyAgent

# AudienceAnalyzer 系统提示词
AUDIENCE_ANALYZER_SYSTEM_MESSAGE = """你是OpenMic系统的【受众分析师（AudienceAnalyzer）】，专注于分析目标受众并优化内容适配度。

## ⚠️ 重要：职责边界
你只负责【受众分析】，绝对不要：
- 不要创作脱口秀段子内容（这是JokeWriter的职责）
- 不要制定创作策略（这是ComedyDirector的职责）
- 不要添加表演标记（这是PerformanceCoach的职责）
- 不要评估质量打分（这是QualityController的职责）

## 核心职责
1. **受众画像**：分析目标受众的特征、偏好和文化背景
2. **内容适配**：评估内容是否符合目标受众的理解能力和兴趣点
3. **文化敏感性**：识别可能引起不适的内容，提出修改建议
4. **共鸣优化**：建议如何增强内容与受众的共鸣

## 受众类型分析
### 年轻人（18-30岁）
- 熟悉网络文化和流行梗
- 偏好快节奏、犀利的幽默
- 对校园、职场、恋爱话题有共鸣
- 可接受自嘲和吐槽风格

### 中年人（30-50岁）
- 重视生活智慧和人生感悟
- 偏好观察类、温情类幽默
- 对家庭、工作、社会话题有共鸣
- 注重内容的品味和深度

### 大学生群体
- 对学业压力、校园生活高度共鸣
- 熟悉二次元、游戏等亚文化
- 接受度高，容易被创意内容吸引
- 对社会热点有敏锐的关注

### 职场人群
- 对工作压力、办公室政治有共鸣
- 偏好含蓄、机智的幽默
- 重视专业性和洞察力
- 喜欢能带来启发的内容

## 分析维度
1. **文化适配度**：内容是否符合受众的文化背景和认知
2. **语言适配度**：用语是否符合受众的表达习惯
3. **话题相关度**：话题是否与受众生活经历相关
4. **幽默接受度**：幽默类型是否符合受众偏好
5. **敏感度检查**：是否存在可能冒犯受众的内容

## 输出格式
【受众分析报告】

目标受众：{受众描述}

**适配评分**（1-10分）
- 文化适配度：X分
- 语言适配度：X分
- 话题相关度：X分
- 幽默接受度：X分

**优势分析**
1. {内容优势1}
2. {内容优势2}

**改进建议**
1. {具体建议1}
2. {具体建议2}

**敏感内容提醒**
- {需要注意的敏感点，如有}

请基于专业的受众分析，为创作团队提供有价值的适配建议！
"""


class AudienceAnalyzerAgent(BaseComedyAgent):
    """
    受众分析师智能体
    
    核心职责：
    - 目标受众分析
    - 内容适配度评估
    - 文化敏感性检查
    - 共鸣优化建议
    """
    
    def __init__(
        self,
        llm_config: Dict[str, Any],
        name: str = "AudienceAnalyzer",
        **kwargs
    ):
        """
        初始化受众分析师智能体
        
        Args:
            llm_config: LLM配置
            name: 智能体名称
        """
        description = (
            "受众分析师，负责分析目标受众特征，评估内容适配度，提供优化建议。"
            "当需要考虑受众反应、评估内容是否合适、或需要文化敏感性检查时，应该让AudienceAnalyzer发言。"
        )
        
        super().__init__(
            name=name,
            system_message=AUDIENCE_ANALYZER_SYSTEM_MESSAGE,
            llm_config=llm_config,
            description=description,
            **kwargs
        )
    
    def get_audience_profile(self, audience_type: str) -> Dict[str, Any]:
        """
        获取受众画像
        
        Args:
            audience_type: 受众类型
            
        Returns:
            受众画像字典
        """
        profiles = {
            "年轻人": {
                "age_range": "18-30",
                "characteristics": ["熟悉网络文化", "接受新事物", "追求个性"],
                "preferred_topics": ["校园", "职场", "恋爱", "网络热点"],
                "humor_style": ["犀利", "自嘲", "网络梗"],
                "taboos": ["过于老套的笑话", "说教内容"]
            },
            "中年人": {
                "age_range": "30-50",
                "characteristics": ["注重品味", "重视深度", "生活阅历丰富"],
                "preferred_topics": ["家庭", "工作", "人生感悟"],
                "humor_style": ["观察", "温情", "智慧"],
                "taboos": ["过于低俗", "网络黑话"]
            },
            "大学生": {
                "age_range": "18-25",
                "characteristics": ["学业压力", "社交活跃", "亚文化爱好"],
                "preferred_topics": ["考试", "室友", "食堂", "恋爱"],
                "humor_style": ["自嘲", "吐槽", "二次元梗"],
                "taboos": ["脱离校园生活"]
            },
            "职场人群": {
                "age_range": "25-45",
                "characteristics": ["工作压力", "追求效率", "重视价值"],
                "preferred_topics": ["工作", "领导", "加班", "生活平衡"],
                "humor_style": ["机智", "讽刺", "自嘲"],
                "taboos": ["过于轻浮", "不尊重专业"]
            }
        }
        
        profile = profiles.get(audience_type, profiles["年轻人"])
        self.log_action("获取受众画像", {"audience_type": audience_type})
        return profile
