#!/usr/bin/env python3
"""
并行视频下载器
支持同时下载多个视频，大幅提高效率
"""

import json
import subprocess
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from typing import List, Dict, Tuple
import threading

console = Console()

class ParallelVideoDownloader:
    """并行视频下载器"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.downloads_dir = Path("./downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()  # 用于线程安全的控制台输出

    def _log(self, message: str, video_idx: int = 0, prefix: str = "📥"):
        """线程安全的日志输出"""
        with self.lock:
            if video_idx > 0:
                console.print(f"{prefix}[{video_idx:02d}] {message}")
            else:
                console.print(f"{prefix} {message}")

    def download_single_video(self, video_info: Dict, index: int) -> bool:
        """下载单个视频"""
        try:
            media_url = video_info['media_url']
            referer = video_info['referer']
            title = video_info['title']

            # 清理文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            output_template = str(self.downloads_dir / f"{safe_title}.%(ext)s")

            self._log(f"开始下载: {title}", index, "📥")

            # 优化的yt-dlp命令
            cmd = [
                "yt-dlp",
                "--referer", referer,
                "--concurrent-fragments", "16",  # 高并发片段
                "--merge-output-format", "mp4",
                "--windows-filenames",
                "--no-part",
                "--retries", "5",
                "--fragment-retries", "5",
                "--progress",
                "--no-warnings",  # 减少警告信息
                "--quiet",  # 更少输出
                "-o", output_template,
                media_url
            ]

            # 运行下载命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=3600  # 1小时超时
            )

            self._log(f"下载完成: {title}", index, "✅")
            return True

        except subprocess.TimeoutExpired:
            self._log(f"超时: {title}", index, "⏰")
            return False
        except subprocess.CalledProcessError as e:
            self._log(f"失败: {title} (code: {e.returncode})", index, "❌")
            return False
        except Exception as e:
            self._log(f"错误: {title} - {str(e)[:50]}", index, "⚠️")
            return False

    def download_all_parallel(self, videos: List[Dict], max_workers: int = None) -> Tuple[int, int]:
        """并行下载所有视频"""
        if max_workers is None:
            max_workers = self.max_workers

        console.print(f"\n[bold cyan]🚀 开始并行下载 {len(videos)} 个视频[/bold cyan]")
        console.print(f"[dim]工作线程数: {max_workers}[/dim]")
        console.print("[dim]按 Ctrl+C 停止所有下载[/dim]")

        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_idx = {
                executor.submit(self.download_single_video, video, idx): idx
                for idx, video in enumerate(videos, 1)
            }

            # 显示进度
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]下载进度...", total=len(videos))

                # 处理完成的任务
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        self._log(f"任务异常: {e}", idx, "💥")
                        fail_count += 1

                    progress.update(task, advance=1)

        return success_count, fail_count

    def show_download_summary(self, videos: List[Dict], success_count: int, fail_count: int):
        """显示下载总结"""
        console.print(f"\n[bold magenta]📊 下载结果总结[/bold magenta]")
        console.print("=" * 60)

        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("状态", style="dim", width=8)
        table.add_column("数量", justify="right", style="cyan")
        table.add_column("百分比", justify="right", style="green")

        total = success_count + fail_count
        table.add_row("✅ 成功", str(success_count), f"{(success_count/total*100):.1f}%")
        table.add_row("❌ 失败", str(fail_count), f"{(fail_count/total*100):.1f}%")
        table.add_row("📊 总计", str(total), "100%")

        console.print(table)

        # 显示已下载的视频列表
        console.print(f"\n[bold cyan]📂 已下载文件 (downloads/目录):[/bold cyan]")
        mp4_files = list(self.downloads_dir.glob("*.mp4"))
        for file in sorted(mp4_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            size_mb = file.stat().st_size / (1024 * 1024)
            time_str = time.strftime("%H:%M:%S", time.localtime(file.stat().st_mtime))
            console.print(f"  • {file.name[:40]}... ({size_mb:.1f} MB) [{time_str}]")

        if len(mp4_files) > 10:
            console.print(f"  ... 以及 {len(mp4_files) - 10} 个其他文件")

def load_video_info(json_file: str = "captured_videos.json") -> List[Dict]:
    """加载视频信息"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        console.print(f"[green]✓[/green] 从 {json_file} 加载 {len(videos)} 个视频")
        return videos
    except Exception as e:
        console.print(f"[red]✗[/red] 读取JSON失败: {e}")
        return []

def main():
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold magenta]  并行视频下载器 - 同时下载多个视频[/bold magenta]")
    console.print("[bold magenta]  显著提高批量下载效率[/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")

    # 加载视频信息
    videos = load_video_info("captured_videos.json")
    if not videos:
        console.print("[yellow]⚠[/yellow] 没有找到视频信息")
        return

    # 显示视频列表
    console.print(f"[bold cyan]📋 可下载的视频 ({len(videos)}个):[/bold cyan]")
    for i, video in enumerate(videos[:10], 1):
        title = video.get('title', '未知标题')
        file_type = video.get('file_type', 'unknown')
        quality = video.get('quality', 'unknown')
        console.print(f"  {i:2d}. {title}")

    if len(videos) > 10:
        console.print(f"  ... 以及 {len(videos) - 10} 个其他视频")

    # 询问并行数
    from rich.prompt import IntPrompt
    max_workers = IntPrompt.ask(
        f"\n[bold]输入并行下载数 (1-{len(videos)})[/bold]",
        default=min(5, len(videos)),
        choices=[str(i) for i in range(1, len(videos) + 1)]
    )

    # 选择要下载的视频
    from rich.prompt import Prompt
    choice = Prompt.ask(
        "\n[bold]下载哪些视频？[/bold]",
        choices=["a", "s"],
        default="a"
    )

    if choice.lower() == "s":
        # 选择特定视频
        selection = Prompt.ask(
            "输入要下载的视频序号 (用逗号分隔，如: 1,3,5)",
            default="1"
        )
        selected_indices = [int(idx.strip()) - 1 for idx in selection.split(",") if idx.strip().isdigit()]
        selected_videos = [videos[i] for i in selected_indices if 0 <= i < len(videos)]
    else:
        # 下载全部
        selected_videos = videos

    console.print(f"\n[bold green]🎯 准备下载 {len(selected_videos)} 个视频，并行度 {max_workers}[/bold green]")

    # 创建下载器并开始下载
    downloader = ParallelVideoDownloader(max_workers=max_workers)
    start_time = time.time()

    try:
        success, fail = downloader.download_all_parallel(selected_videos, max_workers)

        duration = time.time() - start_time
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)

        console.print(f"\n[bold green]⏱️ 总耗时: {hours}h {minutes}m {seconds}s[/bold green]")
        downloader.show_download_summary(selected_videos, success, fail)

    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 用户中断，正在清理...[/yellow]")
        # 可以添加清理逻辑
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 用户中断操作[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")