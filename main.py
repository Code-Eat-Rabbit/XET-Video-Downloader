#!/usr/bin/env python3
"""
全景路演视频批量下载工具
使用 Playwright 捕获视频地址，并通过 yt-dlp 下载视频
支持直接 MP4 链接和 M3U8 流媒体
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
    
    def __init__(self, user_data_dir: str = "./browser_session", output_dir: str = "./downloads", audio_only: bool = True):
        self.user_data_dir = Path(user_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.captured_urls: List[Dict[str, str]] = []
        self.audio_only = audio_only  # 是否只下载音频
        
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
    
    def setup_request_handler(self, page: Page, debug: bool = False):
        """设置请求拦截处理器"""
        def handle_request(request):
            url = request.url
            headers = request.headers
            resource_type = request.resource_type
            
            # 调试模式：显示所有视频相关请求
            if debug and resource_type in ['media', 'video', 'xhr', 'fetch']:
                console.print(f"[dim]DEBUG - {resource_type}: {url[:100]}...[/dim]")
            
            # 匹配 M3U8 流媒体链接
            if ".m3u8" in url:
                referer = headers.get("referer", "")
                page_url = page.url
                
                # 避免重复添加
                if not any(item['media_url'] == url for item in self.captured_urls):
                    self.captured_urls.append({
                        'media_url': url,
                        'referer': referer,
                        'page_url': page_url,
                        'title': page.title() or "未知标题",
                        'type': 'm3u8'
                    })
                    console.print(f"[green]✓[/green] 捕获到 M3U8 视频: [cyan]{page.title()}[/cyan]")
            
            # 匹配直接的 MP4/视频文件链接（全景路演等网站）
            elif (url.endswith(('.mp4', '.m4v', '.mov', '.avi', '.mkv', '.flv', '.webm')) or \
                  ('.mp4' in url and headers.get('sec-fetch-dest') == 'video') or \
                  resource_type == 'media'):
                
                # 过滤掉太小的文件（可能是广告或缩略图）
                # 只捕获可能是完整视频的链接
                if any(ext in url.lower() for ext in ['.mp4', '.m4v', '.mov', '.avi', '.mkv', '.flv', '.webm']):
                    referer = headers.get("referer", "")
                    origin = headers.get("origin", "")
                    page_url = page.url
                    user_agent = headers.get("user-agent", "")
                    
                    # 避免重复添加
                    if not any(item['media_url'] == url for item in self.captured_urls):
                        self.captured_urls.append({
                            'media_url': url,
                            'referer': referer,
                            'origin': origin,
                            'page_url': page_url,
                            'title': page.title() or "未知标题",
                            'user_agent': user_agent,
                            'type': 'direct'
                        })
                        console.print(f"[green]✓[/green] 捕获到直接视频链接: [cyan]{page.title()}[/cyan]")
                        if debug:
                            console.print(f"[dim]  URL: {url}[/dim]")
        
        page.on("request", handle_request)
    
    def capture_video_urls(self, urls: List[str], headless: bool = False, wait_time: int = 10, debug: bool = False) -> List[Dict[str, str]]:
        """
        捕获视频地址
        
        Args:
            urls: 视频页面URL列表
            headless: 是否使用无头模式
            wait_time: 每个页面等待时间（秒），首次登录建议30秒以上
            debug: 是否开启调试模式，显示所有媒体请求
            
        Returns:
            捕获到的视频信息列表
        """
        console.print(f"\n[bold cyan]🎬 开始捕获视频地址...[/bold cyan]")
        console.print(f"[dim]待处理URL数量: {len(urls)}[/dim]")
        if debug:
            console.print(f"[yellow]调试模式已开启[/yellow]")
        
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
            self.setup_request_handler(page, debug=debug)
            
            for idx, url in enumerate(urls, 1):
                try:
                    console.print(f"\n[bold]处理 [{idx}/{len(urls)}][/bold]: {url}")
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # 等待页面初始加载
                    console.print(f"[dim]等待页面加载...[/dim]")
                    page.wait_for_timeout(3000)
                    
                    # 尝试查找并点击视频播放按钮
                    clicked = False
                    try:
                        # 尝试多种播放按钮选择器（优先匹配全景路演的播放按钮）
                        play_selectors = [
                            'i.play',  # 全景路演播放按钮: <i class="play"></i>
                            '.videoBox i.play',  # 全景路演视频框中的播放按钮
                            '.videoBox .play',  # 备用选择器
                            'video',  # HTML5 video 标签
                            'button[class*="play"]',
                            'div[class*="play"]',
                            'button[aria-label*="播放"]',
                            'button[aria-label*="play"]',
                            '.video-play-button',
                            '.play-button',
                            '[class*="PlayButton"]',
                        ]
                        
                        for selector in play_selectors:
                            try:
                                element = page.locator(selector).first
                                if element.is_visible(timeout=1000):
                                    element.click()
                                    console.print(f"[dim]已点击播放元素: {selector}[/dim]")
                                    clicked = True
                                    break
                            except:
                                continue
                        
                        if clicked:
                            # 点击后等待视频请求
                            console.print(f"[dim]等待视频请求（{wait_time}秒）...[/dim]")
                            page.wait_for_timeout(wait_time * 1000)
                        else:
                            # 没有找到播放按钮，可能视频自动加载
                            console.print(f"[dim]未找到播放按钮，等待自动加载（{wait_time}秒）...[/dim]")
                            page.wait_for_timeout(wait_time * 1000)
                    
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] 播放按钮处理异常: {str(e)}")
                        # 继续等待，可能视频会自动加载
                        page.wait_for_timeout(wait_time * 1000)
                    
                except Exception as e:
                    console.print(f"[red]✗[/red] 处理失败: {str(e)}")
                    continue
            
            context.close()
        
        return self.captured_urls
    
    def download_video(self, video_info: Dict[str, str], index: int) -> bool:
        """
        下载单个视频或音频
        
        Args:
            video_info: 视频信息字典
            index: 视频序号
            
        Returns:
            下载是否成功
        """
        media_url = video_info['media_url']
        referer = video_info.get('referer', '')
        title = video_info['title']
        video_type = video_info.get('type', 'm3u8')
        
        # 清理文件名，移除非法字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        
        if self.audio_only:
            console.print(f"\n[bold cyan]🎵 下载音频:[/bold cyan] {title}")
            console.print(f"[dim]类型: {video_type}[/dim]")
            console.print(f"[dim]模式: 管道处理（边下载边转换）[/dim]")
            
            # 使用管道方案：yt-dlp 输出到 stdout，直接传给 ffmpeg
            return self._download_audio_with_pipe(video_info, safe_title)
        else:
            console.print(f"\n[bold cyan]⬇️  下载视频:[/bold cyan] {title}")
            output_template = str(self.output_dir / f"{safe_title}.%(ext)s")
            console.print(f"[dim]类型: {video_type}[/dim]")
            console.print(f"[dim]模式: 完整视频[/dim]")
            console.print(f"[dim]输出路径: {output_template}[/dim]")
            
            # 根据视频类型构建下载命令（视频模式）
            return self._download_video_file(video_info, output_template, video_type)
    
    def _download_audio_with_pipe(self, video_info: Dict[str, str], safe_title: str) -> bool:
        """
        使用 yt-dlp + ffmpeg 下载器下载音频
        结合最佳音频流选择和 ffmpeg 的高效处理
        
        Args:
            video_info: 视频信息字典
            safe_title: 清理后的文件名
            
        Returns:
            下载是否成功
        """
        media_url = video_info['media_url']
        referer = video_info.get('referer', '')
        user_agent = video_info.get('user_agent', '')
        origin = video_info.get('origin', '')
        
        # 输出文件路径（不带扩展名，让 yt-dlp 自动添加）
        output_template = str(self.output_dir / f"{safe_title}")
        console.print(f"[dim]输出路径: {output_template}.mp3[/dim]")
        
        # 构建 yt-dlp 命令
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",          # 优先音频流，没有则用最佳质量
            "--extract-audio",                # 提取音频（等同于 -x）
            "--audio-format", "mp3",         # 输出 MP3 格式
            "--audio-quality", "128K",       # 固定比特率 128kbps
            "--downloader", "ffmpeg",        # 使用 ffmpeg 作为下载器
            "--downloader-args", "ffmpeg:-stats",  # ffmpeg 显示统计信息
            "-o", f"{output_template}.%(ext)s",    # 输出模板
        ]
        
        # 添加 referer
        if referer:
            cmd.extend(["--referer", referer])
        
        # 添加 user-agent
        if user_agent:
            cmd.extend(["--user-agent", user_agent])
        
        # 添加 origin
        if origin:
            cmd.extend(["--add-header", f"Origin: {origin}"])
        
        # 添加 URL
        cmd.append(media_url)
        
        console.print(f"[dim]执行命令: yt-dlp -f bestaudio/best --extract-audio ...[/dim]")
        console.print(f"[yellow]⏳ 下载中，请查看进度信息...[/yellow]")
        
        try:
            # 执行命令，实时显示输出
            result = subprocess.run(
                cmd,
                check=True,
                text=True,
                capture_output=False  # 让输出直接显示到终端
            )
            
            # 检查输出文件
            output_file = self.output_dir / f"{safe_title}.mp3"
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                console.print(f"[green]✓[/green] 音频下载完成: {safe_title} ({file_size:.2f} MB)")
                return True
            else:
                console.print(f"[red]✗[/red] 音频文件未生成: {safe_title}")
                return False
                
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] 下载失败: {safe_title}")
            console.print(f"[dim]错误代码: {e.returncode}[/dim]")
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] 处理错误: {str(e)}")
            return False
    
    def _download_video_file(self, video_info: Dict[str, str], output_template: str, video_type: str) -> bool:
        """
        下载完整视频文件（非音频模式）
        
        Args:
            video_info: 视频信息字典
            output_template: 输出路径模板
            video_type: 视频类型
            
        Returns:
            下载是否成功
        """
        media_url = video_info['media_url']
        referer = video_info.get('referer', '')
        title = video_info['title']
        
        # 根据视频类型构建不同的下载命令
        if video_type == 'direct':
            # 直接下载 MP4 等视频文件
            cmd = ["yt-dlp"]
            
            # 如果只下载音频
            # 对于直接视频链接，不使用 -f bestaudio（因为没有分离的音频流）
            # 直接下载后提取音频
            if self.audio_only:
                cmd.extend([
                    "-x",  # 提取音频
                    "--audio-format", "mp3",  # 转换为 mp3
                    "--audio-quality", "0",  # 最佳音质
                ])
            
            # 添加其他参数
            cmd.extend([
                "--concurrent-fragments", "5",
                "--progress",
                "-o", output_template,
            ])
            
            # 添加 referer（如果有）
            if referer:
                cmd.extend(["--referer", referer])
            
            # 添加 user-agent（如果有）
            if video_info.get('user_agent'):
                cmd.extend(["--user-agent", video_info['user_agent']])
            
            # 添加 origin（如果有）
            if video_info.get('origin'):
                cmd.extend(["--add-header", f"Origin: {video_info['origin']}"])
            
            cmd.append(media_url)
        else:
            # M3U8 流媒体下载
            cmd = ["yt-dlp"]
            
            # 如果只下载音频
            # M3U8 流媒体可能有分离的音频流，尝试使用 bestaudio/best 回退
            if self.audio_only:
                cmd.extend([
                    "-f", "bestaudio/best",  # 优先音频流，没有则回退到最佳质量
                    "-x",  # 提取音频
                    "--audio-format", "mp3",  # 转换为 mp3
                    "--audio-quality", "0",  # 最佳音质
                ])
            
            # 添加其他参数
            cmd.extend([
                "--referer", referer,
                "--concurrent-fragments", "5",
                "--progress",
                "-o", output_template,
            ])
            
            cmd.append(media_url)
        
        # 显示完整命令（用于调试）
        console.print(f"[dim]执行命令: {' '.join(cmd[:5])}...[/dim]")
        
        try:
            result = subprocess.run(cmd, check=True)
            if self.audio_only:
                console.print(f"[green]✓[/green] 音频下载完成: {title}")
            else:
                console.print(f"[green]✓[/green] 视频下载完成: {title}")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] 下载失败: {title}")
            console.print(f"[dim]错误信息: {e}[/dim]")
            return False
    
    def download_all(self) -> tuple[int, int]:
        """
        下载所有捕获的视频或音频
        
        Returns:
            (成功数量, 失败数量)
        """
        if not self.captured_urls:
            console.print("[yellow]⚠[/yellow] 没有捕获到任何视频地址")
            return 0, 0
        
        if self.audio_only:
            console.print(f"\n[bold green]🎵 开始批量下载 {len(self.captured_urls)} 个音频...[/bold green]")
        else:
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
        table.add_column("类型", style="yellow", width=8)
        table.add_column("页面URL", style="dim", overflow="fold")
        
        for idx, video in enumerate(self.captured_urls, 1):
            video_type = video.get('type', 'm3u8')
            table.add_row(
                str(idx),
                video['title'],
                video_type,
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
    console.print("[bold magenta]  全景路演音频批量下载工具[/bold magenta]")
    console.print("[bold magenta]  支持自动捕获视频地址并提取音频[/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")
    
    # 询问是否只下载音频
    audio_only = Confirm.ask("是否只下载音频（MP3格式）？", default=True)
    
    downloader = VideoDownloader(audio_only=audio_only)
    
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
    headless = not Confirm.ask("\n是否显示浏览器窗口？（建议显示以观察播放按钮点击）", default=True)
    
    # 询问等待时间
    if not headless:
        console.print("\n[cyan]💡 提示：等待时间用于视频加载和点击播放按钮（建议15-30秒）[/cyan]")
    wait_time_str = Prompt.ask("每个页面等待时间（秒）", default="20" if not headless else "15")
    try:
        wait_time = int(wait_time_str)
    except ValueError:
        wait_time = 30 if not headless else 10
        console.print(f"[yellow]输入无效，使用默认值: {wait_time}秒[/yellow]")
    
    # 询问是否开启调试模式
    debug = Confirm.ask("\n是否开启调试模式？（显示所有媒体请求，帮助排查问题）", default=False)
    
    # 捕获视频地址
    captured = downloader.capture_video_urls(urls, headless=headless, wait_time=wait_time, debug=debug)
    
    if not captured:
        console.print("\n[yellow]⚠[/yellow] 未能捕获到任何视频地址")
        console.print("可能的原因:")
        console.print("  - 播放按钮未被点击（请使用显示浏览器模式手动点击）")
        console.print("  - 页面加载时间不足（尝试增加等待时间）")
        console.print("  - URL格式不正确")
        console.print("  - 开启调试模式查看详细请求信息")
        sys.exit(1)
    
    # 显示捕获结果
    downloader.show_captured_videos()
    
    # 保存捕获信息
    if Confirm.ask("\n是否保存捕获的视频信息到JSON文件？", default=True):
        downloader.save_captured_info()
    
    # 询问是否开始下载
    download_prompt = "是否开始下载音频？" if audio_only else "是否开始下载视频？"
    if Confirm.ask(f"\n{download_prompt}", default=True):
        success, fail = downloader.download_all()
        
        # 显示下载结果
        console.print("\n" + "=" * 60)
        console.print(f"[bold green]下载完成！[/bold green]")
        console.print(f"  成功: [green]{success}[/green] 个")
        console.print(f"  失败: [red]{fail}[/red] 个")
        console.print(f"  输出目录: [cyan]{downloader.output_dir.absolute()}[/cyan]")
        if audio_only:
            console.print(f"  格式: [yellow]MP3[/yellow]")
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

