# !/usr/bin/env python3
"""鼠标操作模块 - 提供完整的鼠标控制功能

本模块是 xtdamo 鼠标操作的核心实现，封装了大漠插件的所有鼠标相关API，
并提供了增强的高级方法，支持更复杂的鼠标操作场景。

核心功能:
    - 鼠标移动：MoveTo（绝对）, MoveR（相对）, MoveToEx（随机偏移）
    - 鼠标点击：LeftClick, RightClick, MiddleClick, LeftDoubleClick
    - 按键控制：LeftDown/LeftUp, RightDown/RightUp（用于拖拽）
    - 滚轮操作：WheelUp, WheelDown
    - 位置获取：GetCursorPos
    - 延迟控制：SetMouseDelay

增强功能:
    - position 属性：便利的位置获取和设置
    - click_left：带持续时间的点击（支持长按效果）
    - click_right：带持续时间的右键点击
    - safe_click：安全点击（随机延迟+自动复位，防检测）

架构说明:
    Mouse 类采用双层设计：
    1. 标准API层：大写开头的方法（如 MoveTo），直接映射大漠插件API
    2. 增强功能层：小写开头的方法（如 safe_click），提供额外功能
    这种设计既保持了API的标准性，又提供了使用便利性。

使用示例:
    标准API:
        >>> from xtdamo import DmExcute
        >>> dm = DmExcute()
        >>> dm.Mouse.MoveTo(100, 200)  # 移动到指定位置
        >>> dm.Mouse.LeftClick()  # 左键点击

    便利属性:
        >>> x, y = dm.Mouse.position  # 获取当前位置
        >>> dm.Mouse.position = (500, 300)  # 设置位置

    增强功能:
        >>> dm.Mouse.click_left(100, 200, t=1.0)  # 长按1秒
        >>> dm.Mouse.safe_click(300, 400, auto_reset_pos=True)  # 安全点击

    拖拽操作:
        >>> dm.Mouse.MoveTo(100, 100)
        >>> dm.Mouse.LeftDown()
        >>> dm.Mouse.MoveTo(200, 200)
        >>> dm.Mouse.LeftUp()

注意事项:
    - 所有坐标为屏幕绝对坐标（窗口绑定后为窗口坐标）
    - safe_click 方法包含随机延迟，适合需要反检测的场景
    - click_left/click_right 支持持续时间，适合长按操作
    - 滚轮每次调用滚动一格，连续滚动需要循环调用

性能建议:
    - 频繁移动时使用 MoveTo 而非 position 属性
    - 简单点击使用 LeftClick 而非 click_left
    - 需要反检测时才使用 safe_click（有性能开销）

技术规格:
    Python版本：3.10+
    依赖：大漠插件 7.2129+
    类型注解：完整支持

作者信息:
    Author       : sandorn <sandorn@live.cn>
    Github       : https://github.com/sandorn/xtdamo
    LastEditTime : 2025-10-25
    License      : MIT

参考文档:
    - 大漠插件官方文档
    - xtdamo项目文档
==============================================================
"""

from __future__ import annotations

import random
from time import sleep
from typing import Any, Literal


class Mouse:
    """鼠标操作控制器

    提供完整的鼠标操作功能，包括移动、点击、拖拽、滚轮等。
    包含标准API方法和增强的高级封装方法。

    Attributes:
        dm_instance: 大漠插件实例

    Examples:
        基本使用:
        >>> mouse = Mouse(dm_instance)
        >>> mouse.MoveTo(100, 200)  # 移动鼠标
        >>> mouse.LeftClick()  # 左键点击

        使用便利属性:
        >>> x, y = mouse.position  # 获取当前位置
        >>> mouse.position = (500, 300)  # 设置位置

        高级封装:
        >>> mouse.click_left(100, 200, t=0.3)  # 带持续时间的点击
        >>> mouse.safe_click(300, 400)  # 安全点击（带随机延迟）

    Note:
        - 标准方法：大写开头（如 MoveTo）
        - 增强方法：小写开头（如 click_left, safe_click）
        - 使用 position 属性方便获取/设置鼠标位置
    """

    def __init__(self, dm_instance: Any) -> None:
        """初始化鼠标操作控制器

        Args:
            dm_instance: 大漠插件实例

        Raises:
            ValueError: 当 dm_instance 为 None 时抛出
        """
        if not dm_instance:
            raise ValueError('dmobject cannot be None')
        self.dm_instance = dm_instance

    @property
    def position(self) -> tuple[int, int]:
        """获取当前鼠标位置

        Returns:
            tuple[int, int]: (x, y) 坐标元组

        Examples:
            >>> x, y = mouse.position
            >>> print(f'鼠标位置: ({x}, {y})')
        """
        return self.dm_instance.GetCursorPos(x=0, y=0)[1:]

    @position.setter
    def position(self, xy: tuple[int, int]) -> None:
        """设置鼠标位置

        Args:
            xy: 包含 (x, y) 坐标的元组

        Raises:
            ValueError: 如果坐标格式不正确
            TypeError: 如果输入不是可迭代对象

        Examples:
            >>> mouse.position = (100, 200)
        """
        try:
            x, y = xy
            if not (isinstance(x, int) and isinstance(y, int)):
                raise ValueError('坐标值必须为整数')
            self.MoveTo(x, y)
        except (TypeError, ValueError) as e:
            raise ValueError('请输入格式为(x, y)的坐标元组') from e

    # ==================== 增强的鼠标方法 ====================

    def click_left(self, x: int, y: int, t: float = 0.5) -> Literal[1]:
        """左键点击（带持续时间）

        移动到指定位置并执行左键点击，支持自定义按键持续时间。
        适合需要长按或短按效果的场景。

        Args:
            x (int): 点击位置 X 坐标
            y (int): 点击位置 Y 坐标
            t (float, optional): 按键按下持续时间（秒），默认 0.5

        Returns:
            Literal[1]: 始终返回 1

        Examples:
            快速点击（短按）:
            >>> mouse.click_left(100, 200, t=0.1)

            长按效果:
            >>> mouse.click_left(100, 200, t=2.0)

            标准点击:
            >>> mouse.click_left(300, 400)

        Note:
            - 这是增强方法，比标准 LeftClick 多了持续时间参数
            - 适合模拟长按、蓄力等操作
            - 标准单击请使用 LeftClick() 方法

        See Also:
            - LeftClick: 标准左键单击
            - click_right: 右键点击（带持续时间）
        """
        self.dm_instance.MoveTo(x, y)
        self.dm_instance.LeftDown()
        sleep(t)
        self.dm_instance.LeftUp()
        return 1

    def click_right(self, x: int, y: int, t: float = 0.5) -> Literal[1]:
        """右键点击（带持续时间）

        移动到指定位置并执行右键点击，支持自定义按键持续时间。

        Args:
            x (int): 点击位置 X 坐标
            y (int): 点击位置 Y 坐标
            t (float, optional): 按键按下持续时间（秒），默认 0.5

        Returns:
            Literal[1]: 始终返回 1

        Examples:
            右键菜单:
            >>> mouse.click_right(100, 200)

            长按右键:
            >>> mouse.click_right(100, 200, t=1.0)

        Note:
            - 增强方法，支持持续时间
            - 标准右键点击请使用 RightClick()

        See Also:
            - RightClick: 标准右键单击
            - click_left: 左键点击（带持续时间）
        """
        self.dm_instance.MoveTo(x, y)
        self.dm_instance.RightDown()
        sleep(t)
        self.dm_instance.RightUp()
        return 1

    def safe_click(self, x: int, y: int, auto_reset_pos: bool = False) -> Literal[1]:
        """安全的鼠标点击（带随机延迟和复位）

        高级点击方法，包含随机延迟和可选的鼠标复位功能，
        更接近人工操作，适合需要反检测的场景。

        Args:
            x (int): 目标 X 坐标
            y (int): 目标 Y 坐标
            auto_reset_pos (bool, optional): 是否在点击后复位鼠标
                - True: 点击后随机偏移返回原位附近
                - False: 保持在点击位置，默认值

        Returns:
            Literal[1]: 成功返回 1

        Raises:
            KeyError: 点击操作失败时抛出

        Examples:
            基本安全点击:
            >>> mouse.safe_click(100, 200)

            点击后复位:
            >>> mouse.safe_click(300, 400, auto_reset_pos=True)

        Note:
            - 包含 50-400ms 的随机延迟，模拟人工操作
            - auto_reset_pos=True 时会随机偏移 50-300 像素返回
            - 适合需要规避检测的自动化场景
            - 比标准 LeftClick 更安全但稍慢

        See Also:
            - LeftClick: 标准左键点击
            - click_left: 带持续时间的点击
        """
        try:
            x0, y0 = self.position
            self.dm_instance.MoveTo(x, y)
            self.dm_instance.LeftClick()
            sleep(random.randint(50, 400) / 1000)
            if auto_reset_pos:
                self.dm_instance.MoveTo(x0 + random.randint(50, 300), y0 + random.randint(50, 300))
            return 1
        except Exception as e:
            raise KeyError(f'安全点击操作失败: {e}') from e

    # ==================== 标准鼠标API方法 ====================

    def GetCursorPos(self, x: int = 0, y: int = 0) -> tuple[int, int, int]:
        """获取当前鼠标坐标

        获取鼠标在屏幕上的当前位置。

        Args:
            x (int, optional): 输出参数X，通常传0，默认0
            y (int, optional): 输出参数Y，通常传0，默认0

        Returns:
            tuple[int, int, int]: (结果, X坐标, Y坐标)
                - 结果: 1表示成功，0表示失败
                - X坐标: 鼠标的X位置
                - Y坐标: 鼠标的Y位置

        Examples:
            获取鼠标位置:
            >>> ret, x, y = dm.Mouse.GetCursorPos()
            >>> if ret:
            ...     print(f'鼠标位置: ({x}, {y})')

            使用 position 属性（推荐）:
            >>> x, y = dm.Mouse.position
            >>> print(f'鼠标位置: ({x}, {y})')

        Note:
            - 推荐使用 position 属性替代此方法
            - 返回的是屏幕绝对坐标
            - 实时获取，不受窗口绑定影响

        See Also:
            - position: 属性方式获取位置
            - MoveTo: 移动鼠标到指定位置
        """
        return self.dm_instance.GetCursorPos(x, y)

    def SetMouseDelay(
        self,
        type: str = 'dx',
        delay: float = 100,
    ) -> int:
        """设置鼠标操作延迟

        配置鼠标操作的延迟时间，影响所有鼠标相关方法。

        Args:
            type (str, optional): 鼠标模式
                - 'normal': 正常模式
                - 'windows': Windows消息模式
                - 'dx': DirectX模式，默认值
            delay (int, optional): 延迟时间（毫秒）
                - 默认: 100
                - 范围: 通常 10-1000ms

        Returns:
            int: 设置结果
                - 1: 设置成功
                - 0: 设置失败

        Examples:
            设置较短延迟（快速操作）:
            >>> dm.Mouse.SetMouseDelay('dx', 10)

            设置较长延迟（模拟人工操作）:
            >>> dm.Mouse.SetMouseDelay('windows', 200)

        Note:
            - 延迟时间影响鼠标操作的速度
            - 过短的延迟可能导致某些程序无法正确识别
            - 建议根据目标程序调整合适的延迟
            - 也可以使用 set_delay 方法

        See Also:
            - set_delay: 封装的延迟设置方法
        """
        return self.dm_instance.SetMouseDelay(type, delay)

    def LeftClick(self) -> int:
        """鼠标左键单击

        在当前鼠标位置执行左键单击操作。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            先移动后点击:
            >>> dm.Mouse.MoveTo(100, 200)
            >>> dm.Mouse.LeftClick()

            配合查找使用:
            >>> found, x, y = dm.找图返回坐标(0, 0, 1920, 1080, 'button.bmp')
            >>> if found:
            ...     dm.Mouse.MoveTo(x, y)
            ...     dm.Mouse.LeftClick()

        Note:
            - 点击当前鼠标位置
            - 完整的按下和释放操作
            - 有配置的延迟时间

        See Also:
            - LeftDown: 按下左键（不释放）
            - LeftUp: 释放左键
            - LeftDoubleClick: 左键双击
        """
        return self.dm_instance.LeftClick()

    def LeftDoubleClick(self) -> int:
        """鼠标左键双击

        在当前鼠标位置执行左键双击操作。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            双击打开文件:
            >>> dm.Mouse.MoveTo(100, 200)
            >>> dm.Mouse.LeftDoubleClick()

        Note:
            - 连续执行两次快速点击
            - 适用于需要双击的场景
            - 双击间隔由系统设置决定

        See Also:
            - LeftClick: 单击
        """
        return self.dm_instance.LeftDoubleClick()

    def LeftDown(self) -> int:
        """鼠标左键按下（不释放）

        按下鼠标左键但不释放，需要配合 LeftUp 使用。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            模拟拖拽:
            >>> dm.Mouse.MoveTo(100, 100)
            >>> dm.Mouse.LeftDown()
            >>> dm.Mouse.MoveTo(200, 200)
            >>> dm.Mouse.LeftUp()

            长按操作:
            >>> dm.Mouse.LeftDown()
            >>> sleep(2)  # 按住2秒
            >>> dm.Mouse.LeftUp()

        Note:
            - 必须配合 LeftUp 使用
            - 常用于拖拽操作
            - 按键会一直保持按下状态直到调用 LeftUp

        See Also:
            - LeftUp: 释放左键
            - LeftClick: 完整的点击操作
        """
        return self.dm_instance.LeftDown()

    def LeftUp(self) -> int:
        """鼠标左键释放

        释放之前按下的鼠标左键。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            配合 LeftDown 拖拽:
            >>> dm.Mouse.MoveTo(100, 100)
            >>> dm.Mouse.LeftDown()
            >>> dm.Mouse.MoveTo(200, 200)
            >>> dm.Mouse.LeftUp()

        Note:
            - 必须与 LeftDown 配对使用
            - 释放的必须是之前按下的左键

        See Also:
            - LeftDown: 按下左键
        """
        return self.dm_instance.LeftUp()

    def MiddleClick(self) -> int:
        """鼠标中键单击

        在当前鼠标位置执行中键单击操作。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            中键点击链接（在新标签页打开）:
            >>> dm.Mouse.MoveTo(500, 300)
            >>> dm.Mouse.MiddleClick()

        Note:
            - 中键通常是滚轮按下
            - 部分鼠标可能没有中键
            - 浏览器中常用于新标签页打开

        See Also:
            - LeftClick: 左键点击
            - RightClick: 右键点击
        """
        return self.dm_instance.MiddleClick()

    def MoveR(self, rx: int, ry: int) -> int:
        """鼠标相对移动

        相对于当前位置移动鼠标。

        Args:
            rx (int): X轴偏移量
                - 正数向右，负数向左
            ry (int): Y轴偏移量
                - 正数向下，负数向上

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            向右移动50像素:
            >>> dm.Mouse.MoveR(50, 0)

            向下移动100像素:
            >>> dm.Mouse.MoveR(0, 100)

            斜向移动:
            >>> dm.Mouse.MoveR(30, 50)

            回退:
            >>> dm.Mouse.MoveR(-50, -50)

        Note:
            - 相对于当前位置的偏移
            - 适合需要微调位置的场景
            - 可以使用负数反向移动

        See Also:
            - MoveTo: 绝对位置移动
            - move_r: 封装方法
        """
        return self.dm_instance.MoveR(rx, ry)

    def MoveTo(self, x: int, y: int) -> int:
        """鼠标移动到绝对坐标

        将鼠标移动到屏幕的指定绝对坐标。

        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            移动到屏幕中心（1920x1080）:
            >>> dm.Mouse.MoveTo(960, 540)

            移动后点击:
            >>> dm.Mouse.MoveTo(100, 200)
            >>> dm.Mouse.LeftClick()

        Note:
            - 最常用的鼠标移动方法
            - 坐标是屏幕绝对坐标
            - 窗口绑定后使用窗口坐标

        See Also:
            - MoveR: 相对移动
            - MoveToEx: 带随机偏移的移动
            - move_to: 封装方法
        """
        return self.dm_instance.MoveTo(x, y)

    def MoveToEx(self, x: int, y: int, w: int, h: int) -> int:
        """鼠标移动到坐标（带随机偏移）

        移动到指定坐标附近的随机位置。

        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            w (int): X轴随机偏移范围
                - 实际X = x ± random(0, w)
            h (int): Y轴随机偏移范围
                - 实际Y = y ± random(0, h)

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            移动到按钮区域（带5像素随机偏移）:
            >>> dm.Mouse.MoveToEx(100, 200, 5, 5)
            >>> dm.Mouse.LeftClick()

            更大的随机范围:
            >>> dm.Mouse.MoveToEx(500, 300, 20, 20)

        Note:
            - 模拟人工操作的随机性
            - 适合点击较大的目标区域
            - 偏移量是双向的（±范围）

        See Also:
            - MoveTo: 精确移动
        """
        return self.dm_instance.MoveToEx(x, y, w, h)

    def RightClick(self) -> int:
        """鼠标右键单击

        在当前鼠标位置执行右键单击操作。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            右键打开菜单:
            >>> dm.Mouse.MoveTo(100, 200)
            >>> dm.Mouse.RightClick()

        Note:
            - 通常用于打开上下文菜单
            - 完整的按下和释放操作

        See Also:
            - RightDown: 按下右键
            - RightUp: 释放右键
            - LeftClick: 左键点击
        """
        return self.dm_instance.RightClick()

    def RightDown(self) -> int:
        """鼠标右键按下（不释放）

        按下鼠标右键但不释放，需要配合 RightUp 使用。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            >>> dm.Mouse.RightDown()
            >>> sleep(1)
            >>> dm.Mouse.RightUp()

        Note:
            - 必须配合 RightUp 使用
            - 较少使用，通常直接用 RightClick

        See Also:
            - RightUp: 释放右键
            - RightClick: 完整的右键点击
        """
        return self.dm_instance.RightDown()

    def RightUp(self) -> int:
        """鼠标右键释放

        释放之前按下的鼠标右键。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            >>> dm.Mouse.RightDown()
            >>> sleep(0.5)
            >>> dm.Mouse.RightUp()

        Note:
            - 必须与 RightDown 配对使用

        See Also:
            - RightDown: 按下右键
        """
        return self.dm_instance.RightUp()

    def WheelDown(self) -> int:
        """鼠标滚轮向下滚动

        模拟鼠标滚轮向下滚动一格。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            向下滚动页面:
            >>> for _ in range(5):
            ...     dm.Mouse.WheelDown()
            ...     sleep(0.1)

            滚动到页面底部:
            >>> for _ in range(10):
            ...     dm.Mouse.WheelDown()

        Note:
            - 每次调用滚动一格
            - 可以连续调用实现多格滚动
            - 滚动方向：向下（内容向上）

        See Also:
            - WheelUp: 向上滚动
        """
        return self.dm_instance.WheelDown()

    def WheelUp(self) -> int:
        """鼠标滚轮向上滚动

        模拟鼠标滚轮向上滚动一格。

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            向上滚动页面:
            >>> for _ in range(5):
            ...     dm.Mouse.WheelUp()
            ...     sleep(0.1)

            返回页面顶部:
            >>> for _ in range(10):
            ...     dm.Mouse.WheelUp()

        Note:
            - 每次调用滚动一格
            - 可以连续调用实现多格滚动
            - 滚动方向：向上（内容向下）

        See Also:
            - WheelDown: 向下滚动
        """
        return self.dm_instance.WheelUp()
