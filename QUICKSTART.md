# 快速开始指南

## 🚀 5分钟快速上手

### 步骤 1: 安装依赖

```bash
# 运行自动设置脚本
./setup.sh
```

或者手动安装：

```bash
# 1. 安装系统工具（macOS）
brew install yt-dlp ffmpeg

# 2. 安装 Python 依赖
uv sync

# 3. 安装浏览器驱动
uv run playwright install chromium
```

### 步骤 2: 准备 URL

**方式 A: 单个视频**
- 直接在程序中输入URL

**方式 B: 批量下载**
- 创建 `urls.txt` 文件（可参考 `urls.txt.example`）
- 每行一个URL

```txt
https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx1
https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx2
```

### 步骤 3: 运行程序

```bash
uv run python main.py
```

### 步骤 4: 首次登录

- 第一次运行选择"是"显示浏览器窗口
- 在弹出的浏览器中扫码或手机号登录
- 登录信息会保存在 `browser_session` 目录
- 后续运行可以选择"否"使用无头模式

### 步骤 5: 等待下载

- 程序会自动捕获视频地址
- 显示视频列表确认
- 自动下载到 `downloads` 目录

## 📝 使用示例

### 示例 1: 下载单个视频

```bash
$ uv run python main.py

# 输入选项
选择: 1 (手动输入)
URL: https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx
显示浏览器: 是 (首次)
```

### 示例 2: 批量下载课程

创建 `my_course.txt`:
```
https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx1
https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx2
https://appezrn4igg1968.h5.xet.citv.cn/p/course/video/v_xxx3
```

运行:
```bash
$ uv run python main.py

选择: 2 (从文件读取)
文件路径: my_course.txt
显示浏览器: 否 (已登录)
```

### 示例 3: 编程方式使用

查看 `examples.py` 获取更多示例：

```bash
uv run python examples.py
```

## 🔧 常见问题

### Q1: 未捕获到视频地址？

**A:** 
- 确保已登录（首次使用显示浏览器）
- 检查URL是否正确
- 增加等待时间

### Q2: 下载失败？

**A:**
- 检查 yt-dlp 是否安装: `yt-dlp --version`
- 检查网络连接
- 查看错误信息

### Q3: 视频质量不是最高清？

**A:**
- 程序默认捕获 `v.f421220`（最高清）
- 检查是否所有视频都支持高清

### Q4: 如何删除登录信息重新登录？

**A:**
```bash
rm -rf browser_session/
```

## 📂 输出文件说明

```
fetch-video/
├── browser_session/          # 浏览器登录会话
├── downloads/                # 下载的视频文件
│   ├── 01_视频标题1.mp4
│   ├── 02_视频标题2.mp4
│   └── ...
└── captured_videos.json     # 捕获的视频信息（可选）
```

## 💡 进阶技巧

### 1. 只捕获不下载

修改代码或在交互时选择"否"跳过下载，保存JSON文件供后续处理。

### 2. 自定义文件名

修改 `main.py` 中的 `output_template`：

```python
output_template = str(self.output_dir / f"{safe_title}.%(ext)s")
```

### 3. 加速下载

修改并发片段数：

```python
"--concurrent-fragments", "10",  # 默认是 5
```

### 4. 下载字幕

添加 yt-dlp 参数：

```python
"--write-subs",
"--sub-lang", "zh-CN",
```

## 🎯 最佳实践

1. **首次使用**
   - 显示浏览器完成登录
   - 测试单个视频

2. **批量下载**
   - 使用无头模式
   - 准备好URL列表文件

3. **网络优化**
   - 稳定的网络环境
   - 适当的并发数

4. **保存记录**
   - 导出 JSON 文件
   - 便于后续管理

## ⚡ 快捷命令

```bash
# 快速设置
./setup.sh

# 运行主程序
uv run python main.py

# 运行示例
uv run python examples.py

# 清理下载
rm -rf downloads/*

# 重新登录
rm -rf browser_session/
```

## 📞 需要帮助？

- 查看 [README.md](README.md) 获取完整文档
- 检查 [examples.py](examples.py) 获取代码示例
- 提交 Issue 报告问题

---

**开始您的第一次下载吧！** 🎉

