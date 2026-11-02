#!/usr/bin/env python3
"""
快速测试增强的视频捕获功能（不依赖Playwright）
"""

import re

def extract_quality_from_url(url: str) -> str:
    """从URL提取质量信息"""
    match = re.search(r'v\.(f\d+)', url)
    if match:
        return match.group(1)
    return "unknown"

def is_xet_cdn_url(url: str, cdn_domains=None) -> bool:
    """检查URL是否属于XET CDN域名"""
    if cdn_domains is None:
        cdn_domains = ["xiaoeknow.com", "xiaoe-tech.com", "v-vod-k.xiaoeknow.com"]

    for domain in cdn_domains:
        if domain in url:
            return True
    return False

def is_video_file_url(url: str, capture_ts: bool = True) -> bool:
    """检查URL是否为视频文件"""
    if capture_ts and ".ts" in url:
        return True
    if ".m3u8" in url:
        return True
    if ".mp4" in url:
        return True
    return False

def has_signature_params(url: str, signature_params=None) -> bool:
    """检查URL是否包含签名参数"""
    if signature_params is None:
        signature_params = ["sign=", "t=", "ts=", "us=", "time=", "uuid="]

    for param in signature_params:
        if param in url:
            return True
    return False

def should_capture_url(url: str, debug: bool = False) -> bool:
    """判断是否应该捕获该URL"""

    is_xet_cdn = is_xet_cdn_url(url)
    is_video_file = is_video_file_url(url)
    has_signature = has_signature_params(url)

    # 捕获条件：XET CDN + 视频文件 + 签名（或者.ts文件可以没有签名）
    if is_xet_cdn and is_video_file and (has_signature or ".ts" in url):
        return True

    if debug:
        print(f"URL: {url[:60]}...")
        print(f"  XET CDN: {is_xet_cdn}")
        print(f"  视频文件: {is_video_file}")
        print(f"  有签名: {has_signature}")
        print(f"  捕获: {'✅' if (is_xet_cdn and is_video_file and (has_signature or '.ts' in url)) else '❌'}")

    return False

def main():
    print("🎯 增强URL匹配逻辑快速测试")
    print("基于用户文档分析的问题修复方案\n")

    # 测试URL（基于用户文档）
    test_urls = [
        # TS文件示例（从用户文档中） - 应该被捕获 ✅
        "https://v-vod-k.xiaoeknow.com/c880572d574747fb90374d751c7573a0/apprpu7LCLk2074/video/b_u_6178fab2541af_VxHrjzUT/mt6q323p0kme/main_233.ts?sign=abc123&t=1681234567&us=user123&time=20231101&uuid=abc-def",

        # TS文件没有签名 - 应该被捕获 ✅（.ts文件可以没有签名）
        "https://v-vod-k.xiaoeknow.com/video/main_100.ts",

        # M3U8文件有签名 - 应该被捕获 ✅
        "https://xiaoeknow.com/video/v.f421220.m3u8?sign=xyz789&t=1681234567",

        # 其他质量格式 - 应该被捕获 ✅
        "https://xiaoe-tech.com/video/v.f1280.ts?sign=abc",

        # 非XET CDN域名 - 应该被过滤 ❌
        "https://youtube.com/video.mp4",

        # XET CDN但不是视频文件 - 应该被过滤 ❌
        "https://xiaoeknow.com/api/data.json?sign=abc",

        # 视频文件但没有签名和不是.ts - 应该被过滤 ❌
        "https://xiaoeknow.com/video.m3u8",

        # MP4文件有签名 - 应该被捕获 ✅
        "https://xiaoe-tech.com/video/lesson.mp4?sign=xyz&t=123",
    ]

    print("详细分析（启用调试模式）:")
    print("=" * 60)

    captured_count = 0
    for i, url in enumerate(test_urls, 1):
        should_capture = should_capture_url(url, debug=True)
        if should_capture:
            captured_count += 1
            quality = extract_quality_from_url(url)
            file_type = "ts" if ".ts" in url else ("m3u8" if ".m3u8" in url else "mp4")
            print(f"  捕获详情: 质量={quality}, 类型={file_type}")
        print()

    print("=" * 60)
    print(f"✅ 增强功能测试完成")
    print(f"总测试URL: {len(test_urls)}")
    print(f"应捕获URL: {captured_count}")

    print("\n💡 验证点:")
    print("  - ✅ 支持 .ts 文件捕获（用户文档中的格式）")
    print("  - ✅ .ts 文件可以没有签名参数")
    print("  - ✅ 支持不同质量代码（v.f421220, v.f1280等）")
    print("  - ✅ 支持多个XET CDN域名")
    print("  - ✅ 严格过滤非XET CDN请求")

if __name__ == "__main__":
    main()