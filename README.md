# 全景路演音频批量下载工具

一个基于 Playwright 和 yt-dlp 的自动化音频提取工具，专门用于批量下载全景路演等网站的音频内容（默认提取为 MP3 格式）。

## ✨ 特性

- 🎵 **音频提取** - 自动提取视频中的音频，转换为 MP3 格式
- 🎯 **自动捕获** - 使用 Playwright 自动拦截并捕获视频地址（支持 M3U8 和直接 MP4 链接）
- 🔐 **登录保持** - 使用持久化浏览器会话，首次登录后自动保存状态
- 📦 **批量下载** - 支持批量处理多个视频URL
- 🎬 **多格式支持** - 支持 M3U8 流媒体和直接 MP4/MKV/AVI 等视频文件
- 🎼 **高音质** - 使用最佳音质设置（`--audio-quality 0`）
- 📊 **友好界面** - 使用 Rich 库提供美观的终端界面
- 💾 **信息保存** - 可选保存捕获的视频信息为 JSON 文件
- ⚡ **并发下载** - 使用 yt-dlp 的并发分片下载加速

## 📋 系统要求

- Python 3.10 或更高版本
- macOS / Linux / Windows
- [uv](https://docs.astral.sh/uv/) - Python 包管理工具
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载工具
- [ffmpeg](https://ffmpeg.org/) - 视频处理工具（推荐）

## 🚀 快速开始

### 1. 安装系统依赖

**macOS (使用 Homebrew):**
```bash
brew install yt-dlp ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install yt-dlp ffmpeg
```

**Windows (使用 Scoop):**
```bash
scoop install yt-dlp ffmpeg
```

或者使用 pip:
```bash
pip install yt-dlp
```

### 2. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 安装项目依赖

```bash
# 克隆或进入项目目录
cd fetch-video

# 使用 uv 安装依赖
uv sync

# 安装 Playwright 浏览器驱动
uv run playwright install chromium
```

### 4. 运行程序

```bash
uv run python main.py
```

## 📖 使用指南

### 交互式使用

运行程序后，按照提示操作：

1. **输入 URL**
   - 选项 1: 手动输入单个或多个URL（用逗号分隔）
   - 选项 2: 从文本文件读取URL列表

2. **选择浏览器模式**
   - 首次运行建议显示浏览器窗口，以便完成登录
   - 后续可以使用无头模式（后台运行）

3. **选择格式**
   - 选择是否只下载音频（MP3格式）或完整视频
   - 默认为音频模式

4. **等待捕获**
   - 程序会自动访问每个URL并捕获视频地址（M3U8 或直接视频链接）
   - 捕获成功后会显示视频列表及类型

5. **下载音频**
   - 确认下载后，程序会自动提取音频并转换为 MP3
   - 音频文件保存在 `downloads` 目录

### 从文件批量下载

创建 `urls.txt` 文件，每行一个URL：

```text
https://rs.p5w.net/html/175671238578643.shtml
https://rs.p5w.net/html/175671238578644.shtml
https://rs.p5w.net/html/175671238578645.shtml
```

然后运行程序，选择选项 2，输入文件路径。

## 🔧 配置说明

### 目录结构

```
fetch-video/
├── main.py                    # 主程序
├── pyproject.toml            # 项目配置（uv 管理）
├── README.md                 # 说明文档
├── .gitignore               # Git 忽略文件
├── browser_session/         # 浏览器会话数据（自动生成）
├── downloads/               # 视频下载目录（自动生成）
└── captured_videos.json     # 捕获的视频信息（可选生成）
```

### 自定义配置

您可以在代码中修改以下参数：

```python
# main.py 中的 VideoDownloader 类初始化
downloader = VideoDownloader(
    user_data_dir="./browser_session",  # 浏览器会话目录
    output_dir="./downloads"             # 视频输出目录
)
```

## 🛠️ 高级用法

### 仅捕获不下载

程序支持先捕获视频信息，保存为 JSON，稍后再下载：

```python
from main import VideoDownloader

downloader = VideoDownloader()
urls = ["https://..."]
downloader.capture_video_urls(urls, headless=True)
downloader.save_captured_info("videos.json")
```

### 自定义下载参数

修改 `download_video` 方法中的 yt-dlp 参数：

```python
cmd = [
    "yt-dlp",
    "--referer", referer,
    "--concurrent-fragments", "10",  # 增加并发数
    "--format", "best",               # 指定格式
    "--merge-output-format", "mp4",  # 合并格式
    "-o", output_template,
    media_url
]
```

## ⚠️ 注意事项

1. **播放按钮点击**
   - 首次运行请选择"显示浏览器窗口"
   - 程序会自动尝试点击播放按钮（全景路演网站的 `<i class="play"></i>` 按钮）
   - 如果自动点击失败，可在等待期间手动点击
   - 点击播放后视频才会开始加载

2. **视频类型**
   - 程序支持两种视频类型：
     - **直接视频链接**: MP4/MKV/AVI 等直接下载链接（全景路演主要使用）
     - **M3U8 流媒体**: HLS 流媒体格式
   - 自动识别视频类型，无需手动配置

3. **网络问题**
   - 确保网络稳定
   - 下载失败可以重新运行程序，已下载的视频不会重复下载

4. **法律声明**
   - 仅用于下载您有权访问的视频内容
   - 请勿用于商业用途或侵权目的

## 🐛 故障排除

### 问题: 未捕获到视频地址

**解决方案:**
- 确保已登录（使用显示浏览器模式）
- 增加等待时间（在交互提示中输入更大的秒数，如 30-60 秒）
- 开启调试模式查看所有媒体请求
- 在显示浏览器模式下，等待期间可以手动点击播放按钮
- 检查 URL 是否正确

### 问题: 播放按钮未被自动点击

**解决方案:**
- 使用显示浏览器模式，在等待期间手动点击播放按钮
- 工具会自动尝试多种播放按钮选择器
- 如需添加自定义选择器，可编辑 `main.py` 中的 `play_selectors` 列表
- 某些视频会自动加载，不需要点击播放按钮

### 问题: 下载失败

**解决方案:**
- 检查 yt-dlp 和 ffmpeg 是否正确安装
- 查看错误信息，可能是网络问题
- 尝试手动使用 yt-dlp 下载测试

### 问题: Playwright 浏览器未安装

**解决方案:**
```bash
uv run playwright install chromium
```

## 📝 示例

### 示例 1: 下载单个音频

```bash
$ uv run python main.py
# 是否只下载音频（MP3格式）？ [Y/n]: y
# 选择选项 1: 手动输入
# 输入 URL: https://rs.p5w.net/html/175671238578643.shtml
# 选择显示浏览器: 是
# 等待时间: 20秒
# 开启调试模式: 否
# 等待捕获...（程序会自动点击播放按钮）
# 是否开始下载音频？ [Y/n]: y
# ✓ 音频下载完成
```

### 示例 2: 批量下载音频

创建 `urls.txt`:
```
https://rs.p5w.net/html/175671238578643.shtml
https://rs.p5w.net/html/175671238578644.shtml
```

运行:
```bash
$ uv run python main.py
# 是否只下载音频（MP3格式）？ [Y/n]: y
# 选择选项 2: 从文件读取
# 输入文件路径: urls.txt
# 选择显示浏览器: 是
# 等待时间: 15秒
# 开启调试模式: 否
# 等待捕获...
# 是否开始下载音频？ [Y/n]: y
# 🎵 开始批量下载 2 个音频...
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载
- [Rich](https://github.com/Textualize/rich) - 终端美化

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**Happy Downloading! 🎉**

