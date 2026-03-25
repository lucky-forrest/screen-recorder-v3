"""时间戳管理器

提供各种格式的时间戳生成工具。
"""
from datetime import datetime, timedelta


def generate_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """生成标准化时间戳

    Args:
        fmt: 格式字符串

    Returns:
        str: 格式化时间戳字符串
    """
    return datetime.now().strftime(fmt)


def generate_session_id(date_only: bool = False) -> str:
    """生成会话ID

    格式：
    - with date: YYYYMMDD_HHMMSS
    - date only: YYYYMMDD_HHMM

    Args:
        date_only: 是否只包含日期不包含秒

    Returns:
        str: 会话ID
    """
    now = datetime.now()
    if date_only:
        return now.strftime("%Y%m%d_%H%M")
    return now.strftime("%Y%m%d_%H%M%S")


def format_duration(seconds: int) -> str:
    """格式化持续时间

    Args:
        seconds: 秒数

    Returns:
        str: 格式化字符串，如 "00:01:23"
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    print("Current timestamp:", generate_timestamp())
    print("Session ID:", generate_session_id())
    print("Date-only Session ID:", generate_session_id(date_only=True))
    print("Duration: 3661 seconds ->", format_duration(3661))
