"""测试 SelectorGroupChat 的正确用法"""
import asyncio
import os
import sys

# 手动加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily

# 获取 API Key
api_key = os.getenv("DEEPSEEK_API_KEY", "")
print(f"API Key 状态: {'已配置 (' + api_key[:8] + '...)' if api_key else '未配置'}")

if not api_key:
    print("错误: 请在 .env 文件中配置 DEEPSEEK_API_KEY")
    sys.exit(1)

# 创建模型客户端
model_info = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "family": ModelFamily.UNKNOWN,
}

model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    api_key=api_key,
    base_url="https://api.deepseek.com/v1",
    model_info=model_info,
)

print("模型客户端创建成功")

# 创建简单的智能体
agent1 = AssistantAgent(
    name="Agent1",
    model_client=model_client,
    system_message="你是Agent1，用中文简单回复后说'请Agent2继续'",
    description="Agent1负责第一个回复"
)

agent2 = AssistantAgent(
    name="Agent2",
    model_client=model_client,
    system_message="你是Agent2，用中文简单回复后说 TERMINATE",
    description="Agent2负责最后一个回复并结束对话"
)

print(f"智能体创建成功: {agent1.name}, {agent2.name}")

# 创建终止条件
termination = MaxMessageTermination(max_messages=10) | TextMentionTermination("TERMINATE")

# 创建 SelectorGroupChat
team = SelectorGroupChat(
    participants=[agent1, agent2],
    model_client=model_client,
    termination_condition=termination,
    selector_prompt="根据对话选择下一个发言者。如果还没人说话，选Agent1；如果Agent1说了，选Agent2。"
)

print("团队创建成功")

async def run_test():
    print("\n开始测试对话...")
    print("=" * 50)
    
    try:
        # 使用 run_stream
        async for message in team.run_stream(task="请用中文打个招呼"):
            msg_type = type(message).__name__
            print(f"\n收到消息类型: {msg_type}")
            
            if hasattr(message, 'source') and hasattr(message, 'content'):
                print(f"  来源: {message.source}")
                content = message.content if message.content else "(空)"
                print(f"  内容: {content[:500] if len(str(content)) > 500 else content}")
            elif hasattr(message, 'messages'):
                print(f"  最终结果，共 {len(message.messages)} 条消息")
                for i, msg in enumerate(message.messages):
                    if hasattr(msg, 'source') and hasattr(msg, 'content'):
                        print(f"    [{i+1}] {msg.source}: {str(msg.content)[:100]}...")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("测试完成")

if __name__ == "__main__":
    asyncio.run(run_test())
