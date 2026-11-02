#!/usr/bin/env python3
"""
简单清理工具 - 只清理不询问
"""

import os
import json
from pathlib import Path

def simple_cleanup():
    """简单清理 - 删除片段文件，保留视频信息"""
    download_dir = "./downloads"
    download_path = Path(download_dir)

    if not download_path.exists():
        print("📁 下载目录不存在")
        return

    print("🧹 正在清理片段文件...")

    # 查找所有片段文件
    part_files = list(download_path.glob("*.part*"))
    print(f"📊 找到 {len(part_files)} 个片段文件")

    # 统计文件大小
    total_size = 0
    deleted_count = 0
    for part_file in part_files:
        try:
            if part_file.is_file():
                total_size += part_file.stat().st_size
                # 删除文件
                part_file.unlink()
                deleted_count += 1
                if deleted_count % 100 == 0:
                    print(f"  🗑️ 已删除 {deleted_count} 个文件...")
        except Exception as e:
            print(f"  ❌ 删除失败 {part_file.name}: {e}")

    total_size_mb = total_size / (1024 * 1024)
    print(f"\n✅ 清理完成")
    print(f"  已删除: {deleted_count} 个文件")
    print(f"  释放空间: {total_size_mb:.2f} MB")

    # 检查现存文件
    remaining_files = list(download_path.glob("*"))
    mp4_files = list(download_path.glob("*.mp4"))
    mkv_files = list(download_path.glob("*.mkv"))
    webm_files = list(download_path.glob("*.webm"))

    print(f"\n📂 保留的文件:")
    for vf in mp4_files + mkv_files + webm_files:
        size_mb = vf.stat().st_size / (1024 * 1024)
        print(f"  ✓ {vf.name} ({size_mb:.2f} MB)")

    # 检查视频信息
    json_file = "captured_videos.json"
    if Path(json_file).exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                videos = json.load(f)
            print(f"\n📋 捕获的视频信息:")
            print(f"  共 {len(videos)} 个视频URL已保存")
            print("  前3个视频:")
            for i, video in enumerate(videos[:3], 1):
                title = video.get('title', '未知标题')
                file_type = video.get('file_type', 'unknown')
                quality = video.get('quality', 'unknown')
                print(f"    {i}. {title} ({file_type}, {quality})")
        except Exception as e:
            print(f"\n❌ 读取视频信息失败: {e}")

    print("\n🎯 下一步建议:")
    print("  1. 重新运行主程序下载视频 (python main.py)")
    print("  2. 使用优化的下载参数，确保完整合并")
    print("  3. 观察下载过程，不要提前中断")

def reinstall_dependencies():
    """重新安装项目依赖（如果需要）"""
    print("\n🔧 检查依赖...")
    try:
        import subprocess
        # 检查yt-dlp
        subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True)
        print("  ✅ yt-dlp 可用")

        # 检查playwright
        import playwright
        print("  ✅ playwright 可用")

        print("\n✅ 所有依赖正常")
    except Exception as e:
        print(f"  ⚠️ 依赖错误: {e}")
        print("  建议运行: uv sync")
        print("  然后运行: uv run playwright install chromium")

if __name__ == "__main__":
    print("=" * 50)
    print("🏗️ XET视频下载器 - 清理和修复工具")
    print("=" * 50)

    simple_cleanup()
    reinstall_dependencies()

    print("\n" + "=" * 50)
    print("✅ 工具运行完毕")
    print("💡 运行 python main.py 开始下载")