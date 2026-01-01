#!/usr/bin/env python3
"""
小鹅通视频批量下载工具
使用 Playwright 捕获 m3u8 地址，并通过 yt-dlp 下载视频
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
    """视频下载器主类"""
    
    def __init__(self, user_data_dir: str = "./browser_session", output_dir: str = "./downloads"):
        self.user_data_dir = Path(user_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.captured_urls: List[Dict[str, str]] = []
        
    def check_dependencies(self) -> bool:
        """检查系统依赖是否安装"""
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
            console.print("[red]✗[/red] 未检测到 yt-dlp，请先安装:")
            console.print("  [yellow]brew install yt-dlp[/yellow]  (macOS)")
            console.print("  [yellow]pip install yt-dlp[/yellow]   (通用)")
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
    
    def setup_request_handler(self, page: Page):
        """设置请求拦截处理器"""
        def handle_request(request):
            url = request.url
            # 匹配小鹅通的 M3U8 签名链接
            if ".m3u8" in url and "sign=" in url:
                # 优先捕获高清版本 (f421220)
                if "v.f421220" in url:
                    referer = request.headers.get("referer", "")
                    page_url = page.url
                    
                    # 避免重复添加
                    if not any(item['media_url'] == url for item in self.captured_urls):
                        self.captured_urls.append({
                            'media_url': url,
                            'referer': referer,
                            'page_url': page_url,
                            'title': page.title() or "未知标题"
                        })
                        console.print(f"[green]✓[/green] 捕获到视频: [cyan]{page.title()}[/cyan]")
        
        page.on("request", handle_request)
    
    def capture_video_urls(self, urls: List[str], headless: bool = False, wait_time: int = 10) -> List[Dict[str, str]]:
        """
        捕获视频地址
        
        Args:
            urls: 视频页面URL列表
            headless: 是否使用无头模式
            wait_time: 每个页面等待时间（秒），首次登录建议30秒以上
            
        Returns:
            捕获到的视频信息列表
        """
        console.print(f"\n[bold cyan]🎬 开始捕获视频地址...[/bold cyan]")
        console.print(f"[dim]待处理URL数量: {len(urls)}[/dim]")
        
        with sync_playwright() as p:
            # 使用持久化上下文保存登录状态，使用 Edge 浏览器
            # 如果想用 Chrome，改为 p.chromium; 用 Firefox 改为 p.firefox
            try:
                # 尝试使用系统安装的 Edge 浏览器
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=headless,
                    channel='msedge',  # 使用 Microsoft Edge
                    args=['--no-sandbox'],
                    viewport={'width': 1280, 'height': 720}
                )
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] 无法启动 Edge 浏览器，尝试使用 Chromium: {e}")
                # 如果 Edge 不可用，回退到 Chromium
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=headless,
                    args=['--no-sandbox'],
                    viewport={'width': 1280, 'height': 720}
                )
            
            page = context.new_page()
            self.setup_request_handler(page)
            
            for idx, url in enumerate(urls, 1):
                try:
                    console.print(f"\n[bold]处理 [{idx}/{len(urls)}][/bold]: {url}")
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # 等待视频加载
                    console.print(f"[dim]等待视频加载（{wait_time}秒）...[/dim]")
                    page.wait_for_timeout(wait_time * 1000)
                    
                    # 尝试点击播放按钮（如果存在）
                    try:
                        play_button = page.locator('button[class*="play"], div[class*="play"]').first
                        if play_button.is_visible(timeout=2000):
                            play_button.click()
                            console.print("[dim]已点击播放按钮[/dim]")
                            page.wait_for_timeout(5000)
                    except:
                        pass
                    
                except Exception as e:
                    console.print(f"[red]✗[/red] 处理失败: {str(e)}")
                    continue
            
            context.close()
        
        return self.captured_urls
    
    def download_video(self, video_info: Dict[str, str], index: int) -> bool:
        """
        下载单个视频
        
        Args:
            video_info: 视频信息字典
            index: 视频序号
            
        Returns:
            下载是否成功
        """
        media_url = video_info['media_url']
        referer = video_info['referer']
        title = video_info['title']
        
        # 清理文件名，移除非法字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # 只使用标题作为文件名，不加序号前缀
        output_template = str(self.output_dir / f"{safe_title}.%(ext)s")
        
        console.print(f"\n[bold cyan]⬇️  下载视频:[/bold cyan] {title}")
        console.print(f"[dim]输出路径: {output_template}[/dim]")
        
        cmd = [
            "yt-dlp",
            "--referer", referer,
            "--concurrent-fragments", "5",
            "--progress",
            "-o", output_template,
            media_url
        ]
        
        try:
            result = subprocess.run(cmd, check=True)
            console.print(f"[green]✓[/green] 下载完成: {title}")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] 下载失败: {title}")
            console.print(f"[dim]错误信息: {e}[/dim]")
            return False
    
    def download_all(self) -> tuple[int, int]:
        """
        下载所有捕获的视频
        
        Returns:
            (成功数量, 失败数量)
        """
        if not self.captured_urls:
            console.print("[yellow]⚠[/yellow] 没有捕获到任何视频地址")
            return 0, 0
        
        console.print(f"\n[bold green]📥 开始批量下载 {len(self.captured_urls)} 个视频...[/bold green]")
        
        success_count = 0
        fail_count = 0
        
        for idx, video_info in enumerate(self.captured_urls, 1):
            if self.download_video(video_info, idx):
                success_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count
    
    def show_captured_videos(self):
        """显示捕获到的视频列表"""
        if not self.captured_urls:
            console.print("[yellow]⚠[/yellow] 没有捕获到任何视频")
            return
        
        table = Table(title="捕获到的视频列表", show_header=True, header_style="bold magenta")
        table.add_column("序号", style="dim", width=6)
        table.add_column("标题", style="cyan")
        table.add_column("页面URL", style="dim", overflow="fold")
        
        for idx, video in enumerate(self.captured_urls, 1):
            table.add_row(
                str(idx),
                video['title'],
                video['page_url']
            )
        
        console.print("\n")
        console.print(table)
    
    def save_captured_info(self, filename: str = "captured_videos.json"):
        """保存捕获的视频信息到JSON文件"""
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.captured_urls, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓[/green] 视频信息已保存到: {filepath.absolute()}")


def load_urls_from_file(filepath: str) -> List[str]:
    """从文件加载URL列表"""
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls


def main():
    """主函数"""
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold magenta]  小鹅通视频批量下载工具 (XET Video Downloader)[/bold magenta]")
    console.print("[bold magenta]  支持自动捕获 m3u8 地址并批量下载[/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")
    
    downloader = VideoDownloader()
    
    # 检查依赖
    if not downloader.check_dependencies():
        console.print("\n[red]请先安装必要的依赖，然后重新运行程序[/red]")
        sys.exit(1)
    
    # 获取URL列表
    console.print("\n[bold cyan]📝 请输入视频URL[/bold cyan]")
    console.print("选项:")
    console.print("  1. 手动输入URL（多个URL用逗号或换行分隔）")
    console.print("  2. 从文件读取URL列表")
    
    choice = Prompt.ask("请选择", choices=["1", "2"], default="1")
    
    urls = []
    if choice == "1":
        url_input = Prompt.ask("\n请输入URL")
        # 支持逗号或换行分隔
        urls = [u.strip() for u in re.split(r'[,\n]+', url_input) if u.strip()]
    else:
        filepath = Prompt.ask("请输入文件路径", default="urls.txt")
        try:
            urls = load_urls_from_file(filepath)
        except FileNotFoundError:
            console.print(f"[red]✗[/red] 文件不存在: {filepath}")
            sys.exit(1)
    
    if not urls:
        console.print("[red]✗[/red] 没有输入任何URL")
        sys.exit(1)
    
    console.print(f"[green]✓[/green] 已加载 {len(urls)} 个URL")
    
    # 询问是否使用无头模式
    headless = not Confirm.ask("\n是否显示浏览器窗口？（首次运行建议显示以完成登录）", default=True)
    
    # 询问等待时间
    if not headless:
        console.print("\n[cyan]💡 提示：首次登录需要扫码，建议设置较长等待时间（如30-60秒）[/cyan]")
    wait_time_str = Prompt.ask("每个页面等待时间（秒）", default="30" if not headless else "10")
    try:
        wait_time = int(wait_time_str)
    except ValueError:
        wait_time = 30 if not headless else 10
        console.print(f"[yellow]输入无效，使用默认值: {wait_time}秒[/yellow]")
    
    # 捕获视频地址
    captured = downloader.capture_video_urls(urls, headless=headless, wait_time=wait_time)
    
    if not captured:
        console.print("\n[yellow]⚠[/yellow] 未能捕获到任何视频地址")
        console.print("可能的原因:")
        console.print("  - 需要登录（请使用显示浏览器模式并手动登录）")
        console.print("  - 页面加载时间不足")
        console.print("  - URL格式不正确")
        sys.exit(1)
    
    # 显示捕获结果
    downloader.show_captured_videos()
    
    # 保存捕获信息
    if Confirm.ask("\n是否保存捕获的视频信息到JSON文件？", default=True):
        downloader.save_captured_info()
    
    # 询问是否开始下载
    if Confirm.ask("\n是否开始下载视频？", default=True):
        success, fail = downloader.download_all()
        
        # 显示下载结果
        console.print("\n" + "=" * 60)
        console.print(f"[bold green]下载完成！[/bold green]")
        console.print(f"  成功: [green]{success}[/green] 个")
        console.print(f"  失败: [red]{fail}[/red] 个")
        console.print(f"  输出目录: [cyan]{downloader.output_dir.absolute()}[/cyan]")
        console.print("=" * 60)
    else:
        console.print("\n[yellow]已取消下载操作[/yellow]")


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

