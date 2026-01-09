import streamlit as st
import requests
import time
import base64

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="OpenMic - AI脱口秀工场",
    page_icon="🎙️",
    layout="wide"
)

if "script_text" not in st.session_state:
    st.session_state.script_text = ""
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "voice_options" not in st.session_state:
    st.session_state.voice_options = []

# --- 辅助函数 ---

def get_voices():
    try:
        # 只有当列表为空时才去请求，避免每次刷新都请求
        if not st.session_state.voice_options:
            resp = requests.get(f"{API_BASE_URL}/voices", timeout=5)
            if resp.status_code == 200:
                st.session_state.voice_options = resp.json().get("voices", [])
    except Exception as e:
        st.warning(f"无法获取音色列表 (后端可能还在启动): {e}")

def poll_task(task_id, status_container, prefix="处理"):
    progress_bar = status_container.progress(0)
    status_text = status_container.empty()
    
    while True:
        try:
            r = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
            if r.status_code != 200:
                status_text.error("无法获取任务状态")
                break
                
            task = r.json()
            status = task["status"]
            prog = task.get("progress", 0.0)
            stage = task.get("current_stage", "处理中...")
            
            progress_bar.progress(int(prog * 100))
            status_text.info(f"🔄 [{prefix}] {stage}")
            
            if status == "completed":
                status_text.success(f"✅ {prefix}完成！")
                progress_bar.empty()
                
                res = requests.get(f"{API_BASE_URL}/tasks/{task_id}/result")
                return res.json()
            
            elif status == "failed":
                status_text.error(f"❌ 任务失败: {task.get('current_stage')}")
                return None
                
            time.sleep(2)
            
        except Exception as e:
            status_text.error(f"轮询错误: {e}")
            return None

with st.sidebar:
    st.header("🎛️ 导演控制台")
    
    # API Key
    with st.expander("🔑 API Key 设置", expanded=False):
        user_api_key = st.text_input("OpenAI/DeepSeek Key", type="password", key="api_key_input")
    
    st.divider()
    
    st.subheader("1️⃣ 剧本设定")
    topic = st.text_input("🎤 主题", placeholder="例如：我的奇葩室友")
    style_map = {"观察类": "观察类", "自嘲类": "自嘲类", "吐槽类": "吐槽类"}
    style_label = st.radio("🎭 风格", list(style_map.keys()))
    duration = st.slider("⏳ 时长 (分钟)", 1, 10, 3)
    audience = st.text_input("👥 观众", value="年轻人")
    
    btn_generate_script = st.button("📝 生成剧本", type="primary", use_container_width=True)

    st.divider()

    st.subheader("2️⃣ 演播设定")
    get_voices()
    
    if st.session_state.voice_options:
        voice_names = [v['name'] for v in st.session_state.voice_options]
        
        # 下面这行保持不变
        selected_voice_idx = st.selectbox("🗣️ 选择演员音色", range(len(voice_names)), format_func=lambda x: voice_names[x])
        selected_voice_id = st.session_state.voice_options[selected_voice_idx]['id']
    else:
        st.warning("暂无可用音色 (请确保后端已启动)")
        selected_voice_id = "random"

st.title("🎙️ OpenMic AI Studio")

col_script, col_audio = st.columns([1.5, 1])

if btn_generate_script:
    if not topic:
        st.toast("请先输入主题！", icon="⚠️")
    else:
        with st.status("正在召集AI编剧团队...", expanded=True) as status:
            payload = {
                "topic": topic,
                "style": style_map[style_label],
                "duration_minutes": duration,
                "target_audience": audience,
                "api_key": user_api_key if user_api_key else None
            }
            
            try:
                resp = requests.post(f"{API_BASE_URL}/generate", json=payload)
                if resp.status_code == 200:
                    task_id = resp.json()["task_id"]
                    result = poll_task(task_id, status, prefix="创作")
                    
                    if result["script"]:
                        st.session_state.script_text = result["script"]
                        st.session_state.audio_data = None
                        status.update(label="剧本创作完成！", state="complete", expanded=False)
                    else:
                        status.update(label="剧本创作失败！请检查API key和模型是否配置正确", state="error", expanded=False)
            except Exception as e:
                st.error(f"请求失败: {e}")

with col_script:
    st.subheader("📜 剧本工坊")
    if st.session_state.script_text:
        new_script = st.text_area(
            "您可以修改下方剧本，确认无误后点击右侧生成音频：",
            value=st.session_state.script_text,
            height=600,
            key="script_editor" 
        )
        st.session_state.script_text = new_script
        
        st.caption(f"当前字数: {len(st.session_state.script_text)}")
    else:
        st.info("👈 请先在左侧输入主题并点击“生成剧本”")

with col_audio:
    st.subheader("🎧 演播室")
    
    if st.session_state.script_text:
        st.write("剧本已就绪。选择好音色后，点击下方按钮开始录制。")
        
        btn_generate_audio = st.button("🎹 开始语音合成", type="primary", use_container_width=True)
        
        if btn_generate_audio:
            with st.status("正在进行语音合成...", expanded=True) as status:
                payload = {
                    "script": st.session_state.script_text, # 使用当前编辑器里的文本
                    "voice_id": selected_voice_id,
                    "api_key": user_api_key if user_api_key else None
                }
                
                try:
                    resp = requests.post(f"{API_BASE_URL}/generate_audio", json=payload)
                    if resp.status_code == 200:
                        task_id = resp.json()["task_id"]
                        result = poll_task(task_id, status, prefix="录制")
                        
                        if result:
                            # 存入 Session State
                            st.session_state.audio_data = result
                            status.update(label="音频录制完成！", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"请求失败: {e}")
        
        st.divider()
        
        if st.session_state.audio_data:
            audio_info = st.session_state.audio_data
            
            try:
                audio_url = audio_info["audio_url"]
                b64_data = audio_url.split(",")[1]
                audio_bytes = base64.b64decode(b64_data)
                
                st.success("✨ 录制成功！")
                st.audio(audio_bytes, format="audio/wav")
                
                st.download_button(
                    label="💾 下载 .wav 音频",
                    data=audio_bytes,
                    file_name="comedy_show.wav",
                    mime="audio/wav"
                )
                
                with st.expander("查看润色后的台词 (含情绪标注)"):
                    st.write(audio_info.get("refined_text", "无详细数据"))
                    
            except Exception as e:
                st.error(f"音频解析失败: {e}")

    else:
        st.empty() 

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>OpenMic v0.2.0 | Powered by Multi-Agent & TTS</div>", unsafe_allow_html=True)