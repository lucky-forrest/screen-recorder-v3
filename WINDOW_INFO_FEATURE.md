# 鼠标操作窗口信息记录功能

## 功能概述

开始录制后，软件会自动记录鼠标操作时涉及的窗口信息，包括：

- **窗口句柄** (window_handle)
- **窗口标题** (window_title)
- **窗口类名** (window_class_name)
- **进程ID** (window_process_id)
- **进程名称** (window_process_name)
- **控件句柄** (control_handle)
- **控件类名** (control_class_name)
- **控件文本** (control_text)

这些信息会记录在导出的CSV和JSON文件中，便于后续分析和调试。

## 功能特点

1. **自动记录**：在录制过程中自动获取，无需用户额外操作
2. **精准定位**：通过pywin32 API获取精确的窗口和控件信息
3. **单进程跟踪**：可识别不同应用程序的窗口
4. **控件级别**：精确到鼠标悬停或点击的具体控件

## 系统要求

安装以下依赖包：

```bash
pip install pywin32>=306 psutil>=5.9.0
```

## 使用方式

### 1. 基本使用

启动录屏软件后，进行正常操作即可：

```python
from gui import OperationRecorderGUI

# 启动GUI应用
app = OperationRecorderGUI()
app.root.mainloop()
```

### 2. 录制时会自动记录

- **鼠标移动**：记录当前位置的窗口和控件信息
- **鼠标点击**：记录点击位置的窗口和控件信息
- **UI元素交互**：自动识别并记录UI元素信息

导出文件（CSV/JSON）会自动包含这些额外字段。

### 3. 测试窗口信息获取

可以使用测试脚本来验证功能：

```bash
python test_window_info.py
```

测试脚本会：

1. 获取当前窗口的完整信息
2. 枚举窗口中的所有可交互控件
3. 获取鼠标悬停位置的控件信息
4. 输出详细信息到控制台

## 导出文件格式

### CSV格式

```csv
timestamp,event_type,detail,x,y,window_title,element_type,element_content,window_handle,window_class_name,window_process_id,control_handle,control_class_name,control_text
2026-03-30T10:00:00.123456,key_press,Key: Enter,0,0,Python IDE,Other,,16832348,CASCADIA_HOSTING_WINDOW_CLASS,22960,3081190,CASCADIA_HOSTING_WINDOW_CLASS,Claude Code
2026-03-30T10:00:01.456789,mouse_click,Mouse left Click,100,200,Notepad,Other,,3081190,CASCADIA_HOSTING_WINDOW_CLASS,12345,3456789,EDIT,输入文本...
```

### JSON格式

```json
{
  "time": "2026-03-30T10:00:00.123456",
  "type": "key_press",
  "detail": "Key: Enter",
  "x": 0,
  "y": 0,
  "window_title": "Python IDE",
  "element_type": "Other",
  "element_content": "",
  "window_handle": 16832348,
  "window_class_name": "CASCADIA_HOSTING_WINDOW_CLASS",
  "window_process_id": 22960,
  "window_process_name": "WindowsTerminal.exe",
  "control_handle": 3081190,
  "control_class_name": "CASCADIA_HOSTING_WINDOW_CLASS",
  "control_text": "Claude Code",
  "operation_category": "",
  "show_behavior_marker": true
}
```

## 技术实现

### 核心模块

**window_info_monitor.py**

- `WindowInfoMonitor`: 主监控类
  - `get_current_window_info()`: 获取当前鼠标所在窗口的信息
  - `get_hovered_control_info()`: 获取鼠标悬停位置的控件信息
  - `get_window_controls()`: 枚举窗口中的所有控件

### API使用示例

```python
from window_info_monitor import get_monitor

# 获取监控器单例
monitor = get_monitor()

# 获取当前窗口
window_info = monitor.get_current_window_info()
print(f"窗口标题: {window_info.title}")
print(f"窗口句柄: {window_info.handle}")

# 获取控件信息
control_info = monitor.get_hovered_control_info()
if control_info:
    print(f"控件文本: {control_info.text}")
    print(f"控件句柄: {control_info.handle}")
```

### 数据结构

#### WindowInfo

```python
@dataclass
class WindowInfo:
    handle: int                    # 窗口句柄
    title: str                     # 窗口标题
    class_name: str                # 窗口类名
    process_id: int                # 进程ID
    process_name: str              # 进程名称
    visible: bool                  # 窗口是否可见
    enabled: bool                  # 窗口是否启用
    active: bool                   # 窗口是否是活动窗口
    rect: tuple[int, int, int, int]  # 窗口位置和尺寸
```

#### ControlInfo

```python
@dataclass
class ControlInfo:
    handle: int                    # 控件句柄
    class_name: str                # 控件类名
    style: int                     # 控件样式
    text: str                      # 控件文本
    caption: str                   # 控件标题
    is_enabled: bool               # 是否启用
    is_visible: bool               # 是否可见
    is_focused: bool               # 是否处于焦点
    rect: tuple[int, int, int, int]  # 控件位置和尺寸
```

## 应用场景

1. **自动化测试**：记录操作对应的具体窗口和控件，便于测试脚本复现
2. **UI调试**：快速定位问题发生的窗口和控件
3. **用户行为分析**：分析用户在不同应用间切换的模式
4. **屏幕录制回放**：关联操作与具体窗口，提高回放准确性

## 性能考虑

- 窗口信息获取使用进程级缓存，减少重复查询
- 默认分析频率限制在可接受范围内（参见`UIAnalysisConfig.ANALYSIS_INTERVAL`）
- 控件枚举仅在需要时执行，避免不必要的性能开销

## 注意事项

1. 某些系统控件可能没有清晰的标题或文本，这是正常现象
2. 特殊样式控件（如分组框、容器）也可能被记录
3. 获取窗口信息需要适当的系统权限
4. 如果鼠标在窗口外，可能无法获取有效的窗口信息

## 常见问题

**Q: 为什么某些窗口没有记录详细信息？**
A: 可能是窗口不可见、被禁用，或者没有可识别的子控件。

**Q: 如何过滤特定类型的控件？**
A: 可以通过`control_info.style`的模块值来判断控件类型，参考[Windows控件样式文档](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-styles)。

**Q: 可以记录多级窗口结构吗？**
A: 目前支持记录顶层窗口及其直接子控件。如需更深层级的结构，可以扩展`_get_window_info()`方法。
