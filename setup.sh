#!/bin/bash
# 项目快速设置脚本

set -e

echo "🚀 小鹅通视频下载工具 - 快速设置"
echo "=================================="
echo ""

# 检查 uv 是否安装
echo "📦 检查 uv 是否安装..."
if ! command -v uv &> /dev/null; then
    echo "❌ 未检测到 uv，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv 安装完成"
else
    echo "✅ uv 已安装"
fi

# 检查 yt-dlp
echo ""
echo "📦 检查 yt-dlp 是否安装..."
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ 未检测到 yt-dlp"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "💡 请运行: brew install yt-dlp"
    else
        echo "💡 请运行: pip install yt-dlp"
    fi
    exit 1
else
    echo "✅ yt-dlp 已安装 ($(yt-dlp --version))"
fi

# 检查 ffmpeg
echo ""
echo "📦 检查 ffmpeg 是否安装..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  未检测到 ffmpeg (推荐安装)"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "💡 建议运行: brew install ffmpeg"
    fi
else
    echo "✅ ffmpeg 已安装"
fi

# 安装项目依赖
echo ""
echo "📦 安装项目依赖..."
uv sync

# 安装 Playwright 浏览器
echo ""
echo "📦 安装 Playwright 浏览器..."
uv run playwright install chromium

echo ""
echo "✅ 设置完成！"
echo ""
echo "🎉 您现在可以运行程序了:"
echo "   uv run python main.py"
echo ""

