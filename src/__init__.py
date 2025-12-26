"""
OpenMic 源代码包初始化
"""

from .config.settings import config_manager, ConfigManager
from .agents import (
    ComedyDirectorAgent,
    JokeWriterAgent,
    AudienceAnalyzerAgent,
    PerformanceCoachAgent,
    QualityControllerAgent
)
from .orchestrator import ComedyGroupChat, create_comedy_team, ComedyWorkflow

__version__ = "0.1.0"
__author__ = "OpenMic Team"

__all__ = [
    # 配置
    "config_manager",
    "ConfigManager",
    # 智能体
    "ComedyDirectorAgent",
    "JokeWriterAgent", 
    "AudienceAnalyzerAgent",
    "PerformanceCoachAgent",
    "QualityControllerAgent",
    # 协作系统
    "ComedyGroupChat",
    "create_comedy_team",
    "ComedyWorkflow"
]
