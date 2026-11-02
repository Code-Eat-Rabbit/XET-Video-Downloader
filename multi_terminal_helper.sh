#!/bin/bash
# 多终端并行下载助手脚本

echo "========================================"
echo "  🚀 XET视频 - 多终端并行下载助手"
echo "========================================"

# 配置
PROJECT_DIR="/Users/mac/projects/XET-Video-Downloader-main"
JSON_FILE="captured_videos.json.backup"
VIDEO_COUNT=23  # 总共23个视频
WINDOW_COUNT=3  # 开启3个窗口

# 检查环境
if [ ! -f "$PROJECT_DIR/$JSON_FILE" ]; then
    echo "❌ 找不到视频信息文件: $JSON_FILE"
    echo "请先备份原有文件: cp captured_videos.json captured_videos.json.backup"
    exit 1
fi

# 计算每个窗口的视频数
VIDEOS_PER_WINDOW=$(( (VIDEO_COUNT + WINDOW_COUNT - 1) / WINDOW_COUNT ))

echo ""
echo "📊 配置信息:"
echo "  - 总视频数: $VIDEO_COUNT"
echo "  - 窗口数: $WINDOW_COUNT"
echo "  - 每窗口视频数: $VIDEOS_PER_WINDOW"
echo "  - 预计并发: $WINDOW_COUNT 个视频同时下载"
echo "  - 总耗时: 约 30-90 分钟 (ffmpeg加速)"
echo ""

# 准备各组视频
echo "🔄 准备视频分组..."
cd "$PROJECT_DIR"

for i in $(seq 1 $WINDOW_COUNT); do
    START=$(( (i-1) * VIDEOS_PER_WINDOW ))
    END=$(( START + VIDEOS_PER_WINDOW - 1 ))
    END=$(( END < VIDEO_COUNT ? END : VIDEO_COUNT-1 ))

    # 创建JSON文件
    python3 -c "
import json
with open('$JSON_FILE', 'r', encoding='utf-8') as f:
    videos = json.load(f)
selected = videos[$START:$END+1]
output_file = f'selected_videos_window_{i}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(selected, f)
print(f'窗口{i}: {START+1}-{END+1} = {len(selected)}个视频 -> {output_file}')
"
done

echo ""
echo "========================================"
echo "📝 执行步骤 (手动操作):"
echo "========================================"
echo ""
echo "1. 打开 $WINDOW_COUNT 个终端窗口"
echo "2. 在每个终端中执行对应命令:"
echo ""

for i in $(seq 1 $WINDOW_COUNT); do
    echo "窗口 $i:"
    echo "  # 清理环境"
    echo "  cd $PROJECT_DIR"
    echo "  mkdir -p downloads_window_$i"
    echo "  "
    echo "  # 设置环境变量"
    echo "  source ~/.local/bin/env"
    echo "  export PATH=\"\$PATH:/Users/mac/Library/Python/3.9/bin\""
    echo "  "
    echo "  # 运行下载器"
    echo "  uv run python main.py <<< \"2\"$'\\n'\"selected_videos_window_$i.json\"$'\\n'\"n\"$'\\n'\"10\""
    echo "  "
    echo "  或者手动操作:"
    echo "  uv run python main.py"
    echo "  -> 选择2 (从文件读取)"
    echo "  -> 输入: selected_videos_window_$i.json"
    echo "  -> 选择: n (无头模式)"
    echo "  -> 等待: 10秒"
    echo ""
    echo "========================================"
done

echo ""
echo "💡 监控建议:"
echo "- 用 'top' 查看CPU使用率"
echo "- 用 'nettop' 查看网络流量"
echo "- 用 'df -h' 检查磁盘空间"
echo "- 用 'du -h downloads_window_*' 查看下载进度"
echo ""
echo "🛑 停止所有下载:"
echo "  每个终端窗口按 Ctrl+C"
echo ""
echo "✅ 完成后合并文件:"
echo "  mv downloads_window_*/* downloads/ 2>/dev/null"