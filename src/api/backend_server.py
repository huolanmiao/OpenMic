
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
    print("cannot find src modules, make sure to run from project root")


TASKS: Dict[str, dict] = {}
SPEECH_PIPELINE: Optional['StandupSpeechPipeline'] = None

def get_speech_pipeline():
    """init speech pipeline"""
    global SPEECH_PIPELINE
    if SPEECH_PIPELINE is None:
        print("🔊 正在初始化语音生成模型...")
        # 这里使用默认配置初始化，如果需要动态key，可以在 run 时处理或重新设计
        SPEECH_PIPELINE = StandupSpeechPipeline(
            device="cuda",  # 如果报错请改为 "cpu"
            llm_config=config_manager.get_autogen_llm_config()
        )
        print("✅ 语音模型加载完成")
    return SPEECH_PIPELINE

class ComedyStyle(str, Enum):
    OBSERVATION = "观察类"
    SELF_DEPRECATION = "自嘲类"
    ROAST = "吐槽类"

class GenerationRequest(BaseModel):
    topic: str = Field(..., description="主题")
    style: ComedyStyle = Field(default=ComedyStyle.OBSERVATION)
    duration_minutes: int = Field(default=3)
    target_audience: str = Field(default="年轻人")
    api_key: Optional[str] = None

class AudioGenerationRequest(BaseModel):
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


async def process_text_task(task_id: str, request: GenerationRequest):
    try:
        def update_task_progress(stage_name: str, progress_val: float):
            if task_id in TASKS:
                TASKS[task_id]["current_stage"] = stage_name
                TASKS[task_id]["progress"] = progress_val
                
                print(f"DEBUG [Task {task_id[:8]}]: {stage_name} ({progress_val*100:.0f}%)")

        update_task_progress("正在初始化多智能体配置...", 0.05)
        
        llm_config = config_manager.get_autogen_llm_config()
        if request.api_key and request.api_key.strip():
            if "config_list" in llm_config:
                for config in llm_config["config_list"]:
                    config["api_key"] = request.api_key
        
        team = ComedyGroupChat(
            llm_config=llm_config,
            max_round=25,
            on_step_change=update_task_progress  # 绑定回调
        )
        
        result = await team.run_async(
            topic=request.topic,
            style=request.style.value,
            duration_minutes=request.duration_minutes,
            target_audience=request.target_audience
        )
        
        # import json
        # with open("/data/ctl/projects/OpenMic/outputs/comedy_20260109_130803.json", 'r') as f:
        #     result = json.load(f)
        
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
    """audio processing task"""
    try:
        TASKS[task_id]["status"] = "processing"
        TASKS[task_id]["progress"] = 0.1
        TASKS[task_id]["current_stage"] = "加载语音引擎..."
        
        pipeline = get_speech_pipeline()
        
        TASKS[task_id]["progress"] = 0.3
        TASKS[task_id]["current_stage"] = "正在根据语境调整语调..."
        
        if request.voice_id and request.voice_id != "random":
            pipeline.set_voice(request.voice_id)
        
        print(f"开始生成音频，文本长度: {len(request.script)}")
        result = pipeline.run(request.script, return_text=True, return_control=True)
        
        TASKS[task_id]["progress"] = 0.8
        TASKS[task_id]["current_stage"] = "音频编码中..."
        
        audio_data = result["audio"]
        sample_rate = 16000
        
        scaled_audio = (audio_data * 32767).astype(np.int16)
        
        wav_buffer = io.BytesIO()
        write(wav_buffer, sample_rate, scaled_audio)
        wav_bytes = wav_buffer.getvalue()
        
        # Base64
        audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        audio_url = f"data:audio/wav;base64,{audio_b64}"
        
        TASKS[task_id]["result"] = {
            "audio_url": audio_url,
            "refined_text": result.get("text", ""),
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
        task_id = str(uuid.uuid4())
        TASKS[task_id] = {
            "task_id": task_id, "status": "pending", "progress": 0.0,
            "current_stage": "准备生成剧本", "result": None
        }
        bg_tasks.add_task(process_text_task, task_id, request)
        return {"task_id": task_id, "status": "pending", "message": "剧本生成任务已提交"}

    @app.post("/generate_audio", response_model=TaskResponse)
    async def generate_audio(request: AudioGenerationRequest, bg_tasks: BackgroundTasks):
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
        try:
            pipeline = get_speech_pipeline()
            voices = pipeline.list_voices()
            
            formatted_voices = []
            for k, v in voices.items():
                comment = v.get('comment')
                
                if comment:
                    display_name = f"{comment}"
                else:
                    display_name = f"{k}"

                formatted_voices.append({
                    "id": k, 
                    "name": display_name,
                    "comment": comment or ""
                })

            return {"voices": formatted_voices}

        except Exception as e:
            print(f"获取音色失败: {e}")
            return {"voices": [{"id": "random", "name": "默认音色 (随机选择)", "comment": "系统自动选择"}]}
            
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)