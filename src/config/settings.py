"""
OpenMic 配置管理模块
负责加载和管理系统配置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class LLMConfig:
    """LLM配置类"""
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    temperature: float = 0.8
    max_tokens: int = 4096
    timeout: int = 120


@dataclass
class AgentConfig:
    """智能体配置类"""
    name: str
    system_message: str
    description: str = ""
    max_consecutive_auto_reply: int = 10


@dataclass
class ComedyStyle:
    """脱口秀风格配置"""
    name: str  # 观察类、自嘲类、吐槽类
    description: str
    tone: str  # 语调特点
    pacing: str  # 节奏特点
    humor_type: str  # 幽默类型


@dataclass 
class PerformanceConfig:
    """表演配置"""
    target_duration_minutes: int = 3  # 目标时长(分钟)
    style: str = "观察类"  # 表演风格
    target_audience: str = "年轻人"  # 目标受众
    language: str = "zh-CN"  # 语言


@dataclass
class SystemConfig:
    """系统全局配置"""
    log_level: str = "INFO"
    debug_mode: bool = False
    output_dir: str = "outputs"
    cache_dir: str = "cache"


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        
        # 加载配置
        self.llm_config = self._load_llm_config()
        self.system_config = self._load_system_config()
        self.comedy_styles = self._load_comedy_styles()
        
        self._initialized = True
    
    def _load_llm_config(self) -> LLMConfig:
        """加载LLM配置"""
        config_file = self.config_dir / "llm_config.json"
        
        # 优先从环境变量读取
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = os.getenv("DEFAULT_MODEL", "deepseek-chat")
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return LLMConfig(
                    model=model or data.get("config_list", [{}])[0].get("model", "deepseek-chat"),
                    api_key=api_key or data.get("config_list", [{}])[0].get("api_key", ""),
                    base_url=base_url or data.get("config_list", [{}])[0].get("base_url", ""),
                    temperature=data.get("temperature", 0.8),
                    max_tokens=data.get("max_tokens", 4096),
                    timeout=data.get("timeout", 120)
                )
        
        return LLMConfig(api_key=api_key, base_url=base_url, model=model)
    
    def _load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        return SystemConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug_mode=os.getenv("DEBUG_MODE", "False").lower() == "true",
            output_dir=str(self.project_root / "outputs"),
            cache_dir=str(self.project_root / "cache")
        )
    
    def _load_comedy_styles(self) -> Dict[str, ComedyStyle]:
        """加载脱口秀风格配置"""
        return {
            "观察类": ComedyStyle(
                name="观察类",
                description="通过敏锐观察日常生活中的细节和矛盾，引发共鸣和笑声",
                tone="轻松、睿智",
                pacing="中等语速，适时停顿",
                humor_type="洞察式幽默"
            ),
            "自嘲类": ComedyStyle(
                name="自嘲类", 
                description="以自身经历和缺点为素材，用自我调侃的方式引发笑声",
                tone="谦逊、自我解嘲",
                pacing="语速稍快，情绪起伏明显",
                humor_type="自我解嘲式幽默"
            ),
            "吐槽类": ComedyStyle(
                name="吐槽类",
                description="针对社会现象、人际关系等进行犀利点评和吐槽",
                tone="犀利、夸张",
                pacing="语速快，重音明显",
                humor_type="讽刺式幽默"
            )
        }
    
    def get_autogen_llm_config(self) -> Dict[str, Any]:
        """获取AutoGen格式的LLM配置"""
        return {
            "config_list": [
                {
                    "model": self.llm_config.model,
                    "api_key": self.llm_config.api_key,
                    "base_url": self.llm_config.base_url,
                }
            ],
            "temperature": self.llm_config.temperature,
            "timeout": self.llm_config.timeout,
        }
    
    def get_comedy_style(self, style_name: str) -> Optional[ComedyStyle]:
        """获取指定风格配置"""
        return self.comedy_styles.get(style_name)
    
    def list_comedy_styles(self) -> List[str]:
        """列出所有可用风格"""
        return list(self.comedy_styles.keys())


# 全局配置实例
config_manager = ConfigManager()
