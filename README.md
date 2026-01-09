# OpenMic: 基于多智能体框架的智能脱口秀生成系统

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![AutoGen 0.7.5](https://img.shields.io/badge/AutoGen-0.7.5-green.svg)](https://github.com/microsoft/autogen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于AutoGen多智能体框架的端到端脱口秀生成系统，实现从主题输入到专业表演脚本的完整流程。

## 🎯 项目概述

OpenMic是一个创新的AI脱口秀生成系统，使用5个专业化的智能体协作创作符合中文stand-up comedy特点的表演内容：

| 智能体 | 角色 | 职责 |
|--------|------|------|
| 🎬 **ComedyDirector** | 喜剧导演 | 整体策略制定和风格控制 |
| 👥 **AudienceAnalyzer** | 受众分析师 | 受众适配分析和文化评估 |
| ✍️ **JokeWriter** | 段子写手 | 核心内容创作（Setup-Punchline结构） |
| 🎤 **PerformanceCoach** | 表演教练 | 表演标记和语音指导 |
| ✅ **QualityController** | 质量控制官 | 内容评估和质量把关 |

## 📋 任务进度

- [x] **任务一**：AutoGen多智能体系统架构（30分）✅ 已完成
- [ ] **任务二**：基于CFunSet的中文幽默内容生成（25分）
- [x] **任务三**：专业级语音合成与表演优化（30分）✅ 已完成
- [X] **任务四**：系统集成与用户体验（15分）✅ 已完成

---

## 🏗️ 项目结构详解

```
OpenMic/
├── main.py                      # 🚀 主入口文件（命令行/交互模式）
├── requirements.txt             # pip依赖列表
├── environment.yml              # Conda环境配置
├── README.md                    # 项目说明文档
├── .env.example                 # 环境变量模板
│
├── config/
│   └── llm_config.json          # 🔧 LLM模型配置文件
│
├── src/                         # 核心源代码目录
│   ├── __init__.py
│   │
│   ├── agents/                  # 📦 智能体模块（任务一核心）
│   │   ├── __init__.py          # 导出所有智能体类
│   │   ├── base_agent.py        # 基础智能体抽象类
│   │   ├── comedy_director.py   # 喜剧导演智能体
│   │   ├── audience_analyzer.py # 受众分析师智能体
│   │   ├── joke_writer.py       # 段子写手智能体
│   │   ├── performance_coach.py # 表演教练智能体
│   │   └── quality_controller.py# 质量控制官智能体
│   │
│   ├── orchestrator/            # 📦 协作调度模块
│   │   ├── __init__.py          # 导出ComedyGroupChat
│   │   ├── comedy_chat.py       # ⭐ SelectorGroupChat核心实现
│   │   └── workflow.py          # 工作流状态管理
│   │
│   ├── config/                  # 📦 配置管理模块
│   │   ├── __init__.py
│   │   └── settings.py          # ConfigManager单例类
│   │
│   ├── generators/              # 📦 内容生成模块（任务二预留）
│   │   └── __init__.py
│   │
│   ├── speech/                  # 📦 语音合成模块（任务三核心）
│   │   └── __init__.py
│   │
│   └── api/                     # 📦 Web API模块（任务四预留）
│       └── __init__.py
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_agents.py           # 智能体测试
│   ├── test_groupchat.py        # GroupChat测试
│   └── test_import.py           # 导入测试
│
└── outputs/                     # 输出目录（生成的脚本JSON）
    └── *.json
```

### 核心模块说明

#### 1. `src/agents/` - 智能体模块

每个智能体继承自 `BaseComedyAgent`，封装了角色特定的系统提示词和行为：

```python
# 智能体层次结构
BaseComedyAgent (基类)
├── ComedyDirectorAgent     # 制定创作策略，输出【创作策略】
├── AudienceAnalyzerAgent   # 分析受众，输出【受众分析报告】
├── JokeWriterAgent         # 创作脚本，输出【脱口秀脚本草稿】
├── PerformanceCoachAgent   # 添加表演标记，输出【表演指导方案】
└── QualityControllerAgent  # 质量评估，输出【质量评估报告】+【最终脚本】
```

#### 2. `src/orchestrator/comedy_chat.py` - 协作调度核心

使用AutoGen的 `SelectorGroupChat` 实现多智能体协作：

```python
class ComedyGroupChat:
    """
    关键特性：
    - 使用 selector_func 强制工作流顺序
    - 支持为每个智能体配置独立的模型
    - 内置循环优化机制（质量不通过时返回JokeWriter）
    """
```

**工作流顺序**：
```
ComedyDirector → AudienceAnalyzer → JokeWriter → PerformanceCoach → QualityController
       ↑                                                                      │
       └──────────────────── 如果"不通过" ←────────────────────────────────────┘
```

#### 3. `src/config/settings.py` - 配置管理

使用单例模式的 `ConfigManager` 管理所有配置：

```python
from src.config import config_manager

# 获取LLM配置
llm_config = config_manager.get_autogen_llm_config()

# 获取表演风格
style = config_manager.get_comedy_style("吐槽类")

# 列出所有风格
styles = config_manager.list_comedy_styles()  # ["观察类", "自嘲类", "吐槽类"]
```

---

## 🚀 快速开始

### 1. 环境准备

#### 方式一：使用Conda（推荐）

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate openmic
```

#### 方式二：使用pip

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

**方式一**：使用环境变量（推荐）

```bash
# 复制模板
copy .env.example .env

# 编辑 .env 文件
DEEPSEEK_API_KEY=sk-your-api-key-here
```

**方式二**：直接编辑配置文件

编辑 `config/llm_config.json`：
```json
{
    "config_list": [
        {
            "model": "deepseek-chat",
            "api_key": "sk-your-api-key-here",
            "base_url": "https://api.deepseek.com/v1"
        }
    ],
    "temperature": 0.8,
    "max_tokens": 4096
}
```

### 3. 下载音频生成模型权重
从huggingface上下载 ChatTTS model (https://huggingface.co/2Noise/ChatTTS) 到目录 `Openmic/models`

### 4. 运行系统
系统有多种运行模式，我们准备了图形界面的web前端，运行方法如下：

```bash
# 运行后端服务器
python src/api/backend_server.py

# 运行前端app，此时你可以在浏览器上打开http://localhost:8501来进行图形界面交互
streamlit run ./src/api/app.py --server.port 8501

# 如果你希望能够在公网上访问这个服务器，请安装cloudflared，并使用下面的指令实现公网穿透，就可以在公网上进行访问了
cloudflared tunnel --url http://127.0.0.1:8501
```

此外，如果希望直接在控制台上交互，可以参照下面的方法

```bash

# 交互模式（推荐初次使用）
python main.py -i

# 命令行模式
python main.py --topic "期末考试" --style "吐槽类" --duration 3 --audience "大学生"

# 指定输出文件
python main.py -t "网购经历" -s "观察类" -d 5 -a "职场白领" -o outputs/my_script.json

# 查看帮助
python main.py --help

# 查看智能体信息
python main.py --info
```
命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--topic` | `-t` | 脱口秀主题 | - |
| `--style` | `-s` | 表演风格 | 观察类 |
| `--duration` | `-d` | 目标时长(分钟) | 3 |
| `--audience` | `-a` | 目标受众 | 年轻人 |
| `--output` | `-o` | 输出文件路径 | outputs/comedy_脚本_{timestamp}.json |
| `--interactive` | `-i` | 交互模式 | False |
| `--info` | - | 显示智能体信息 | - |
| `--debug` | - | 调试模式 | False |

---

## 🔧 配置其他模型

### 方式一：全局切换模型

修改 `config/llm_config.json`：

```json
{
    "config_list": [
        {
            "model": "gpt-4o",
            "api_key": "sk-your-openai-key",
            "base_url": "https://api.openai.com/v1"
        }
    ]
}
```

**支持的模型示例**：

| 模型 | base_url | 说明 |
|------|----------|------|
| `deepseek-chat` | `https://api.deepseek.com/v1` | DeepSeek（默认） |
| `gpt-4o` | `https://api.openai.com/v1` | OpenAI GPT-4o |
| `gpt-3.5-turbo` | `https://api.openai.com/v1` | OpenAI GPT-3.5 |
| `claude-3-5-sonnet-20241022` | `https://api.anthropic.com/v1` | Anthropic Claude |
| `qwen-turbo` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 阿里通义千问 |
| `glm-4` | `https://open.bigmodel.cn/api/paas/v4` | 智谱GLM-4 |

### 方式二：为不同智能体配置独立模型

在代码中使用 `agent_model_configs` 参数：

```python
from src.orchestrator import ComedyGroupChat

# 为不同智能体配置不同模型
agent_configs = {
    'ComedyDirector': {
        'config_list': [{
            'model': 'gpt-4o',
            'api_key': 'sk-openai-key',
            'base_url': 'https://api.openai.com/v1'
        }]
    },
    'JokeWriter': {
        'config_list': [{
            'model': 'deepseek-chat',
            'api_key': 'sk-deepseek-key', 
            'base_url': 'https://api.deepseek.com/v1'
        }]
    },
    # 其他智能体使用默认配置
}

# 创建团队
team = ComedyGroupChat(
    llm_config=default_config,
    agent_model_configs=agent_configs  # 独立模型配置
)
```

### 方式三：使用环境变量

```bash
# .env 文件
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat
```

---

## 📖 Python API使用

### 基本用法

```python
import asyncio
from src.orchestrator import ComedyGroupChat
from src.config import config_manager

async def main():
    # 获取配置
    llm_config = config_manager.get_autogen_llm_config()
    
    # 创建团队
    team = ComedyGroupChat(
        llm_config=llm_config,
        max_round=25  # 最大对话轮数
    )
    
    # 运行创作
    result = await team.run(
        topic="期末考试",
        style="吐槽类",
        duration_minutes=3,
        target_audience="大学生"
    )
    
    # 获取结果
    print(f"总轮数: {result['rounds']}")
    print(f"最终脚本: {result['final_script']}")
    
    return result

# 运行
result = asyncio.run(main())
```

### 高级用法：自定义智能体

```python
from src.agents import BaseComedyAgent

class CustomAgent(BaseComedyAgent):
    """自定义智能体"""
    
    def __init__(self, llm_config, **kwargs):
        super().__init__(
            name="CustomAgent",
            system_message="""你是一个专业的...
            
            输出格式：
            【自定义报告】
            ...""",
            llm_config=llm_config,
            description="自定义智能体的简短描述",
            **kwargs
        )
```

---

## 🔌 后续任务接口预留

### 任务二：内容生成模块 (`src/generators/`)

```python
# 预留接口示例
from src.generators import HumorGenerator, CFunSetLoader

class HumorGenerator:
    """幽默内容生成器"""
    
    def load_cfunset(self, dataset_path: str):
        """加载CFunSet数据集"""
        pass
    
    def generate_setup_punchline(self, topic: str) -> dict:
        """生成Setup-Punchline结构笑话"""
        pass
    
    def expand_topic(self, topic: str) -> List[str]:
        """主题扩展算法"""
        pass
```

---

## 📊 输出格式

生成的JSON文件结构：

```json
{
    "metadata": {
        "topic": "期末考试",
        "style": "吐槽类",
        "duration_minutes": 3,
        "target_audience": "大学生",
        "timestamp": "2025-12-27T01:42:00",
        "total_rounds": 5
    },
    "messages": [
        {
            "role": "ComedyDirector",
            "content": "【创作策略】..."
        },
        {
            "role": "AudienceAnalyzer", 
            "content": "【受众分析报告】..."
        },
        {
            "role": "JokeWriter",
            "content": "【脱口秀脚本草稿】..."
        },
        {
            "role": "PerformanceCoach",
            "content": "【表演指导方案】..."
        },
        {
            "role": "QualityController",
            "content": "【质量评估报告】...【最终脚本】..."
        }
    ],
    "final_script": "完整的最终脚本文本..."
}
```

---

## 🧪 测试

```bash
# 导入测试
python test_import.py

# 智能体测试
python tests/test_agents.py

# GroupChat测试
python test_groupchat.py
```

---

## 🛠️ 开发指南

### 添加新智能体

1. 在 `src/agents/` 创建新文件
2. 继承 `BaseComedyAgent`
3. 在 `src/agents/__init__.py` 导出
4. 在 `comedy_chat.py` 的工作流中注册

### 修改工作流顺序

编辑 `src/orchestrator/comedy_chat.py` 中的 `_create_workflow_selector()` 方法：

```python
workflow_order = [
    "ComedyDirector",
    "AudienceAnalyzer",
    "JokeWriter",
    "PerformanceCoach", 
    "QualityController"
]
```

---

## 📚 技术栈

- **Python 3.11+**
- **AutoGen 0.7.5** - 多智能体框架
- **Rich** - 终端美化输出
- **python-dotenv** - 环境变量管理
- **DeepSeek API** - 默认LLM后端

---

## 📄 License

MIT License

## 👥 Contributors

OpenMic Team
