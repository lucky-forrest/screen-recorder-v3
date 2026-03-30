# Python 项目代码规范

## 代码风格

### 命名规范

#### 变量和函数
- 使用**小写字母**和下划线分隔：`user_name`, `current_time`, `is_valid`
- 私有变量前缀单下划线：`_internal_var`
- 常量使用大写字母和下划线：`MAX_RETRIES`, `DEFAULT_TIMEOUT`
- 函数名使用**动词开头**，语义明确：`get_user_data()`, `validate_input()`

#### 类名
- 使用**驼峰命名法**(CapWords)
- 首字母大写，单词间无分隔：`DatabaseManager`, `EventHandler`
- 私有类前缀单下划线：`_BaseModel`

#### 模块名
- 使用小写字母和下划线：`config_manager`, `keyboard_monitor`
- 避免使用单字母变量名(除了循环变量i/j)
- 避免使用无意义的缩写

### 文件组织

#### 项目结构
```
screen-recorder-v3/
├── gui.py                      # 主GUI程序（操作记录器界面）
├── recorder_engine.py          # 录制引擎核心
├── window_info_monitor.py      # 窗口信息监控器
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
├── README.md                   # 项目主文档
├── WINDOW_INFO_FEATURE.md      # 窗口信息功能文档
├── CLAUDE.md                   # 开发规范文档
└── .gitignore
```

#### 每个文件
- 文件名与类名保持一致(*-monitor.py 对应 Monitor类)
- 每个模块必须有`__init__.py`
- 文件内不包含空行超过2行
- 每个模块一行导入，分块分组：`标准库` → `第三方库` → `本地模块`

## 代码编写规范

### 推荐的结构

```python
"""模块描述

长篇文档字符串说明模块功能

参考文档:
- https://example.com
"""
import sys
import os
from typing import Optional

# 常量
DEFAULT_PORT = 8080
MAX_RETRIES = 3

# 第三方库
import requests

# 本地模块
from core.keyboard_monitor import KeyboardListener
from core.mouse_monitor import MouseListener


class DatabaseManager:
    """数据库管理类

    该类负责数据库的初始化、连接管理和数据操作
    """

    def __init__(self, db_path: str):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """获取数据库连接

        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        if self._connection is None:
            self._connect()
        return self._connection

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> List[Dict]:
        """执行查询并返回结果

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            List[Dict]: 查询结果字典列表

        Raises:
            DatabaseError: 数据库操作失败时抛出
            QueryError: 查询语法错误时抛出
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return self._fetch_all(cursor)
        except sqlite3.Error as e:
            raise DatabaseError(f"Database query failed: {e}")

    def _connect(self):
        """建立数据库连接"""
        # 连接逻辑
        pass

    def _fetch_all(self, cursor):
        """获取所有结果"""
        rows = cursor.fetchall()
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in rows]


if __name__ == "__main__":
    # 简单的测试代码
    manager = DatabaseManager("test.db")
    print(f"Database connected: {manager.connection is not None}")
```

### 注释规范

- **模块级文档字符串**：说明模块的用途和关键依赖
- **类文档字符串**：说明类的用途、继承关系、重要方法
- **方法文档字符串**：使用Google风格，包含Args/Returns/Raises
- **复杂逻辑行内注释**：解释非显而易见的代码
- **避免重复代码**：复杂逻辑抽取为单独方法后再行内只保留调用

```python
# 不推荐
def calculate_distance(point_a, point_b):
    # 计算两点距离
    import math
    if not point_a or not point_b:
        return 0.0
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    return math.sqrt(dx*dx + dy*dy)

# 推荐
def calculate_distance(point_a, point_b):
    """计算空间中两点之间的欧几里得距离"""
    if not point_a or not point_b:
        return 0.0
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    return math.sqrt(dx ** 2 + dy ** 2)
```

### 类型注解

- 所有函数必须有返回类型注解
- 可选参数使用`Optional[type]`
- 集合类型使用`List[type]`, `Dict[str, type]`
- 如果类型过多，使用`typing.Any`或自定义类型别名

```python
from typing import List, Dict, Optional, Tuple
from datetime import datetime

Operation = Dict[str, any]  # 类型别名


def process_operations(
    operations: List[Operation],
    threshold: int
) -> Tuple[List[Operation], List[Operation]]:
    """处理操作列表，分离重要操作和注释操作

    Args:
        operations: 操作列表
        threshold: 重要操作的阈值

    Returns:
        元组: (重要操作列表, 注释/省略操作列表)
    """
    # 实现
    pass
```

### 异常处理

- 直接捕获**具体异常**类型，不使用宽泛的Exception
- 在except块中提供有意义的错误信息
- 使用finally确保资源释放
- 自定义异常需要继承Exception并添加文档字符串

```python
# 不推荐
try:
    read_file()
except Exception as e:
    print(f"Error: {e}")

# 推荐
from core.exceptions import ConfigurationError, OSError

try:
    read_configuration()
except (ConfigurationError, OSError) as e:
    raise ConfigurationError(f"Failed to load config: {e}") from e
finally:
    if file_handle:
        file_handle.close()
```

### 黄金法则

1. **DRY (Don't Repeat Yourself)**: 相同功能抽取为函数或方法
2. **SOLID原则**: 遵循单一职责、开闭原则
3. **KISS (Keep It Simple)**: 保持代码简单易懂
4. **cURLY (Check Your Release Version)**: 提交前检查版本、测试
5. **写文档**：复杂代码必须有清晰的文档字符串

## 文档要求

### README.md
- 项目简介
- 安装步骤
- 使用说明
- 示例代码
- 常见问题(FAQ)

### 模块级别
- 详细的函数/类文档字符串
- 返回值和异常的说明
- 使用示例

### API文档
- 主要函数/方法的详细说明
- 输入输出参数
- 性能特征说明

## 测试规范

### 测试结构
- 每个模块对应一个或多个测试文件
- 测试函数以`test_`开头
- 单元测试和集成测试分离

### 测试示例

```python
# tests/test_keyboard_monitor.py
import unittest
from unittest.mock import MagicMock
from core.keyboard_monitor import KeyboardListener


class TestKeyboardListener(unittest.TestCase):
    """键盘监听器单元测试"""

    def setUp(self):
        """初始化测试环境"""
        self.sample_key = 'a'
        self.listener = KeyboardListener()

    def test_record_key_press(self):
        """测试记录按键事件"""
        mock_callback = MagicMock()
        self.listener.add_callback(mock_callback)

        # 触发按键事件
        self.listener._on_press(self.sample_key)

        # 验证回调被调用
        mock_callback.assert_called_once_with(
            'keyboard',
            'a',
            timestamp=self.listener.last_timestamp
        )

    def test_invalid_key_raises_error(self):
        """测试非法按键应抛出异常"""
        with self.assertRaises(ValueError):
            self.listener._on_press(None)


if __name__ == '__main__':
    unittest.main()
```

## 性能优化原则

1. **批量操作**: 数据库批量写入而非逐条插入
2. **懒加载**: 只在需要时加载数据
3. **缓存常用数据**: 使用字典或LRU缓存
4. **异步处理**: I/O操作使用asyncio或线程池
5. **避免创建临时对象**: 在循环外创建复用

```python
# 不推荐 - 内存占用高
def process_large_data(data_list):
    results = []
    for item in data_list:
        result = transform(item)
        results.append(result)
    return results

# 推荐 - 内存友好
def process_large_data(data_list):
    results = []
    for item in data_list:
        results.append(transform(item))
    return results

def slow_transform(item):
    # 返回生成器而非列表
    for result in expensive_process(item):
        yield result
```

## Git提交规范

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型(type)
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建工具/辅助工具变更

### 示例

```
feat(keyboard_monitor): add hotkey support

Implement keyboard hotkey registration with multi-key combinations.
Support for modifier keys (Ctrl, Alt, Shift) and custom shortcuts.

Fixes #123
```

## 质量检查

### 提交前检查清单
- [ ] 代码遵循本规范
- [ ] 所有代码通过单元测试
- [ ] 添加了必要的文档字符串
- [ ] 导入语句清楚，无重复导入
- [ ] 没有硬编码的魔法数字
- [ ] 移除了调试代码(print语句)
- [ ] Git提交信息符合规范
- [ ] 无语法错误和Lint警告

### 抽象和封装原则
- 避免过早优化
- 接口层级不超过3层
- 不暴露内部实现细节
- 提供清晰的访问接口

## 开发流程建议

1. **功能拆分**: 将复杂功能拆分为小块
2. **渐进实现**: 从最简单的版本开始，逐步完善
3. **持续重构**: 随着理解的深入优化代码
4. **测试驱动**: 编写测试用例先行
5. **代码审查**: 关键代码需要审查

## 版本号规范

遵循语义化版本(semantic versioning): `MAJOR.MINOR.PATCH`

- MAJOR: 不兼容的API变更
- MINOR: 向下兼容的新功能
- PATCH: 向下兼容的bug修复

示例: 2.1.3 → 3.0.0 → 3.1.0 → 3.1.1

## 项目实际功能说明

### 核心功能模块

#### 1. 录制引擎 (recorder_engine.py)
负责收集和记录所有事件数据，包括：
- 键盘事件监听
- 鼠标事件监听
- UI元素识别和检测
- 窗口信息记录
- 暂停/恢复/停止控制
- 数据导出（CSV/JSON格式）

#### 2. 窗口信息监控 (window_info_monitor.py)
自动记录鼠标操作时的窗口和控件信息：
- 窗口句柄和标题
- 窗口类名和进程ID
- 进程名称
- 控件句柄和类名
- 控件文本内容

这些信息被**追加到**原有的event_handler模块中，用于增强录制数据的上下文信息。

#### 3. UI元素检测 (element_detector/)
智能识别屏幕上的UI元素：
- 文本框 (TextboxDetector)
- 按钮 (ButtonDetector)
- 下拉框 (DropdownDetector)

使用pyautogui和OCR技术进行元素识别。

#### 4. 视频生成 (video_generator.py)
将操作过程录制为可回放的视频：
- 高帧率录制（默认30 FPS）
- 可配置质量（默认85）
- 支持输出MP4格式

#### 5. GUI界面 (gui.py)
基于Tkinter的现代化界面：
- 开始/暂停/停止控制
- 实时状态显示（事件数、录制时长）
- 操作日志输出
- 保存动画效果
- 停止确认弹窗

### 数据模型 (data/event.py)

定义了完整的事件数据结构：

**核心事件类：**
- `KeyboardEvent`: 键盘事件
- `MouseEvent`: 鼠标事件
- `UIElementInfo`: UI元素信息
- `WindowSpecificInfo`: 窗口和控件详细信息（新增）
- `OperationEvent`: 综合操作事件

**扩展事件类：**
- `SessionStartEvent`: 录制会话开始
- `SessionEndEvent`: 录制会话结束

### 配置系统 (config/)

在config.json中控制录制行为：

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

### 导出格式

#### CSV格式
```csv
timestamp,event_type,detail,x,y,window_title,element_type,element_content,window_handle,window_class_name,window_process_id,window_process_name,control_handle,control_class_name,control_text
2026-03-30T14:23:01,key_press,a,100,200,Code Editor,textbox,user input,264176,Notepad,21388,notepad.exe,12345,EDIT,输入文本
```

#### JSON格式
```json
{
    "time": "2026-03-30T14:23:01Z",
    "type": "key_press",
    "detail": "a",
    "x": 100,
    "y": 200,
    "window_title": "Code Editor",
    "element_type": "textbox",
    "element_content": "用户输入",
    "window_handle": 264176,
    "window_class_name": "Notepad",
    "window_process_id": 21388,
    "window_process_name": "notepad.exe",
    "control_handle": 12345,
    "control_class_name": "EDIT",
    "control_text": "输入文本",
    "operation_category": "",
    "show_behavior_marker": true
}
```
