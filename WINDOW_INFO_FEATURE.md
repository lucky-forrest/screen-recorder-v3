# 鼠标操作窗口信息记录功能

## 🎯 功能概述

本功能是**Advanced Computer Operation Recorder**的增强功能，会自动记录鼠标操作时涉及的窗口和控件详细信息。所有窗口和控件信息都会被追加到原有的键盘、鼠标事件中并导出，无需额外配置。

记录的信息包括：

### 核心 8 项信息
- **窗口句柄** (window_handle) - Windows窗口唯一标识
- **窗口标题** (window_title) - 显示的标题文字
- **窗口类名** (window_class_name) - 窗口类别的系统标识
- **进程ID** (window_process_id) - 运行进程的ID
- **进程名称** (window_process_name) - 可读的进程名称
- **控件句柄** (control_handle) - 窗口内控件句柄
- **控件类名** (control_class_name) - 控件类型标识
- **控件文本** (control_text) - 控件显示的文本内容

## ✨ 功能特点

1. **自动记录**：在录制过程中自动获取，无需用户额外操作
2. **精准定位**：通过pywin32 API获取精确的窗口和控件信息
3. **单进程跟踪**：可识别不同应用程序的窗口
4. **控件级别**：精确到鼠标悬停或点击的具体控件

## 🔧 系统要求

### 必需依赖（已包含在requirements.txt中）

```bash
pywin32>=306      # Windows API调用（窗口/控件）
psutil>=5.9.0     # 进程信息获取
```

说明：
- 所有依赖已包含在项目的 `requirements.txt` 中
- 项目会自动安装这些依赖，无需单独安装
- 其他功能依赖库（opencv-python, pynput等）无需额外安装

## 💡 使用方式

### 自动集成（推荐）

本功能已深度集成到录制系统中，无需额外配置：

1. **启动录制**：点击"开始录制"按钮，窗口信息监控会自动启动
2. **进行操作**：正常使用键盘、鼠标进行操作
3. **查看信息**：窗口信息会自动记录到事件中
4. **导出数据**：CSV/JSON导出会包含所有窗口和控件信息

### 自动记录的事件类型

- ✅ **鼠标移动**：记录鼠标经过的窗口和当前位置的控件信息
- ✅ **鼠标点击**：记录点击位置的窗口和控件信息
- ✅ **UI元素交互**：自动识别UI元素并记录相关窗口信息
- ✅ **键盘输入**：记录输入时的活动窗口信息

导出文件（CSV/JSON）会**自动**包含这些字段，无需手动配置。

### 性能说明

- 窗口信息获取使用进程级缓存，避免重复查询
- 默认分析频率不会影响录制性能
- 在高负载系统上可能略有影响（已优化）

## 📊 导出文件格式

### CSV 格式

CSV文件新增了**窗口信息列**，便于分类和分析：

```csv
timestamp,event_type,detail,x,y,window_title,element_type,element_content,window_handle,window_class_name,window_process_id,window_process_name,control_handle,control_class_name,control_text
2026-03-30T10:00:01.123456,key_press,a,640,480,Notepad,textbox,Test123,264176,Notepad,21388,notepad.exe,12345,EDIT,输入文本
2026-03-30T10:00:02.456789,mouse_click,left,800,600,Browser,textbox,搜索框,145473,CASCADIA_HOSTING_WINDOW_CLASS,22960,WindowsTerminal.exe,3081190,CASCADIA_HOSTING_WINDOW_CLASS,百度一下
2026-03-30T10:00:03.789012,ui_element_interaction,Button,900,650,Calculator,button,=,145473,CASCADIA_HOSTING_WINDOW_CLASS,22960,WindowsTerminal.exe,3456789,WBUTTON,=
```

#### 窗口信息字段说明（新增）

| 字段 | 说明 | 示例 |
|------|------|------|
| `window_handle` | 窗口句柄（唯一标识） | `264176` |
| `window_class_name` | 窗口类名（系统类型） | `Notepad` |
| `window_process_id` | 进程ID | `21388` |
| `window_process_name` | 进程名称（可读） | `notepad.exe` |
| `control_handle` | 控件句柄（子元素） | `12345` |
| `control_class_name` | 控件类名 | `EDIT` |
| `control_text` | 控件文本内容 | `输入文本` |

### JSON 格式

JSON文件包含完整的上下文数据：

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

#### JSON数据结构

```json
{
  "time": "2026-03-30T10:00:00.123456",
  "type": "事件类型",
  "detail": "详细描述",
  "x": 640,
  "y": 480,
  "window_title": "窗口标题",
  "element_type": "UI元素类型",
  "element_content": "UI元素文本",
  "operation_category": "操作分类",
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

## 🔧 技术实现

### 如何工作

本模块使用以下技术实现窗口和控件信息获取：

1. **Windows API调用**
   - 使用 `pywin32` 调用 `FindWindow` 和 `GetWindowText` 获取窗口信息
   - 使用 `EnumWindows` 枚举所有顶层窗口
   - 使用 `GetWindowThreadProcessId` 获取进程信息

2. **控件遍历**
   - 使用 `SendMessage` 和 `WM_GETDLGCODE` 获取控件信息
   - 使用 `EnumChildWindows` 遍历窗口的所有子控件
   - 使用 `GetClassName` 获取控件类名

3. **鼠标位置追踪**
   - 使用 `GetCursorPos` 获取当前鼠标坐标
   - 使用 `WindowFromPoint` 和 `ChildWindowFromPoint` 定位鼠标所在的控件

4. **性能优化**
   - 使用进程级缓存（`_window_cache`）避免重复查询
   - 窗口信息仅在窗口标题或类名变化时更新缓存
   - 控件信息在鼠标位置变化时才重新查询

### 核心模块

**window_info_monitor.py**

本模块提供窗口信息监控功能：

- **WindowInfoMonitor**: 主监控类
  - `get_current_window_info()`: 获取当前鼠标所在窗口的信息
  - `get_hovered_control_info()`: 获取鼠标悬停位置的控件信息
  - `get_window_controls()`: 枚举窗口中的所有控件
  - `update_window_cache()`: 更新窗口信息缓存
  - `get_window_info_cached()`: 从缓存获取窗口信息

- **WindowInfo**: 窗口信息数据类
  - `handle`: 窗口句柄（唯一标识）
  - `title`: 窗口标题（显示的文字）
  - `class_name`: 窗口类名（系统类型）
  - `process_id`: 进程ID
  - `process_name`: 进程名称（可读格式）
  - `visible`: 是否可见
  - `enabled`: 是否启用
  - `active`: 是否是活动窗口
  - `rect`: 窗口位置和尺寸

- **ControlInfo**: 控件信息数据类
  - `handle`: 控件句柄
  - `class_name`: 控件类名
  - `style`: 控件样式
  - `text`: 控件文本内容
  - `caption`: 控件标题
  - `is_enabled`: 是否启用
  - `is_visible`: 是否可见
  - `is_focused`: 是否处于焦点
  - `rect`: 控件位置和尺寸

### 内部集成

本模块已深度集成到 **recorder_engine.py** 中，在以下场景会自动调用窗口信息监控：

1. **鼠标移动事件**：每次鼠标移动时获取当前窗口和控件信息
2. **鼠标点击事件**：点击时记录窗口和控件上下文
3. **UI检测区域**：在检测UI元素时同步更新窗口信息
4. **键盘事件**：记录输入时的活动窗口信息

**无需手动调用任何API**，数据会自动记录到 `OperationEvent` 对象中。

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
    rect: tuple[int, int, int, int]  # 窗口位置和尺寸 (左、 上、 右、 下)
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
    rect: tuple[int, int, int, int]  # 控件位置和尺寸 (左、 上、 右、 下)
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
