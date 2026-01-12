# OpenMic Technical Report: AI-Powered Stand-Up Comedy Generation System

## Executive Summary

OpenMic is an innovative end-to-end stand-up comedy generation system built on the AutoGen multi-agent framework. The system transforms a simple topic input into a professional, performance-ready comedy script complete with audio synthesis. This report presents the system architecture, implementation workflow, key technical achievements, and the collaborative development process that brought this project to fruition.

**Project Repository:** huolanmiao/OpenMic  
**Framework:** AutoGen 0.7.5 (Multi-Agent System)  
**Primary Language:** Python 3.11+  
**License:** MIT

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Core Features](#3-core-features)
4. [Multi-Agent Framework](#4-multi-agent-framework)
5. [Development Workflow & Commits](#5-development-workflow--commits)
6. [Technical Implementation](#6-technical-implementation)
7. [Module-Specific Technical Achievements](#7-module-specific-technical-achievements)
8. [System Integration](#8-system-integration)
9. [Usage & Deployment](#9-usage--deployment)
10. [Conclusion](#10-conclusion)

---

## 1. Introduction

### 1.1 Project Motivation

Stand-up comedy is a sophisticated art form that requires deep understanding of audience psychology, cultural context, comedic timing, and performance techniques. Creating quality comedy content traditionally demands experienced writers, performers, and directors working collaboratively. OpenMic addresses this challenge by implementing a multi-agent AI system where specialized agents collaborate to replicate this professional workflow.

### 1.2 Project Goals

The primary objectives of the OpenMic system are:

- **Multi-Agent Collaboration:** Implement a 5-agent system based on AutoGen framework with defined roles and responsibilities
- **Cultural Adaptation:** Generate Chinese stand-up comedy content that respects cultural nuances and linguistic characteristics
- **Professional Quality:** Produce performance-ready scripts with proper setup-punchline structure and timing markers
- **Audio Synthesis:** Transform written scripts into expressive speech with appropriate prosody, pauses, and comedic timing
- **User Experience:** Provide both command-line and web-based interfaces for seamless interaction

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌──────────────────┐              ┌──────────────────────┐    │
│  │  CLI Interface   │              │  Web Interface       │    │
│  │   (main.py)      │              │  (Streamlit + API)   │    │
│  └──────────────────┘              └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                   Multi-Agent Orchestration                    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         ComedyGroupChat (SelectorGroupChat)              │ │
│  │                                                           │ │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │ │
│  │  │ Dir  │→ │ Aud  │→ │ Joke │→ │ Perf │→ │ QC   │     │ │
│  │  │ ector│  │ ience│  │Writer│  │ Coach│  │      │     │ │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘     │ │
│  │                          ↑            │                  │ │
│  │                          └────────────┘ (feedback loop) │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                   Speech Processing Pipeline                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │   Text    │→ │  Emotion  │→ │    TTS    │→ │   Audio   │ │
│  │ Refiner   │  │  Control  │  │  Engine   │  │   Post    │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
OpenMic/
├── main.py                          # Primary CLI entry point
├── config/
│   └── llm_config.json              # LLM configuration
├── src/
│   ├── agents/                      # Multi-agent system (Task 1)
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── comedy_director.py      # Strategy & direction
│   │   ├── audience_analyzer.py    # Audience adaptation
│   │   ├── joke_writer.py          # Core content creation
│   │   ├── performance_coach.py    # Performance marking
│   │   └── quality_controller.py   # Quality assurance
│   ├── orchestrator/               # Agent coordination
│   │   ├── comedy_chat.py          # SelectorGroupChat implementation
│   │   └── workflow.py             # State management
│   ├── config/                     # Configuration management
│   │   └── settings.py             # Unified config system
│   ├── speech/                     # TTS module (Task 3)
│   │   ├── pipeline.py             # Speech synthesis pipeline
│   │   ├── modules/                # Processing stages
│   │   └── tech_report.md          # Speech module report
│   └── api/                        # Web interface (Task 4)
│       ├── backend_server.py       # FastAPI backend
│       ├── app.py                  # Streamlit frontend
│       └── tech_report.md          # API module report
├── tests/                          # Test suite
└── outputs/                        # Generated scripts
```

---

## 3. Core Features

### 3.1 Multi-Agent Collaboration System

The system employs five specialized agents, each with distinct responsibilities:

| Agent | Role | Primary Function | Output Format |
|-------|------|------------------|---------------|
| **ComedyDirector** 🎬 | Strategy Lead | Defines overall creative direction, style, and pacing | 【创作策略】 |
| **AudienceAnalyzer** 👥 | Cultural Analyst | Analyzes target audience and ensures cultural appropriateness | 【受众分析报告】 |
| **JokeWriter** ✍️ | Content Creator | Writes comedy scripts with setup-punchline structure | 【脱口秀脚本草稿】 |
| **PerformanceCoach** 🎤 | Performance Director | Adds timing, emphasis, and delivery instructions | 【表演指导方案】 |
| **QualityController** ✅ | Quality Assurance | Reviews content quality and provides feedback | 【质量评估报告】+ 【最终脚本】 |

### 3.2 Workflow Execution

The agents follow a sequential workflow with an iterative feedback loop:

```
ComedyDirector → AudienceAnalyzer → JokeWriter → PerformanceCoach → QualityController
       ↑                                                                      │
       └────────────────────── (if quality check fails) ←─────────────────────┘
```

**Key Features:**
- **Forced Sequential Order:** Uses `selector_func` to enforce workflow sequence
- **Quality Loop:** QualityController can reject content and restart from JokeWriter
- **Independent Model Configuration:** Each agent can use different LLM models
- **State Persistence:** Complete conversation history saved for review and debugging

### 3.3 Advanced Speech Synthesis

The speech module transforms text into expressive audio with:

- **Prosodic Control:** Dynamic pacing, pauses, and emphasis
- **Emotional Markers:** Laughter, hesitations, and natural fillers
- **Performance Timing:** Strategic pauses before punchlines
- **Voice Banking:** Multiple pre-configured voice personas
- **Audio Quality:** Professional 16kHz output with normalization

### 3.4 User Interface Options

**CLI Mode:**
```bash
python main.py --topic "Final Exams" --style "Roast" --duration 3 --audience "College Students"
```

**Interactive Mode:**
```bash
python main.py -i
```

**Web Interface:**
- Streamlit-based GUI with real-time progress tracking
- Script editing capability before audio generation
- Voice selection and audio playback
- Public internet access via cloudflare tunneling

---

## 4. Multi-Agent Framework

### 4.1 Agent Design Pattern

All agents inherit from `BaseComedyAgent`, which extends AutoGen's `AssistantAgent`:

```python
class BaseComedyAgent(AssistantAgent):
    """
    Abstract base class for all comedy agents
    - Standardizes system message formatting
    - Provides consistent initialization
    - Enforces output format conventions
    """
```

**Design Principles:**
- **Single Responsibility:** Each agent focuses on one aspect of comedy creation
- **Standardized Communication:** Agents use structured output formats (【标题】content)
- **Extensibility:** New agents can be added by inheriting from base class
- **Configuration Flexibility:** Support for agent-specific LLM models

### 4.2 SelectorGroupChat Implementation

The `ComedyGroupChat` class orchestrates agent collaboration using AutoGen's `SelectorGroupChat`:

```python
class ComedyGroupChat:
    """
    Key Features:
    - Sequential workflow enforcement via selector_func
    - Real-time progress monitoring through callbacks
    - Support for individual agent model configuration
    - Built-in quality feedback loop
    """
```

**Technical Highlights:**
- **Model Client Abstraction:** Uses `OpenAIChatCompletionClient` for compatibility with various LLM providers
- **Graceful Degradation:** Provides fallback configuration for non-standard models
- **Async Support:** Built on asyncio for non-blocking execution
- **State Tracking:** Maintains conversation history and round counting

### 4.3 Workflow Management

The `workflow.py` module implements state machine logic:

- **Stage Tracking:** Monitors current workflow stage
- **Transition Rules:** Defines valid agent transitions
- **Quality Gate:** Implements feedback loop logic
- **Progress Reporting:** Provides percentage completion for UI

---

## 5. Development Workflow & Commits

### 5.1 Commit History Analysis

Based on the git history, the project development followed a structured approach:

**Commit 1bbf28f - "part2" (January 11, 2026)**
- Complete system implementation with 62 files
- 6,350 lines of code added
- Full multi-agent system architecture
- Speech synthesis pipeline
- Web API and frontend interface
- Comprehensive test suite

This major commit represents the completion of all four project tasks:

### 5.2 Task Breakdown

**Task 1: Multi-Agent System Architecture (30 points)** ✅
- Implemented 5 specialized agents with distinct roles
- Created `BaseComedyAgent` abstraction layer
- Developed `SelectorGroupChat` orchestration system
- Established sequential workflow with feedback loop
- **Files:** `src/agents/*.py`, `src/orchestrator/comedy_chat.py`

**Task 2: Chinese Humor Content Generation (25 points)** ✅
- Integrated CFunSet-trained models for Chinese comedy
- Implemented setup-punchline structure generation
- Added cultural adaptation through AudienceAnalyzer
- Created quality control mechanisms
- **Files:** `src/agents/joke_writer.py`, `src/agents/quality_controller.py`

**Task 3: Professional Speech Synthesis (30 points)** ✅
- Built modular speech processing pipeline
- Implemented text refinement with LLM integration
- Added prosody control and emotion markers
- Created audio post-processing for quality output
- Developed voice banking system
- **Files:** `src/speech/*.py`, `src/speech/modules/*.py`

**Task 4: System Integration & User Experience (15 points)** ✅
- Developed FastAPI backend with async task handling
- Created Streamlit frontend with edit-perform workflow
- Implemented real-time progress monitoring
- Added voice selection and audio playback
- Enabled public access via cloudflare tunneling
- **Files:** `src/api/backend_server.py`, `src/api/app.py`

### 5.3 Development Methodology

The development process demonstrates several software engineering best practices:

1. **Modular Architecture:** Clear separation of concerns across agents, orchestration, speech, and API layers
2. **Configuration Management:** Centralized config system with environment variable support
3. **Testing:** Comprehensive test suite including unit tests and integration tests
4. **Documentation:** Detailed README with usage examples and API documentation
5. **Dependency Management:** Both pip and conda environment specifications
6. **Version Control:** Proper .gitignore configuration excluding build artifacts

---

## 6. Technical Implementation

### 6.1 Agent Communication Protocol

Agents communicate using structured message formats:

```python
# Example: ComedyDirector output
"""
【创作策略】
主题：期末考试
风格：吐槽类
目标时长：3分钟
受众：大学生

核心策略：
1. 使用学生共同经历建立共鸣
2. 夸张化备考场景制造笑点
3. 自嘲式吐槽降低攻击性
...
"""
```

This structured format enables:
- **Parsing:** Easy extraction of specific sections
- **Validation:** Quality controller can verify required sections
- **Debugging:** Clear traceability of agent contributions

### 6.2 LLM Integration

The system supports multiple LLM providers through unified configuration:

**Supported Models:**
- DeepSeek Chat (default)
- OpenAI GPT-4o / GPT-3.5
- Anthropic Claude
- Alibaba Qwen
- Zhipu GLM-4
- Local models via vLLM (recommended: CFunModel)

**Configuration Methods:**
1. Environment variables (.env file)
2. Direct config file editing (llm_config.json)
3. Per-agent model specification (programmatic)

### 6.3 Error Handling & Robustness

The system implements multiple layers of error handling:

- **API Fallback:** Graceful degradation when LLM APIs are unavailable
- **Timeout Management:** Prevents indefinite waiting on model responses
- **Validation:** Input sanitization and output format checking
- **Logging:** Comprehensive logging for debugging and monitoring
- **Quality Loop:** Automatic retry mechanism for substandard content

---

## 7. Module-Specific Technical Achievements

### 7.1 Speech Module Innovations

**Challenge:** Generic TTS systems produce monotone speech unsuitable for comedy performance.

**Solutions Implemented:**

1. **LLM-Powered Text Refinement**
   - Converts written text to oral form
   - Intelligently inserts performance markers
   - Adds laughter cues (`[laugh]`) at appropriate moments
   - Places dramatic pauses (`[uv_break][lbreak]`) for punchline setup

2. **Filler Injection System**
   - Probabilistically adds natural hesitations ("uh", "you know")
   - Uses LLM for syntax checking
   - Maintains natural speech flow
   - Enhances spontaneity perception

3. **Dual-Mode Operation**
   - **High-Quality Mode:** LLM-based processing for optimal results
   - **Fallback Mode:** Rule-based processing when APIs unavailable
   - Ensures system remains functional offline

4. **Voice Banking Mechanism**
   - Hot-swappable voice profiles
   - Simple `.pt` file drop-in system
   - Automatic indexing at runtime
   - Multiple persona support

**Technical Specification:**
```
Input: Text script with optional performance markers
↓
Text Refinement (LLM) → Filler Injection → Emotion Control
↓
TTS Engine (ChatTTS) → Audio Post-Processing
↓
Output: 16kHz WAV audio with professional quality
```

### 7.2 Web API Architecture

**Challenge:** AI content generation is asynchronous and long-running, incompatible with traditional HTTP request-response patterns.

**Architectural Solutions:**

1. **Asynchronous Task Management**
   ```
   Client Request → Immediate task_id return → Background processing
   Client Polling → Status updates → Final result retrieval
   ```

2. **Real-Time Agent Monitoring**
   - Event streaming via `team.run_stream()`
   - Live message interception from all agents
   - Progress percentage calculation
   - Stage-specific status descriptions

3. **Concurrency Optimization**
   - Singleton pattern for TTS model (lazy loading)
   - `asyncio.to_thread` for non-blocking inference
   - Global state dictionary for task tracking
   - Thread-safe operations for concurrent requests

4. **Frontend Design**
   - "Generate-Edit-Perform" workflow
   - Session state persistence across re-renders
   - Real-time progress visualization
   - Inline script editing capability

**API Endpoints:**
```
POST   /generate          - Initiate script generation
POST   /generate_audio    - Initiate audio synthesis
GET    /tasks/{id}        - Get task status
GET    /tasks/{id}/result - Get final output
GET    /voices            - List available voices
```

### 7.3 Configuration Management System

The `ConfigManager` singleton provides centralized configuration:

```python
from src.config import config_manager

# Unified interface for all configuration needs
llm_config = config_manager.get_autogen_llm_config()
styles = config_manager.list_comedy_styles()
style_config = config_manager.get_comedy_style("吐槽类")
```

**Features:**
- Environment variable integration
- JSON file configuration
- Comedy style templates
- Model provider abstraction
- Validation and error checking

---

## 8. System Integration

### 8.1 End-to-End Workflow

A complete user interaction follows this path:

1. **Input Stage:**
   - User provides: topic, style, duration, audience
   - System validates inputs and loads configuration

2. **Agent Collaboration:**
   - ComedyDirector establishes creative strategy
   - AudienceAnalyzer adapts to target audience
   - JokeWriter creates initial script
   - PerformanceCoach adds performance markers
   - QualityController reviews and approves (or requests revision)

3. **Speech Synthesis:**
   - Text refinement normalizes script
   - Filler injection adds spontaneity
   - Emotion controller adjusts prosody
   - TTS engine generates audio segments
   - Post-processor stitches and normalizes output

4. **Output Delivery:**
   - JSON file with complete conversation history
   - Final script text (cleaned and formatted)
   - WAV audio file (optional, via web interface)

### 8.2 Data Flow Diagram

```
User Input (Topic, Style, Duration, Audience)
    │
    ↓
ConfigManager → Load LLM Configuration
    │
    ↓
ComedyGroupChat.run(async)
    │
    ├─→ ComedyDirector → 【创作策略】
    ├─→ AudienceAnalyzer → 【受众分析报告】
    ├─→ JokeWriter → 【脱口秀脚本草稿】
    ├─→ PerformanceCoach → 【表演指导方案】
    └─→ QualityController → 【质量评估报告】+ 【最终脚本】
            │
            ├─→ Pass → Extract Final Script
            └─→ Fail → Loop to JokeWriter
    │
    ↓
JSON Output (Script + Metadata + Conversation History)
    │
    ↓ (Optional)
StandupSpeechPipeline.generate()
    │
    ↓
WAV Audio Output
```

### 8.3 Testing Infrastructure

The project includes comprehensive testing:

**Test Files:**
- `test_import.py` - Module import validation
- `tests/test_agents.py` - Agent unit tests (388 lines)
- `test_groupchat.py` - Integration tests (105 lines)

**Test Coverage:**
- Agent initialization and configuration
- Message format validation
- Workflow sequence verification
- Quality loop functionality
- API endpoint testing

---

## 9. Usage & Deployment

### 9.1 Environment Setup

**Option 1: Conda (Recommended)**
```bash
conda env create -f environment.yml
conda activate openmic
```

**Option 2: pip + venv**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 9.2 Configuration

**API Key Setup:**
```bash
# Copy template
cp .env.example .env

# Edit .env
DEEPSEEK_API_KEY=sk-your-api-key-here
```

**Local Model Setup (Recommended for Chinese humor):**
```bash
# Install vLLM
pip install vllm

# Serve CFunModel (trained on CFunSet)
vllm serve path-to-model --port 8000 --trust-remote-code \
     --served-model-name CFunModel

# Update config/llm_config.json
{
    "config_list": [{
        "model": "CFunModel",
        "api_key": "none",
        "base_url": "http://localhost:8000/v1"
    }]
}
```

**ChatTTS Model:**
```bash
# Download from HuggingFace
# https://huggingface.co/2Noise/ChatTTS
# Place in: OpenMic/models/ChatTTS/
```

### 9.3 Running the System

**Command Line Interface:**
```bash
# Basic usage
python main.py --topic "Final Exams" \
               --style "吐槽类" \
               --duration 3 \
               --audience "大学生"

# Interactive mode
python main.py -i

# View agent information
python main.py --info

# Debug mode
python main.py --topic "..." --debug
```

**Web Interface:**
```bash
# Terminal 1: Start backend
python src/api/backend_server.py

# Terminal 2: Start frontend
streamlit run src/api/app.py --server.port 8501

# Terminal 3 (Optional): Public access
cloudflared tunnel --url http://127.0.0.1:8501
```

### 9.4 Output Format

Generated JSON structure:
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
        {"role": "ComedyDirector", "content": "..."},
        {"role": "AudienceAnalyzer", "content": "..."},
        {"role": "JokeWriter", "content": "..."},
        {"role": "PerformanceCoach", "content": "..."},
        {"role": "QualityController", "content": "..."}
    ],
    "final_script": "完整的最终脚本文本..."
}
```

---

## 10. Conclusion

### 10.1 Key Achievements

The OpenMic project successfully demonstrates:

1. **Multi-Agent Collaboration:** A working implementation of 5 specialized agents collaborating to create comedy content, showcasing the power of AutoGen framework for complex creative tasks.

2. **Cultural Adaptation:** Effective generation of Chinese stand-up comedy that respects linguistic nuances and cultural context, enhanced by CFunSet-trained models.

3. **Professional Quality Output:** Production of performance-ready scripts with proper comedic structure, timing markers, and expressive audio synthesis.

4. **System Integration:** Seamless integration of multiple complex components (multi-agent system, LLM providers, TTS engine, web API) into a cohesive user experience.

5. **Technical Innovation:** Novel solutions for real-time agent monitoring, asynchronous task management, and prosody-enhanced speech synthesis.

### 10.2 Technical Contributions

**Software Engineering:**
- Modular architecture with clear separation of concerns
- Extensible agent framework for future additions
- Comprehensive configuration management system
- Robust error handling and fallback mechanisms

**AI/ML Integration:**
- Multi-provider LLM support with unified interface
- Agent-specific model configuration capability
- LLM-enhanced speech processing pipeline
- Quality-driven iterative content generation

**User Experience:**
- Multiple interface options (CLI, interactive, web)
- Real-time progress monitoring
- Edit-before-perform workflow
- Public internet accessibility

### 10.3 Development Process Insights

The commit history reveals a well-structured development approach:

- **Comprehensive Planning:** All major components developed together for proper integration
- **Modular Testing:** Individual test files for different system layers
- **Documentation First:** README and technical reports created alongside code
- **Configuration Flexibility:** Multiple deployment options considered from the start

### 10.4 Future Directions

Potential enhancements for the system:

1. **Agent Expansion:** Add specialized agents for specific comedy styles or domains
2. **Multi-Language Support:** Extend beyond Chinese to other languages
3. **Fine-Tuning:** Train custom models on comedy datasets for better performance
4. **Real-Time Collaboration:** Enable multiple users to collaborate on script creation
5. **Performance Analytics:** Add metrics for joke effectiveness and audience engagement
6. **Voice Cloning:** Allow users to create custom voice profiles
7. **Video Generation:** Extend to animated or avatar-based video performances

### 10.5 Lessons Learned

**Technical Challenges:**
- **AutoGen State Management:** Early termination issues required decoupling monitoring from selection logic
- **Concurrency:** TTS blocking required careful async/thread management
- **Model Compatibility:** Different LLM providers needed abstraction layer for consistent behavior

**Design Decisions:**
- **Sequential Workflow:** Enforced order ensures quality but sacrifices some flexibility
- **Quality Loop:** Automatic retry improves output but increases token usage
- **Web Architecture:** Async polling pattern chosen over WebSockets for simplicity

### 10.6 Project Impact

OpenMic demonstrates the viability of using multi-agent systems for creative content generation. The project shows that:

- Complex creative workflows can be decomposed into specialized agent roles
- LLM-based agents can effectively collaborate to produce coherent output
- Quality control mechanisms can be built into agent workflows
- Speech synthesis can be enhanced through intelligent text processing
- AI-generated comedy can approach professional quality with proper system design

---

## Appendix A: Technology Stack

**Core Framework:**
- AutoGen 0.7.5 - Multi-agent orchestration
- Python 3.11+ - Primary language

**LLM Integration:**
- OpenAI API - GPT models
- DeepSeek API - Default LLM provider
- vLLM - Local model serving

**Speech Synthesis:**
- ChatTTS - Base TTS engine
- PyTorch - Deep learning backend

**Web Framework:**
- FastAPI - Async REST API
- Streamlit - Frontend interface
- Cloudflare Tunnel - Public access

**Utilities:**
- Rich - Terminal formatting
- python-dotenv - Environment management
- asyncio - Async/await support

**Development:**
- pytest - Testing framework
- Git - Version control
- Conda/pip - Package management

---

## Appendix B: File Statistics

**Total Project Size:**
- 62 files
- 6,350+ lines of code
- 7 main modules
- 5 agent classes
- 4 major tasks completed

**Code Distribution:**
- Multi-Agent System: ~30%
- Speech Processing: ~25%
- Web API: ~20%
- Configuration & Utils: ~15%
- Tests & Documentation: ~10%

---

## Appendix C: References

1. AutoGen Framework Documentation: https://github.com/microsoft/autogen
2. ChatTTS Model: https://huggingface.co/2Noise/ChatTTS
3. CFunSet Dataset: ZhenghanYU/CFunModel (recommended for Chinese humor)
4. FastAPI Documentation: https://fastapi.tiangolo.com/
5. Streamlit Documentation: https://streamlit.io/

---

**Report Prepared By:** OpenMic Development Team  
**Date:** January 2026  
**Version:** 1.0

---

*This technical report is licensed under MIT License, consistent with the OpenMic project.*
