"""
Web API模块 (任务四 - 完整实现：文本生成 + 语音合成)
FastAPI后端API实现
"""

import uuid
import io
import base64
import numpy as np
from scipy.io.wavfile import write
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- 引入你的核心逻辑 ---
try:
    from src.orchestrator import ComedyGroupChat
    from src.speech import StandupSpeechPipeline  # 新增
    from src.config import config_manager
except ImportError:
    print("⚠️ 警告: 未找到 src 模块，请确保在项目根目录下运行")

# --- 全局变量 ---
TASKS: Dict[str, dict] = {}

# 语音管道单例 (避免重复加载模型)
SPEECH_PIPELINE: Optional['StandupSpeechPipeline'] = None

def get_speech_pipeline():
    """获取或初始化语音管道"""
    global SPEECH_PIPELINE
    if SPEECH_PIPELINE is None:
        print("🔊 正在初始化语音生成模型 (首次运行可能较慢)...")
        # 这里使用默认配置初始化，如果需要动态key，可以在 run 时处理或重新设计
        SPEECH_PIPELINE = StandupSpeechPipeline(
            device="cuda",  # 如果报错请改为 "cpu"
            llm_config=config_manager.get_autogen_llm_config()
        )
        print("✅ 语音模型加载完成")
    return SPEECH_PIPELINE


# --- Pydantic模型定义 ---

class ComedyStyle(str, Enum):
    OBSERVATION = "观察类"
    SELF_DEPRECATION = "自嘲类"
    ROAST = "吐槽类"

class GenerationRequest(BaseModel):
    """文本生成请求"""
    topic: str = Field(..., description="主题")
    style: ComedyStyle = Field(default=ComedyStyle.OBSERVATION)
    duration_minutes: int = Field(default=3)
    target_audience: str = Field(default="年轻人")
    api_key: Optional[str] = None

class AudioGenerationRequest(BaseModel):
    """新增：音频生成请求"""
    script: str = Field(..., description="要朗读的剧本内容")
    voice_id: str = Field(default="random", description="音色ID")
    api_key: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    current_stage: Optional[str]
    result: Optional[dict] = None


# --- 后台任务逻辑 ---
async def process_text_task(task_id: str, request: GenerationRequest):
    """
    处理文本生成的后台任务
    """
    try:
        # ✨ 定义回调函数：供智能体内部调用
        def update_task_progress(stage_name: str, progress_val: float):
            if task_id in TASKS:
                TASKS[task_id]["current_stage"] = stage_name
                TASKS[task_id]["progress"] = progress_val
                # 同时也记录在后台日志，方便调试
                print(f"DEBUG [Task {task_id[:8]}]: {stage_name} ({progress_val*100:.0f}%)")

        # 初始状态更新
        update_task_progress("正在初始化多智能体配置...", 0.05)
        
        # 获取配置
        llm_config = config_manager.get_autogen_llm_config()
        if request.api_key and request.api_key.strip():
            # 动态覆盖 API Key (逻辑同前)
            if "config_list" in llm_config:
                for config in llm_config["config_list"]:
                    config["api_key"] = request.api_key
        
        # ✨ 关键：将回调函数 update_task_progress 传给 ComedyGroupChat
        team = ComedyGroupChat(
            llm_config=llm_config,
            max_round=25,
            on_step_change=update_task_progress  # 绑定回调
        )
        
        # 运行创作流程
        # 现在，team 内部每一步调用 self.on_step_change，都会更新 TASKS 字典
        result = await team.run_async(
            topic=request.topic,
            style=request.style.value,
            duration_minutes=request.duration_minutes,
            target_audience=request.target_audience
        )
        
        # import json
        # with open("/data/ctl/projects/OpenMic/outputs/comedy_20260109_130803.json", 'r') as f:
        #     result = json.load(f)
        # 任务完成后的最终处理
        final_script = result.get("final_script") or result.get("performance_markers")
        
        TASKS[task_id]["result"] = {"script": final_script}
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 1.0
        TASKS[task_id]["current_stage"] = "剧本创作已完成，可以生成音频了"
        
    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["current_stage"] = f"创作过程中断: {str(e)}"
        import traceback
        traceback.print_exc()

async def process_audio_task(task_id: str, request: AudioGenerationRequest):
    """新增：处理音频生成"""
    try:
        TASKS[task_id]["status"] = "processing"
        TASKS[task_id]["progress"] = 0.1
        TASKS[task_id]["current_stage"] = "加载语音引擎..."
        
        # 1. 获取管道 (第一次会比较慢)
        pipeline = get_speech_pipeline()
        
        # 如果用户传了 Key，这里可能需要临时更新配置，
        # 但由于 Pipeline 初始化较重，暂复用初始化时的配置，或者仅用于 LLM 润色部分
        
        TASKS[task_id]["progress"] = 0.3
        TASKS[task_id]["current_stage"] = "正在根据语境调整语调..."
        
        if request.voice_id and request.voice_id != "random":
            pipeline.set_voice(request.voice_id)
        
        # 2. 运行管道
        # return_text=True 会返回润色后的文本（增加了语气词等）
        print(f"开始生成音频，文本长度: {len(request.script)}")
        result = pipeline.run(request.script, return_text=True, return_control=True)
        
        TASKS[task_id]["progress"] = 0.8
        TASKS[task_id]["current_stage"] = "音频编码中..."
        
        # 3. 处理音频数据 (NumPy -> WAV -> Base64)
        audio_data = result["audio"]
        sample_rate = 16000
        
        # 归一化并转为 16-bit 整数
        scaled_audio = (audio_data * 32767).astype(np.int16)
        
        # 写入内存 Buffer
        wav_buffer = io.BytesIO()
        write(wav_buffer, sample_rate, scaled_audio)
        wav_bytes = wav_buffer.getvalue()
        
        # 转 Base64
        audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        audio_url = f"data:audio/wav;base64,{audio_b64}"
        
        TASKS[task_id]["result"] = {
            "audio_url": audio_url,
            "refined_text": result.get("text", ""), # 包含语气标注的文本
            "duration_seconds": len(audio_data) / sample_rate
        }
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["progress"] = 1.0
        TASKS[task_id]["current_stage"] = "音频生成完成"
        
    except Exception as e:
        print(f"音频任务失败: {e}")
        import traceback
        traceback.print_exc()
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["current_stage"] = f"错误: {str(e)}"


# --- FastAPI应用 ---

def create_app() -> FastAPI:
    app = FastAPI(title="OpenMic API", version="0.2.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.post("/generate", response_model=TaskResponse)
    async def generate_comedy(request: GenerationRequest, bg_tasks: BackgroundTasks):
        """步骤1：生成剧本"""
        task_id = str(uuid.uuid4())
        TASKS[task_id] = {
            "task_id": task_id, "status": "pending", "progress": 0.0,
            "current_stage": "准备生成剧本", "result": None
        }
        bg_tasks.add_task(process_text_task, task_id, request)
        return {"task_id": task_id, "status": "pending", "message": "剧本生成任务已提交"}

    @app.post("/generate_audio", response_model=TaskResponse)
    async def generate_audio(request: AudioGenerationRequest, bg_tasks: BackgroundTasks):
        """步骤2：生成音频 (新增接口)"""
        task_id = str(uuid.uuid4())
        TASKS[task_id] = {
            "task_id": task_id, "status": "pending", "progress": 0.0,
            "current_stage": "准备生成音频", "result": None
        }
        bg_tasks.add_task(process_audio_task, task_id, request)
        return {"task_id": task_id, "status": "pending", "message": "音频生成任务已提交"}
    
    @app.get("/tasks/{task_id}", response_model=TaskStatus)
    async def get_task_status(task_id: str):
        task = TASKS.get(task_id)
        if not task: raise HTTPException(404, "任务不存在")
        return task
    
    @app.get("/tasks/{task_id}/result")
    async def get_task_result(task_id: str):
        task = TASKS.get(task_id)
        if not task or task["status"] != "completed":
            raise HTTPException(400, "任务未完成或不存在")
        return task["result"]
    
    @app.get("/voices")
    async def list_voices():
        """获取可用音色列表"""
        try:
            pipeline = get_speech_pipeline()
            voices = pipeline.list_voices()
            
            formatted_voices = []
            for k, v in voices.items():
                # 核心修改：优先使用 comment 作为名字
                # 如果 comment 是 "成熟男声"，ID 是 "spk_1"
                # 显示名称就会变成："成熟男声 (spk_1)" 这样既直观又有区分度
                comment = v.get('comment')
                
                if comment:
                    # 有描述时：只显示描述和性别，ID放后面或者不放
                    # 例如: "开朗大叔 (Male) - spk_1"
                    display_name = f"{comment}"
                else:
                    # 没描述时回退到 ID
                    display_name = f"{k}"

                formatted_voices.append({
                    "id": k,            # 传给算法的真实ID
                    "name": display_name, # 给前端显示的友好名称
                    "comment": comment or ""
                })

            return {"voices": formatted_voices}

        except Exception as e:
            print(f"获取音色失败: {e}")
            # 出错时的默认返回也要改得友好一点
            return {"voices": [{"id": "random", "name": "默认音色 (随机选择)", "comment": "系统自动选择"}]}
            
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)