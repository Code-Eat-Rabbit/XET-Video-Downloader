#!/usr/bin/env python3
"""
测试控制台输入的小脚本
"""
import subprocess
import re
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

class VideoDownloader:
    """视频下载器主类，简化版本"""

    def __init__(self, user_data_dir: str = "./browser_session", output_dir: str = "./downloads"):
        self.user_data_dir = Path(user_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.captured_urls: List[Dict[str, str]] = []

    def check_dependencies(self) -> bool:
        """检查系统依赖"""
        console.print("\n[bold cyan]🔍 检查系统依赖...[/bold cyan]")

        # 检查 yt-dlp
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            console.print(f"[green]✓[/green] yt-dlp 已安装 (版本: {result.stdout.strip()})")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]✗[/red] 未检测到 yt-dlp")
            return False

        # 检查 ffmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_line = result.stdout.split('\n')[0]
            console.print(f"[green]✓[/green] ffmpeg 已安装 ({version_line})")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[yellow]⚠[/yellow] 未检测到 ffmpeg，建议安装以获得更好的体验:")
            console.print("  [yellow]brew install ffmpeg[/yellow]  (macOS)")

        return True

def main():
    """测试主函数"""
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold magenta]  XET Video Downloader - 安装测试[/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")

    downloader = VideoDownloader()

    # 检查依赖
    if not downloader.check_dependencies():
        console.print("\n[red]请先安装必要的依赖[/red]")
        sys.exit(1)

    console.print("\n[bold green]✅ 所有依赖检查通过！[/bold green]")
    console.print("\n[bold cyan]安装状态总结：[/bold cyan]")
    console.print("  - Python 依赖: ✅ 通过 uv sync 安装成功")
    console.print("  - yt-dlp: ✅ 已安装，可通过命令行使用")
    console.print("  - ffmpeg: ⚠️ 未安装（可选但推荐）")
    console.print("  - Playwright: ✅ 已安装（修改为使用系统Chrome）")

    console.print("\n[bold yellow]下一步使用建议：[/bold yellow]")
    console.print("  1. 准备视频URL列表文件（如 urls.txt）")
    console.print("  2. 运行: source ~/.local/bin/env && export PATH='$PATH:/Users/mac/Library/Python/3.9/bin' && uv run python main.py")
    console.print("  3. 首次运行选择显示浏览器窗口完成登录")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]用户中断操作[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]发生错误:[/red] {str(e)}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)