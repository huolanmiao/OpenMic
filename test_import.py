"""测试AutoGen导入"""
try:
    print("测试 autogen_agentchat...")
    import autogen_agentchat
    print(f"  版本: {autogen_agentchat.__version__ if hasattr(autogen_agentchat, '__version__') else '未知'}")
    print(f"  模块内容: {dir(autogen_agentchat)}")
except Exception as e:
    print(f"  导入失败: {e}")

try:
    print("\n测试 autogen_agentchat.agents...")
    from autogen_agentchat import agents
    print(f"  agents 模块内容: {dir(agents)}")
except Exception as e:
    print(f"  导入失败: {e}")

try:
    print("\n测试 AssistantAgent...")
    from autogen_agentchat.agents import AssistantAgent
    print(f"  AssistantAgent 导入成功: {AssistantAgent}")
except Exception as e:
    print(f"  导入失败: {e}")

try:
    print("\n测试 SelectorGroupChat...")
    from autogen_agentchat.teams import SelectorGroupChat
    print(f"  SelectorGroupChat 导入成功: {SelectorGroupChat}")
except Exception as e:
    print(f"  导入失败: {e}")

try:
    print("\n测试 OpenAIChatCompletionClient...")
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    print(f"  OpenAIChatCompletionClient 导入成功: {OpenAIChatCompletionClient}")
except Exception as e:
    print(f"  导入失败: {e}")

try:
    print("\n测试 ModelFamily...")
    from autogen_core.models import ModelFamily
    print(f"  ModelFamily 导入成功: {ModelFamily}")
except Exception as e:
    print(f"  导入失败: {e}")

print("\n=== 测试完成 ===")
