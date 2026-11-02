#!/usr/bin/env python3
"""
测试增强后的视频捕获功能
专门用于测试调试模式和新的URL匹配逻辑
"""

import re
from main import VideoDownloader

def test_url_matching():
    """测试URL匹配逻辑"""
    print("🔍 测试增强的URL匹配逻辑")
    print("=" * 60)

    # 模拟测试URL（基于用户文档中的示例）
    test_urls = [
        # TS文件示例（从用户文档中）
        "https://v-vod-k.xiaoeknow.com/c880572d574747fb90374d751c7573a0/apprpu7LCLk2074/video/b_u_6178fab2541af_VxHrjzUT/mt6q323p0kme/main_233.ts?sign=REDACTED&t=REDACTED&us=REDACTED&time=REDACTED&uuid=REDACTED",

        # 高清M3U8示例（原逻辑）
        "https://example.com/video/v.f421220.m3u8?sign=abc123",

        # XET CDN域的不同格式
        "https://xiaoe-tech.com/course/video/lesson.mp4?sign=xyz",
        "https://app.xiaoeknow.com/media/main_100.ts",

        # 非XET CDN域名（应该被过滤）
        "https://youtube.com/video.mp4",
        "https://other.com/video.m3u8"
    ]

    downloader = VideoDownloader(debug_mode=True)

    print("\n测试XET CDN域名检测:")
    for url in test_urls:
        is_cdn = downloader._is_xet_cdn_url(url)
        print(f"  {url[:40]}... -> {'✅' if is_cdn else '❌'}")

    print("\n测试视频文件检测:")
    for url in test_urls:
        is_video = downloader._is_video_file_url(url)
        print(f"  {url[:40]}... -> {'✅' if is_video else '❌'}")

    print("\n测试签名参数检测:")
    for url in test_urls:
        has_sig = downloader._has_signature_params(url)
        print(f"  {url[:40]}... -> {'✅' if has_sig else '❌'}")

    print("\n测试质量信息提取:")
    quality_urls = [
        "https://example.com/video/v.f421220.m3u8",
        "https://example.com/video/v.f1280.ts",
        "https://example.com/video/v.f854.mp4",
        "https://example.com/video/without_quality.mp4"
    ]

    for url in quality_urls:
        quality = downloader._extract_quality_info(url)
        print(f"  {url} -> {quality}")

def test_downloader_initialization():
    """测试下载器初始化"""
    print("\n🔍 测试下载器初始化")
    print("=" * 60)

    # 测试默认初始化
    dl1 = VideoDownloader()
    print(f"✅ 默认初始化: debug_mode={dl1.debug_mode}, capture_ts={dl1.capture_ts}")

    # 测试启用调试模式
    dl2 = VideoDownloader(debug_mode=True)
    print(f"✅ 启用调试模式: debug_mode={dl2.debug_mode}")

    # 测试自定义CDN域名
    custom_domains = ["mycdn.com", "my-platform.com"]
    dl3 = VideoDownloader(cdn_domains=custom_domains)
    print(f"✅ 自定义CDN域名: {dl3.cdn_domains}")

def main():
    print("🎯 XET Video Downloader 增强功能测试")
    print("基于用户文档分析的问题修复方案\n")

    test_downloader_initialization()
    test_url_matching()

    print("\n" + "=" * 60)
    print("✅ 增强功能测试完成")
    print("💡 建议下一步:")
    print("  1. 运行主程序启用调试模式")
    print("  2. 使用实际的XET视频链接进行测试")
    print("  3. 观察网络请求日志，确认是否捕获到.ts文件")

if __name__ == "__main__":
    main()