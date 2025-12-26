"""
ComedyWorkflow - 脱口秀创作工作流管理
实现策略制定→受众分析→内容创作→表演指导→质量控制的循环优化流程
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """工作流阶段枚举"""
    INIT = auto()               # 初始化
    STRATEGY = auto()           # 策略制定
    AUDIENCE_ANALYSIS = auto()  # 受众分析
    CONTENT_CREATION = auto()   # 内容创作
    PERFORMANCE_DESIGN = auto() # 表演设计
    QUALITY_CONTROL = auto()    # 质量控制
    REVISION = auto()           # 修订阶段
    COMPLETED = auto()          # 完成
    FAILED = auto()             # 失败


@dataclass
class WorkflowState:
    """工作流状态"""
    current_stage: WorkflowStage = WorkflowStage.INIT
    iteration: int = 0
    max_iterations: int = 3
    
    # 各阶段输出
    strategy: Optional[str] = None
    audience_analysis: Optional[str] = None
    content: Optional[str] = None
    performance_markers: Optional[str] = None
    quality_report: Optional[str] = None
    
    # 质量评分
    quality_score: float = 0.0
    quality_passed: bool = False
    
    # 时间记录
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 历史记录
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_history(self, stage: WorkflowStage, content: str, metadata: Optional[Dict] = None):
        """添加历史记录"""
        self.history.append({
            "stage": stage.name,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "iteration": self.iteration
        })


class ComedyWorkflow:
    """
    脱口秀创作工作流管理器
    
    管理整个创作流程的状态和转换，确保流程的有序执行和质量控制
    """
    
    def __init__(
        self,
        max_iterations: int = 3,
        quality_threshold: float = 35.0,
        on_stage_change: Optional[Callable[[WorkflowStage, WorkflowState], None]] = None
    ):
        """
        初始化工作流管理器
        
        Args:
            max_iterations: 最大迭代次数
            quality_threshold: 质量通过阈值（满分50）
            on_stage_change: 阶段变更回调函数
        """
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.on_stage_change = on_stage_change
        
        self.state = WorkflowState(max_iterations=max_iterations)
        
        # 定义阶段转换规则
        self._transitions = {
            WorkflowStage.INIT: [WorkflowStage.STRATEGY],
            WorkflowStage.STRATEGY: [WorkflowStage.AUDIENCE_ANALYSIS],
            WorkflowStage.AUDIENCE_ANALYSIS: [WorkflowStage.CONTENT_CREATION],
            WorkflowStage.CONTENT_CREATION: [WorkflowStage.PERFORMANCE_DESIGN],
            WorkflowStage.PERFORMANCE_DESIGN: [WorkflowStage.QUALITY_CONTROL],
            WorkflowStage.QUALITY_CONTROL: [WorkflowStage.COMPLETED, WorkflowStage.REVISION],
            WorkflowStage.REVISION: [WorkflowStage.CONTENT_CREATION, WorkflowStage.FAILED],
            WorkflowStage.COMPLETED: [],
            WorkflowStage.FAILED: []
        }
        
        logger.info("ComedyWorkflow初始化完成")
    
    def start(self, topic: str, style: str, duration: int, audience: str) -> WorkflowState:
        """
        启动工作流
        
        Args:
            topic: 创作主题
            style: 表演风格
            duration: 目标时长
            audience: 目标受众
        """
        self.state = WorkflowState(max_iterations=self.max_iterations)
        self.state.start_time = datetime.now()
        
        # 记录初始参数
        self.state.add_history(
            WorkflowStage.INIT,
            f"主题: {topic}, 风格: {style}, 时长: {duration}分钟, 受众: {audience}",
            {"topic": topic, "style": style, "duration": duration, "audience": audience}
        )
        
        logger.info(f"工作流启动 - 主题: {topic}")
        return self.state
    
    def transition_to(self, next_stage: WorkflowStage, content: Optional[str] = None) -> bool:
        """
        转换到下一阶段
        
        Args:
            next_stage: 目标阶段
            content: 当前阶段的输出内容
            
        Returns:
            是否成功转换
        """
        current = self.state.current_stage
        
        # 检查转换是否合法
        if next_stage not in self._transitions.get(current, []):
            logger.warning(f"非法的阶段转换: {current.name} -> {next_stage.name}")
            return False
        
        # 保存当前阶段输出
        if content:
            self._save_stage_output(current, content)
        
        # 执行转换
        old_stage = self.state.current_stage
        self.state.current_stage = next_stage
        
        # 更新迭代次数
        if next_stage == WorkflowStage.REVISION:
            self.state.iteration += 1
        
        # 检查是否超过最大迭代
        if self.state.iteration >= self.max_iterations:
            if next_stage == WorkflowStage.REVISION:
                self.state.current_stage = WorkflowStage.FAILED
                logger.warning("达到最大迭代次数，工作流失败")
        
        # 回调通知
        if self.on_stage_change:
            self.on_stage_change(next_stage, self.state)
        
        logger.info(f"阶段转换: {old_stage.name} -> {next_stage.name}")
        return True
    
    def _save_stage_output(self, stage: WorkflowStage, content: str):
        """保存阶段输出"""
        if stage == WorkflowStage.STRATEGY:
            self.state.strategy = content
        elif stage == WorkflowStage.AUDIENCE_ANALYSIS:
            self.state.audience_analysis = content
        elif stage == WorkflowStage.CONTENT_CREATION:
            self.state.content = content
        elif stage == WorkflowStage.PERFORMANCE_DESIGN:
            self.state.performance_markers = content
        elif stage == WorkflowStage.QUALITY_CONTROL:
            self.state.quality_report = content
        
        self.state.add_history(stage, content)
    
    def update_quality_score(self, score: float) -> bool:
        """
        更新质量评分并判断是否通过
        
        Args:
            score: 质量评分（满分50）
            
        Returns:
            是否通过质量检查
        """
        self.state.quality_score = score
        self.state.quality_passed = score >= self.quality_threshold
        
        logger.info(f"质量评分: {score}/50, 通过: {self.state.quality_passed}")
        return self.state.quality_passed
    
    def complete(self) -> WorkflowState:
        """完成工作流"""
        self.state.current_stage = WorkflowStage.COMPLETED
        self.state.end_time = datetime.now()
        
        duration = (self.state.end_time - self.state.start_time).total_seconds()
        logger.info(f"工作流完成，耗时: {duration:.2f}秒")
        
        return self.state
    
    def fail(self, reason: str = "") -> WorkflowState:
        """标记工作流失败"""
        self.state.current_stage = WorkflowStage.FAILED
        self.state.end_time = datetime.now()
        
        self.state.add_history(WorkflowStage.FAILED, reason)
        logger.error(f"工作流失败: {reason}")
        
        return self.state
    
    def get_current_stage(self) -> WorkflowStage:
        """获取当前阶段"""
        return self.state.current_stage
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.state.current_stage == WorkflowStage.COMPLETED
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.state.current_stage == WorkflowStage.FAILED
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作流摘要"""
        duration = None
        if self.state.start_time and self.state.end_time:
            duration = (self.state.end_time - self.state.start_time).total_seconds()
        
        return {
            "current_stage": self.state.current_stage.name,
            "iteration": self.state.iteration,
            "quality_score": self.state.quality_score,
            "quality_passed": self.state.quality_passed,
            "duration_seconds": duration,
            "is_completed": self.is_completed(),
            "is_failed": self.is_failed(),
            "history_count": len(self.state.history)
        }
    
    def get_final_output(self) -> Optional[Dict[str, Any]]:
        """获取最终输出"""
        if not self.is_completed():
            return None
        
        return {
            "strategy": self.state.strategy,
            "audience_analysis": self.state.audience_analysis,
            "content": self.state.content,
            "performance_markers": self.state.performance_markers,
            "quality_report": self.state.quality_report,
            "quality_score": self.state.quality_score,
            "iterations": self.state.iteration + 1
        }
