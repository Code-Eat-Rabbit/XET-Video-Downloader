#!/usr/bin/env python3
"""
重新下载视频测试 - 测试优化的下载参数
"""

import json
import subprocess
import re
from pathlib import Path
import sys
import os

def load_video_info(json_file: str = "captured_videos.json"):
    """加载视频信息"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        return videos
    except Exception as e:
        print(f"❌ 读取JSON失败: {e}")
        return []

def redownload_with_optimized_params():
    """使用优化参数重新下载视频"""

    # 加载视频信息
    videos = load_video_info()
    if not videos:
        print("❌ 没有找到视频信息")
        return False

    print(f"📋 找到 {len(videos)} 个视频信息")

    # 使用第一个视频进行测试
    video = videos[0]
    title = video['title']
    media_url = video['media_url']
    referer = video['referer']

    print(f"\n🎬 重新下载: {title}")
    print(f"📥 URL: {media_url[:60]}...")

    # 清理文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    output_template = f"downloads/{safe_title}.%(ext)s"

    # 确保下载目录存在
    download_dir = Path("downloads")
    download_dir.mkdir(exist_ok=True)

    # 删除可能已存在的文件
    incomplete_file = download_dir / f"{safe_title}.mp4"
    if incomplete_file.exists():
        print(f"🗑️ 删除不完整文件: {incomplete_file.name}")
        incomplete_file.unlink()

    # 优化的yt-dlp命令
    cmd = [
        "yt-dlp",
        "--referer", referer,
        "--concurrent-fragments", "16",  # 增加并发片段数
        "--merge-output-format", "mp4",  # 强制合并为mp4
        "--windows-filenames",           # 安全文件名
        "--no-part",                     # 不创建.part文件
        "--retries", "10",               # 更多重试
        "--fragment-retries", "10",      # 片段重试次数
        "--abort-on-unavailable-fragment",  # 确保完整性
        "--progress",                    # 显示进度
        "--newline",                     # 逐行输出
        "--verbose",                     # 详细输出
        "-o", output_template,
        media_url
    ]

    print(f"\n⚙️  使用优化参数:")
    print(f"  - 并发片段数: 8")
    print(f"  - 强制合并为: mp4")
    print(f"  - 输出文件: {output_template}")
    print(f"  - 禁止创建.part文件")

    print("\n" + "="*60)
    print("📥 开始下载...")
    print("="*60)

    try:
        # 运行yt-dlp
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # 实时显示输出
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # 显示关键信息
            if "download" in line.lower() or "eta" in line.lower():
                print(f"📊 {line}")
            elif "fragment" in line.lower() or "segment" in line.lower():
                print(f"🔗 {line}")
            elif "destination" in line.lower() or "output" in line.lower():
                print(f"💾 {line}")
            elif "error" in line.lower() or "warning" in line.lower():
                print(f"⚠️  {line}")
            elif "merge" in line.lower() or "finish" in line.lower():
                print(f"✅ {line}")
            elif "http" in line.lower() or "https" in line.lower():
                # 过滤掉过长的URL日志
                if len(line) < 100:
                    print(f"🌐 {line}")

        process.wait()

        print("\n" + "="*60)

        if process.returncode == 0:
            # 检查生成的文件
            if incomplete_file.exists():
                file_size_mb = incomplete_file.stat().st_size / (1024 * 1024)
                print(f"✅ 下载完成: {incomplete_file.name}")
                print(f"📏 文件大小: {file_size_mb:.2f} MB")

                if file_size_mb > 100:  # 假设完整视频 > 100MB
                    print("🎉 视频看起来是完整的!")
                else:
                    print("⚠️  文件大小较小，可能需要进一步检查")
            else:
                print("❌ 输出文件未找到")

            return process.returncode == 0
        else:
            print(f"❌ 下载失败，退出码: {process.returncode}")
            return False

    except Exception as e:
        print(f"❌ 下载过程出错: {e}")
        import traceback
        print(f"🔍 详细错误: {traceback.format_exc()}")
        return False

def check_ffmpeg_availability():
    """检查ffmpeg是否可用"""
    try:
        result = subprocess.run(
            ["which", "ffmpeg"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ ffmpeg 可用: {result.stdout.strip()}")
        return True
    except Exception as e:
        print("⚠️  ffmpeg 不可用")
        print("💡 提示: 安装ffmpeg可以提高HLS解密速度")
        return False

def main():
    print("="*60)
    print("🎯 XET视频重新下载 - 优化合并测试")
    print("="*60)

    # 检查ffmpeg
    print("\n🔧 系统检查:")
    check_ffmpeg_availability()

    # 重新下载视频
    success = redownload_with_optimized_params()

    if success:
        print("\n" + "="*60)
        print("🎊 测试成功!")
        print("💡 您可以:")
        print("  1. 播放 downloads/ 目录中的视频文件")
        print("  2. 检查文件是否完整")
        print("  3. 如果需要，运行完整的主程序下载所有视频")
    else:
        print("\n" + "="*60)
        print("⚠️  测试失败")
        print("💡 可能的解决方案:")
        print("  1. 检查网络连接")
        print("  2. 确保URL仍然有效")
        print("  3. 考虑安装ffmpeg")
        print("  4. 调整并发参数（可能太大）")

    print("="*60)

if __name__ == "__main__":
    main()
