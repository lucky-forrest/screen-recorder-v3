"""操作记录器GUI

基于Tkinter的图形用户界面，提供录制控制、实时状态显示和日志输出。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue
from typing import Optional
from datetime import datetime, timedelta
import os

from recorder_engine import RecorderEngine
from video_generator import VideoGenerator
import utils.config_loader as config_loader


class OperationRecorderGUI:
    """操作记录器主界面"""

    def __init__(self, root: Optional[tk.Tk] = None):
        """初始化GUI

        Args:
            root: 根窗口（可以自动创建）
        """
        self.root = root if root else tk.Tk()
        self.root.title("Advanced Computer Operation Recorder")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 加载配置
        self.config = config_loader.load_config()

        # 录制状态
        self.is_recording = False
        self.session_id: Optional[str] = None
        self.event_count = 0
        self.recording_start_time: Optional[datetime] = None
        self.is_exporting = False

        # 保存动画相关
        self.save_indicator_id = None
        self.save_step = 0
        self._save_animation_running = False

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
            command=self._export_data,
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

            # 注册录制事件回调
            self.recorder.on_event(self._on_recorder_event)
            print(f"[GUI] Event callback registered")

            self.session_id = self.recorder.start_recording()
            self.event_count = 0
            self.recording_start_time = datetime.now()
            self.is_recording = True

            print(f"[GUI] Session started: {self.session_id}")

            # 更新按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.export_button.config(state=tk.DISABLED)

            # 更新状态显示
            self._update_status()
            self._log(f"📷 录制开始: Session {self.session_id}")
            self._log(f"👆 已注册事件回调，请在键盘上操作...")
            print(f"[GUI] Ready - waiting for events")

            # 启动视频生成
            self.video_generator.start_generating(self.session_id)

        except Exception as e:
            self._log(f"启动录制失败: {e}")
            messagebox.showerror("错误", f"无法启动录制: {e}")

    def _pause_recording(self):
        """暂停录制"""
        # 实现暂停功能
        self._log("录制暂停: 暂未实现暂停回调，请直接停止录制")

    def _stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return

        # 创建确认窗口
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("确认停止录制")
        confirm_window.geometry("400x150")
        confirm_window.resizable(False, False)
        confirm_window.transient(self.root)
        confirm_window.grab_set()

        # 居中显示
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        confirm_window.geometry(f"+{x}+{y}")

        # 内容
        center_frame = ttk.Frame(confirm_window, padding="20")
        center_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            center_frame,
            text="📦 正在保存文件...",
            font=("Arial", 16, "bold"),
            foreground="#2196F3"
        ).pack(pady=10)

        action_frame = ttk.Frame(center_frame)
        action_frame.pack(pady=10)

        self.export_button.config(state=tk.DISABLED)

        def on_confirm():
            confirm_window.destroy()
            self._stop_recording_impl()

        def on_cancel():
            confirm_window.destroy()
            self.export_button.config(state=tk.NORMAL)

        ttk.Button(action_frame, text="确定保存", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=10)

    def _stop_recording_impl(self):
        """执行停止录制的实际逻辑"""
        try:
            # 停止视频生成
            self.video_generator.stop_generating()

            # 停止录制引擎
            events = self.recorder.stop_recording()

            # 开始导出数据（现在有动画了）
            self._export_data()

            self.is_recording = False

            # 更新按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.export_button.config(state=tk.NORMAL)

            # 更新状态和日志
            self._update_status()
            elapsed = (datetime.now() - self.recording_start_time).total_seconds() if self.recording_start_time else 0
            self._log(f"✅ 录制结束: 会话 {self.session_id}")
            self._log(f"📊 事件统计: 共捕获 {len(events)} 个事件")
            self._log(f"⏱️ 录制时长: {format_duration(int(elapsed))}")

            # 显示完成弹窗
            elapsed_str = format_duration(int(elapsed))
            messagebox.showinfo(
                "✨ 录制完成",
                f"所有文件已成功保存！\n\n"
                f"📝 日志文件: Event Log\n"
                f"🎬 视频文件: Operation Video\n"
                f"📊 事件数量: {len(events)}\n"
                f"⏱️ 录制时长: {elapsed_str}"
            )

        except Exception as e:
            self._log(f"❌ 停止录制失败: {e}")
            messagebox.showerror("错误", f"无法停止录制: {e}")
            self.export_button.config(state=tk.NORMAL)

    def _export_data(self, show_animation=True):
        """导出数据

        Args:
            show_animation: 是否显示保存动画（只在停止录制时显示）
        """
        if not self.session_id:
            messagebox.showwarning("警告", "没有正在录制的会话")
            return

        try:
            if show_animation:
                # 开始保存动画
                self._start_saving_animation()

            self._log("📥 开始导出数据...")

            events_already_saved = []
            # 导出CSV
            if self.recorder.save_to_csv():
                self._log("✓ CSV文件已生成")
                events_already_saved.append("CSV")
            else:
                self._log("✗ CSV文件生成失败")

            # 导出JSON
            if self.recorder.save_to_json():
                self._log("✓ JSON文件已生成")
                events_already_saved.append("JSON")
            else:
                self._log("✗ JSON文件生成失败")

            # 导出视频
            if self.is_recording:  # 确保录制状态为True
                video_path = self.video_generator.get_video_path()
                # 添加结束事件
                self.video_generator.stop_generating(wait=True)
                self._log("🎬 正在生成视频...")
            else:
                video_path = self.video_generator.get_video_path()
                self._log("⚠ 未检测到录制事件，视频可能为空")

            import time
            time.sleep(1)  # 等待视频生成

            video_path = self.video_generator.get_video_path()

            # 获取输出文件夹路径（绝对路径）
            import os
            config = config_loader.load_config()
            # 支持新旧两种配置格式
            if config.get("output"):
                if "json" in config["output"]:
                    data_folder_str = config["output"]["json"]
                else:
                    data_folder_str = config["output"].get("data", config.get("paths", {}).get("data", "./output"))
            else:
                data_folder_str = config.get("paths", {}).get("data", "./output")
            data_folder = os.path.abspath(data_folder_str)

            # 检查文件是否成功生成
            files_generated = []
            if video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 10240:
                self._log(f"✓ 视频文件已生成 ({(os.path.getsize(video_path)/1024/1024):.1f} MB)")
                files_generated.append("视频文件")

                # 尝试自动打开文件夹
                if os.path.exists(data_folder):
                    try:
                        os.startfile(data_folder)
                        self._log(f"📂 已打开文件夹: {data_folder}")
                    except Exception as e:
                        self._log(f"⚠ 无法打开文件夹: {e}")
                else:
                    self._log(f"⚠ 数据文件夹不存在: {data_folder}")
            else:
                self._log("⚠ 视频时长过短或未检测到录制事件")
                self._log("💡 建议：录制时至少进行1-2次鼠标点击或键盘操作")
                files_generated.append("视频文件（可能为空）")

            if show_animation:
                # 停止保存动画
                self._stop_saving_animation()
                self._update_status()

            # 根据导出结果显示不同消息
            files_display = ", ".join(files_generated)
            if len(files_generated) >= 2:
                messagebox.showinfo(
                    "✅ 导出成功",
                    f"所有文件已成功保存到 {data_folder}！\n\n"
                    f"📋 已生成文件:\n"
                    f"  • {files_display}\n"
                    f"  • 会话ID: {self.session_id}"
                )
            else:
                messagebox.showwarning(
                    "⚠ 导出部分完成",
                    f"部分文件未能正常生成\n\n"
                    f"请检查程序日志查看详细错误信息。\n"
                    f"会话ID: {self.session_id}\n"
                    f"点击打开文件夹"
                )
                if os.path.exists(data_folder):
                    os.startfile(data_folder)

                if len(events_already_saved) >= 1:
                    events_text = ", ".join(events_already_saved)
                    messagebox.showinfo(
                        "部分导出",
                        f"部分文件已成功生成！\n\n"
                        f"已生成: {events_text}\n\n"
                        f"请查看data文件夹中的文件"
                    )

        except Exception as e:
            import traceback
            self._log(f"❌ 导出失败: {e}")
            self._log(traceback.format_exc())
            messagebox.showerror("错误", f"导出失败: {e}\n\n详细信息已记录在日志中")
            if show_animation:
                self._stop_saving_animation()

    def _update_status(self):
        """更新状态显示"""
        if self.is_recording:
            self.status_label.config(text="状态: 录制中 (Recording)")
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(text="状态: 待机 (Standby)")
            self.status_label.config(foreground="black")

        if self.session_id:
            self.session_label.config(text=f"会话ID: {self.session_id}")
        else:
            self.session_label.config(text="会话ID: -")

        self.event_count_label.config(text=f"事件数量: {self.event_count}")
        # 录制时长更新在循环中进行

    def _log(self, message: str):
        """添加日志

        Args:
            message: 日志消息
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 更新控制台输出
        print(log_msg)

    def _update_gui_loop(self):
        """更新GUI循环"""
        if self.is_recording:
            # 更新事件计数（从录制引擎获取）
            try:
                events = self.recorder.get_session_events()
                event_diff = len(events) - self.event_count
                if event_diff > 0:
                    self.event_count += event_diff
                    self.event_count_label.config(text=f"事件数量: {self.event_count}")
            except Exception:
                pass

            # 更新录制时长
            elapsed = (datetime.now() - self.recording_start_time).total_seconds()
            self.recording_time_label.config(text=f"录制时长: {format_duration(int(elapsed))}")

            # 实时预览（简化版）
            self._update_preview()

        # 10ms后再次调用
        self.root.after(10, self._update_gui_loop)

    def _start_saving_animation(self):
        """开始显示保存动画"""
        self._save_animation_running = True
        self.save_step = 0
        self._update_save_animation()

    def _stop_saving_animation(self):
        """停止保存动画"""
        self._save_animation_running = False
        if self.save_indicator_id:
            self.root.after_cancel(self.save_indicator_id)
            self.save_indicator_id = None

    def _update_save_animation(self):
        """更新保存动画"""
        if not self._save_animation_running:
            return

        # 清空保存指示器区域
        self.preview_canvas.delete("save_indicator")

        # 动画步骤：0=保存.gif 1=保存✓ 2=完成.gif 3=清空
        messages = [
            "💾 正在保存文件...",
            "⏳ 处理中...",
            "✨ 正在生成视频...",
            ""
        ]

        # 使用交替颜色
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#888888"]

        # 绘制动画文字
        message = messages[self.save_step % 4]
        color = colors[self.save_step % 4]

        y = 60
        x = 500
        self.preview_canvas.create_text(
            x, y,
            text=message,
            fill=color if message else "#888888",
            font=("Arial", 16, "bold"),
            tags="save_indicator"
        )

        # 添加闪烁效果
        if self.save_step % 4 < 3:
            if self.save_step % 2 == 0:
                self.preview_canvas.create_text(
                    x, y + 25,
                    text="━━━━━━━━━━━━━━━━━━━━",
                    fill=color,
                    font=("Arial", 12),
                    tags="save_indicator"
                )

        self.save_step += 1
        self.save_indicator_id = self.root.after(800, self._update_save_animation)

    def _update_preview(self):
        """更新实时预览"""
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
                last_event.element_info
                x, y = last_event.coordinates
                coord_text = f"Position: ({x}, {y})"
                self.preview_canvas.create_text(
                    20, y_offset + 10,
                    text=coord_text,
                    fill="#888888",
                    anchor=tk.W,
                    font=("Arial", 9)
                )

    def _on_recorder_event(self, event):
        """处理录制事件的回调

        Args:
            event: OperationEvent对象
        """
        self.event_count += 1

    def _on_close(self):
        """窗口关闭事件"""
        if self.is_recording:
            if messagebox.askokcancel("退出", "录制正在进行，确定要退出吗？"):
                self._stop_recording()

        self.root.destroy()


def format_duration(seconds: int) -> str:
    """格式化持续时间

    Args:
        seconds: 秒数

    Returns:
        str: 格式化字符串
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # 创建并运行GUI
    app = OperationRecorderGUI()
    app.root.mainloop()
