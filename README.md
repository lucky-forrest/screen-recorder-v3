# Advanced Computer Operation Recorder

一个强大的电脑操作记录工具，能够智能识别UI元素并详细记录用户的交互行为。

## 功能特性

- **智能UI元素识别**：自动识别文本框、按钮、下拉框等UI元素
- **实时数据监听**：捕获键盘移动、点击、滚轮等事件
- **多格式数据导出**：支持CSV、JSON和MP4三种格式
  - CSV：结构化数据，便于数据分析
  - JSON：完整的事件快照和上下文
  - MP4：操作视频回放，可视化操作流程
- **现代化UI**：友好的Tkinter图形用户界面
  - 可视化实时预览面板
  - 停止录制确认弹窗
  - 保存动画效果
- **状态监控**：实时显示录制状态、事件数量和录制时长

## 技术栈

- **Python >= 3.9**
- **pynput**: 输入设备监控
- **pygetwindow**: 窗口信息获取
- **pyautogui**: 屏幕截图和UI元素识别
- **opencv-python**: 图像处理
- **Pillow**: 图像处理
- **pytesseract**: OCR文字识别
- **tkinter**: GUI界面

## 安装

### 1. 克隆或下载项目

```bash
cd C:\WorkSpace\screen-recorder-v3
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装Tesseract-OCR（用于OCR功能）

- **Windows**: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

## 使用方法

### 基本用法

1. **启动程序**

```bash
python gui.py
```

2. **开始录制**
   - 点击"开始录制 (Start)"按钮
   - 程序会生成一个基于时间戳的Session ID
   - UI元素监测器会自动启动

3. **进行操作**
   - 在屏幕上进行键盘输入、鼠标点击等操作
   - UI元素识别器会自动分析鼠标位置附近的元素
   - 实时日志会显示捕获到的操作

4. **停止录制**
   - 点击"停止录制 (Stop)"按钮
   - 程序会自动导出CSV和JSON格式的数据
   - 视频会在后台生成

5. **查看结果**
   - CSV文件：`output/csv/<session_id>_operation_log.csv`
   - JSON文件：`output/json/<session_id>_operation_log.json`
   - 视频文件：`output/mp4/<session_id>_operation_video.mp4`

   所有生成的文件会自动保存到对应的子文件夹中。

### 命令行使用

```bash
# 直接运行GUI程序
python gui.py

# 或使用启动脚本（Windows）
start_debug.bat
```

## 项目结构

```
screen-recorder-v3/
├── gui.py                      # 主GUI程序
├── recorder_engine.py          # 录制引擎核心
├── event_handler.py            # 事件监听器
├── ui_analyzer.py              # UI元素分析器
├── video_generator.py          # 视频生成器
├── data/
│   └── event.py                # 数据模型定义
├── element_detector/           # UI元素检测模块
│   ├── base_detector.py        # 检测器基类
│   ├── textbox_detector.py     # 文本框检测器
│   ├── button_detector.py      # 按钮检测器
│   └── dropdown_detector.py    # 下拉框检测器
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── config_loader.py        # 配置加载器
│   ├── timestamp_manager.py    # 时间戳管理器
│   └── file_manager.py         # 文件管理器
├── start_debug.bat             # 启动脚本（Windows）
├── config.json                 # 配置文件
├── requirements.txt            # 依赖声明
├── README.md                   # 项目文档
└── CLAUDE.md                   # 开发规范
```

## 配置说明

编辑`config.json`文件自定义录制行为：

```json
{
    "paths": {
        "data": "./data",
        "videos": "./videos"
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

### 配置项说明

#### 路径配置
- `paths.data`: 数据文件（CSV、JSON）保存路径
- `paths.videos`: 视频文件保存路径

#### 录制配置
- `recording.enabled`: 是否启用录制功能

#### 视频配置
- `video.enabled`: 是否启用视频生成
- `video.framerate`: 视频帧率（FPS）
- `video.output_quality`: 输出质量（0-100）

#### UI元素检测配置
- `ui_detection.enabled`: 是否启用UI元素检测
- `ui_detection.confidence_threshold`: 元素识别置信度阈值（0-1）
- `ui_detection.element_detection_frequency`: 元素检测频率（秒）

## 数据格式

### CSV格式

```csv
timestamp, event_type, detail, x, y, window_title, element_type, element_content
2026-03-28 14:23:01, key_press, a,,,Code Editor,textbox,user input
2026-03-28 14:23:02, mouse_click, left,640,360,Browser Window,button,Submit
```

### JSON格式

```json
{
    "session_id": "20260328_142300",
    "start_time": "2026-03-28T14:23:00Z",
    "events": [
        {
            "time": "2026-03-28T14:23:01Z",
            "type": "key_press",
            "detail": "a",
            "context": {
                "window": "Code Editor"
            }
        }
    ]
}
```

## 注意事项

1. **权限要求**：在某些系统中，深度监听可能需要管理员权限
2. **OCR性能**：OCR识别较慢，可以通过关闭ocr_enabled改进性能
3. **资源占用**：持续录制会占用一定CPU和内存，建议定期检查
4. **隐私保护**：记录的交互内容可能包含敏感信息，请谨慎使用

## 开发指南

请参考 `CLAUDE.md` 文件了解项目的代码规范和开发流程。

## 常见问题

**Q: 录制后找不到数据文件？**

A: 检查是否启用了导出功能，数据文件会保存在 `data/` 目录中。

**Q: UI元素识别不准确？**

A: 调整 `config.json` 中的 `confidence_threshold` 参数，通常在0.6-0.8之间。

**Q: OCR无法使用？**

A: 确保已安装Tesseract-OCR并正确配置环境变量。

**Q: 视频生成失败？**

A: 检查 `videos/` 目录权限，确保有写权限。

## 未来改进方向

- 机器学习模型提高UI元素识别精度
- 支持更多UI框架（Electron、Qt、WinForms等）
- 实现操作意图推理（如表单填写完整性判断）
- 添加隐私保护模式过滤敏感信息
- 支持远程同步和分析

## License

MIT License

## 贡献

欢迎提交Issue和Pull Request！
