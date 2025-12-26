"""
OpenMic - 脱口秀生成系统主入口
基于AutoGen多智能体框架的智能脱口秀生成系统

使用方法:
    python main.py --topic "校园糗事" --style "自嘲类" --duration 3 --audience "大学生"
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from src.config.settings import config_manager
from src.orchestrator import ComedyGroupChat, create_comedy_team

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich控制台
console = Console()


def setup_logging(debug: bool = False):
    """配置日志系统"""
    level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(level)
    
    # 设置autogen日志级别
    logging.getLogger("autogen").setLevel(logging.WARNING)


def print_banner():
    """打印系统横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ██████╗ ███████╗███╗   ██╗███╗   ███╗██╗ ██████╗   ║
║  ██╔═══██╗██╔══██╗██╔════╝████╗  ██║████╗ ████║██║██╔════╝   ║
║  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║██╔████╔██║██║██║        ║
║  ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██║╚██╔╝██║██║██║        ║
║  ╚██████╔╝██║     ███████╗██║ ╚████║██║ ╚═╝ ██║██║╚██████╗   ║
║   ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝     ╚═╝╚═╝ ╚═════╝   ║
║                                                               ║
║        基于多智能体框架的智能脱口秀生成系统 v0.1.0              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_agents_info():
    """打印智能体信息"""
    agents_info = """
## 🎭 智能体团队

| 角色 | 职责 |
|------|------|
| 🎬 ComedyDirector | 喜剧导演 - 整体策略制定和风格控制 |
| ✍️ JokeWriter | 段子写手 - 核心内容创作 |
| 👥 AudienceAnalyzer | 受众分析师 - 受众适配分析 |
| 🎤 PerformanceCoach | 表演教练 - 语音表达策略和表演标记 |
| ✅ QualityController | 质量控制官 - 内容评估和质量控制 |
    """
    console.print(Markdown(agents_info))


def validate_config() -> bool:
    """验证配置是否完整"""
    llm_config = config_manager.get_autogen_llm_config()
    api_key = llm_config["config_list"][0].get("api_key", "")
    
    if not api_key or api_key == "YOUR_DEEPSEEK_API_KEY":
        console.print(Panel(
            "[red]错误：未配置API密钥！[/red]\n\n"
            "请按以下步骤配置：\n"
            "1. 复制 .env.example 为 .env\n"
            "2. 在 .env 文件中填入您的 DeepSeek API 密钥\n"
            "   或者修改 config/llm_config.json 中的 api_key",
            title="配置错误",
            border_style="red"
        ))
        return False
    
    return True


def run_comedy_generation(
    topic: str,
    style: str = "观察类",
    duration: int = 3,
    audience: str = "年轻人",
    output_file: Optional[str] = None
) -> dict:
    """
    运行脱口秀生成流程
    
    Args:
        topic: 创作主题
        style: 表演风格 (观察类/自嘲类/吐槽类)
        duration: 目标时长(分钟)
        audience: 目标受众
        output_file: 输出文件路径
        
    Returns:
        生成结果字典
    """
    console.print(Panel(
        f"🎯 主题: {topic}\n"
        f"🎭 风格: {style}\n"
        f"⏱️ 时长: {duration}分钟\n"
        f"👥 受众: {audience}",
        title="创作参数",
        border_style="green"
    ))
    
    # 获取LLM配置
    llm_config = config_manager.get_autogen_llm_config()
    
    # 创建脱口秀创作团队
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("正在初始化智能体团队...", total=None)
        
        comedy_team = create_comedy_team(
            llm_config=llm_config,
            max_round=25
        )
        
        progress.update(task, description="智能体团队初始化完成！")
    
    console.print("\n[bold green]🚀 开始创作流程...[/bold green]\n")
    console.print("=" * 60)
    
    # 运行创作流程
    try:
        result = comedy_team.run(
            topic=topic,
            style=style,
            duration_minutes=duration,
            target_audience=audience
        )
        
        console.print("=" * 60)
        console.print("\n[bold green]✅ 创作完成！[/bold green]\n")
        
        # 显示结果摘要
        if result.get("script"):
            console.print(Panel(
                result["script"][:1000] + "..." if len(result.get("script", "")) > 1000 else result.get("script", ""),
                title="📝 生成的脱口秀内容（预览）",
                border_style="cyan"
            ))
        
        # 保存结果
        if output_file:
            save_result(result, output_file)
            console.print(f"\n[green]结果已保存到: {output_file}[/green]")
        
        return result
        
    except Exception as e:
        console.print(f"\n[red]❌ 创作过程中出现错误: {e}[/red]")
        logger.exception("创作流程异常")
        raise


def save_result(result: dict, output_file: str):
    """保存生成结果"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 添加元数据
    result["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "version": "0.1.0"
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def interactive_mode():
    """交互式模式"""
    console.print("\n[bold cyan]进入交互模式[/bold cyan]\n")
    
    # 获取主题
    topic = console.input("[bold]请输入脱口秀主题: [/bold]")
    if not topic.strip():
        topic = "我的网购经历"
        console.print(f"[dim]使用默认主题: {topic}[/dim]")
    
    # 选择风格
    console.print("\n[bold]请选择表演风格:[/bold]")
    console.print("  1. 观察类 - 通过观察日常生活引发共鸣")
    console.print("  2. 自嘲类 - 以自身经历自我调侃")
    console.print("  3. 吐槽类 - 犀利点评社会现象")
    
    style_choice = console.input("\n请输入选项 (1/2/3) [默认1]: ").strip()
    styles = {"1": "观察类", "2": "自嘲类", "3": "吐槽类"}
    style = styles.get(style_choice, "观察类")
    
    # 设置时长
    duration_input = console.input("\n请输入目标时长(分钟) [默认3]: ").strip()
    try:
        duration = int(duration_input) if duration_input else 3
        duration = max(1, min(10, duration))  # 限制在1-10分钟
    except ValueError:
        duration = 3
    
    # 选择受众
    console.print("\n[bold]请选择目标受众:[/bold]")
    console.print("  1. 年轻人 (18-30岁)")
    console.print("  2. 大学生")
    console.print("  3. 职场人群")
    console.print("  4. 中年人 (30-50岁)")
    
    audience_choice = console.input("\n请输入选项 (1/2/3/4) [默认1]: ").strip()
    audiences = {"1": "年轻人", "2": "大学生", "3": "职场人群", "4": "中年人"}
    audience = audiences.get(audience_choice, "年轻人")
    
    # 确认参数
    console.print("\n")
    confirm = console.input("[bold]确认开始创作? (y/n) [默认y]: [/bold]").strip().lower()
    
    if confirm in ("", "y", "yes"):
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/comedy_{timestamp}.json"
        
        run_comedy_generation(
            topic=topic,
            style=style,
            duration=duration,
            audience=audience,
            output_file=output_file
        )
    else:
        console.print("[yellow]已取消创作[/yellow]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OpenMic - 基于多智能体框架的智能脱口秀生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --topic "校园糗事" --style "自嘲类"
  python main.py --topic "我的网购经历" --duration 5 --audience "年轻人"
  python main.py -i  # 交互模式
        """
    )
    
    parser.add_argument(
        "-t", "--topic",
        type=str,
        help="脱口秀主题"
    )
    
    parser.add_argument(
        "-s", "--style",
        type=str,
        choices=["观察类", "自嘲类", "吐槽类"],
        default="观察类",
        help="表演风格 (默认: 观察类)"
    )
    
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=3,
        help="目标时长(分钟) (默认: 3)"
    )
    
    parser.add_argument(
        "-a", "--audience",
        type=str,
        default="年轻人",
        help="目标受众 (默认: 年轻人)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出文件路径"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="交互模式"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="调试模式"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="显示智能体信息"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.debug)
    
    # 打印横幅
    print_banner()
    
    # 显示智能体信息
    if args.info:
        print_agents_info()
        return
    
    # 验证配置
    if not validate_config():
        sys.exit(1)
    
    # 交互模式
    if args.interactive or not args.topic:
        interactive_mode()
        return
    
    # 命令行模式
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/comedy_{timestamp}.json"
    
    run_comedy_generation(
        topic=args.topic,
        style=args.style,
        duration=args.duration,
        audience=args.audience,
        output_file=output_file
    )


if __name__ == "__main__":
    main()
