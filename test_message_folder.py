"""测试消息名称文件夹功能

演示如何使用消息名称来创建文件夹并保存文件。
"""
from utils.file_manager import FileManager
from utils.path_manager import PathManager
from pathlib import Path
import tempfile
import os


def test_sanitize_filename():
    """测试文件名过滤"""
    print("=" * 60)
    print("测试文件名过滤功能")
    print("=" * 60)

    test_cases = [
        "test/file:name*?\"<>\|测试",
        "录制_2024",
        "My Recording-2024",
        "Normal Name"
    ]

    for name in test_cases:
        filtered = FileManager.sanitize_filename(name)
        print(f"原始: {name}")
        print(f"过滤后: {filtered}")
        print()


def test_message_directory_creation():
    """测试消息名称目录创建"""
    print("=" * 60)
    print("测试消息名称目录创建")
    print("=" * 60)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        path_manager = PathManager()
        path_manager.base_dir = Path(tmpdir)

        # 测试不同名称
        test_names = [
            "test/file:name",
            "录制会话",
            "My Recording_2024"
        ]

        for name in test_names:
            cleaned = FileManager.sanitize_filename(name)

            # 获取目录路径
            msg_dir = path_manager.get_message_directory(name)
            print(f"消息名称: '{name}'")
            print(f"过滤后: '{cleaned}'")
            print(f"目录路径: {msg_dir}")
            print(f"目录存在: {msg_dir.exists()}")

            # 创建目录
            msg_dir.mkdir(parents=True, exist_ok=True)
            print(f"创建后存在: {msg_dir.exists()}")

            # 创建示例文件
            (msg_dir / "test.csv").write_text("test")
            (msg_dir / "test.json").write_text("test")
            (msg_dir / "test.mp4").write_bytes(b"testing")
            print(f"文件数量: {len(list(msg_dir.iterdir()))}")
            print()


def test_file_paths():
    """测试文件路径"""
    print("=" * 60)
    print("测试文件路径生成")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        path_manager = PathManager()
        path_manager.base_dir = Path(tmpdir)

        message_name = "测试录制_2024"

        # 测试不同类型文件的路经
        csv_path = path_manager.get_message_csv_file_path(message_name)
        json_path = path_manager.get_message_json_file_path(message_name)
        video_path = path_manager.get_message_video_file_path(message_name)

        print(f"消息名称: '{message_name}'")
        print(f"CSV路径: {csv_path}")
        print(f"JSON路径: {json_path}")
        print(f"视频路径: {video_path}")

        # 创建目录
        path_manager.get_message_directory(message_name).mkdir(parents=True, exist_ok=True)

        # 确认路径格式正确
        print(f"\n路径格式验证:")
        print(f"  CSV目录: {csv_path.parent}")
        print(f"  CSV文件名: {csv_path.name}")
        print(f"  JSON目录: {json_path.parent}")
        print(f"  JSON文件名: {json_path.name}")
        print(f"  视频目录: {video_path.parent}")
        print(f"  视频文件名: {video_path.name}")


if __name__ == "__main__":
    # 执行所有测试
    print("\n")
    test_sanitize_filename()
    test_message_directory_creation()
    test_file_paths()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
