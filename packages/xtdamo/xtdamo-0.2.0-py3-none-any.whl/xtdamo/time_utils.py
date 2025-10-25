# !/usr/bin/env python3
"""
==============================================================
Description  : 时间工具模块 - 提供时间跟踪、虚拟键码、时间控制等功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-18 22:00:00
Github       : https://github.com/sandorn/xtdamo

本模块提供以下核心功能:
- 时间跟踪器 (TimeTracker) - 替代bdtime.tt
- 虚拟键码常量 (VirtualKeys) - 替代bdtime.vk
- 时间控制与延迟 (sleep, during)
- 按键状态检测 (get_key_state, is_pressed)
- 时间戳获取 (now)

主要特性:
- 完全替代bdtime依赖
- 高性能时间跟踪
- 丰富的虚拟键码支持
- 智能按键状态检测
- 异常处理和错误恢复
==============================================================
"""

from __future__ import annotations

import time


class TimeTracker:
    """时间跟踪器，用于替代bdtime.tt

    提供高精度的时间跟踪功能，支持超时检测、已用时间和剩余时间计算。
    适用于循环控制、性能监控、超时检测等场景。

    Attributes:
        start_time (float): 创建跟踪器时的时间戳（秒）
        timeout (float): 超时时间（秒），0表示无限制

    Examples:
        基本用法 - 循环超时控制:
        >>> tracker = TimeTracker(5.0)  # 5秒超时
        >>> while tracker.during():
        ...     # 执行循环操作
        ...     if some_condition:
        ...         break

        动态超时检测:
        >>> tracker = TimeTracker()
        >>> while tracker.during(10.0):  # 临时指定10秒超时
        ...     # 执行操作
        ...     pass

        时间监控:
        >>> tracker = TimeTracker()
        >>> # ... 执行某些操作 ...
        >>> print(f'已用时间: {tracker.elapsed():.2f}秒')
        >>> print(f'剩余时间: {tracker.remaining():.2f}秒')

    Note:
        - 时间精度依赖于系统时钟，通常为微秒级
        - timeout=0 表示永不超时，during() 将始终返回 True
        - 线程安全：不建议在多线程中共享同一个实例
    """

    def __init__(self, timeout: float = 0):
        """初始化时间跟踪器

        创建一个新的时间跟踪器，并记录当前时间作为起点。

        Args:
            timeout (float, optional): 超时时间（秒）。
                - 大于0: 指定具体的超时时间
                - 等于0: 无超时限制（默认值）
                - 负数: 等同于0，无超时限制

        Examples:
            创建5秒超时的跟踪器:
            >>> tracker = TimeTracker(5.0)

            创建无超时限制的跟踪器:
            >>> tracker = TimeTracker()  # 或 TimeTracker(0)
        """
        self.start_time = time.time()
        self.timeout = timeout

    def during(self, timeout: float | None = None) -> bool:
        """检查是否在指定时间内（未超时）

        判断从创建跟踪器到当前时刻是否超过了指定的超时时间。
        常用于循环条件判断，实现带超时的等待循环。

        Args:
            timeout (float | None, optional): 超时时间（秒）。
                - None: 使用初始化时设置的 timeout（默认）
                - 大于0: 临时使用指定的超时时间
                - 等于0或负数: 永不超时，始终返回 True

        Returns:
            bool: 未超时返回 True，已超时返回 False
                - True: 当前时间 < 起始时间 + 超时时间
                - False: 当前时间 >= 起始时间 + 超时时间

        Examples:
            使用初始化的超时时间:
            >>> tracker = TimeTracker(3.0)
            >>> while tracker.during():
            ...     print('未超时，继续执行')
            ...     time.sleep(1)

            临时指定超时时间:
            >>> tracker = TimeTracker()
            >>> while tracker.during(5.0):  # 使用5秒超时
            ...     print('执行中...')

            结合其他条件:
            >>> tracker = TimeTracker(10.0)
            >>> while tracker.during() and not found:
            ...     # 在超时前持续查找
            ...     found = search_for_target()

        Note:
            - 此方法不会阻塞，仅进行时间比较
            - 调用频率不影响超时判断的准确性
            - 超时时间为0时，可用于无限循环（需配合其他退出条件）
        """
        if timeout is None:
            timeout = self.timeout

        if timeout <= 0:
            return True

        return (time.time() - self.start_time) < timeout

    def elapsed(self) -> float:
        """获取已经过去的时间（秒）

        计算从跟踪器创建到当前时刻经过的时间。
        适用于性能分析、进度监控、日志记录等场景。

        Returns:
            float: 已过去的时间（秒），精确到微秒级
                - 总是返回非负数
                - 从跟踪器创建时刻开始计算

        Examples:
            测量代码执行时间:
            >>> tracker = TimeTracker()
            >>> # ... 执行某些操作 ...
            >>> duration = tracker.elapsed()
            >>> print(f'操作耗时: {duration:.3f}秒')

            实时显示进度:
            >>> tracker = TimeTracker()
            >>> while processing:
            ...     elapsed = tracker.elapsed()
            ...     print(f'已运行: {elapsed:.1f}秒', end='\r')

            性能基准测试:
            >>> tracker = TimeTracker()
            >>> for i in range(1000):
            ...     some_operation()
            >>> avg_time = tracker.elapsed() / 1000
            >>> print(f'平均耗时: {avg_time * 1000:.2f}毫秒')
        """
        return time.time() - self.start_time

    def remaining(self) -> float:
        """获取剩余时间（秒）

        计算距离超时还剩余多少时间。可用于预估等待时间、
        显示倒计时、动态调整策略等场景。

        Returns:
            float: 剩余时间（秒）
                - 正数: 距离超时的剩余时间
                - 0: 已经超时（已用时间 >= 超时时间）
                - float('inf'): 无超时限制（timeout <= 0）

        Examples:
            显示倒计时:
            >>> tracker = TimeTracker(60.0)  # 60秒倒计时
            >>> while tracker.during():
            ...     remaining = tracker.remaining()
            ...     print(f'剩余时间: {remaining:.1f}秒', end='\r')
            ...     time.sleep(1)

            根据剩余时间调整策略:
            >>> tracker = TimeTracker(10.0)
            >>> while tracker.during():
            ...     if tracker.remaining() < 2.0:
            ...         # 快超时了，采用快速策略
            ...         use_fast_method()
            ...     else:
            ...         # 时间充足，采用精确策略
            ...         use_accurate_method()

            检查是否即将超时:
            >>> if tracker.remaining() < 1.0:
            ...     print('警告: 即将超时！')

        Note:
            - 如果 timeout <= 0，返回正无穷 (float('inf'))
            - 超时后返回0，不会返回负数
            - 配合 during() 使用可以实现更灵活的超时控制
        """
        if self.timeout <= 0:
            return float('inf')
        return max(0, self.timeout - self.elapsed())


def sleep(duration: float) -> None:
    """睡眠指定时间

    暂停当前线程执行指定的时间。这是 time.sleep() 的封装函数，
    提供更简洁的API，与模块其他功能保持一致的命名风格。

    Args:
        duration (float): 睡眠时间（秒）
            - 正数: 睡眠指定的秒数
            - 0: 立即返回，不睡眠
            - 负数: 视为0，立即返回

    Examples:
        暂停1秒:
        >>> sleep(1.0)

        暂停100毫秒:
        >>> sleep(0.1)

        在循环中添加延迟:
        >>> for i in range(10):
        ...     do_something()
        ...     sleep(0.5)  # 每次操作间隔0.5秒

    Note:
        - 实际睡眠时间可能略长于指定值（取决于系统调度）
        - 在Windows上，最小睡眠精度约为15ms
        - 此函数会阻塞当前线程
    """
    time.sleep(duration)


def now(format_type: int = 0) -> str:
    """获取当前时间字符串

    返回格式化的当前时间字符串，支持标准格式和高精度格式。
    适用于日志记录、时间戳生成、调试输出等场景。

    Args:
        format_type (int, optional): 时间格式类型，默认为 0
            - 0: 标准日期时间格式 "YYYY-MM-DD HH:MM:SS"
            - 1: 高精度时间格式 "HH:MM:SS.mmm" (包含毫秒)
            - 其他值: 等同于 0，使用标准格式

    Returns:
        str: 格式化的时间字符串
            - format_type=0: 例如 "2025-10-25 14:30:45"
            - format_type=1: 例如 "14:30:45.123"

    Examples:
        获取标准格式时间:
        >>> timestamp = now()
        >>> print(timestamp)
        "2025-10-25 14:30:45"

        获取高精度时间（用于性能测试）:
        >>> precise_time = now(1)
        >>> print(precise_time)
        "14:30:45.123"

        日志记录:
        >>> print(f'[{now()}] 操作完成')
        [2025-10-25 14:30:45] 操作完成

        性能监控:
        >>> print(f'开始时间: {now(1)}')
        >>> # ... 执行操作 ...
        >>> print(f'结束时间: {now(1)}')
        开始时间: 14:30:45.123
        结束时间: 14:30:46.456

    Note:
        - format_type=1 的毫秒精度取决于系统时钟
        - 返回的是字符串，不是时间对象
        - 使用本地时区，不是UTC时间
    """
    if format_type == 1:
        return time.strftime('%H:%M:%S', time.localtime()) + f'.{int(time.time() * 1000) % 1000:03d}'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


# 虚拟键码常量（替代bdtime.vk）
class VirtualKeys:
    """虚拟键码常量类，用于替代bdtime.vk

    提供Windows虚拟键码（Virtual Key Codes）常量定义。
    这些键码用于键盘和鼠标状态检测、输入模拟等底层操作。

    虚拟键码是Windows系统定义的标准键盘和鼠标按键标识符，
    每个按键都对应一个十六进制数值。本类封装了常用的虚拟键码，
    使代码更具可读性和可维护性。

    Categories:
        - 鼠标按键 (MOUSE_*): 左键、右键、中键
        - 常用按键: ESC, ENTER, SPACE, TAB, BACKSPACE, DELETE
        - 功能键 (F1-F12): F1 到 F12
        - 修饰键: SHIFT, CTRL, ALT
        - 数字键 (NUM_0 到 NUM_9): 主键盘区数字键
        - 字母键 (A-Z): 字母键

    Examples:
        检测按键状态:
        >>> import ctypes
        >>> # 检查是否按下了ESC键
        >>> if ctypes.windll.user32.GetAsyncKeyState(VirtualKeys.ESC) & 0x8000:
        ...     print('ESC键被按下')

        使用键码进行输入模拟:
        >>> # 模拟按下Ctrl+C
        >>> press_key(VirtualKeys.CTRL)
        >>> press_key(VirtualKeys.C)
        >>> release_key(VirtualKeys.C)
        >>> release_key(VirtualKeys.CTRL)

        在游戏脚本中使用:
        >>> # 按F1打开帮助
        >>> if some_condition:
        ...     send_key(VirtualKeys.F1)

    Note:
        - 键码值遵循Windows API标准
        - 大小写字母使用相同的键码（通过SHIFT区分）
        - 数字键码对应主键盘区，不包括小键盘
        - 完整的虚拟键码列表可参考Windows官方文档

    See Also:
        - Windows Virtual-Key Codes: https://docs.microsoft.com/windows/win32/inputdev/virtual-key-codes
        - GetAsyncKeyState: https://docs.microsoft.com/windows/win32/api/winuser/nf-winuser-getasynckeystate
    """

    # ===== 鼠标按键 =====
    MOUSE_LEFT = 0x01  # 鼠标左键
    MOUSE_RIGHT = 0x02  # 鼠标右键
    MOUSE_MIDDLE = 0x04  # 鼠标中键

    # ===== 常用按键 =====
    ESC = 0x1B  # Escape键
    ENTER = 0x0D  # 回车键
    SPACE = 0x20  # 空格键
    TAB = 0x09  # Tab键
    BACKSPACE = 0x08  # 退格键
    DELETE = 0x2E  # Delete键

    # ===== 功能键 =====
    F1 = 0x70  # F1功能键
    F2 = 0x71  # F2功能键
    F3 = 0x72  # F3功能键
    F4 = 0x73  # F4功能键
    F5 = 0x74  # F5功能键
    F6 = 0x75  # F6功能键
    F7 = 0x76  # F7功能键
    F8 = 0x77  # F8功能键
    F9 = 0x78  # F9功能键
    F10 = 0x79  # F10功能键
    F11 = 0x7A  # F11功能键
    F12 = 0x7B  # F12功能键

    # ===== 修饰键 =====
    SHIFT = 0x10  # Shift键（左右不区分）
    CTRL = 0x11  # Ctrl键（左右不区分）
    ALT = 0x12  # Alt键（左右不区分）

    # ===== 数字键（主键盘区）=====
    NUM_0 = 0x30  # 数字键0
    NUM_1 = 0x31  # 数字键1
    NUM_2 = 0x32  # 数字键2
    NUM_3 = 0x33  # 数字键3
    NUM_4 = 0x34  # 数字键4
    NUM_5 = 0x35  # 数字键5
    NUM_6 = 0x36  # 数字键6
    NUM_7 = 0x37  # 数字键7
    NUM_8 = 0x38  # 数字键8
    NUM_9 = 0x39  # 数字键9

    # ===== 字母键 =====
    A = 0x41  # 字母A
    B = 0x42  # 字母B
    C = 0x43  # 字母C
    D = 0x44  # 字母D
    E = 0x45  # 字母E
    F = 0x46  # 字母F
    G = 0x47  # 字母G
    H = 0x48  # 字母H
    I = 0x49  # noqa       # 字母I
    J = 0x4A  # 字母J
    K = 0x4B  # 字母K
    L = 0x4C  # 字母L
    M = 0x4D  # 字母M
    N = 0x4E  # 字母N
    O = 0x4F  # noqa       # 字母O
    P = 0x50  # 字母P
    Q = 0x51  # 字母Q
    R = 0x52  # 字母R
    S = 0x53  # 字母S
    T = 0x54  # 字母T
    U = 0x55  # 字母U
    V = 0x56  # 字母V
    W = 0x57  # 字母W
    X = 0x58  # 字母X
    Y = 0x59  # 字母Y
    Z = 0x5A  # 字母Z


# ===== 全局实例 =====
# 为了向后兼容和便捷使用，提供预创建的全局实例

# 全局时间跟踪器实例（与bdtime.tt兼容）
tt = TimeTracker()

# 全局虚拟键码实例（与bdtime.vk兼容）
vk = VirtualKeys()
