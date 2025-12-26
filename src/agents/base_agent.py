"""
基础智能体类
为所有脱口秀相关智能体提供基础功能
支持 AutoGen 0.10+ 新版本 API
"""

from typing import Dict, Any, Optional, List
import logging

# AutoGen 0.10+ 导入
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily

logger = logging.getLogger(__name__)


def create_model_client(llm_config: Dict[str, Any]) -> OpenAIChatCompletionClient:
    """
    根据配置创建OpenAI兼容的模型客户端
    
    Args:
        llm_config: LLM配置字典
        
    Returns:
        OpenAIChatCompletionClient实例
    """
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


class BaseComedyAgent:
    """
    OpenMic系统基础智能体类
    封装AutoGen 0.10+的AssistantAgent，提供统一的接口
    
    支持为每个智能体配置独立的LLM模型，实现灵活的模型调度。
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        llm_config: Dict[str, Any],
        description: str = "",
        model_client: Optional[OpenAIChatCompletionClient] = None,
        **kwargs
    ):
        """
        初始化基础智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词，定义智能体角色和行为
            llm_config: LLM配置，包含API密钥、模型名称等
            description: 智能体描述
            model_client: 可选的独立模型客户端，如果提供则使用此客户端而非从llm_config创建
        """
        self._name = name
        self._system_message = system_message
        self._description = description
        self._llm_config = llm_config
        
        # 创建模型客户端 - 支持传入独立的model_client
        if model_client is not None:
            self._model_client = model_client
        else:
            self._model_client = create_model_client(llm_config)
        
        # 创建AutoGen AssistantAgent
        self._agent = AssistantAgent(
            name=name,
            model_client=self._model_client,
            system_message=system_message,
            description=description,
        )
        
        logger.info(f"智能体 [{name}] 初始化完成")
    
    @property
    def name(self) -> str:
        """获取智能体名称"""
        return self._name
    
    @property
    def description(self) -> str:
        """获取智能体描述"""
        return self._description
    
    @property
    def system_message(self) -> str:
        """获取系统提示词"""
        return self._system_message
    
    @property
    def agent(self) -> AssistantAgent:
        """获取底层的AutoGen Agent"""
        return self._agent
    
    def format_message(self, content: str, message_type: str = "normal") -> str:
        """
        格式化输出消息
        
        Args:
            content: 消息内容
            message_type: 消息类型 (normal, suggestion, critique, final)
        
        Returns:
            格式化后的消息
        """
        type_prefixes = {
            "normal": "",
            "suggestion": "【建议】",
            "critique": "【评审意见】",
            "final": "【最终输出】",
            "strategy": "【策略】",
            "analysis": "【分析】"
        }
        
        prefix = type_prefixes.get(message_type, "")
        return f"{prefix}{content}" if prefix else content
    
    def log_action(self, action: str, details: Optional[Dict] = None):
        """
        记录智能体行为日志
        
        Args:
            action: 行为描述
            details: 详细信息
        """
        log_msg = f"[{self._name}] {action}"
        if details:
            log_msg += f" - {details}"
        logger.debug(log_msg)
