"""
ComedyGroupChat - 脱口秀创作团队GroupChat实现
实现5个智能体的协作对话流程
适配 AutoGen 0.10+ 新版本 API
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio

# AutoGen 0.10+ 导入
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily

from ..agents import (
    ComedyDirectorAgent,
    JokeWriterAgent,
    AudienceAnalyzerAgent,
    PerformanceCoachAgent,
    QualityControllerAgent
)

logger = logging.getLogger(__name__)


def create_model_client(llm_config: Dict[str, Any]) -> OpenAIChatCompletionClient:
    """创建模型客户端"""
    config_list = llm_config.get("config_list", [{}])
    config = config_list[0] if config_list else {}
    
    model_name = config.get("model", "deepseek-chat")
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://api.deepseek.com/v1")
    
    # 为非OpenAI模型提供model_info
    model_info = {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    }
    
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        model_info=model_info,
    )


class ComedyGroupChat:
    """
    脱口秀创作团队GroupChat
    
    协调5个核心智能体进行脱口秀内容创作：
    1. ComedyDirector - 喜剧导演，整体策略制定
    2. JokeWriter - 段子写手，内容创作
    3. AudienceAnalyzer - 受众分析师，受众适配
    4. PerformanceCoach - 表演教练，表演标记
    5. QualityController - 质量控制官，质量把关
    
    工作流程：策略制定 → 受众分析 → 内容创作 → 表演指导 → 质量控制 → (循环优化)
    """
    
    def __init__(
        self,
        llm_config: Dict[str, Any],
        max_round: int = 25,
        agent_model_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        初始化脱口秀创作团队
        
        Args:
            llm_config: 默认LLM配置（用于所有智能体）
            max_round: 最大对话轮数（默认25轮以确保流程完整）
            agent_model_configs: 可选的各智能体独立模型配置
                例如: {
                    'ComedyDirector': {'model': 'gpt-4', 'api_key': '...'},
                    'JokeWriter': {'model': 'deepseek-chat', 'api_key': '...'}
                }
        """
        self.llm_config = llm_config
        self.max_round = max_round
        self.agent_model_configs = agent_model_configs or {}
        self.messages: List[Dict[str, Any]] = []
        
        # 创建默认模型客户端（用于selector和没有独立配置的智能体）
        self.model_client = create_model_client(llm_config)
        
        # 初始化智能体（支持独立模型配置）
        self._init_agents()
        
        # 创建团队
        self._init_team()
        
        logger.info("ComedyGroupChat初始化完成")
    
    def _init_agents(self):
        """初始化所有智能体，支持为每个智能体配置独立的模型"""
        
        # 辅助函数：获取智能体的模型配置
        def get_agent_config(agent_name: str) -> Dict[str, Any]:
            if agent_name in self.agent_model_configs:
                # 使用独立配置
                return self.agent_model_configs[agent_name]
            return self.llm_config
        
        # 喜剧导演 - 可使用独立模型
        self.comedy_director = ComedyDirectorAgent(
            llm_config=get_agent_config('ComedyDirector')
        )
        
        # 段子写手 - 可使用独立模型（创作核心，可配置更强的模型）
        self.joke_writer = JokeWriterAgent(
            llm_config=get_agent_config('JokeWriter')
        )
        
        # 受众分析师 - 可使用独立模型
        self.audience_analyzer = AudienceAnalyzerAgent(
            llm_config=get_agent_config('AudienceAnalyzer')
        )
        
        # 表演教练 - 可使用独立模型
        self.performance_coach = PerformanceCoachAgent(
            llm_config=get_agent_config('PerformanceCoach')
        )
        
        # 质量控制官 - 可使用独立模型
        self.quality_controller = QualityControllerAgent(
            llm_config=get_agent_config('QualityController')
        )
        
        # 智能体列表（获取底层agent）
        self.agents = [
            self.comedy_director.agent,
            self.audience_analyzer.agent,
            self.joke_writer.agent,
            self.performance_coach.agent,
            self.quality_controller.agent,
        ]
        
        logger.info(f"已初始化 {len(self.agents)} 个智能体")
    
    def _create_workflow_selector(self):
        """
        创建工作流选择函数 - 支持多轮循环优化
        
        完整工作流：
        ComedyDirector → AudienceAnalyzer → JokeWriter → PerformanceCoach → QualityController
        
        多轮循环机制：
        - 如果QualityController说"不通过"，返回JokeWriter修改
        - JokeWriter修改后，再次经过PerformanceCoach和QualityController
        - 最多允许3次修改循环，超过后强制通过
        """
        # 定义工作流顺序
        workflow_order = [
            "ComedyDirector",
            "AudienceAnalyzer", 
            "JokeWriter",
            "PerformanceCoach",
            "QualityController"
        ]
        
        # 修改循环的工作流（跳过策略制定和受众分析，直接进入创作优化循环）
        revision_workflow = [
            "JokeWriter",
            "PerformanceCoach", 
            "QualityController"
        ]
        
        # 最大修改循环次数
        max_revision_cycles = 3
        
        def workflow_selector(messages) -> str | None:
            """
            根据消息历史选择下一个发言的智能体，支持多轮循环优化
            
            Args:
                messages: 消息历史序列
                
            Returns:
                下一个智能体的名称，或None表示结束
            """
            # 如果没有消息，从ComedyDirector开始
            if not messages:
                return "ComedyDirector"
            
            # 统计各智能体发言次数（用于判断是否在修改循环中）
            agent_counts = {}
            for msg in messages:
                if hasattr(msg, 'source') and msg.source not in ["user", None]:
                    agent_name = msg.source
                    agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
            
            # 计算QualityController已经评估了多少次（用于限制循环次数）
            qc_count = agent_counts.get("QualityController", 0)
            
            # 获取最后一条非user消息的发送者和内容
            last_agent = None
            last_content = ""
            for msg in reversed(messages):
                if hasattr(msg, 'source') and msg.source not in ["user", None]:
                    last_agent = msg.source
                    last_content = getattr(msg, 'content', '') if hasattr(msg, 'content') else ''
                    break
            
            # 如果没有找到智能体消息，从ComedyDirector开始
            if last_agent is None:
                return "ComedyDirector"
            
            # 检查是否正在进行修改循环（JokeWriter发言超过1次说明在修改）
            in_revision_cycle = agent_counts.get("JokeWriter", 0) > 1
            
            # 处理QualityController的评估结果
            if last_agent == "QualityController":
                # 检查是否通过
                has_passed = ("【通过】" in last_content or 
                             ("通过" in last_content and "不通过" not in last_content))
                has_final_script = "【最终脚本】" in last_content or "最终脚本" in last_content
                needs_revision = "不通过" in last_content or "需要修改" in last_content
                
                # 如果通过并输出了最终脚本，流程结束
                if has_passed and has_final_script:
                    logger.info(f"✅ 质量评估通过，流程结束（共{qc_count}轮评估）")
                    return None
                
                # 如果不通过，检查是否超过最大循环次数
                if needs_revision:
                    if qc_count >= max_revision_cycles:
                        logger.warning(f"⚠️ 已达到最大修改次数({max_revision_cycles})，强制进入最终评估")
                        # 可以选择强制通过或再给一次机会
                        return None  # 流程结束，让termination处理
                    else:
                        logger.info(f"🔄 第{qc_count}轮评估不通过，返回JokeWriter进行第{qc_count + 1}轮修改")
                        return "JokeWriter"  # 返回JokeWriter进行修改
                
                # 默认结束
                return None
            
            # 判断当前应该使用哪个工作流
            if in_revision_cycle:
                # 在修改循环中，使用revision_workflow
                if last_agent in revision_workflow:
                    current_index = revision_workflow.index(last_agent)
                    next_index = current_index + 1
                    if next_index < len(revision_workflow):
                        next_agent = revision_workflow[next_index]
                        logger.info(f"🔄 修改循环: {last_agent} → {next_agent}")
                        return next_agent
                    return None
            else:
                # 首轮工作流
                if last_agent in workflow_order:
                    current_index = workflow_order.index(last_agent)
                    next_index = current_index + 1
                    if next_index < len(workflow_order):
                        return workflow_order[next_index]
                    return None
            
            # 如果是未知智能体，默认从ComedyDirector开始
            return "ComedyDirector"
        
        return workflow_selector
    
    def _init_team(self):
        """初始化团队"""
        
        # 定义终止条件 - 使用特殊标记作为终止关键词
        termination = MaxMessageTermination(max_messages=self.max_round) | TextMentionTermination("OPENMIC_DONE")
        
        # 创建工作流选择函数（强制按顺序选择智能体）
        workflow_selector = self._create_workflow_selector()
        
        # 创建选择器提示词 - 作为备用（当selector_func返回None时使用）
        selector_prompt = """你是脱口秀创作团队的工作流调度器。

如果QualityController已经输出了【最终脚本】或说【通过】，请输出任意智能体名称让流程自然结束。

智能体列表：ComedyDirector, AudienceAnalyzer, JokeWriter, PerformanceCoach, QualityController

直接输出智能体名称即可。"""

        # 创建SelectorGroupChat团队 - 使用selector_func强制按顺序选择
        self.team = SelectorGroupChat(
            participants=self.agents,
            model_client=self.model_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            selector_func=workflow_selector,  # 使用自定义选择函数
            allow_repeated_speaker=False,  # 不允许连续重复发言
        )
        
        logger.info("团队初始化完成")
    
    def create_initial_prompt(
        self,
        topic: str,
        style: str = "观察类",
        duration_minutes: int = 3,
        target_audience: str = "年轻人"
    ) -> str:
        """创建初始提示词"""
        prompt = f"""请为以下脱口秀主题创作一段专业的表演内容：

【创作需求】
- 主题：{topic}
- 表演风格：{style}
- 目标时长：{duration_minutes}分钟
- 目标受众：{target_audience}

【工作流程】
1. ComedyDirector 首先制定创作策略和方向
2. AudienceAnalyzer 分析目标受众特点和偏好
3. JokeWriter 根据策略创作脱口秀内容（使用Setup-Punchline结构）
4. PerformanceCoach 添加表演标记（停顿、重音、情感、语气词）
5. QualityController 进行质量评估并决定是否通过
6. 如需修改，返回步骤3进行优化
7. 质量通过后，由QualityController输出【最终脚本】标记的完整内容

请开始创作，ComedyDirector先发言制定策略。"""
        return prompt
    
    async def run_async(
        self,
        topic: str,
        style: str = "观察类",
        duration_minutes: int = 3,
        target_audience: str = "年轻人"
    ) -> Dict[str, Any]:
        """
        异步运行创作流程
        """
        initial_prompt = self.create_initial_prompt(
            topic=topic,
            style=style,
            duration_minutes=duration_minutes,
            target_audience=target_audience
        )
        
        logger.info(f"开始创作流程 - 主题: {topic}, 风格: {style}")
        print(f"\n{'='*60}")
        print("🎭 开始多智能体协作创作...")
        print(f"{'='*60}\n")
        
        # 收集消息
        self.messages = []
        
        # 添加初始任务消息
        self.messages.append({
            "name": "user",
            "content": initial_prompt
        })
        
        try:
            # 使用 run 方法运行团队对话（不是 run_stream）
            result = await self.team.run(task=initial_prompt)
            
            # 处理结果
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if hasattr(msg, 'source') and hasattr(msg, 'content'):
                        msg_source = str(msg.source)
                        msg_content = str(msg.content) if msg.content else ""
                        
                        if msg_content:
                            self.messages.append({
                                "name": msg_source,
                                "content": msg_content
                            })
                            # 打印消息
                            print(f"\n{'='*60}")
                            print(f"🎤 [{msg_source}]:")
                            print(f"{'='*60}")
                            print(msg_content[:2000] + "..." if len(msg_content) > 2000 else msg_content)
            else:
                # 如果结果格式不同，尝试其他方式
                logger.warning(f"结果类型: {type(result)}, 内容: {result}")
                print(f"结果: {result}")
                        
        except Exception as e:
            logger.error(f"对话过程出错: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n⚠️ 对话过程出错: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ 创作完成! 共 {len(self.messages)} 轮对话")
        print(f"{'='*60}\n")
        
        # 提取结果
        result = self._extract_result()
        
        logger.info("创作流程完成")
        return result
    
    def run(
        self,
        topic: str,
        style: str = "观察类",
        duration_minutes: int = 3,
        target_audience: str = "年轻人"
    ) -> Dict[str, Any]:
        """
        同步运行创作流程
        """
        return asyncio.run(self.run_async(
            topic=topic,
            style=style,
            duration_minutes=duration_minutes,
            target_audience=target_audience
        ))
    
    def _extract_result(self) -> Dict[str, Any]:
        """从对话历史中提取创作结果"""
        result = {
            "messages": self.messages,
            "script": None,
            "performance_markers": None,
            "quality_report": None,
            "strategy": None,
            "audience_analysis": None,
            "total_rounds": len(self.messages)
        }
        
        # 遍历消息提取各类内容
        for msg in reversed(self.messages):
            content = str(msg.get("content", ""))
            name = msg.get("name", "")
            
            if not content:
                continue
            
            # 提取最终脚本
            if "【最终输出】" in content or "【最终脚本】" in content:
                result["script"] = content
            
            # 提取表演标记
            if "PerformanceCoach" in name and "表演" in content:
                result["performance_markers"] = content
            
            # 提取质量报告
            if "QualityController" in name and "评估" in content:
                result["quality_report"] = content
            
            # 提取策略
            if "ComedyDirector" in name and "策略" in content:
                result["strategy"] = content
            
            # 提取受众分析
            if "AudienceAnalyzer" in name and "受众" in content:
                result["audience_analysis"] = content
        
        return result
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """获取完整对话历史"""
        return self.messages
    
    def reset(self):
        """重置状态，准备新的创作"""
        self.messages.clear()
        logger.info("GroupChat已重置")


def create_comedy_team(llm_config: Dict[str, Any], **kwargs) -> ComedyGroupChat:
    """
    创建脱口秀创作团队的便捷函数
    """
    return ComedyGroupChat(llm_config=llm_config, **kwargs)
