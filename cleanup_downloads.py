#!/usr/bin/env python3
"""
清理下载目录并修复视频文件
"""

import os
import shutil
import json
from pathlib import Path
import subprocess
from rich.console import Console

console = Console()

def cleanup_downloads(download_dir: str = "./downloads"):
    """清理下载目录的片段文件"""
    download_path = Path(download_dir)

    if not download_path.exists():
        console.print(f"[yellow]⚠[/yellow] 下载目录不存在: {download_dir}")
        return

    console.print(f"[bold cyan]🔧 清理下载目录: {download_dir}[/bold cyan]")

    # 查找所有片段文件
    part_files = list(download_path.glob("*.part*"))

    console.print(f"[dim]找到 {len(part_files)} 个片段文件[/dim]")

    if not part_files:
        console.print("[green]✓[/green] 没有片段文件需要清理")
        return

    # 统计文件大小
    total_size = sum(f.stat().st_size for f in part_files if f.is_file())
    total_size_mb = total_size / (1024 * 1024)

    console.print(f"[yellow]⚠[/yellow] 发现 {len(part_files)} 个片段文件，总计 {total_size_mb:.2f} MB")

    # 询问用户确认
    console.print("\n[bold red]警告: 这将删除所有片段文件![/bold red]")
    console.print("保留的文件:")

    # 显示可能的视频文件
    video_files = list(download_path.glob("*.mp4")) + list(download_path.glob("*.mkv")) + list(download_path.glob("*.webm"))
    for vf in video_files:
        size_mb = vf.stat().st_size / (1024 * 1024)
        console.print(f"  [green]✓[/green] {vf.name} ({size_mb:.2f} MB)")

    from rich.prompt import Confirm
    if Confirm.ask("\n是否删除所有片段文件？", default=False):
        # 删除片段文件
        for part_file in part_files:
            try:
                part_file.unlink()
                console.print(f"  [dim]删除: {part_file.name}[/dim]")
            except Exception as e:
                console.print(f"  [red]✗[/red] 删除失败 {part_file.name}: {e}")

        console.print(f"\n[green]✓[/green] 清理完成，删除 {len(part_files)} 个文件")
    else:
        console.print("[yellow]⚠[/yellow] 取消清理")

def get_video_info_from_json(json_file: str = "captured_videos.json"):
    """从JSON文件获取视频信息"""
    json_path = Path(json_file)

    if not json_path.exists():
        console.print(f"[red]✗[/red] JSON文件不存在: {json_file}")
        return []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)

        console.print(f"[green]✓[/green] 从 {json_file} 加载 {len(videos)} 个视频信息")
        return videos
    except Exception as e:
        console.print(f"[red]✗[/red] 读取JSON失败: {e}")
        return []

def redownload_video(video_info, download_dir: str = "./downloads"):
    """重新下载视频（使用更新的参数）"""
    media_url = video_info['media_url']
    referer = video_info['referer']
    title = video_info['title']

    import re
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    output_template = str(Path(download_dir) / f"{safe_title}.%(ext)s")

    console.print(f"\n[bold cyan]⬇️  重新下载视频:[/bold cyan] {title}")
    console.print(f"[dim]URL: {media_url[:60]}...[/dim]")

    # 优化的yt-dlp命令
    cmd = [
        "yt-dlp",
        "--referer", referer,
        "--concurrent-fragments", "8",  # 增加并发
        "--merge-output-format", "mp4",
        "--windows-filenames",
        "--no-part",
        "--retries", "10",
        "--fragment-retries", "10",
        "--abort-on-unavailable-fragment",
        "--progress",
        "--newline",  # 逐行输出进度
        "-o", output_template,
        media_url
    ]

    try:
        console.print(f"[dim]命令: {' '.join(cmd[:5])}... {' '.join(cmd[-3:])}[/dim]")

        # 运行命令并实时显示进度
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # 读取并显示输出
        for line in process.stdout:
            # 过滤进度信息
            if any(keyword in line for keyword in ["download", "frag", "ETA", "Destination"]):
                console.print(f"[dim]{line.strip()}[/dim]")
            elif "ERROR" in line or "WARNING" in line:
                console.print(f"[yellow]{line.strip()}[/yellow]")

        process.wait()

        if process.returncode == 0:
            console.print(f"[green]✓[/green] 下载完成: {title}")
            return True
        else:
            console.print(f"[red]✗[/red] 下载失败，退出码: {process.returncode}")
            return False

    except Exception as e:
        console.print(f"[red]✗[/red] 下载过程出错: {e}")
        return False

def main():
    console.print("[bold magenta]🎬 XET视频下载 - 清理和修复工具[/bold magenta]")
    console.print("=" * 60)

    # 步骤1：清理片段文件
    console.print("\n[bold]步骤 1: 清理片段文件[/bold]")
    cleanup_downloads()

    # 步骤2：加载视频信息
    console.print("\n[bold]步骤 2: 加载视频信息[/bold]")
    videos = get_video_info_from_json()

    if not videos:
        console.print("[yellow]⚠[/yellow] 没有找到视频信息")
        return

    # 步骤3：重新下载选项
    console.print(f"\n[bold]步骤 3: 重新下载选项 ({len(videos)}个视频)[/bold]")

    for i, video in enumerate(videos, 1):
        title = video['title']
        file_type = video.get('file_type', 'unknown')
        quality = video.get('quality', 'unknown')

        console.print(f"  {i}. {title}")
        console.print(f"     类型: {file_type}, 质量: {quality}")

    from rich.prompt import Prompt
    choice = Prompt.ask("\n请选择要重新下载的视频序号 (或输入 'a' 下载所有)", default="a")

    if choice.lower() == 'a':
        # 下载所有视频
        for i, video in enumerate(videos, 1):
            console.print(f"\n📥 处理视频 {i}/{len(videos)}")
            redownload_video(video)
    else:
        # 下载单个视频
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(videos):
                redownload_video(videos[idx])
            else:
                console.print("[red]✗[/red] 序号无效")
        except ValueError:
            console.print("[red]✗[/red] 输入无效")

    console.print("\n[bold green]✅ 清理和修复完成![/bold green]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 用户中断操作[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")