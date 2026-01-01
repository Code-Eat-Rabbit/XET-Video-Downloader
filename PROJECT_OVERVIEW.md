# 项目概览

## 📦 项目信息

- **项目名称**: 小鹅通视频批量下载工具 (XET Video Downloader)
- **版本**: 0.1.0
- **Python 版本**: 3.10+
- **包管理**: uv
- **主要技术**: Playwright + yt-dlp

## 🎯 核心功能

### 1. 自动捕获视频地址
- 使用 Playwright 模拟浏览器访问
- 实时拦截网络请求
- 自动识别 m3u8 视频地址
- 优先捕获最高清晰度版本

### 2. 批量下载
- 支持单个或多个 URL
- 支持从文件读取 URL 列表
- 并发分片下载加速
- 自动生成合理的文件名

### 3. 会话管理
- 持久化浏览器会话
- 首次登录后自动保存
- 后续无需重复登录

### 4. 友好交互
- 彩色终端输出
- 进度显示
- 交互式选择
- 详细的错误提示

## 📁 文件结构

```
fetch-video/
├── main.py                   # 主程序文件
│   ├── VideoDownloader 类    # 核心下载器类
│   │   ├── check_dependencies()       # 检查系统依赖
│   │   ├── capture_video_urls()       # 捕获视频地址
│   │   ├── download_video()           # 下载单个视频
│   │   ├── download_all()             # 批量下载
│   │   └── show_captured_videos()     # 显示视频列表
│   └── main()                # 主入口函数
│
├── pyproject.toml            # uv 项目配置
│   ├── 项目元数据
│   ├── 依赖声明
│   └── 构建配置
│
├── README.md                 # 完整文档
│   ├── 功能介绍
│   ├── 安装指南
│   ├── 使用说明
│   └── 故障排除
│
├── QUICKSTART.md            # 快速开始指南
│   ├── 5分钟上手
│   ├── 使用示例
│   └── 常见问题
│
├── examples.py              # 使用示例代码
│   ├── 单个视频下载示例
│   ├── 批量下载示例
│   ├── 仅捕获示例
│   └── 自定义配置示例
│
├── setup.sh                 # 自动设置脚本
│   ├── 检查依赖
│   ├── 安装工具
│   └── 配置环境
│
├── urls.txt.example         # URL 文件示例
├── .gitignore              # Git 忽略配置
│
├── docs/                    # 文档目录
│   ├── INSTRUCTION.md       # 原始需求文档
│   ├── video_example.html   # 视频信息示例
│   └── v.f421220.mp4        # 示例视频
│
├── browser_session/         # 浏览器会话（自动生成）
├── downloads/              # 视频下载目录（自动生成）
└── captured_videos.json    # 捕获信息（可选生成）
```

## 🔄 工作流程

```
1. 用户输入
   ↓
2. 检查依赖 (yt-dlp, ffmpeg)
   ↓
3. 启动 Playwright 浏览器
   ↓
4. 访问视频页面
   ↓
5. 拦截网络请求
   ↓
6. 捕获 m3u8 地址
   ↓
7. 显示视频列表
   ↓
8. 调用 yt-dlp 下载
   ↓
9. 保存到 downloads/
```

## 🛠️ 核心技术实现

### Playwright 请求拦截

```python
def handle_request(request):
    url = request.url
    if ".m3u8" in url and "sign=" in url:
        if "v.f421220" in url:  # 最高清版本
            # 捕获视频信息
            self.captured_urls.append({...})
```

### yt-dlp 下载调用

```python
cmd = [
    "yt-dlp",
    "--referer", referer,              # 必需的 Referer
    "--concurrent-fragments", "5",     # 并发下载
    "-o", output_template,             # 输出模板
    media_url                          # m3u8 地址
]
subprocess.run(cmd, check=True)
```

### 持久化会话

```python
context = p.chromium.launch_persistent_context(
    user_data_dir=str(self.user_data_dir),
    headless=headless,
    args=['--no-sandbox']
)
```

## 📊 依赖关系

### Python 依赖
- `playwright>=1.40.0` - 浏览器自动化
- `rich>=13.7.0` - 终端美化

### 系统依赖
- `yt-dlp` - 视频下载核心
- `ffmpeg` - 视频处理（可选但推荐）

## 🚀 使用场景

### 场景 1: 购买的课程批量下载
- 整理课程 URL 列表
- 一次性下载所有视频
- 本地观看学习

### 场景 2: 单个视频下载
- 直接输入视频 URL
- 快速下载保存

### 场景 3: 视频信息收集
- 仅捕获视频地址
- 导出为 JSON
- 后续处理或分析

## 🎨 设计特点

### 1. 模块化设计
- VideoDownloader 类封装核心功能
- 独立的方法处理不同任务
- 易于扩展和维护

### 2. 用户友好
- 交互式界面
- 清晰的提示信息
- 丰富的反馈

### 3. 健壮性
- 完善的异常处理
- 依赖检查
- 错误提示

### 4. 可配置性
- 自定义输出目录
- 可调节并发数
- 灵活的文件命名

## 📈 扩展性

### 可以添加的功能

1. **多线程下载**
   - 同时下载多个视频

2. **断点续传**
   - 下载中断后继续

3. **质量选择**
   - 让用户选择清晰度

4. **进度持久化**
   - 保存下载进度

5. **通知功能**
   - 下载完成后通知

6. **GUI 界面**
   - 图形化操作界面

## 🔒 安全性考虑

- 浏览器会话数据本地存储
- 不传输用户凭证
- 遵循网站 robots.txt
- 仅用于合法下载

## 📝 注意事项

1. **合法使用**
   - 仅下载已购买的内容
   - 遵守平台使用协议

2. **网络环境**
   - 需要稳定的网络连接
   - 大文件下载需要足够带宽

3. **存储空间**
   - 确保有足够的磁盘空间
   - 视频文件通常较大

## 🎓 学习价值

本项目展示了以下技术：

1. **Web 自动化** - Playwright 的使用
2. **网络请求拦截** - 捕获动态加载的资源
3. **子进程调用** - Python 调用外部命令
4. **异步操作** - 处理浏览器事件
5. **用户交互** - Rich 库的使用
6. **项目管理** - uv 包管理器

## 🤝 贡献指南

欢迎贡献代码或提出建议：

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License - 自由使用和修改

## 🙏 致谢

感谢以下开源项目：
- Playwright 团队
- yt-dlp 开发者
- Rich 库作者

---

**项目创建日期**: 2026-01-01  
**最后更新**: 2026-01-01

