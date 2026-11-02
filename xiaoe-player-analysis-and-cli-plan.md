# 小鹅通视频播放技术分析与 XiaoE CLI 项目记录

> 文档用途：记录已观察到的小鹅通课程播放器请求与浏览器能力信息，并整理后续独立媒体工具的技术范围。
>
> **重要边界：**
> 本文中的课程页面及媒体请求属于受版权声明限制的课程。本文仅作技术现象记录，不提供绕过平台限制、提取受保护媒体、规避授权或重组该课程完整视频的操作步骤。后续媒体处理功能仅面向用户自有或明确获授权的本地文件与分片。

## 1. 课程与环境信息

  项目             已观察信息
  ---------------- --------------------------------------
  平台             小鹅通（XiaoEtech）
  商家             动静自在（DongJing ZiZai）
  页面类型         直播结束后的回放
  页面域名         `apprpu7lclk2074.pc.xiaoe-tech.com`
  页面课程标识     `course_332nSJqjYynrfVcm84W310tnxRZ`
  播放器画面尺寸   1920 × 1080
  视频时长         6903 秒（1 小时 55 分 03 秒）
  浏览器           macOS 上的 Chrome 150

课程页面 URL（仅作为本次研究记录，不代表可直接下载）：

``` text
https://apprpu7lclk2074.pc.xiaoe-tech.com/p/t_pc/live_pc/pc/l_6a89131ee4b0694c5bff65ee?course_id=course_332nSJqjYynrfVcm84W310tnxRZ
```

## 2. HTML5 Video 与浏览器能力检测

页面中的视频元素检测结果：

  -----------------------------------------------------------------------------------------------------------------------------------
  检测项                                      结果
  ------------------------------------------- ---------------------------------------------------------------------------------------
  `video.readyState`                          `4`

  `video.currentSrc`                          `blob:` URL

  `video.src`                                 `blob:` URL

  `video.currentSrc` 示例                     `blob:https://apprpu7lclk2074.pc.xiaoe-tech.com/f3037020-ef7f-47d9-a37a-5262b9f04b5b`

  `video.type`                                `null`

  `typeof MediaSource !== 'undefined'`        `true`

  `!!navigator.requestMediaKeySystemAccess`   `true`

  `'onencrypted' in video`                    `true`
  -----------------------------------------------------------------------------------------------------------------------------------

浏览器报告以下 codec 可被 MSE 支持：

``` text
video/mp4; codecs="avc1.640028"  -> true
video/mp4; codecs="avc1.4d401f" -> true
video/mp4; codecs="hvc1.1.6.L120.B0" -> true
```

### 2.1 如何解读

-   `blob:` 形式的 `currentSrc` 常见于 Media Source
    Extensions（MSE）驱动的播放流程，但仅凭这一项不能还原完整媒体管线。
-   `MediaSource` 存在，只能说明浏览器提供 MSE API。
-   `requestMediaKeySystemAccess` 存在，只能说明浏览器提供 Encrypted
    Media Extensions（EME）相关 API。
-   `'onencrypted' in video`
    仅说明该事件属性存在，不能证明页面实际触发了加密事件。
-   `MediaSource.isTypeSupported(...)` 的结果代表浏览器对相应 MIME/codec
    声明的支持，不代表当前课程实际使用了这些 codec。
-   当前证据不足以判断该课程是否使用
    DRM、媒体是否加密、是否存在独立音视频轨，或播放器实际采用何种编码组合。

**结论：** 可以认为浏览器具备 MSE/EME
相关能力，但不能据此断言课程实际启用了
DRM，也不能据此推断媒体可被无损地拼接为单一文件。

## 3. 已观察到的媒体请求现象

用户在 Chrome DevTools 的 Network 面板中观察到：

-   `Media` 分类下没有明显媒体请求。
-   `Fetch/XHR` 分类下持续出现请求。
-   其中一个请求的路径以 `.ts` 结尾，文件名为 `main_233.ts`。

请求 URL 的结构示例（签名及临时参数已省略/脱敏）：

``` text
https://v-vod-k.xiaoeknow.com/
  c880572d574747fb90374d751c7573a0/
  apprpu7LCLk2074/video/
  b_u_6178fab2541af_VxHrjzUT/
  mt6q323p0kme/main_233.ts
  ?sign=[REDACTED]
  &t=[REDACTED]
  &us=[REDACTED]
  &time=[REDACTED]
  &uuid=[REDACTED]
```

可见的路径结构：

  部分           观察值或含义
  -------------- ------------------------------------
  CDN 域名       `v-vod-k.xiaoeknow.com`
  资源路径标识   `c880572d574747fb90374d751c7573a0`
  应用标识       `apprpu7LCLk2074`
  资源路径       `/video/`
  视频样式标识   `b_u_6178fab2541af_VxHrjzUT`
  流/资源标识    `mt6q323p0kme`
  请求文件名     `main_233.ts`
  查询参数       包含签名、时间、用户/会话相关参数

### 3.1 当前能得出的结论

-   `.ts` 后缀表明请求资源以 MPEG-TS
    文件命名；仅凭扩展名不能确认内容是否加密、是否完整、是否可直接解码。
-   `main_233.ts`
    只能证明观察到一个以该名称命名的请求，不能证明分片总数、编号规则、播放顺序或课程整体媒体结构。
-   Fetch/XHR 中出现媒体相关请求并不罕见；请求分类本身不能作为媒体格式或
    DRM 状态的判断依据。
-   请求中的签名和临时参数可能具有时效性或会话绑定属性，不应复制、分享或写入普通日志。
-   DevTools 显示的 `Remote Address: 127.0.0.1:7890`
    表示浏览器请求经过本机代理端口；它不是媒体 CDN 的真实服务地址。

### 3.2 尚未确认的事项

以下事项没有足够证据，不应当作事实：

-   TS 请求是否覆盖全部课程内容。
-   分片是否按数字编号连续排列。
-   是否存在 manifest 或其他播放清单。
-   媒体是否加密或受 DRM 保护。
-   音频和视频是否位于同一分片。
-   分片时间戳是否连续、编码参数是否一致。
-   所有分片是否可以直接 concat/remux 成 MP4。

## 4. 业务接口观察

另一个被观察到的请求：

``` text
POST https://apprpu7lclk2074.pc.xiaoe-tech.com/alive/xe.alive.alive_marquee/1.0.0?app_id=apprpu7LCLk2074
```

响应状态为 `200 OK`，`Content-Type` 为 `application/json`。

根据接口路径名称，该请求看起来与直播间
marquee（跑马灯）业务有关，而不是媒体文件请求。

响应中可见的部分业务字段：

  字段                               值/含义
  ---------------------------------- -------------------
  `shopInfo.shop_name`               `动静自在`
  `shopInfo.shop_id`                 `apprpu7LCLk2074`
  `shopInfo.enable_web_rtc`          `1`
  `shopInfo.is_privacy_protection`   `0`
  `shopInfo.is_watermark`            `0`
  `shopInfo.version_type`            `4`

响应中的 `live.screen_record_cfg` 是一个 JSON 字符串，包含以下配置：

``` json
{
  "switch": 1,
  "desc_switch": 1,
  "desc": "【版权声明】本课程版权归提供者所有，仅限个人学习，严禁任何形式的录制、传播和账号分享。一经发现，平台将依法保留追究权，情节严重者将承担法律责任。"
}
```

以上仅摘录与本次技术分析有关的字段；其他样式字段（字体颜色、字号、位置、透明度、显示秒数等）属于界面呈现配置。

### 4.1 重要说明

-   `is_watermark: 0` 不代表内容没有版权限制。
-   `is_privacy_protection: 0` 不代表没有 DRM 或其他访问控制。
-   `screen_record_cfg` 中的版权声明明确限制录制、传播和账号分享。
-   marquee 接口不是媒体接口，不能用它推断媒体分片结构。

## 5. 初步播放架构判断

基于目前观察，较合理的有限判断是：

1.  页面通过 HTML5 Video 播放媒体。
2.  `blob:` 类型的媒体源与 MSE 使用方式相符。
3.  浏览器具备 MSE/EME API，但尚无证据证明当前课程实际启用了 EME/DRM。
4.  至少观察到一个以 `.ts` 结尾的 Fetch/XHR 请求。
5.  仅凭单个 TS 请求和 `blob:`
    URL，无法还原完整播放清单、分片顺序、授权机制或媒体封装方式。

因此，现阶段应将其记录为"疑似基于 MSE
的分段媒体播放现象"，而不是断言为某一种特定 HLS/DRM 实现。

## 6. 凭据与隐私安全

此前排查过程中曾粘贴过包含认证令牌、用户标识及手机号的请求头信息。这类信息属于敏感凭据或个人信息。

建议采取以下措施：

1.  如果相关会话仍有效，退出账号并重新登录，使旧会话失效。
2.  如平台提供设备管理或会话管理功能，撤销不再使用的旧会话。
3.  不要在聊天、Issue、日志或代码仓库中粘贴
    Cookie、Authorization、`p_token`、`ko_token`、用户标识或带签名的完整媒体
    URL。
4.  分享请求样本前，先删除所有 token、签名、手机号、用户 ID、UUID
    等字段。
5.  工具日志默认只记录域名、路径模板、状态码和耗时，不记录认证头及完整查询参数。

## 7. XiaoE CLI 项目方向

项目暂定名称：`xiaoe-cli`。

### 7.1 目标范围

构建一个通用的本地媒体管理 CLI，支持：

-   记录课程名称、来源页面 URL 等元数据。
-   检查用户本地已有的媒体文件。
-   检查用户自有或明确获授权的 TS 分片。
-   对参数兼容的授权 TS 分片进行合并/转封装。
-   将兼容的本地媒体文件转换为目标格式。
-   管理本地任务和处理结果。

课程 URL
仅用于元数据记录，不自动抓取受限课程页面，也不自动请求、下载或解析该课程的受保护媒体资源。

### 7.2 技术栈

  模块             技术
  ---------------- --------------------------------------
  Runtime          Node.js 22+
  Language         TypeScript
  CLI              Commander
  参数校验         Zod
  Logging          Pino
  媒体探测         FFprobe
  媒体处理         FFmpeg
  本地数据库       SQLite
  测试             Vitest
  后续 Dashboard   React（独立前端，不放入 CLI 主进程）

CLI 主程序不需要 React。React 只在后续确实需要图形化管理界面时引入。

### 7.3 建议目录结构

``` text
xiaoe-cli/
├── src/
│   ├── cli/
│   │   ├── index.ts
│   │   └── commands/
│   │       ├── course.ts
│   │       ├── media.ts
│   │       └── task.ts
│   ├── core/
│   │   ├── media/
│   │   │   ├── inspector.ts
│   │   │   ├── merger.ts
│   │   │   └── converter.ts
│   │   ├── course/
│   │   │   └── manager.ts
│   │   └── storage/
│   │       └── database.ts
│   ├── types/
│   │   ├── course.ts
│   │   └── media.ts
│   └── utils/
│       ├── ffmpeg.ts
│       └── logger.ts
├── tests/
├── test-fixtures/
├── data/
├── package.json
└── tsconfig.json
```

### 7.4 命令设计草案

``` bash
# 记录课程元数据，不抓取页面媒体
xiaoe course add --url "https://example.com/course/123" --name "课程名称"

# 检查本地媒体文件
xiaoe media inspect ./videos/lesson.mp4

# 检查本地 TS 文件
xiaoe media inspect ./segments/001.ts

# 合并用户自有或明确获授权的本地分片
xiaoe media merge --manifest ./segments/manifest.txt --output ./output/lesson.mp4

# 查看任务
xiaoe task list
```

建议使用显式 manifest，而不是依赖文件名数字猜测分片顺序。

## 8. 核心类型草案

``` ts
export interface Course {
  id: string;
  name: string;
  sourceUrl: string;
  createdAt: string;
  updatedAt: string;
}

export interface CourseRepository {
  create(course: Course): Promise<void>;
  findById(id: string): Promise<Course | null>;
  findAll(): Promise<Course[]>;
  delete(id: string): Promise<void>;
}

export type MediaFormat = 'mp4' | 'mpegts' | 'hls' | 'unknown';

export interface MediaInfo {
  filePath: string;
  format: MediaFormat;
  duration?: number;
  size: number;
  width?: number;
  height?: number;
  videoCodec?: string;
  audioCodec?: string;
}

export interface MediaInspector {
  inspect(filePath: string): Promise<MediaInfo>;
}

export interface MediaMerger {
  merge(inputFiles: string[], outputFile: string): Promise<void>;
}

export interface MediaConverter {
  convert(inputFile: string, outputFile: string): Promise<void>;
}
```

## 9. 媒体处理实现注意事项

### 9.1 FFprobe 检查

媒体检查器应通过 FFprobe JSON 输出获取：

-   容器格式。
-   时长与文件大小。
-   视频宽高。
-   视频和音频 codec。
-   音视频流数量及流类型。

不要只依赖文件扩展名判断真实媒体格式。

### 9.2 TS 合并

对自有或明确获授权的本地 TS 文件，合并前应：

1.  由用户提供明确的输入文件清单及顺序。
2.  检查所有输入文件存在且可读。
3.  使用 FFprobe 检查容器、codec、分辨率和音视频流。
4.  检查输入文件是否属于同一组兼容媒体。
5.  将输出写入临时文件，成功后再原子替换目标文件。
6.  失败时清理临时文件，并保留可诊断的错误信息。

FFmpeg concat demuxer 与 `-c copy`
可用于兼容输入的无重编码拼接/转封装，但并不保证任意 TS
文件都能直接封装为
MP4。时间戳不连续、编码参数不同、轨道结构不同等情况可能导致失败或输出异常。

### 9.3 进程执行安全

封装 `spawn` 时应考虑：

-   使用参数数组，不拼接 shell 命令字符串。
-   设置超时和 AbortSignal。
-   限制 stderr/stdout 缓冲大小。
-   处理进程退出码和信号。
-   收到取消请求时终止子进程。
-   对输入和输出路径做校验。
-   不把用户提供的文件名直接拼入 FFmpeg concat 清单而不做转义。
-   日志中不记录认证信息或签名 URL。

## 10. 建议测试样本

可以用 FFmpeg 自行生成一段测试视频，再切分为
TS，用于验证本地媒体检查与合并流程。该测试数据完全由本地生成，不依赖课程平台资源。

``` bash
mkdir -p test-fixtures

ffmpeg \
  -f lavfi -i testsrc=duration=30:size=1280x720:rate=25 \
  -f lavfi -i sine=frequency=1000:duration=30 \
  -c:v libx264 -c:a aac \
  test-fixtures/sample.mp4

ffmpeg \
  -i test-fixtures/sample.mp4 \
  -c copy \
  -f segment \
  -segment_time 10 \
  -reset_timestamps 1 \
  test-fixtures/segment_%03d.ts
```

## 11. 开发阶段规划

  阶段      目标             交付
  --------- ---------------- -----------------------------------------
  Phase 1   Media Core       FFprobe 检查、本地 TS 合并、Vitest 测试
  Phase 2   Course Manager   课程元数据模型、SQLite Repository
  Phase 3   转换与任务       FFmpeg 转换、任务状态与取消
  Phase 4   CLI 完善         参数校验、帮助信息、错误处理、日志
  Phase 5   Dashboard        独立 React UI，查看课程、媒体与任务

## 12. 当前结论与下一步

### 已确认

-   页面使用 `blob:` 作为 video source。
-   浏览器支持 MSE/EME 相关 API。
-   观察到一个 `.ts` 命名的 Fetch/XHR 请求。
-   课程业务响应中存在明确的版权声明，限制录制、传播和账号分享。
-   目前不足以确定实际 DRM 状态、媒体清单、完整分片结构或 TS
    是否可直接合并。

### 建议下一步

优先实现独立的本地媒体工具，不将它连接到该受限课程的媒体请求：

1.  初始化 TypeScript + Node.js CLI 项目。
2.  实现 FFprobe `media inspect`。
3.  为本地测试生成 MP4 与 TS 样本。
4.  实现基于显式 manifest 的本地授权分片合并。
5.  增加 Vitest 测试及 FFmpeg 子进程超时/取消处理。
6.  再实现 SQLite 课程元数据管理与任务队列。

------------------------------------------------------------------------

*文档根据本次对话中用户提供的浏览器检测结果、请求样本及项目讨论整理。敏感
token、签名和个人标识已省略或脱敏。*
