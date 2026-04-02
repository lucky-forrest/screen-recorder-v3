"""GUI对话框模块

包含开始录制、停止录制等确认对话框。
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from pathlib import Path


class RecordingDialog:
    """开始录制对话框"""

    def __init__(
        self,
        parent: tk.Tk,
        application_name: Optional[str] = None
    ):
        """初始化对话框

        Args:
            parent: 父窗口
            application_name: 默认应用名称
        """
        self.parent = parent
        self.application_name = application_name or ""
        self.result: Optional[str] = None

        self._create_dialog()

    def _create_dialog(self):
        """创建对话框UI"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("开始录制")
        self.window.geometry("520x320")
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.configure(bg="#f0f0f0")

        # 居中显示
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 520) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 320) // 2
        self.window.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(
            title_frame,
            text="开始录制前",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#2c3e50"
        ).pack(anchor=tk.W)

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # 应用名称输入
        input_frame = ttk.LabelFrame(main_frame, text="录制应用名称", padding="15")
        input_frame.pack(fill=tk.X)

        ttk.Label(
            input_frame,
            text="请输入或选择要录制的应用：",
            font=("Microsoft YaHei", 11)
        ).pack(anchor=tk.W, pady=(0, 8))

        self.application_name_entry = ttk.Entry(
            input_frame,
            font=("Microsoft YaHei", 12),
            width=45
        )
        self.application_name_entry.insert(0, self.application_name or "请输入应用名称")
        self.application_name_entry.pack(fill=tk.X, ipady=6)
        self.application_name_entry.focus()

        ttk.Label(
            input_frame,
            text="* 此名称将用于筛选录制的事件",
            font=("Microsoft YaHei", 9),
            foreground="#666666"
        ).pack(anchor=tk.W, pady=(5, 0))

        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=0)

        self.cancel_button = ttk.Button(
            btn_frame,
            text="取消",
            command=self._on_cancel,
            width=10
        )
        self.cancel_button.grid(row=0, column=1, padx=(0, 10), pady=5)

        self.start_button = ttk.Button(
            btn_frame,
            text="开始录制",
            command=self._on_start,
            width=12
        )
        self.start_button.grid(row=0, column=2, padx=(0, 5), pady=5)

    def show(self) -> Optional[str]:
        """显示对话框并等待用户输入

        Returns:
            Optional[str]: 用户输入的应用名称，取消返回None
        """
        self.window.wait_window()
        return self.result

    def _on_cancel(self):
        """取消按钮回调"""
        self.result = None
        self.window.destroy()

    def _on_start(self):
        """开始按钮回调"""
        self.result = self.application_name_entry.get().strip()
        if not self.result:
            self.result = None
        self.window.destroy()


class StopRecordingDialog:
    """停止录制确认对话框"""

    def __init__(
        self,
        parent: tk.Tk,
        session_id: str,
        message_name: str
    ):
        """初始化对话框

        Args:
            parent: 父窗口
            session_id: 会话ID
            message_name: 默认消息名称
        """
        self.parent = parent
        self.session_id = session_id
        self.default_message_name = message_name
        self.result: Optional[str] = None

        self._create_dialog()

    def _create_dialog(self):
        """创建对话框UI"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("停止录制确认")
        self.window.geometry("520x300")
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.configure(bg="#f0f0f0")

        # 居中显示
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 520) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 300) // 2
        self.window.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(
            title_frame,
            text="⚠️",
            font=("Arial", 20)
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(
            title_frame,
            text="确定要停止录制并保存文件吗？",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#2c3e50"
        ).pack(side=tk.LEFT)

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # 录制信息
        input_frame = ttk.LabelFrame(main_frame, text="录制信息", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            input_frame,
            text="录制名称（可自定义）：",
            font=("Microsoft YaHei", 11)
        ).pack(anchor=tk.W, pady=(0, 8))

        self.message_name_entry = ttk.Entry(
            input_frame,
            font=("Microsoft YaHei", 12),
            width=40
        )
        default_message = f"录制会话_{self.session_id}"
        self.message_name_entry.insert(0, default_message)
        self.message_name_entry.pack(fill=tk.X, ipady=6)
        self.message_name_entry.focus()

        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=0)
        btn_frame.columnconfigure(2, weight=0)

        self.cancel_button = ttk.Button(
            btn_frame,
            text="取消",
            command=self._on_cancel,
            width=10
        )
        self.cancel_button.grid(row=0, column=1, padx=(0, 10), pady=5)

        self.confirm_button = ttk.Button(
            btn_frame,
            text="确认保存",
            command=self._on_confirm,
            width=12
        )
        self.confirm_button.grid(row=0, column=2, padx=(0, 5), pady=5)

    def show(self) -> Optional[str]:
        """显示对话框并等待用户输入

        Returns:
            Optional[str]: 用户输入的消息名称，取消返回None
        """
        self.window.wait_window()
        return self.result

    def _on_cancel(self):
        """取消按钮回调"""
        self.result = None
        self.window.destroy()

    def _on_confirm(self):
        """确认按钮回调"""
        self.result = self.message_name_entry.get().strip()
        if not self.result:
            self.result = f"录制会话_{self.session_id}"
        self.window.destroy()


def show_error dialog(parent: tk.Tk, title: str, message: str):
    """显示错误对话框

    Args:
        parent: 父窗口
        title: 对话框标题
        message: 错误消息
    """
    messagebox = tk.Toplevel(parent)
    messagebox.title(title)
    messagebox.resizable(False, False)
    messagebox.transient(parent)
    messagebox.grab_set()
    messagebox.configure(bg="#f0f0f0")

    main_frame = ttk.Frame(messagebox, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        main_frame,
        text=f"❌ {message}",
        font=("Microsoft YaHei", 14, "bold"),
        foreground="#D32F2F"
    ).pack(anchor=tk.W, pady=(0, 20))

    ttk.Button(
        main_frame,
        text="确定",
        command=messagebox.destroy,
        width=20
    ).pack(anchor=tk.CENTER)


def show_info_dialog(parent: tk.Tk, title: str, message: str):
    """显示信息对话框

    Args:
        parent: 父窗口
        title: 对话框标题
        message: 信息消息
    """
    messagebox = tk.Toplevel(parent)
    messagebox.title(title)
    messagebox.resizable(False, False)
    messagebox.transient(parent)
    messagebox.grab_set()
    messagebox.configure(bg="#f0f0f0")

    main_frame = ttk.Frame(messagebox, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        main_frame,
        text=f"✨ {message}",
        font=("Microsoft YaHei", 14),
        foreground="#388E3C"
    ).pack(anchor=tk.W, pady=(0, 20))

    ttk.Button(
        main_frame,
        text="确定",
        command=messagebox.destroy,
        width=20
    ).pack(anchor=tk.CENTER)
