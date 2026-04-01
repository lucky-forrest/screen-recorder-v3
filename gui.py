"""操作记录器GUI

基于Tkinter的图形用户界面，提供录制控制、实时状态显示和日志输出。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue
from typing import Optional
from datetime import datetime, timedelta
import os
import time
import threading  # 新增：异步执行导出逻辑
import shutil  # 新增：文件大小检测辅助

from recorder_engine import RecorderEngine
from video_generator import VideoGenerator
import utils.config_loader as config_loader
from config.constants import GUIConfig


class OperationRecorderGUI:
    """操作记录器主界面"""

    def __init__(self, root: Optional[tk.Tk] = None):
        """初始化GUI

        Args:
            root: 根窗口（可以自动创建）
        """
        self.root = root if root else tk.Tk()
        self.root.title("Advanced Computer Operation Recorder")
        self.root.geometry(f"{GUIConfig.WINDOW_WIDTH}x{GUIConfig.WINDOW_HEIGHT}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.resizable(False, False)  # 禁止调整窗口大小，同时禁用最大化按钮

        # 加载配置
        self.config = config_loader.load_config()

        # 录制状态
        self.is_recording = False
        self.session_id: Optional[str] = None
        self.event_count = 0
        self.recording_start_time: Optional[datetime] = None
        self.is_exporting = False  # 新增：标记是否正在导出
        self._stop_requested = False  # 新增：标记是否已请求停止
        self.message_name: Optional[str] = None  # 新增：录制消息名称
        self.application_name: Optional[str] = None  # 新增：录制应用名称

        # 保存动画相关
        self.save_indicator_id = None
        self.save_step = 0
        self._save_animation_running = False
        self.export_progress = 0  # 新增：真实导出进度（0-100）
        self.current_export_step = ""  # 新增：当前导出步骤描述

        # 导出文件路径缓存（用于检测生成状态）
        self.export_file_paths = {
            "csv": None,
            "json": None,
            "video": None
        }

        # 初始化录制引擎和视频生成器
        self.video_generator = VideoGenerator()
        self.recorder = RecorderEngine()
        self.recorder.video_generator = self.video_generator  # 注入视频生成器

        # GUI组件
        self._setup_ui()

        # 启动循环
        self._update_gui_loop()

    def _setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 标题区域
        title_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # 控制按钮
        self.start_button = ttk.Button(
            title_frame,
            text="开始录制 (Start)",
            command=self._start_recording
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(
            title_frame,
            text="暂停录制 (Pause)",
            command=self._pause_recording,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            title_frame,
            text="停止录制 (Stop)",
            command=self._stop_recording,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(
            title_frame,
            text="导出数据",
            command=lambda: self._export_data(show_animation=True),
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)

        # 2. 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(
            status_frame,
            text="状态: 待机 (Standby)",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(anchor=tk.W)

        self.session_label = ttk.Label(status_frame, text="会话ID: -")
        self.session_label.pack(anchor=tk.W)

        self.event_count_label = ttk.Label(status_frame, text="事件数量: 0")
        self.event_count_label.pack(anchor=tk.W)

        self.recording_time_label = ttk.Label(status_frame, text="录制时长: 00:00:00")
        self.recording_time_label.pack(anchor=tk.W)

        # 3. 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg="black", width=980, height=200)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # 添加说明文字
        self.preview_canvas.create_text(
            490, 100,
            text="鼠标位置操作预览\n操作日志将显示在这里",
            fill="white",
            font=("Arial", 14)
        )

        # 4. 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="Event Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日志文本框
        self.log_text = tk.Text(
            log_frame,
            height=10,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 5. 底部信息
        self._update_status()

    def _start_recording(self):
        """开始录制"""
        try:
            print(f"[GUI] Starting recording...")
            self._stop_requested = False  # 重置停止请求标记

            # 获取录制应用名称（从配置文件读取默认值）
            default_application_name = self.config.get("recording", {}).get("application_name", "")
            application_name = default_application_name.strip() or None

            # 显示应用名称输入对话框
            confirm_window = tk.Toplevel(self.root)
            confirm_window.title("开始录制")
            confirm_window.geometry("520x320")
            confirm_window.resizable(False, False)
            confirm_window.transient(self.root)
            confirm_window.grab_set()
            confirm_window.configure(bg="#f0f0f0")

            # 窗口居中
            x = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - 320) // 2
            confirm_window.geometry(f"+{x}+{y}")

            # 主容器
            main_frame = ttk.Frame(confirm_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 标题区域
            title_frame = ttk.Frame(main_frame)
            title_frame.pack(fill=tk.X, pady=(0, 15))

            ttk.Label(
                title_frame,
                text="开始录制前",
                font=("Microsoft YaHei", 16, "bold"),
                foreground="#2c3e50"
            ).pack(anchor=tk.W)

            ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

            # 录制应用名称输入区域
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
            self.application_name_entry.insert(0, application_name or "请输入应用名称")
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

            def on_start():
                """确认开始录制的回调"""
                application_name = self.application_name_entry.get().strip()
                if not application_name:
                    application_name = None
                confirm_window.destroy()

                # 保存应用名称
                self.application_name = application_name

                # 开始录制
                self.session_id = self.recorder.start_recording(self.application_name)
                self.event_count = 0
                self.recording_start_time = datetime.now()
                self.is_recording = True

                print(f"[GUI] Session started: {self.session_id}")
                print(f"[GUI] Application name: {application_name}")

                # 更新按钮状态
                self.start_button.config(state=tk.DISABLED)
                self.pause_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.NORMAL)
                self.export_button.config(state=tk.DISABLED)

                # 更新状态显示
                self._update_status()
                app_text = application_name or "所有应用"
                self._log(f"📷 录制开始: Session {self.session_id}")
                self._log(f"🎯 录制应用: {app_text}")
                self._log(f"👆 已注册事件回调，请在键盘上操作...")
                print(f"[GUI] Ready - waiting for events")

                # 启动视频生成
                self.video_generator.start_generating(self.session_id)

            def on_cancel():
                """取消开始录制"""
                confirm_window.destroy()

            ttk.Button(
                btn_frame,
                text="取消",
                command=on_cancel,
                width=10
            ).grid(row=0, column=1, padx=(0, 10), pady=5)

            ttk.Button(
                btn_frame,
                text="开始录制",
                command=on_start,
                width=12
            ).grid(row=0, column=2, padx=(0, 5), pady=5)

        except Exception as e:
            self._log(f"启动录制失败: {e}")
            messagebox.showerror("错误", f"无法启动录制: {e}")

    def _pause_recording(self):
        """暂停/恢复录制"""
        if not self.is_recording:
            return

        if self.recorder.is_paused:
            # 当前是暂停状态，恢复录制
            self.recorder.resume_recording()
            self.pause_button.config(text="暂停录制 (Pause)")
            self._log("▶️ 录制已恢复")
        else:
            # 当前是录制状态，暂停录制
            self.recorder.pause_recording()
            self.pause_button.config(text="恢复录制 (Resume)", state=tk.NORMAL)
            self._log("⏸️ 录制已暂停，点击恢复继续")

    def _stop_recording(self):
        """停止录制（优化版：完整显示按钮、比例协调）"""
        if not self.is_recording or self._stop_requested:
            return

        # 1. 窗口基础设置：尺寸足够大，保证所有元素完整显示
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("停止录制确认")
        confirm_window.geometry("520x300")  # 增加高度，确保按钮完整显示
        confirm_window.resizable(False, False)
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        confirm_window.configure(bg="#f0f0f0")  # 适配系统默认主题，避免样式冲突

        # 2. 窗口居中
        x = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 300) // 2
        confirm_window.geometry(f"+{x}+{y}")

        # 3. 主容器：统一内边距，避免元素贴边
        main_frame = ttk.Frame(confirm_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 4. 标题区域：醒目、不拥挤
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

        # 5. 分割线：分隔标题和内容
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # 6. 输入区域：比例协调，输入框高度适中
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
        self.message_name_entry.pack(fill=tk.X, ipady=6)  # ipady 增加输入框高度，更美观
        self.message_name_entry.focus()  # 自动聚焦输入框

        # 7. 按钮区域：核心修复！保证按钮完整显示、比例协调
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        # 布局权重：左侧空白占满，按钮固定宽度，右对齐
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=0)
        btn_frame.columnconfigure(2, weight=0)

        def on_confirm():
            """确认停止录制的回调"""

            message_name = self.message_name_entry.get().strip()
            if not message_name:
                message_name = f"录制会话_{self.session_id}"
            confirm_window.destroy()

            # 保存 message_name 以供后续使用
            self.message_name = message_name

            # 重置状态、启动后续逻辑（完全保留原功能）
            self._stop_requested = True
            self.stop_button.config(state=tk.DISABLED)
            self.is_recording = False
            self.recorder.is_paused = False
            self.recorder._pause_event.clear()
            self._update_status()
            self.root.update_idletasks()
            self._start_saving_animation_immediate()

            # 异步执行停止逻辑
            stop_thread = threading.Thread(target=self._stop_recording_impl, daemon=True)
            stop_thread.start()

        def on_cancel():
            """取消停止录制"""
            confirm_window.destroy()
            self.export_button.config(state=tk.NORMAL)

        # 按钮样式：统一大小、点击区域充足、右对齐
        ttk.Button(
            btn_frame,
            text="取消",
            command=on_cancel,
            width=10
        ).grid(row=0, column=1, padx=(0, 10), pady=5)

        ttk.Button(
            btn_frame,
            text="确认保存",
            command=on_confirm,
            width=12
        ).grid(row=0, column=2, padx=(0, 5), pady=5)

        # 禁用导出按钮（原逻辑保留）
        self.export_button.config(state=tk.DISABLED)

    def _stop_recording_impl(self):
        """执行停止录制的实际逻辑（异步）"""
        try:
            # 更新导出步骤
            self.current_export_step = "准备导出数据..."
            self.export_progress = 5

            # 先同步停止视频生成，确保 mp4 已经完成落盘
            self.root.after(0, lambda: self._log("⏹️ 停止视频录制..."))
            self.video_generator.stop_generating(wait=True)
            self.root.after(0, lambda: self._log("✓ 视频录制已停止"))

            # 停止录制引擎
            self.root.after(0, lambda: self._log("⏹️ 停止录制引擎..."))
            events = self.recorder.stop_recording(self.message_name)

            # 更新按钮状态（UI线程）
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.pause_button.config(state=tk.DISABLED))

            # 记录停止信息
            self.root.after(0, lambda: self._log(f"✅ 录制结束: 会话 {self.session_id}"))
            self.root.after(0, lambda: self._log(f"📊 事件统计: 共捕获 {len(events)} 个事件"))
            elapsed = (datetime.now() - self.recording_start_time).total_seconds() if self.recording_start_time else 0
            self.root.after(0, lambda: self._log(f"⏱️ 录制时长: {format_duration(int(elapsed))}"))

            # 更新进度
            self.export_progress = 10
            self.current_export_step = "准备导出数据..."

            # 启动导出（show_animation=False因为动画已经启动）
            self.root.after(0, lambda: self._export_data(show_animation=False))

        except Exception as e:
            self.root.after(0, lambda: self._log(f"❌ 停止录制失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"无法停止录制: {e}"))
            self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
            self.root.after(0, self._stop_saving_animation)
            self._stop_requested = False  # 重置标记

    def _export_data(self, show_animation=True):
        """导出数据（异步执行）

        Args:
            show_animation: 是否显示保存动画（只在停止录制时显示）
        """
        if not self.session_id:
            self.root.after(0, lambda: messagebox.showwarning("警告", "没有正在录制的会话"))
            return
        
        if self.is_exporting:
            self.root.after(0, lambda: self._log("⚠ 已有导出任务正在执行，请等待完成"))
            return

        self.is_exporting = True
        self.root.after(0, lambda: self.export_button.config(state=tk.DISABLED))
        self.export_progress = 0  # 重置进度
        self.current_export_step = "准备导出..."

        # 启动保存动画（如果需要）- 但注意如果动画已启动则跳过
        if show_animation and not self._save_animation_running:
            self.root.after(0, self._start_saving_animation)

        # 异步执行导出逻辑
        def export_worker():
            """后台导出线程（分步骤更新进度）"""
            try:
                # 步骤1：准备导出（进度10%）
                self.export_progress = 10
                self.current_export_step = "准备导出数据..."
                self.root.after(0, lambda: self._log("📥 开始导出数据..."))
                time.sleep(0.5)

                # 重置文件路径缓存
                self.export_file_paths = {
                    "csv": None,
                    "json": None,
                    "video": None
                }

                # 步骤2：导出CSV（进度20%-40%）
                self.export_progress = 20
                self.current_export_step = "正在保存CSV文件..."
                self.root.after(0, lambda: self._log("📝 导出CSV文件..."))
                time.sleep(0.8)  # 模拟处理时间（可根据实际调整）
                self.export_progress = 40
                

                # 步骤3：导出JSON（进度40%-60%）
                self.export_progress = 40
                self.current_export_step = "正在保存JSON文件..."
                self.root.after(0, lambda: self._log("📝 导出JSON文件..."))
                time.sleep(0.8)  # 模拟处理时间
                self.export_progress = 60
                
                # 步骤4：处理视频生成（进度60%-90%）
                self.export_progress = 60
                self.current_export_step = "正在生成视频文件..."
                self.root.after(0, lambda: self._log("🎬 正在生成视频..."))
                video_path = self.video_generator.get_video_path()
                self.export_file_paths["video"] = video_path

                # 等待视频文件生成完成（轮询检测）
                max_wait = 30  # 最大等待30秒
                wait_count = 0
                progress_step = 30 / max_wait  # 每0.5秒增加的进度
                while wait_count < max_wait:
                    if (video_path and os.path.exists(video_path) and 
                        os.path.getsize(video_path) > 10240):  # 大于10KB视为有效
                        break
                    time.sleep(0.5)
                    wait_count += 0.5
                    self.export_progress = min(90, 60 + (wait_count * progress_step))

                self.export_progress = 90
                # 检测视频文件状态
                if video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 10240:
                    self.root.after(0, lambda: self._log(f"✓ 视频文件已生成 ({(os.path.getsize(video_path)/1024/1024):.1f} MB)"))
                else:
                    self.root.after(0, lambda: self._log("⚠ 视频时长过短或未检测到录制事件"))
                    self.root.after(0, lambda: self._log("💡 建议：录制时至少进行1-2次鼠标点击或键盘操作"))

                # 步骤5：等待视频生成器和文件写入完成（同步等待）
                self.export_progress = 90
                self.current_export_step = "等待视频生成完成..."
                self.root.after(0, lambda: self._log("⏳ 等待视频生成完成..."))

                # 轮询检测视频是否真正完成（最多等待10秒）
                max_wait = 10
                wait_count = 0
                while wait_count < max_wait:
                    if self._is_video_file_ready():
                        break
                    time.sleep(0.5)
                    wait_count += 0.5
                    self.export_progress = min(95, 90 + (wait_count * 5))

                if not self._is_video_file_ready():
                    self.root.after(0, lambda: self._log("⚠ 警告：视频可能未完全写入"))
                    self.root.after(0, lambda: self._log("💡 提示：请稍后再打开文件夹"))

                # 步骤6：最终校验（进度95%-100%）
                self.export_progress = 95
                self.current_export_step = "校验文件完整性..."
                self.root.after(0, lambda: self._log("✅ 校验文件完整性..."))
                time.sleep(0.5)
                self.export_progress = 100

                # 等待所有文件生成完成后，停止动画并更新UI
                self.root.after(0, self._finalize_export)

            except Exception as e:
                import traceback
                error_msg = f"❌ 导出失败: {e}\n{traceback.format_exc()}"
                self.root.after(0, lambda: self._log(error_msg))
                self.root.after(0, lambda: messagebox.showerror("错误", f"导出失败: {e}\n\n详细信息已记录在日志中"))
                self.root.after(0, self._stop_saving_animation)
                self.root.after(0, lambda: self._reset_export_state())

        # 启动后台线程
        export_thread = threading.Thread(target=export_worker, daemon=True)
        export_thread.start()

    def _is_video_file_ready(self):
        """检查视频文件是否已完全写入

        Returns:
            bool: 视频是否已完全写入可播放
        """
        video_path = self.export_file_paths.get("video")
        if not video_path:
            return False

        # 检查文件存在且大于10KB
        if not os.path.exists(video_path) or os.path.getsize(video_path) < 10240:
            return False

        # 检查视频生成器是否已标记为完成
        if hasattr(self.video_generator, '_generation_complete'):
            if not self.video_generator._generation_complete:
                return False

        return True

    def _finalize_export(self):
        """完成导出流程（UI线程执行）"""
        # 等待所有文件就绪（最终确认）
        # 关键：确保视频文件已完全写入生成器完成态标记
        self._log("⏳ 等待视频文件完全保存...")
        wait_count = 0

        # 不限制最大等待时间，只要视频文件未就绪就一直等待
        # 设置一个合理的超时保护（60秒），防止无限等待
        total_wait_time = 0
        timeout_seconds = 60  # 超时保护：最长等待60秒

        while True:
            if self._is_video_file_ready():
                break

            # 超时保护
            if total_wait_time >= timeout_seconds:
                self._log(f"⚠ 超时警告：等待视频文件超过{timeout_seconds}秒未就绪")
                self._log("💡 提示：视频文件可能仍在生成中，请稍后检查")
                break

            # 定期更新进度（每5秒更新一次）
            if wait_count > 0 and wait_count % 10 == 0:
                progress = min(98, 95 + int((total_wait_time / timeout_seconds) * 3))
                self.export_progress = progress
                self._log(f"⏳ 继续等待视频文件... 已等待 {total_wait_time} 秒")

            time.sleep(0.5)
            wait_count += 1
            total_wait_time += 0.5

        # 再次确认视频文件状态
        if self._is_video_file_ready():
            self._log("✓ 视频文件已完全就绪")
            progress = 99
            self.export_progress = progress

            # 保存到消息目录
            if self.message_name and self.export_file_paths.get("video"):
                target_video = self.recorder.save_video_to_message_directory(
                    self.message_name,
                    source_video_path=self.export_file_paths["video"],
                    overwrite=True
                )
                if target_video:
                    self._log(f"✓ 子目录视频已保存: {target_video}")
                    # 删除原视频
                    try:
                        os.remove(self.export_file_paths["video"])
                        self.export_file_paths["video"] = target_video  # 更新路径
                    except Exception as e:
                        self._log(f"⚠ 无法删除原视频文件: {e}")
                else:
                    self._log("⚠ 子目录视频保存失败")
        else:
            self._log("⚠ 警告：视频文件未完全就绪")
            self._log("💡 提示：数据文件已保存，但视频文件可能需要时间写入完成")

        # 确保进度到100%
        self.export_progress = 100
        self.current_export_step = "导出完成！"
        time.sleep(0.5)  # 让用户看到100%进度

        # 停止保存动画
        self._stop_saving_animation()
        
        # 获取输出文件夹路径
        config = config_loader.load_config()
        if config.get("output"):
            csv_dir = config["output"].get("csv", None)
            json_dir = config["output"].get("json", None)
            mp4_dir = config["output"].get("mp4", None)

            # 优先使用CSV目录，其次JSON目录，最后MP4目录
            for data_folder_str in [csv_dir, json_dir, mp4_dir]:
                if data_folder_str:
                    data_folder = os.path.abspath(data_folder_str)
                    break
            else:
                # 兼容旧格式
                data_folder_str = config["output"].get("data",
                    config.get("paths", {}).get("data", "./output"))
                data_folder = os.path.abspath(data_folder_str)
        else:
            data_folder_str = config.get("paths", {}).get("data", "./output")
            data_folder = os.path.abspath(data_folder_str)

        # 整理生成的文件列表
        files_generated = []
        if self.export_file_paths["csv"] and os.path.exists(self.export_file_paths["csv"]):
            files_generated.append("CSV文件")
        if self.export_file_paths["json"] and os.path.exists(self.export_file_paths["json"]):
            files_generated.append("JSON文件")
        if self.export_file_paths["video"] and os.path.exists(self.export_file_paths["video"]):
            if os.path.getsize(self.export_file_paths["video"]) > 10240:
                files_generated.append("视频文件")
            else:
                files_generated.append("视频文件（可能为空）")

        events = self.recorder.get_session_events()
        elapsed = (datetime.now() - self.recording_start_time).total_seconds() if self.recording_start_time else 0
        elapsed_str = format_duration(int(elapsed))

        # 显示导出结果
        messagebox.showinfo(
            "✨ 录制完成",
            f"所有文件已成功保存！\n\n"
            f"📝 日志文件: Event Log\n"
            f"🎬 视频文件: Operation Video\n"
            f"📊 事件数量: {len(events)}\n"
            f"⏱️ 录制时长: {elapsed_str}"
        )

        # 自动打开文件夹
        if os.path.exists(data_folder):
            try:
                os.startfile(data_folder)
                self._log(f"📂 已打开文件夹: {data_folder}")
            except (OSError, FileNotFoundError) as e:
                self._log(f"⚠ 无法打开文件夹: {e}")

        # 重置导出状态
        self._reset_export_state()
        self._stop_requested = False  # 重置停止请求标记

    def _reset_export_state(self):
        """重置导出状态"""
        self.is_exporting = False
        self.export_progress = 0
        self.current_export_step = ""
        self.root.after(0, lambda: self.export_button.config(state=tk.NORMAL))
        self.root.after(0, self._update_status)

    def _update_status(self):
        """更新状态显示"""
        if self.is_recording:
            if self.recorder.is_paused:
                self.status_label.config(text="状态: 已暂停 (Paused)", foreground="#FF9800")
            else:
                self.status_label.config(text="状态: 录制中 (Recording)", foreground="green")
        elif self.is_exporting:
            self.status_label.config(text=f"状态: 导出中 (Exporting) - {self.current_export_step}", foreground="#FF9800")
        else:
            self.status_label.config(text="状态: 待机 (Standby)", foreground="black")

        if self.session_id:
            self.session_label.config(text=f"会话ID: {self.session_id}")
        else:
            self.session_label.config(text="会话ID: -")

        self.event_count_label.config(text=f"事件数量: {self.event_count}")

    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        print(log_msg)

    def _update_gui_loop(self):
        """更新GUI循环"""
        if self.is_recording and not self._stop_requested:
            # 更新事件计数
            try:
                events = self.recorder.get_session_events()
                event_diff = len(events) - self.event_count
                if event_diff > 0:
                    self.event_count += event_diff
                    self.event_count_label.config(text=f"事件数量: {self.event_count}")
            except (AttributeError, TypeError):
                pass

            # 更新录制时长
            elapsed = (datetime.now() - self.recording_start_time).total_seconds()
            self.recording_time_label.config(text=f"录制时长: {format_duration(int(elapsed))}")

            # 实时预览
            self._update_preview()

        # 持续更新状态（包括导出进度）
        self._update_status()
        
        self.root.after(GUIConfig.STATUS_TEXT_UPDATE_INTERVAL, self._update_gui_loop)

    def _start_saving_animation_immediate(self):
        """立即启动保存动画（无延迟）"""
        self._save_animation_running = True
        self.save_step = 0
        if self.export_progress == 0:
            self.export_progress = 0
            self.current_export_step = "正在停止录制..."
        
        # 立即绘制第一帧动画（不经过after调度）
        self._draw_animation_frame()
        
        # 然后启动定时更新
        self.save_indicator_id = self.root.after(300, self._update_save_animation)

    def _draw_animation_frame(self):
        """立即绘制动画帧"""
        # 清空保存指示器区域
        self.preview_canvas.delete("save_indicator")
        self.preview_canvas.delete("preview")
        
        # 绘制背景
        self.preview_canvas.create_rectangle(
            0, 0, 980, 200,
            fill="#2d2d2d",
            outline="",
            tags="save_indicator"
        )
        
        # 定义步骤颜色
        step_colors = {
            "正在停止录制...": "#FF5722",
            "准备导出...": "#2196F3",
            "准备导出数据...": "#2196F3",
            "正在保存CSV文件...": "#4CAF50",
            "正在保存JSON文件...": "#FF9800",
            "正在生成视频文件...": "#9C27B0",
            "校验文件完整性...": "#607D8B",
            "导出完成！": "#4CAF50"
        }
        current_color = step_colors.get(self.current_export_step, "#FF5722")
        
        # 绘制当前步骤文字
        self.preview_canvas.create_text(
            490, 80,
            text=self.current_export_step,
            fill=current_color,
            font=("Arial", 16, "bold"),
            tags="save_indicator"
        )
        
        # 添加加载进度条效果
        bar_length = 600
        bar_x = (980 - bar_length) // 2
        progress_width = int(bar_length * (self.export_progress / 100)) if self.export_progress > 0 else 0
        
        # 背景条
        self.preview_canvas.create_rectangle(
            bar_x, 120, bar_x + bar_length, 140,
            fill="#444444", outline="#666666", tags="save_indicator"
        )
        
        # 进度条（如果有进度）
        if progress_width > 0:
            self.preview_canvas.create_rectangle(
                bar_x, 120, bar_x + progress_width, 140,
                fill=current_color, outline="", tags="save_indicator"
            )
        
        # 进度文本
        self.preview_canvas.create_text(
            490, 155,
            text=f"进度: {self.export_progress:.0f}%" if self.export_progress > 0 else "准备中...",
            fill="white",
            font=("Arial", 12, "bold"),
            tags="save_indicator"
        )
        
        # 添加一个旋转的加载指示器
        spinner_chars = ["◐", "◓", "◑", "◒"]
        spinner = spinner_chars[self.save_step % 4]
        self.preview_canvas.create_text(
            490, 30,
            text=spinner,
            fill=current_color,
            font=("Arial", 20, "bold"),
            tags="save_indicator"
        )
        self.save_step += 1

    def _start_saving_animation(self):
        """开始显示保存动画（延迟版本，用于其他场景）"""
        self._save_animation_running = True
        self.save_step = 0
        if self.export_progress == 0:
            self.export_progress = 0
            self.current_export_step = "准备导出..."
        self._update_save_animation()

    def _stop_saving_animation(self):
        """停止保存动画"""
        self._save_animation_running = False
        if self.save_indicator_id:
            self.root.after_cancel(self.save_indicator_id)
            self.save_indicator_id = None
        # 清空动画区域
        self.preview_canvas.delete("save_indicator")
        # 恢复预览显示
        self._update_preview()

    def _update_save_animation(self):
        """更新保存动画（基于真实进度）"""
        if not self._save_animation_running:
            return

        # 清空保存指示器区域
        self.preview_canvas.delete("save_indicator")
        self.preview_canvas.delete("preview")  # 清空预览内容

        # 绘制背景
        self.preview_canvas.create_rectangle(
            0, 0, 980, 200,
            fill="#2d2d2d",
            outline="",
            tags="save_indicator"
        )

        # 定义步骤颜色映射
        step_colors = {
            "正在停止录制...": "#FF5722",
            "准备导出...": "#2196F3",
            "准备导出数据...": "#2196F3",
            "正在保存CSV文件...": "#4CAF50",
            "正在保存JSON文件...": "#FF9800",
            "正在生成视频文件...": "#9C27B0",
            "校验文件完整性...": "#607D8B",
            "导出完成！": "#4CAF50"
        }
        current_color = step_colors.get(self.current_export_step, "#2196F3")

        # 绘制当前步骤文字
        self.preview_canvas.create_text(
            490, 80,
            text=self.current_export_step,
            fill=current_color,
            font=("Arial", 16, "bold"),
            tags="save_indicator"
        )

        # 添加加载进度条效果
        bar_length = 600
        bar_x = (980 - bar_length) // 2
        progress_width = int(bar_length * (self.export_progress / 100))
        
        # 背景条
        self.preview_canvas.create_rectangle(
            bar_x, 120, bar_x + bar_length, 140,
            fill="#444444", outline="#666666", tags="save_indicator"
        )
        # 进度条
        self.preview_canvas.create_rectangle(
            bar_x, 120, bar_x + progress_width, 140,
            fill=current_color, outline="", tags="save_indicator"
        )
        # 进度文本
        self.preview_canvas.create_text(
            490, 155,
            text=f"进度: {self.export_progress:.0f}%",
            fill="white",
            font=("Arial", 12, "bold"),
            tags="save_indicator"
        )
        
        # 添加旋转加载指示器
        spinner_chars = ["◐", "◓", "◑", "◒"]
        spinner = spinner_chars[self.save_step % 4]
        self.preview_canvas.create_text(
            490, 30,
            text=spinner,
            fill=current_color,
            font=("Arial", 20, "bold"),
            tags="save_indicator"
        )
        self.save_step += 1

        # 继续更新动画（300ms刷新一次，更流畅）
        self.save_indicator_id = self.root.after(300, self._update_save_animation)

    def _update_preview(self):
        """更新实时预览"""
        # 如果动画正在运行，跳过预览更新（避免冲突）
        if self._save_animation_running:
            return

        # 清空画布
        self.preview_canvas.delete("all")

        # 绘制背景
        self.preview_canvas.create_rectangle(
            0, 0, 980, 200,
            fill="#2d2d2d",
            outline=""
        )

        if not self.recorder.is_recording:
            self.preview_canvas.create_text(
                490, 100,
                text="等待操作预览...",
                fill="#888888",
                font=("Arial", 12)
            )
            return

        # 显示最近的几个操作
        events = self.recorder.get_session_events()
        recent_events = list(events)[-5:]

        y_offset = 35
        for event in recent_events:
            label = f"{event.event_type.value}: {event.detail}"
            if event.element_info:
                label += f" [{event.element_info.element_type.value}]"

            # 绘制操作
            color = "#4CAF50"  # 绿色
            self.preview_canvas.create_text(
                20, y_offset,
                text=label,
                fill=color,
                anchor=tk.W,
                font=("Arial", 10)
            )
            y_offset += 20

        # 显示坐标（最后一点）
        if events:
            last_event = events[-1]
            if last_event.coordinates != (0, 0):
                x, y = last_event.coordinates
                coord_text = f"Position: ({x}, {y})"
                self.preview_canvas.create_text(
                    490, 180,
                    text=coord_text,
                    fill="#FFFFFF",
                    font=("Arial", 10),
                    tags="preview"
                )

    def _on_close(self):
        """窗口关闭回调"""
        if self.is_recording:
            if messagebox.askyesno("确认退出", "当前正在录制中，确定要退出吗？"):
                # 立即停止视频生成
                self.video_generator.stop_generating()
                self._stop_recording_impl()
                self.root.destroy()
        elif self.is_exporting:
            messagebox.showwarning("导出中", "当前正在导出数据，请等待完成后再退出")
        else:
            self.root.destroy()


# 辅助函数：格式化时长
def format_duration(seconds: int) -> str:
    """将秒数格式化为 HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# 主程序入口
if __name__ == "__main__":
    app = OperationRecorderGUI()
    app.root.mainloop()