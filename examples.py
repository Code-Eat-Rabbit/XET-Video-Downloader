#!/usr/bin/env python3
"""
使用示例脚本
演示如何编程方式使用视频下载器
"""

from main import VideoDownloader

# 示例 1: 下载单个音频
def example_single_audio():
    """下载单个全景路演音频的示例"""
    print("示例 1: 下载单个全景路演音频")
    print("-" * 50)
    
    # audio_only=True 表示只下载音频
    downloader = VideoDownloader(audio_only=True)
    
    # 检查依赖
    if not downloader.check_dependencies():
        return
    
    # 全景路演视频URL
    urls = [
        "https://rs.p5w.net/html/175671238578643.shtml"
    ]
    
    # 捕获视频（显示浏览器以观察播放按钮点击）
    downloader.capture_video_urls(urls, headless=False, wait_time=20)
    
    # 显示捕获结果
    downloader.show_captured_videos()
    
    # 下载音频（会自动提取为 MP3）
    downloader.download_all()


# 示例 2: 批量下载多个音频
def example_batch_download():
    """批量下载多个全景路演音频的示例"""
    print("示例 2: 批量下载多个全景路演音频")
    print("-" * 50)
    
    # 只下载音频
    downloader = VideoDownloader(audio_only=True)
    
    # 检查依赖
    if not downloader.check_dependencies():
        return
    
    # 多个全景路演视频URL
    urls = [
        "https://rs.p5w.net/html/175671238578643.shtml",
        "https://rs.p5w.net/html/175671238578644.shtml",
        "https://rs.p5w.net/html/175671238578645.shtml",
    ]
    
    # 捕获视频
    downloader.capture_video_urls(urls, headless=False, wait_time=15)
    
    # 保存捕获信息
    downloader.save_captured_info("my_audios.json")
    
    # 下载所有音频
    success, fail = downloader.download_all()
    print(f"\n完成！成功: {success}, 失败: {fail}")


# 示例 3: 下载完整视频（非音频）
def example_download_video():
    """下载完整视频的示例"""
    print("示例 3: 下载完整视频（非音频模式）")
    print("-" * 50)
    
    # audio_only=False 表示下载完整视频
    downloader = VideoDownloader(audio_only=False)
    
    if not downloader.check_dependencies():
        return
    
    urls = ["https://rs.p5w.net/html/175671238578643.shtml"]
    
    # 捕获并下载完整视频
    downloader.capture_video_urls(urls, headless=False, wait_time=15)
    downloader.download_all()
    
    print("\n完整视频下载完成")


# 示例 4: 自定义输出目录
def example_custom_output():
    """自定义输出目录的示例"""
    print("示例 4: 自定义输出目录")
    print("-" * 50)
    
    # 自定义输出目录，下载音频
    downloader = VideoDownloader(
        user_data_dir="./my_browser_data",
        output_dir="./my_audios",
        audio_only=True
    )
    
    if not downloader.check_dependencies():
        return
    
    urls = ["https://rs.p5w.net/html/175671238578643.shtml"]
    
    downloader.capture_video_urls(urls, headless=False, wait_time=15)
    downloader.download_all()


if __name__ == "__main__":
    print("=" * 50)
    print("全景路演音频下载器 - 使用示例")
    print("=" * 50)
    print("\n请选择要运行的示例:")
    print("1. 下载单个音频")
    print("2. 批量下载多个音频")
    print("3. 下载完整视频（非音频模式）")
    print("4. 自定义输出目录")
    print()
    
    choice = input("请输入选项 (1-4): ").strip()
    
    if choice == "1":
        example_single_audio()
    elif choice == "2":
        example_batch_download()
    elif choice == "3":
        example_download_video()
    elif choice == "4":
        example_custom_output()
    else:
        print("无效选项")

