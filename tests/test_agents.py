"""
OpenMic 任务一测试脚本
测试AutoGen多智能体系统架构

运行方式:
    python tests/test_agents.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import MagicMock, patch


class TestAgentInitialization(unittest.TestCase):
    """测试智能体初始化"""
    
    def setUp(self):
        """测试前置配置"""
        self.mock_llm_config = {
            "config_list": [
                {
                    "model": "deepseek-chat",
                    "api_key": "test_key",
                    "base_url": "https://api.deepseek.com/v1"
                }
            ],
            "temperature": 0.8,
            "timeout": 120
        }
    
    def test_comedy_director_init(self):
        """测试ComedyDirector初始化"""
        from src.agents import ComedyDirectorAgent
        
        agent = ComedyDirectorAgent(llm_config=self.mock_llm_config)
        
        self.assertEqual(agent.name, "ComedyDirector")
        self.assertIn("喜剧导演", agent.description)
        self.assertIsNotNone(agent.system_message)
    
    def test_joke_writer_init(self):
        """测试JokeWriter初始化"""
        from src.agents import JokeWriterAgent
        
        agent = JokeWriterAgent(llm_config=self.mock_llm_config)
        
        self.assertEqual(agent.name, "JokeWriter")
        self.assertIn("段子写手", agent.description)
    
    def test_audience_analyzer_init(self):
        """测试AudienceAnalyzer初始化"""
        from src.agents import AudienceAnalyzerAgent
        
        agent = AudienceAnalyzerAgent(llm_config=self.mock_llm_config)
        
        self.assertEqual(agent.name, "AudienceAnalyzer")
        self.assertIn("受众分析", agent.description)
    
    def test_performance_coach_init(self):
        """测试PerformanceCoach初始化"""
        from src.agents import PerformanceCoachAgent
        
        agent = PerformanceCoachAgent(llm_config=self.mock_llm_config)
        
        self.assertEqual(agent.name, "PerformanceCoach")
        self.assertIn("表演", agent.description)
    
    def test_quality_controller_init(self):
        """测试QualityController初始化"""
        from src.agents import QualityControllerAgent
        
        agent = QualityControllerAgent(llm_config=self.mock_llm_config)
        
        self.assertEqual(agent.name, "QualityController")
        self.assertIn("质量", agent.description)


class TestComedyDirectorFunctions(unittest.TestCase):
    """测试ComedyDirector功能"""
    
    def setUp(self):
        self.mock_llm_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
    
    def test_create_strategy(self):
        """测试创建策略功能"""
        from src.agents import ComedyDirectorAgent
        
        agent = ComedyDirectorAgent(llm_config=self.mock_llm_config)
        strategy = agent.create_strategy(
            topic="校园糗事",
            style="自嘲类",
            duration_minutes=3,
            target_audience="大学生"
        )
        
        self.assertEqual(strategy["topic"], "校园糗事")
        self.assertEqual(strategy["style"], "自嘲类")
        self.assertEqual(strategy["duration_minutes"], 3)
        self.assertEqual(strategy["target_audience"], "大学生")
        self.assertEqual(strategy["estimated_jokes"], 9)  # 3分钟 * 3个笑点


class TestAudienceAnalyzerFunctions(unittest.TestCase):
    """测试AudienceAnalyzer功能"""
    
    def setUp(self):
        self.mock_llm_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
    
    def test_get_audience_profile(self):
        """测试获取受众画像"""
        from src.agents import AudienceAnalyzerAgent
        
        agent = AudienceAnalyzerAgent(llm_config=self.mock_llm_config)
        
        profile = agent.get_audience_profile("大学生")
        
        self.assertIn("age_range", profile)
        self.assertIn("characteristics", profile)
        self.assertIn("preferred_topics", profile)
        self.assertIn("humor_style", profile)


class TestPerformanceCoachFunctions(unittest.TestCase):
    """测试PerformanceCoach功能"""
    
    def setUp(self):
        self.mock_llm_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
    
    def test_get_timing_params(self):
        """测试获取时间参数"""
        from src.agents import PerformanceCoachAgent
        
        agent = PerformanceCoachAgent(llm_config=self.mock_llm_config)
        params = agent.get_timing_params()
        
        self.assertEqual(params["pause_short"], 0.3)
        self.assertEqual(params["pause_medium"], 0.8)
        self.assertEqual(params["pause_long"], 2.0)
    
    def test_parse_performance_markers(self):
        """测试解析表演标记"""
        from src.agents import PerformanceCoachAgent
        
        agent = PerformanceCoachAgent(llm_config=self.mock_llm_config)
        
        content = """
        <pause:short/>这是一段测试内容
        <emotion:excited>太棒了</emotion>
        <emphasis>重点</emphasis>
        <filler:呃/>然后呢
        """
        
        result = agent.parse_performance_markers(content)
        
        self.assertEqual(len(result["pauses"]), 1)
        self.assertEqual(len(result["emotions"]), 1)
        self.assertEqual(len(result["emphases"]), 1)
        self.assertEqual(len(result["fillers"]), 1)


class TestQualityControllerFunctions(unittest.TestCase):
    """测试QualityController功能"""
    
    def setUp(self):
        self.mock_llm_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
    
    def test_get_evaluation_criteria(self):
        """测试获取评估标准"""
        from src.agents import QualityControllerAgent
        
        agent = QualityControllerAgent(llm_config=self.mock_llm_config)
        criteria = agent.get_evaluation_criteria()
        
        self.assertIn("幽默度", criteria)
        self.assertIn("结构完整性", criteria)
        self.assertIn("语言质量", criteria)
        self.assertIn("文化适配度", criteria)
        self.assertIn("表演适配度", criteria)
    
    def test_calculate_total_score(self):
        """测试计算综合得分"""
        from src.agents import QualityControllerAgent
        
        agent = QualityControllerAgent(llm_config=self.mock_llm_config)
        
        scores = {
            "幽默度": 8,
            "结构完整性": 7,
            "语言质量": 8,
            "文化适配度": 7,
            "表演适配度": 8
        }
        
        total = agent.calculate_total_score(scores)
        
        # 期望得分应该在合理范围内
        self.assertGreater(total, 30)
        self.assertLessEqual(total, 50)
    
    def test_check_passing(self):
        """测试通过检查"""
        from src.agents import QualityControllerAgent
        
        agent = QualityControllerAgent(llm_config=self.mock_llm_config)
        
        # 测试通过情况
        scores = {"幽默度": 8, "结构完整性": 7, "语言质量": 8, "文化适配度": 7, "表演适配度": 8}
        result = agent.check_passing(40, scores)
        self.assertTrue(result["passed"])
        
        # 测试不通过情况 - 总分不足
        result = agent.check_passing(30, scores)
        self.assertFalse(result["passed"])
        
        # 测试不通过情况 - 单项不足
        low_scores = {"幽默度": 4, "结构完整性": 7, "语言质量": 8, "文化适配度": 7, "表演适配度": 8}
        result = agent.check_passing(40, low_scores)
        self.assertFalse(result["passed"])


class TestWorkflow(unittest.TestCase):
    """测试工作流"""
    
    def test_workflow_stages(self):
        """测试工作流阶段"""
        from src.orchestrator.workflow import ComedyWorkflow, WorkflowStage
        
        workflow = ComedyWorkflow()
        
        # 启动工作流
        state = workflow.start(
            topic="测试主题",
            style="观察类",
            duration=3,
            audience="年轻人"
        )
        
        self.assertEqual(workflow.get_current_stage(), WorkflowStage.INIT)
        
        # 转换阶段
        self.assertTrue(workflow.transition_to(WorkflowStage.STRATEGY, "策略内容"))
        self.assertEqual(workflow.get_current_stage(), WorkflowStage.STRATEGY)
        
        self.assertTrue(workflow.transition_to(WorkflowStage.AUDIENCE_ANALYSIS))
        self.assertEqual(workflow.get_current_stage(), WorkflowStage.AUDIENCE_ANALYSIS)
    
    def test_workflow_quality_check(self):
        """测试工作流质量检查"""
        from src.orchestrator.workflow import ComedyWorkflow
        
        workflow = ComedyWorkflow(quality_threshold=35)
        workflow.start("测试", "观察类", 3, "年轻人")
        
        # 测试通过
        self.assertTrue(workflow.update_quality_score(40))
        
        # 测试不通过
        self.assertFalse(workflow.update_quality_score(30))
    
    def test_workflow_summary(self):
        """测试工作流摘要"""
        from src.orchestrator.workflow import ComedyWorkflow, WorkflowStage
        
        workflow = ComedyWorkflow()
        workflow.start("测试", "观察类", 3, "年轻人")
        
        summary = workflow.get_summary()
        
        self.assertIn("current_stage", summary)
        self.assertIn("iteration", summary)
        self.assertIn("quality_score", summary)


class TestGroupChat(unittest.TestCase):
    """测试GroupChat"""
    
    def test_group_chat_init(self):
        """测试GroupChat初始化"""
        from src.orchestrator import ComedyGroupChat
        
        mock_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
        
        chat = ComedyGroupChat(llm_config=mock_config)
        
        # 验证所有智能体都已创建
        self.assertEqual(len(chat.agents), 6)  # 5个核心智能体 + 1个用户代理
        
        # 验证智能体名称
        agent_names = [agent.name for agent in chat.agents]
        self.assertIn("ComedyDirector", agent_names)
        self.assertIn("JokeWriter", agent_names)
        self.assertIn("AudienceAnalyzer", agent_names)
        self.assertIn("PerformanceCoach", agent_names)
        self.assertIn("QualityController", agent_names)
    
    def test_create_initial_prompt(self):
        """测试创建初始提示词"""
        from src.orchestrator import ComedyGroupChat
        
        mock_config = {
            "config_list": [{"model": "test", "api_key": "test"}],
            "temperature": 0.8
        }
        
        chat = ComedyGroupChat(llm_config=mock_config)
        
        prompt = chat.create_initial_prompt(
            topic="校园糗事",
            style="自嘲类",
            duration_minutes=3,
            target_audience="大学生"
        )
        
        self.assertIn("校园糗事", prompt)
        self.assertIn("自嘲类", prompt)
        self.assertIn("3分钟", prompt)
        self.assertIn("大学生", prompt)
        self.assertIn("ComedyDirector", prompt)


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def test_comedy_styles(self):
        """测试喜剧风格配置"""
        from src.config.settings import ConfigManager
        
        manager = ConfigManager()
        
        styles = manager.list_comedy_styles()
        self.assertEqual(len(styles), 3)
        self.assertIn("观察类", styles)
        self.assertIn("自嘲类", styles)
        self.assertIn("吐槽类", styles)
        
        # 获取具体风格
        style = manager.get_comedy_style("观察类")
        self.assertIsNotNone(style)
        self.assertEqual(style.name, "观察类")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestAgentInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestComedyDirectorFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestAudienceAnalyzerFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceCoachFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityControllerFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupChat))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
