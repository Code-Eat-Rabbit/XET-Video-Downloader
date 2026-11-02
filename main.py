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

# ================================
# XET平台配置常量（根据用户文档分析）
# ================================
# XET CDN 域名（从用户文档中提取）
XET_CDN_DOMAINS = [
    "xiaoeknow.com",
    "xiaoe-tech.com",
    "v-vod-k.xiaoeknow.com",
    "encrypt-k-vod.xet.tech",  # 新增：真正的视频CDN
    "vod.xet.tech",
    "v-vod-k.xiaoeknow.com"
]

# XET上报域名（这些不应该被捕获）
XET_REPORT_DOMAINS = [
    "alivereport.xiaoeknow.com",
    "report.xiaoeknow.com",
    "log.xiaoeknow.com"
]

# 真正的视频文件扩展名（支持 .ts 和 .m3u8）
VIDEO_EXTENSIONS = [".ts", ".m3u8", ".mp4"]

# 签名参数变体（根据用户文档中的观察）
SIGNATURE_PARAMS = ["sign=", "t=", "ts=", "us=", "time=", "uuid="]

# 真正视频URL的关键字
REAL_VIDEO_KEYWORDS = ["v.f", "v.f146750", "v.f421220", "/vod/", "/video/"]


class VideoDownloader:
    """视频下载器主类"""

    def __init__(self, user_data_dir: str = "./browser_session", output_dir: str = "./downloads",
                 debug_mode: bool = False, capture_ts: bool = True, cdn_domains: Optional[List[str]] = None):
        self.user_data_dir = Path(user_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.captured_urls: List[Dict[str, str]] = []
        self.debug_mode = debug_mode
        self.capture_ts = capture_ts
        self.cdn_domains = cdn_domains if cdn_domains else XET_CDN_DOMAINS
        self.request_stats = {"total": 0, "filtered": 0, "captured": 0}

    def enable_debug_logging(self):
        """启用详细调试日志"""
        console.print("[yellow]🔧 启用调试模式[/yellow]")
        console.print("[dim]将显示所有网络请求和过滤过程[/dim]")
        self.debug_mode = True

    def show_request_stats(self):
        """显示请求统计信息"""
        total = len(self.captured_urls)
        ts_count = sum(1 for v in self.captured_urls if v.get('file_type') == 'ts')
        m3u8_count = sum(1 for v in self.captured_urls if v.get('file_type') == 'm3u8')
        mp4_count = sum(1 for v in self.captured_urls if v.get('file_type') == 'mp4')

        console.print(f"[cyan]📊 请求统计:[/cyan]")
        console.print(f"  总捕获数: {total}")
        console.print(f"  .ts 文件: {ts_count}")
        console.print(f"  .m3u8 文件: {m3u8_count}")
        console.print(f"  .mp4 文件: {mp4_count}")
        console.print(f"  过滤的请求: {self.request_stats.get('filtered', 0)}")

        if total == 0 and not self.debug_mode:
            console.print("[yellow]💡 提示: 建议启用调试模式查看网络请求[/yellow]")
        
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

    def _extract_real_m3u8_url(self, url: str) -> Optional[str]:
        """
        从上报URL中提取真正的m3u8 URL

        参数:
            url: 可能是上报接口的URL，包含编码的play_url参数

        返回:
            真正的视频m3u8 URL，如果不是上报接口则返回原URL
        """
        import urllib.parse

        # 如果不是上报接口，直接返回
        if not self._is_report_url(url):
            return url

        if self.debug_mode:
            console.print(f"[dim]尝试从上报接口提取真实m3u8: {url[:60]}...[/dim]")

        try:
            # 解析URL
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # 尝试多个可能的参数名
            for param_key in ['params%5Bplay_url%5D', 'params[play_url]', 'play_url', 'url']:
                if param_key in params:
                    # 获取第一个值并解码
                    encoded_url = params[param_key][0]
                    real_url = urllib.parse.unquote(encoded_url)

                    if self.debug_mode:
                        console.print(f"[dim]提取成功: {real_url[:60]}...[/dim]")
                    return real_url

            if self.debug_mode:
                console.print(f"[dim]未找到play_url参数: {url[:60]}...[/dim]")
            return None

        except Exception as e:
            if self.debug_mode:
                console.print(f"[dim]提取失败: {e}[/dim]")
            return None

    def _is_report_url(self, url: str) -> bool:
        """检查URL是否是上报接口"""
        for domain in XET_REPORT_DOMAINS:
            if domain in url:
                return True
        return False

    def _is_valid_video_url(self, url: str) -> bool:
        """检查URL是否是有效的视频URL（不是上报接口，且包含关键特征）"""
        # 排除上报接口
        if self._is_report_url(url):
            return False

        # 检查是否包含视频特征
        for keyword in REAL_VIDEO_KEYWORDS:
            if keyword in url:
                return True

        # 检查是否包含签名参数（.ts文件可能没有签名）
        if self._has_signature_params(url):
            return True

        # .ts文件即使没有签名也应该被捕获
        if ".ts" in url:
            return True

        return False

    def _is_xet_cdn_url(self, url: str) -> bool:
        """检查 URL 是否属于 XET CDN 域名"""
        for domain in self.cdn_domains:
            if domain in url:
                return True
        return False

    def _is_video_file_url(self, url: str) -> bool:
        """检查 URL 是否为视频文件"""
        if self.capture_ts and ".ts" in url:
            return True
        if ".m3u8" in url:
            return True
        if ".mp4" in url:
            return True
        return False

    def _has_signature_params(self, url: str) -> bool:
        """检查 URL 是否包含签名参数"""
        for param in SIGNATURE_PARAMS:
            if param in url:
                return True
        return False

    def _extract_quality_info(self, url: str) -> str:
        """从 URL 提取质量信息"""
        import re
        match = re.search(r'v\.(f\d+)', url)
        if match:
            return match.group(1)
        return "unknown"

    def setup_request_handler(self, page: Page):
        """设置增强的请求拦截处理器，支持 .ts 和 .m3u8"""
        def handle_request(request):
            original_url = request.url  # 保存原始URL
            url = original_url  # 当前处理的URL
            self.request_stats["total"] += 1

            # 调试模式：记录所有请求
            if self.debug_mode:
                console.print(f"[dim][{self.request_stats['total']}] 请求: {url[:80]}...[/dim]")

            # 检查是否为 XET URL（CDN 或 上报接口）
            is_xet_url = self._is_xet_cdn_url(url) or self._is_report_url(url)
            if not is_xet_url:
                if self.debug_mode:
                    console.print(f"  [dim]过滤: 非XET域名[/dim]")
                self.request_stats["filtered"] += 1
                return

            # 尝试提取真正的 m3u8 URL（可能从上报表单中提取）
            real_url = self._extract_real_m3u8_url(url)

            if real_url and real_url != url:
                # 成功提取到真正的视频URL
                if self.debug_mode:
                    console.print(f"  [dim]提取到真实URL: {real_url[:60]}...[/dim]")

                # 使用真实URL进行后续检查
                url = real_url
            elif real_url is None:
                # 是上报接口但没有提取到play_url
                if self.debug_mode:
                    console.print(f"  [dim]过滤: 上报接口无play_url[/dim]")
                self.request_stats["filtered"] += 1
                return

            # 检查是否为真正的视频文件URL（使用完整的验证逻辑）
            if not self._is_valid_video_url(url):
                if self.debug_mode:
                    console.print(f"  [dim]过滤: 无效的视频URL[/dim]")
                self.request_stats["filtered"] += 1
                return

            # 检查是否包含签名参数（.ts文件可以没有签名）
            has_signature = self._has_signature_params(url)
            if not has_signature and not ".ts" in url:
                if self.debug_mode:
                    console.print(f"  [dim]过滤: 没有签名参数[/dim]")
                self.request_stats["filtered"] += 1
                return

            # 提取质量信息
            quality_code = self._extract_quality_info(url)

            # 确定文件类型
            file_type = "unknown"
            if ".ts" in url:
                file_type = "ts"
            elif ".m3u8" in url:
                file_type = "m3u8"
            elif ".mp4" in url:
                file_type = "mp4"

            # 避免重复添加
            if not any(item['media_url'] == url for item in self.captured_urls):
                capture_info = {
                    'media_url': url,
                    'referer': request.headers.get("referer", ""),
                    'page_url': page.url,
                    'title': page.title() or "未知标题",
                    'quality': quality_code,
                    'file_type': file_type
                }

                # 如果是上报接口提取而来的，保存原始URL用于调试
                if real_url and real_url != original_url:
                    capture_info['original_report_url'] = original_url

                self.captured_urls.append(capture_info)

                self.request_stats["captured"] += 1
                console.print(f"[green]✓[/green] 捕获到视频: [cyan]{page.title()}[/cyan] ({file_type}, 质量: {quality_code})")

                if self.debug_mode:
                    console.print(f"  [dim]捕获详情: {url[:60]}...[/dim]")
            else:
                if self.debug_mode:
                    console.print(f"  [dim]跳过: 重复URL[/dim]")

        page.on("request", handle_request)
    
    def capture_video_urls(self, urls: List[str], headless: bool = False,
                       wait_time: int = 10, debug_mode: bool = False) -> List[Dict[str, str]]:
        """
        捕获视频地址

        Args:
            urls: 视频页面URL列表
            headless: 是否使用无头模式
            wait_time: 每个页面等待时间（秒），首次登录建议30秒以上
            debug_mode: 是否启用调试模式，显示所有网络请求

        Returns:
            捕获到的视频信息列表
        """
        if debug_mode:
            console.print("[yellow]🔧 调试模式已启用[/yellow]")
            self.debug_mode = True
        console.print(f"\n[bold cyan]🎬 开始捕获视频地址...[/bold cyan]")
        console.print(f"[dim]待处理URL数量: {len(urls)}[/dim]")
        
        with sync_playwright() as p:
            # 使用持久化上下文保存登录状态，优先使用 Google Chrome
            # 如果想用 Edge，改为 channel='msedge'; 用 Firefox 改为 p.firefox
            try:
                # 尝试使用系统安装的 Google Chrome 浏览器
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=headless,
                    channel='chrome',  # 使用 Google Chrome
                    args=['--no-sandbox'],
                    viewport={'width': 1280, 'height': 720}
                )
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] 无法启动 Chrome 浏览器，尝试使用 Edge: {e}")
                try:
                    # 如果 Chrome 不可用，尝试 Edge
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(self.user_data_dir),
                        headless=headless,
                        channel='msedge',  # 使用 Microsoft Edge
                        args=['--no-sandbox'],
                        viewport={'width': 1280, 'height': 720}
                    )
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] 无法启动 Edge 浏览器，尝试使用系统浏览器: {e}")
                    # 回退到默认浏览器
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
            "--concurrent-fragments", "16",
            "--progress",
            "--merge-output-format", "mp4",  # 强制合并为mp4格式
            "--windows-filenames",  # 使用Windows安全文件名
            "--no-part",  # 不下载额外的文件
            "--retries", "10",  # 重试次数
            "--fragment-retries", "10",  # 片段重试次数
            "--abort-on-unavailable-fragment",  # 缺失片段时中止
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
            # 如果启用了调试模式，显示请求统计
            if self.debug_mode:
                self.show_request_stats()
            return

        # 如果启用了调试模式，先显示请求统计
        if self.debug_mode:
            self.show_request_stats()

        table = Table(title="捕获到的视频列表", show_header=True, header_style="bold magenta")
        table.add_column("序号", style="dim", width=6)
        table.add_column("标题", style="cyan")
        table.add_column("类型", style="yellow", width=8)
        table.add_column("质量", style="green", width=10)
        table.add_column("页面URL", style="dim", overflow="fold")

        for idx, video in enumerate(self.captured_urls, 1):
            file_type = video.get('file_type', 'unknown')
            quality = video.get('quality', 'unknown')
            table.add_row(
                str(idx),
                video['title'],
                file_type,
                quality,
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

    # 询问是否启用调试模式
    debug_mode = Confirm.ask("\n是否启用调试模式？（详细显示网络请求）", default=False)
    if debug_mode:
        downloader.enable_debug_logging()

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
    captured = downloader.capture_video_urls(urls, headless=headless, wait_time=wait_time, debug_mode=debug_mode)

    if not captured:
        console.print("\n[yellow]⚠[/yellow] 未能捕获到任何视频地址")

        if debug_mode:
            console.print("[yellow]调试模式下的详细分析:[/yellow]")
            console.print("  - 请检查上面显示的请求日志")
            console.print("  - 确认是否有XET CDN域名的请求")
            console.print("  - 确认是否有 .ts 或 .m3u8 文件的请求")
            console.print("  - 确认请求是否包含签名参数")
        else:
            console.print("可能的原因:")
            console.print("  - 需要登录（请使用显示浏览器模式并手动登录）")
            console.print("  - 页面加载时间不足")
            console.print("  - URL格式不正确")
            console.print("  - 建议启用调试模式查看更多信息")

        # 即使在捕获失败时也显示请求统计
        if debug_mode or downloader.debug_mode:
            downloader.show_request_stats()

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
