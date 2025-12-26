"""
GroupChat 协作系统模块
实现多智能体协作的核心逻辑
"""

from .comedy_chat import ComedyGroupChat, create_comedy_team
from .workflow import ComedyWorkflow, WorkflowStage

__all__ = [
    "ComedyGroupChat",
    "create_comedy_team",
    "ComedyWorkflow",
    "WorkflowStage"
]
