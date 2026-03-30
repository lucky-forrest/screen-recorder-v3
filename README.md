# Advanced Computer Operation Recorder

一个强大的电脑操作记录工具，能够持续记录用户的交互行为（键盘、鼠标），智能识别UI元素和窗口信息，并支持多种格式的深度分析数据导出。

## 功能特性

### 🔥 核心功能
- **键盘事件录制**：详细记录按键操作，包括修饰键组合
- **鼠标事件录制**：记录鼠标移动、点击（左/右/中键）、滚轮滚动
- **智能UI元素识别**：自动识别文本框、按钮、下拉框等UI元素
- **窗口信息监控**：记录鼠标操作时的窗口和控件详细信息（句柄、类名、进程信息）
- **视频录制功能**：将操作过程录制为可回放的视频

### 📊 数据导出
- **CSV格式**：结构化表格数据，便于Excel打开和分析
- **JSON格式**：包含完整的事件快照、上下文、窗口信息和UI元素元数据
- **MP4视频格式**：可视化操作流程回放

### 💻 现代化界面
- **实时状态面板**：显示录制状态、事件数量、持续时间
- **操作日志窗口**：实时滚动显示所有捕获的操作
- **优雅的交互**：保存动画效果、停止确认弹窗
- **敏感信息标记**：内置行为标记（privacy-aware）

### ⚙️ 配置灵活
- 可通过config.json自定义录制参数
- 支持事件队列大小配置
- 可调UI元素识别置信度
- 自定义视频输出质量和帧率

## 技术栈

- **Python >= 3.9**
- **pynput**: 键盘/鼠标事件监听
- **pygetwindow**: 窗口信息获取
- **pywin32**: Windows API调用（窗口/控件信息）
- **psutil**: 进程信息获取
- **pyautogui**: 屏幕截图和UI元素识别
- **opencv-python**: 图像处理
- **Pillow**: 图像处理
- **pytesseract**: OCR文字识别（可选）
- **tkinter**: GUI界面
- **numpy**: 数值计算

## 安装

### 1. 获取项目

```bash
cd C:\WorkSpace\screen-recorder-v3
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 可选：安装Tesseract-OCR（用于UI元素识别）

- **Windows**: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 4. 启动程序

```bash
# Windows
python gui.py

# 或使用启动脚本（Windows专用）
start_debug.bat
```

## 使用方法

### 基本操作流程

1. **启动程序**
   - 运行 `python gui.py`
   - 程序启动后会显示主界面

2. **开始录制**
   - 点击"开始录制 (Start)"按钮
   - 系统会生成一个时间戳格式的Session ID
   - 界面状态更新为"正在录制..."

3. **进行操作**
   - 在电脑上进行键盘输入、鼠标点击等操作
   - 实时日志窗口会滚动显示所有捕获的事件
   - UI元素识别器会自动分析鼠标位置附近的UI元素
   - 窗口信息监控器会自动记录鼠标操作时的窗口和控件信息

4. **暂停/继续**
   - 可随时点击"暂停录制 (Pause)"按钮暂停录制
   - 再次点击后可继续录制

5. **停止录制**
   - 点击"停止录制 (Stop)"按钮
   - 系统会弹出确认对话框
   - 点击确认后开始导出数据，进度会实时显示

6. **查看导出文件**
   - CSV文件：`output/csv/<SessionID>_operation_log.csv`
   - JSON文件：`output/json/<SessionID>_operation_log.json`
   - 视频文件：`output/mp4/<SessionID>_operation_video.mp4`

所有文件会自动保存到对应的子文件夹中。

## 配置说明

### config.json 配置文件

编辑 `config.json` 来自定义录制行为：

```json
{
    "output": {
        "csv": "./output",
        "json": "./output",
        "mp4": "./output"
    },
    "recording": {
        "enabled": true,
        "event_queue_size": 10000
    },
    "video": {
        "enabled": true,
        "framerate": 30,
        "output_quality": 85
    },
    "ui_detection": {
        "enabled": true,
        "confidence_threshold": 0.7,
        "element_detection_frequency": 0.1
    }
}
```

#### 配置项详细说明

**output (输出路径)**
- `csv`: CSV数据文件保存路径
- `json`: JSON数据文件保存路径
- `mp4`: 视频文件保存路径

**recording (录制设置)**
- `enabled`: 是否启用录制功能
- `event_queue_size`: 事件队列最大容量，防止内存溢出

**video (视频设置)**
- `enabled`: 是否启用视频生成
- `framerate`: 视频帧率（FPS），推荐30-60
- `output_quality`: 输出质量（0-100），推荐80-95

**ui_detection (UI元素检测)**
- `enabled`: 是否启用UI元素识别
- `confidence_threshold`: 元素识别置信度阈值（0-1），推荐0.6-0.8
- `element_detection_frequency`: UI检测间隔（秒），推荐0.05-0.2

## 数据格式说明

### CSV 格式

CSV文件提供了结构化的表格数据，便于在Excel中打开和分析：

```csv
timestamp,event_type,detail,x,y,window_title,element_type,element_content,window_handle,window_class_name,window_process_id,window_process_name,control_handle,control_class_name,control_text
2026-03-30T10:00:01.123,key_press,a,640,480,Notepad,textbox,Test123,264176,Notepad,21388,notepad.exe,12345,EDIT,输入文本
2026-03-30T10:00:02.456,mouse_click,left,800,600,Browser,textbox,搜索框,145473,CASCADIA_HOSTING_WINDOW_CLASS,22960,WindowsTerminal.exe,3081190,CASCADIA_HOSTING_WINDOW_CLASS,百度一下
```

#### 字段说明

- `timestamp`: 事件发生时间
- `event_type`: 事件类型
- `detail`: 详细描述
- `x, y`: 鼠标坐标
- `window_title`: 活动窗口标题
- `element_type`: UI元素类型
- `element_content`: UI元素文本内容
- `window_handle`: 窗口句柄（新增）
- `window_class_name`: 窗口类名（新增）
- `window_process_id`: 窗口进程ID（新增）
- `window_process_name`: 进程名称（新增）
- `control_handle`: 控件句柄（新增）
- `control_class_name`: 控件类名（新增）
- `control_text`: 控件文本（新增）

### JSON 格式

JSON文件提供了完整的上下文数据，包含事件详情、窗口信息和UI元素元数据：

```json
{
  "time": "2026-03-30T10:00:01.123456",
  "type": "key_press",
  "detail": "a",
  "x": 640,
  "y": 480,
  "window_title": "Notepad",
  "element_type": "textbox",
  "element_content": "Test123",
  "operation_category": "输入操作",
  "show_behavior_marker": true,
  "window_handle": 264176,
  "window_class_name": "Notepad",
  "window_process_id": 21388,
  "window_process_name": "notepad.exe",
  "control_handle": 12345,
  "control_class_name": "EDIT",
  "control_text": "输入文本"
}
```

### 视频格式

MP4视频文件以原样记录操作流程，可回看用户的完整操作：

- **格式**: MP4
- **帧率**: 默认30 FPS
- **质量**: 默认85（可配置）
- **编码**: H.264
- **分辨率**: 与源屏幕相同

## 项目结构

```
screen-recorder-v3/
├── gui.py                      # 主GUI程序（操作记录器界面）
├── recorder_engine.py          # 录制引擎核心（事件收集和处理）
├── window_info_monitor.py      # 窗口信息监控器（新增）
├── event_handler.py            # 事件监听器
├── video_generator.py          # 视频生成器
├── element_detector/           # UI元素检测模块
│   ├── base_detector.py        # 检测器基类
│   ├── textbox_detector.py     # 文本框检测器
│   ├── button_detector.py      # 按钮检测器
│   └── dropdown_detector.py    # 下拉框检测器
├── data/
│   └── event.py                # 数据模型定义
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── config_loader.py        # 配置加载器
│   ├── file_manager.py         # 文件管理器
│   ├── path_manager.py         # 路径管理器
│   └── timestamp_manager.py    # 时间戳管理器
├── config/                     # 配置模块
│   └── constants.py            # GUI配置常量
├── updater/                    # 更新模块
├── output/                     # 输出目录（自动生成）
│   ├── csv/                    # CSV格式数据
│   ├── json/                   # JSON格式数据
│   └── mp4/                    # MP4视频文件
├── start_debug.bat             # Windows启动脚本
├── requirements.txt            # Python依赖声明
├── config.json                 # 应用配置文件
├── README.md                   # 项目文档
├── WINDOW_INFO_FEATURE.md      # 窗口信息功能文档
└── CLAUDE.md                   # 开发规范文档
```

## 窗口信息功能

本项目支持鼠标操作窗口信息记录功能，可自动获取以下详细信息：

- **窗口句柄** (window_handle)
- **窗口标题** (window_title)
- **窗口类名** (window_class_name)
- **进程ID** (window_process_id)
- **进程名称** (window_process_name)
- **控件句柄** (control_handle)
- **控件类名** (control_class_name)
- **控件文本** (control_text)

这些信息会被追加到所有导出的CSV和JSON文件中，可用于：
- 按窗口分类分析操作行为
- 定位特定应用的操作日志
- 自动化测试复现（关联操作到具体窗口）
- 用户行为分析（应用间切换模式）

查看 `WINDOW_INFO_FEATURE.md` 了解更多详情。

## 高级功能

### 录制消息名称

在GUI界面中，可以自定义录制会话的命名方式，便于按项目或任务分类管理。

### 暂停/恢复功能

支持在录制过程中暂停和恢复，适用于不需要记录中间某些操作的场景。

### 实时状态监控

界面实时显示：
- 录制状态
- 已捕获事件数量
- 录制持续时间
- 当前活动窗口

## 注意事项

### 1. 权限要求
- 在某些Linux系统上可能需要管理员权限才能正确录制
- 部分系统窗口（如系统控件）可能没有可读的标题

### 2. 性能考虑
- 持续录制会占用一定的CPU和内存资源
- 音频录制功能需安装额外音频相关库
- UI元素识别依赖OCR，可能影响性能（通过降低检测频率改善）

### 3. 隐私保护
- 录制的内容可能包含敏感信息（如密码、个人信息）
- 建议在处理敏感数据时谨慎使用录制工具
- 数据导出文件可能包含窗口标题等可识别信息

### 4. 文件大小
- 录制时长越长，文件越大，建议定期检查磁盘空间
- 视频文件会占用较大空间，可根据需要调整输出质量

## 常见问题

### Q: 录制后找不到数据文件？

**A**: 请检查：
1. 是否成功点击"停止录制"按钮
2. `output/` 目录是否具有写权限
3. 配置文件中的输出路径是否正确

### Q: UI元素识别不准确？

**A**: 尝试调整配置：
1. 降低 `ui_detection.confidence_threshold` 到 0.6-0.7
2. 增加 `ui_detection.element_detection_frequency` 到 0.2-0.3 秒
3. 确保目标窗口是活跃状态

### Q: 窗口信息没有记录？

**A**: 暂时未记录窗口信息是正常现象。请确保：
1. 鼠标当前在活动窗口内
2. 目标窗口未被禁用
3. 程序已正确调用 `window_info_monitor` 模块

### Q: OCR无法识别文字？

**A**:
1. 检查Tesseract-OCR是否正确安装
2. 确保已配置环境变量 `TESSDATA_PREFIX`
3. 尝试调整图片对比度或分辨率

### Q: 视频生成失败？

**A**:
1. 检查 `videos/` 目录是否有写权限
2. 确认操作系统支持MP4格式录制
3. 降低 `video.output_quality` 尝试生成

### Q: Python版本要求？

**A**: 项目需要 Python 3.9 或更高版本。请使用：
```bash
python --version
```

### Q: 如何卸载/退出程序？

**A**:
- 点击"停止录制"按钮（会弹出确认）
- 或者直接关闭程序窗口（会自动停止录制并提示保存）

## 应用场景

### 1. 自动化测试与技术支持
- 记录操作步骤，用于测试用例验证
- 记录用户问题报告，便于复现和修复

### 2. 用户行为分析
- 分析用户在特定应用或系统中的操作模式
- 研究用户交互习惯和效率

### 3. 教育与培训
- 录制操作教程和最佳实践
- 生成可回放的学习材料

### 4. 系统管理和维护
- 记录账号登录过程
- 监控管理员操作日志

### 5. 流程审计与合规
- 符合部分行业的日志记录要求
- 操作行为的持久化记录

## 未来改进方向

- [ ] 添加音频录制功能（麦克风输入）
- [ ] 支持多显示器配置
- [ ] 提供数据统计分析面板
- [ ] 实现本地数据库存储
- [ ] 支持远程数据同步和分析
- [ ] 集成机器学习模型提高识别精度
- [ ] 增加更多UI元素检测类型（表格、树形控件等）

## 开发指南

查看 `CLAUDE.md` 了解项目的代码规范和开发流程。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.1.0 (2026-03-30)
- ✨ 新增窗口信息记录功能
- ✨ 支持控件级别信息记录
- 📝 完善文档结构

### v1.0.0 (2026-03-27)
- 🎉 初始版本发布
- ✨ 支持键盘、鼠标事件录制
- ✨ 支持CSV和JSON导出
- ✨ 支持视频录制
- ✨ UI元素识别
