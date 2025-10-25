# !/usr/bin/env python3
"""
==============================================================
Description  : 高级功能封装模块 - 提供图像识别、文本识别、高级操作等功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-18 22:00:00
Github       : https://github.com/sandorn/xtdamo

本模块提供以下核心功能:
- 图像识别与查找 (FindPic, FindPicEx)
- 文本识别与查找 (FindStr, FindStrEx)
- 颜色识别与查找 (FindColor, FindColorEx)
- 高级操作封装 (safe_click, find_and_click)
- 智能等待与重试机制

主要特性:
- 支持多种图像格式识别
- 智能相似度匹配
- 自动重试机制
- 异常处理与错误恢复
- 性能优化的查找算法
==============================================================
"""

from __future__ import annotations

import math
import random
from time import sleep
from typing import Any

from .config import Config
from .time_utils import TimeTracker


class ApiProxy:
    def __init__(self, dm_instance: Any, core_engine: Any | None = None) -> None:
        """高级功能封装（高级接口层）

        提供对核心引擎的高级封装，简化常用操作，增强易用性。

        Args:
            dm_instance: 大漠插件实例 (必须)
            core_engine: 核心引擎实例 (可选)，用于调用底层核心方法

        Raises:
            ValueError: 如果 dm_instance 为 None

        Note:
            - 作为高级接口层，应优先调用 core_engine 的方法而非直接调用 dm_instance
            - 提供更友好的中文接口和智能化的参数处理
        """
        if not dm_instance:
            raise ValueError('dmobject参数不能为空')
        self.dm_instance = dm_instance
        self.core_engine = core_engine
        self._last_error = ''  # 新增错误记录属性

    def 绑定窗口(
        self,
        hwnd: int,
        display: str | None = None,
        mouse: str | None = None,
        keypad: str | None = None,
        public: str = 'dx.public.fake.window.min|dx.public.hack.speed',
        mode: int | None = None,
    ) -> bool:
        """绑定窗口（高级接口）

        高级窗口绑定方法，提供参数验证、错误处理和友好的错误提示。

        Args:
            hwnd (int): 窗口句柄
                - 必须是有效的窗口句柄（非0）
            display (str | None, optional): 显示模式
                - None: 使用默认配置 ('gdi')
                - 可选值: 'normal', 'gdi', 'gdi2', 'dx', 'dx2'
            mouse (str | None, optional): 鼠标模式
                - None: 使用默认配置 ('windows3')
                - 可选值: 'normal', 'windows', 'windows2', 'windows3', 'dx', 'dx2'
            keypad (str | None, optional): 键盘模式
                - None: 使用默认配置 ('windows')
                - 可选值: 'normal', 'windows', 'dx'
            public (str, optional): 公共参数
                - 默认: 'dx.public.fake.window.min|dx.public.hack.speed'
            mode (int | None, optional): 绑定模式
                - None: 使用默认配置 (101)
                - 可选值: 0, 1, 2, 3, 4, 5, 6, 7, 101, 103

        Returns:
            bool: 绑定是否成功
                - True: 绑定成功

        Raises:
            AssertionError: 当窗口句柄无效或绑定失败时
            ValueError: 当提供的参数值不在有效范围内时

        Examples:
            基本使用（使用默认配置）:
            >>> hwnd = dm.FindWindow('', '游戏窗口')
            >>> if dm.绑定窗口(hwnd):
            ...     print('绑定成功，可以进行后台操作')

            自定义绑定参数:
            >>> success = dm.绑定窗口(hwnd, display='dx2', mouse='windows3', mode=101)

            参数验证（自动检测无效参数）:
            >>> try:
            ...     dm.绑定窗口(hwnd, display='invalid_mode')
            ... except ValueError as e:
            ...     print(f'参数错误: {e}')

        Note:
            - 会自动验证参数的有效性，无效参数会抛出 ValueError
            - 绑定失败时会抛出 AssertionError 并包含详细错误信息
            - 参数为 None 时使用默认配置，不会覆盖默认值

        See Also:
            - Config.BIND_MODES: 所有有效的绑定模式
            - 解绑窗口: 解除窗口绑定
        """
        # 验证窗口句柄
        assert hwnd != 0, f'无效的窗口句柄: {hwnd}'

        # 参数验证会在 Config.get_bind_config 中进行
        # 优先使用 CoreEngine 的方法（如果可用）
        try:
            bind_config = Config.get_bind_config(
                display=display,
                mouse=mouse,
                keypad=keypad,
                mode=mode,
            )
            ret = self.dm_instance.BindWindowEx(
                hwnd,
                bind_config['display'],
                bind_config['mouse'],
                bind_config['keypad'],
                public,
                bind_config['mode'],
            )
        except ValueError as e:
            # 参数验证失败，重新抛出带有更友好的错误信息
            raise ValueError(f'绑定参数无效: {e}') from e

        # 检查绑定结果
        if ret != 1:
            error_msg = Config.get_error_message(ret)
            self._last_error = str(ret)

            raise AssertionError(
                f'窗口绑定失败!\n'
                f'  窗口句柄: {hwnd}\n'
                f'  错误代码: {ret}\n'
                f'  错误信息: {error_msg}\n'
                f'  绑定配置: display={display or "gdi"}, '
                f'mouse={mouse or "windows3"}, '
                f'keypad={keypad or "windows"}, '
                f'mode={mode or 101}'
            )

        return True

    def 解绑窗口(self) -> bool:
        """解绑窗口（高级接口）

        解除当前窗口的绑定状态，释放相关资源。

        Returns:
            bool: 解绑是否成功
                - True: 解绑成功
                - False: 解绑失败（可能未绑定或解绑出错）

        Examples:
            基本使用:
            >>> if dm.解绑窗口():
            ...     print('解绑成功')

            完整的绑定-操作-解绑流程:
            >>> hwnd = dm.FindWindow('', '游戏窗口')
            >>> if dm.绑定窗口(hwnd):
            ...     # 执行一些后台操作
            ...     dm.LeftClick()
            ...     # 操作完成后解绑
            ...     dm.解绑窗口()

        Note:
            - 使用完窗口绑定后建议及时解绑，释放资源
            - 即使未绑定窗口，调用此方法也不会报错

        See Also:
            - 绑定窗口: 绑定窗口
        """
        ret = self.dm_instance.UnBindWindow()
        return ret == 1

    def 获取窗口标题(self, hwnd: int) -> str:
        """获取窗口标题

        根据窗口句柄获取窗口的标题文本。

        Args:
            hwnd (int): 窗口句柄

        Returns:
            str: 窗口标题文本
                - 成功: 返回窗口标题字符串
                - 失败: 返回空字符串

        Examples:
            获取记事本标题:
            >>> hwnd = dm.FindWindow('', 'Notepad')
            >>> title = dm.获取窗口标题(hwnd)
            >>> print(title)

            验证窗口:
            >>> if title := dm.获取窗口标题(hwnd):
            ...     print(f'找到窗口: {title}')

        Note:
            - 窗口句柄必须是有效的
            - 如果窗口不存在，返回空字符串

        See Also:
            - FindWindow: 查找窗口
            - GetWindowState: 获取窗口状态
        """
        return self.dm_instance.GetWindowTitle(hwnd)

    def _parse_result(self, ret: str) -> tuple[int, int]:
        """解析大漠插件返回的坐标字符串

        将大漠插件的查找方法返回的字符串格式（如 "id|x|y"）
        解析为标准的坐标元组，增强容错性。

        Args:
            ret (str): 大漠插件返回的结果字符串
                - 标准格式: "id|x|y"
                - 部分格式: "id|x"
                - 空值或无效格式

        Returns:
            tuple[int, int]: 解析后的坐标 (x, y)
                - 完整坐标: (x, y) 当 parts[1] 和 parts[2] 都有效
                - 部分坐标: (x, 0) 当只有 parts[1] 有效
                - 无效坐标: (0, 0) 当解析失败或输入无效

        Examples:
            标准格式解析:
            >>> self._parse_result('0|100|200')
            (100, 200)

            部分格式解析:
            >>> self._parse_result('0|100')
            (100, 0)

            无效格式处理:
            >>> self._parse_result('')
            (0, 0)
            >>> self._parse_result('invalid')
            (0, 0)

        Note:
            - 使用 '|' 作为分隔符
            - parts[0] 通常是图片ID或其他标识
            - parts[1] 是 X 坐标
            - parts[2] 是 Y 坐标
            - 对所有异常进行捕获，保证返回元组格式
            - (0, 0) 表示无效坐标或查找失败

        See Also:
            - _find_and_act: 使用此方法解析查找结果
        """
        parts = (ret or '').split('|')
        try:
            if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                return (int(parts[1]), int(parts[2]))
            if len(parts) >= 2 and parts[1].isdigit():
                # 如果只有一个有效数字，返回(x, 0)的形式
                return (int(parts[1]), 0)
            return (0, 0)
        except (ValueError, IndexError):
            return (0, 0)

    def _find_and_act(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        find_func,
        target: str,
        timeout: float = 0,
        click: bool = False,
        reset_pos: bool = False,
        disappear: bool = False,
        confidence: float = Config.DEFAULT_SIMILARITY,
    ) -> tuple[bool, int, int]:
        """通用查找执行方法 - 核心查找逻辑封装

        提供统一的查找、等待、点击逻辑，支持超时、重试、消失检测等功能。
        是所有找图、找字方法的底层实现。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            find_func (callable): 查找函数
                - 签名: func(x1, y1, x2, y2, target) -> str
                - 返回: "id|x|y" 格式的字符串
            target (str): 查找目标
                - 图片查找: 图片路径或图片名称
                - 文字查找: 要查找的文字内容
            timeout (float, optional): 超时时间（秒）
                - 0: 只查找一次，默认值
                - >0: 持续查找直到超时或找到
            click (bool, optional): 是否点击找到的位置
                - True: 找到后自动点击
                - False: 只返回坐标，默认值
            reset_pos (bool, optional): 点击后是否复位鼠标
                - True: 点击后将鼠标移回原位
                - False: 保持在点击位置，默认值
            disappear (bool, optional): 是否等待目标消失
                - True: 持续点击直到目标消失
                - False: 找到即返回，默认值
            confidence (float, optional): 相似度
                - 范围: 0.0-1.0
                - 默认: Config.DEFAULT_SIMILARITY

        Returns:
            tuple[bool, int, int]: 查找结果 (状态, X坐标, Y坐标)
                - 状态: True 找到/消失, False 未找到
                - X坐标: 最后一次找到的 X 位置（未找到为 0）
                - Y坐标: 最后一次找到的 Y 位置（未找到为 0）

        Examples:
            查找图片并点击:
            >>> state, x, y = self._find_and_act(0, 0, 1920, 1080, lambda *args: self.dm_instance.FindPicE(*args), 'button.bmp', timeout=5, click=True)

            等待目标消失:
            >>> state, _, _ = self._find_and_act(0, 0, 800, 600, find_func, 'loading.bmp', timeout=30, disappear=True)

        Note:
            - 查找循环中有 50-400ms 的随机延迟，防止CPU占用过高
            - disappear=True 时，会持续查找直到目标消失
            - click=True 时，调用 safe_click 方法进行点击
            - 超时返回 (False, 0, 0)
            - 使用 TimeTracker 进行精确的超时控制

        See Also:
            - 找图单击: 使用此方法查找并点击图片
            - 找字单击: 使用此方法查找并点击文字
            - _parse_result: 解析查找结果
        """
        state = False
        x: int = 0
        y: int = 0

        # 创建时间跟踪器
        time_tracker = TimeTracker(timeout)

        while time_tracker.during():
            x, y = self._parse_result(find_func(x1, y1, x2, y2, target))

            if x > 0 and y > 0:
                if click:
                    self.dm_instance.MoveTo(x, y)
                    self.dm_instance.LeftClick()
                    if reset_pos:
                        self.dm_instance.MoveTo(x + random.randint(50, 300), y + random.randint(50, 300))
                state = True
                if not disappear:
                    break

            elif disappear:
                break

            sleep(random.randint(50, 400) / 1000)

        return state, x, y

    def 找字单击至消失(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        text: str,
        color: str,
        timeout: float = 0,
        reset_pos: bool = False,
    ) -> tuple[bool, int, int]:
        """查找文字并持续点击直到消失

        在指定区域内查找文字，找到后点击，持续操作直到文字消失。
        适用于需要重复点击才能消失的UI元素（如确认按钮、弹窗等）。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            text (str): 要查找的文字内容
            color (str): 文字颜色（十六进制格式，如 "FFFFFF"）
            timeout (float, optional): 超时时间（秒）
                - 0: 无限等待直到消失，默认值
                - >0: 最多等待指定秒数
            reset_pos (bool, optional): 点击后是否复位鼠标
                - True: 点击后将鼠标移回原位
                - False: 保持在点击位置，默认值

        Returns:
            tuple[bool, int, int]: (是否消失, 最后X坐标, 最后Y坐标)
                - 是否消失: True 目标已消失, False 超时未消失
                - X坐标: 最后一次找到的 X 位置
                - Y坐标: 最后一次找到的 Y 位置

        Examples:
            关闭弹窗（持续点击直到消失）:
            >>> disappeared, x, y = dm.找字单击至消失(0, 0, 1920, 1080, '确定', 'FFFFFF', timeout=10)
            >>> if disappeared:
            ...     print('弹窗已关闭')

            点击后复位鼠标:
            >>> dm.找字单击至消失(100, 100, 500, 300, '关闭', 'FF0000', reset_pos=True)

        Note:
            - 会持续点击直到文字消失或超时
            - 使用默认相似度 Config.DEFAULT_SIMILARITY
            - 每次查找间隔 50-400ms 随机延迟
            - 适合处理需要多次点击的UI元素

        See Also:
            - 找字单击: 找到后点击一次即返回
            - 找图单击至消失: 图片版本的持续点击
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, t: self.dm_instance.FindStrE(
                x1,
                y1,
                x2,
                y2,
                t,
                color,
                Config.DEFAULT_SIMILARITY,
            ),
            text,
            timeout,
            click=True,
            reset_pos=reset_pos,
            disappear=True,
        )

    def 找字单击(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        text: str,
        color: str,
        timeout: float = 0,
        reset_pos: bool = False,
    ) -> tuple[bool, int, int]:
        """查找文字并点击一次

        在指定区域内查找文字，找到后点击一次即返回。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            text (str): 要查找的文字内容
            color (str): 文字颜色（十六进制格式）
            timeout (float, optional): 超时时间（秒）
                - 0: 只查找一次，默认值
                - >0: 持续查找直到找到或超时
            reset_pos (bool, optional): 点击后是否复位鼠标，默认 False

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)

        Examples:
            查找并点击按钮:
            >>> found, x, y = dm.找字单击(0, 0, 1920, 1080, '开始游戏', 'FFFFFF', timeout=5)
            >>> if found:
            ...     print(f'已点击按钮，位置: ({x}, {y})')

        See Also:
            - 找字单击至消失: 持续点击直到消失
            - 找字返回坐标: 只查找不点击
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, t: self.dm_instance.FindStrE(x1, y1, x2, y2, t, color, Config.DEFAULT_SIMILARITY),
            text,
            timeout,
            click=True,
            reset_pos=reset_pos,
        )

    def 找字返回坐标(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        text: str,
        color: str,
        timeout: float = 0,
    ) -> tuple[bool, int, int]:
        """查找文字并返回坐标（不点击）

        在指定区域内查找文字，返回其坐标位置，但不执行点击操作。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            text (str): 要查找的文字内容
            color (str): 文字颜色（十六进制格式）
            timeout (float, optional): 超时时间（秒）
                - 0: 只查找一次，默认值
                - >0: 持续查找直到找到或超时

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)
                - 是否找到: True 找到, False 未找到
                - X坐标: 文字中心 X 位置（未找到为 0）
                - Y坐标: 文字中心 Y 位置（未找到为 0）

        Examples:
            查找文字获取坐标:
            >>> found, x, y = dm.找字返回坐标(0, 0, 1920, 1080, '开始', 'FFFFFF', timeout=3)
            >>> if found:
            ...     print(f'文字位置: ({x}, {y})')
            ...     # 可以自定义后续操作，如右键点击
            ...     dm.RightClick()

            检查文字是否存在:
            >>> exists, _, _ = dm.找字返回坐标(100, 100, 500, 300, '提示', 'FF0000')
            >>> if exists:
            ...     print('提示文字存在')

        Note:
            - 只返回坐标，不执行任何点击或移动操作
            - 适合需要获取位置后进行自定义操作的场景
            - 使用默认相似度 Config.DEFAULT_SIMILARITY

        See Also:
            - 找字单击: 查找并点击
            - 简易找字: 更简单的查找接口
        """
        state, (x, y) = False, (0, 0)
        time_tracker = TimeTracker(timeout)
        while time_tracker.during():
            x, y = self._parse_result(self.dm_instance.FindStrE(x1, y1, x2, y2, text, color, Config.DEFAULT_SIMILARITY))
            if x > 0 and y > 0:
                state = True
                break
        return state, x, y

    def 简易找字(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        text: str,
        color: str,
        timeout: float = 0,
    ) -> tuple[bool, int, int]:
        """简易文字查找（只返回状态和坐标）

        简化版的文字查找方法，只返回查找结果，不执行点击操作。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            text (str): 要查找的文字内容
            color (str): 文字颜色（十六进制格式）
            timeout (float, optional): 超时时间（秒），默认 0

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)

        Examples:
            快速查找文字:
            >>> found, x, y = dm.简易找字(0, 0, 800, 600, '确定', 'FFFFFF')

        Note:
            - 这是最简单的查找接口，适合快速检测
            - 使用默认相似度

        See Also:
            - 找字返回坐标: 功能相同的标准接口
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda *args: self.dm_instance.FindStrE(*args, Config.DEFAULT_SIMILARITY),
            text,
            timeout,
        )

    def 找图单击至消失(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        pic_name: str,
        timeout: float = 0,
        scan_mode: int = 0,
        reset_pos: bool = False,
    ) -> tuple[bool, int, int]:
        """查找图片并持续点击直到消失

        在指定区域内查找图片，找到后点击，持续操作直到图片消失。
        适用于需要重复点击才能消失的UI元素。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            pic_name (str): 图片文件名或路径
                - 支持格式: bmp, jpg, png
                - 可以是相对路径或绝对路径
            timeout (float, optional): 超时时间（秒）
                - 0: 无限等待直到消失，默认值
                - >0: 最多等待指定秒数
            scan_mode (int, optional): 扫描模式
                - 0: 从左到右，从上到下（默认）
                - 1: 从中心向四周
                - 2: 从右到左，从下到上
            reset_pos (bool, optional): 点击后是否复位鼠标，默认 False

        Returns:
            tuple[bool, int, int]: (是否消失, 最后X坐标, 最后Y坐标)

        Examples:
            关闭弹窗（持续点击）:
            >>> disappeared, x, y = dm.找图单击至消失(0, 0, 1920, 1080, 'close_button.bmp', timeout=10)

        Note:
            - 会持续点击直到图片消失或超时
            - 使用默认相似度和透明色
            - 适合处理需要多次点击的UI

        See Also:
            - 找图单击: 找到后点击一次即返回
            - 找字单击至消失: 文字版本的持续点击
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, n: self.dm_instance.FindPicE(x1, y1, x2, y2, n, '000000', Config.DEFAULT_SIMILARITY, scan_mode),
            pic_name,
            timeout,
            click=True,
            reset_pos=reset_pos,
            disappear=True,
        )

    def 找图单击(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        pic_name: str,
        timeout: float = 0,
        scan_mode: int = 0,
        reset_pos: bool = False,
    ) -> tuple[bool, int, int]:
        """查找图片并点击一次

        在指定区域内查找图片，找到后点击一次即返回。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            pic_name (str): 图片文件名或路径
            timeout (float, optional): 超时时间（秒），默认 0
            scan_mode (int, optional): 扫描模式，默认 0
            reset_pos (bool, optional): 点击后是否复位鼠标，默认 False

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)

        Examples:
            查找并点击按钮:
            >>> found, x, y = dm.找图单击(0, 0, 1920, 1080, 'start_btn.bmp', timeout=5)

        See Also:
            - 找图单击至消失: 持续点击直到消失
            - 找图返回坐标: 只查找不点击
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, n: self.dm_instance.FindPicE(x1, y1, x2, y2, n, '000000', Config.DEFAULT_SIMILARITY, scan_mode),
            pic_name,
            timeout,
            click=True,
            reset_pos=reset_pos,
        )

    def 找图返回坐标(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        pic_name: str,
        timeout: float = 0,
        scan_mode: int = 0,
    ) -> tuple[bool, int, int]:
        """查找图片并返回坐标（不点击）

        在指定区域内查找图片，返回其坐标位置，但不执行点击操作。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            pic_name (str): 图片文件名或路径
            timeout (float, optional): 超时时间（秒），默认 0
            scan_mode (int, optional): 扫描模式，默认 0

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)

        Examples:
            查找图片获取坐标:
            >>> found, x, y = dm.找图返回坐标(0, 0, 1920, 1080, 'target.bmp', timeout=3)
            >>> if found:
            ...     print(f'图片位置: ({x}, {y})')

        Note:
            - 只返回坐标，不执行任何操作
            - 适合需要获取位置后进行自定义操作的场景

        See Also:
            - 找图单击: 查找并点击
            - 简易找图: 更简单的查找接口
        """
        state, x, y = self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, n: self.dm_instance.FindPicE(x1, y1, x2, y2, n, '000000', Config.DEFAULT_SIMILARITY, scan_mode),
            pic_name,
            timeout,
        )
        return state, x, y

    def 简易找图(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        pic_name: str,
        timeout: float = 0,
        scan_mode: int = 0,
    ) -> tuple[bool, int, int]:
        """简易图片查找（只返回状态和坐标）

        简化版的图片查找方法，只返回查找结果，不执行点击操作。

        Args:
            x1 (int): 查找区域左上角 X 坐标
            y1 (int): 查找区域左上角 Y 坐标
            x2 (int): 查找区域右下角 X 坐标
            y2 (int): 查找区域右下角 Y 坐标
            pic_name (str): 图片文件名或路径
            timeout (float, optional): 超时时间（秒），默认 0
            scan_mode (int, optional): 扫描模式，默认 0

        Returns:
            tuple[bool, int, int]: (是否找到, X坐标, Y坐标)

        Examples:
            快速查找图片:
            >>> found, x, y = dm.简易找图(0, 0, 800, 600, 'icon.bmp')

        Note:
            - 这是最简单的图片查找接口
            - 适合快速检测图片是否存在

        See Also:
            - 找图返回坐标: 功能相同的标准接口
        """
        return self._find_and_act(
            x1,
            y1,
            x2,
            y2,
            lambda x1, y1, x2, y2, n: self.dm_instance.FindPicE(x1, y1, x2, y2, n, '000000', Config.DEFAULT_SIMILARITY, scan_mode),
            pic_name,
            timeout,
        )

    def 简易识字(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: str,
        confidence: float = Config.DEFAULT_SIMILARITY,
        timeout: float = 0,
    ) -> str | bool:
        """OCR文字识别

        使用大漠插件的 OCR 功能识别指定区域内的文字内容。

        Args:
            x1 (int): 识别区域左上角 X 坐标
            y1 (int): 识别区域左上角 Y 坐标
            x2 (int): 识别区域右下角 X 坐标
            y2 (int): 识别区域右下角 Y 坐标
            color (str): 文字颜色（十六进制格式，如 "FFFFFF"）
            confidence (float, optional): 相似度
                - 范围: 0.0-1.0
                - 默认: Config.DEFAULT_SIMILARITY
            timeout (float, optional): 超时时间（秒）
                - 0: 只识别一次，默认值
                - >0: 持续识别直到成功或超时

        Returns:
            str | bool: 识别结果
                - 成功: 返回识别到的文字字符串
                - 失败: 返回 False

        Examples:
            识别文字:
            >>> text = dm.简易识字(100, 100, 500, 200, 'FFFFFF')
            >>> if text:
            ...     print(f'识别到文字: {text}')

            带超时的识别:
            >>> text = dm.简易识字(0, 0, 800, 100, 'FF0000', timeout=5)
            >>> if text:
            ...     print(f'识别结果: {text}')

            自定义相似度:
            >>> text = dm.简易识字(200, 200, 600, 300, 'FFFFFF', confidence=0.8, timeout=3)

        Note:
            - 需要预先配置大漠插件的字库文件
            - 识别精度受字库质量和相似度参数影响
            - timeout > 0 时会持续重试，每次间隔 100-400ms
            - 返回 False 表示识别失败或超时

        See Also:
            - Ocr: 大漠原生 OCR 方法
            - FindStr: 查找指定文字
        """

        def ocr_operation():
            result = self.dm_instance.Ocr(x1, y1, x2, y2, color, confidence)
            return result if result else None

        if timeout > 0:
            time_tracker = TimeTracker(timeout)
            while time_tracker.during():
                if text := ocr_operation():
                    return text
                sleep(random.uniform(Config.DEFAULT_MOUSE_DELAY, 0.4))
        else:
            if text := ocr_operation():
                return text
        return False

    def 圆形渐开找鼠标(
        self,
        start_x: int,
        start_y: int,
        cursor_code: int,
        radius: float = 1,
        step: float = 1,
        max_circles: int = 6,
    ) -> bool:
        """通过渐开螺旋轨迹查找并点击特定光标

        以指定起点为中心，按照渐开螺旋轨迹移动鼠标，
        查找特定特征码的光标并执行点击操作。

        轨迹说明：
            - 起点: (start_x, start_y)
            - 初始半径: radius
            - 半径增长: 每20度增加 step 像素
            - 角度步长: 每次旋转 10 度
            - 最大圈数: max_circles

        Args:
            start_x (int): 螺旋轨迹的起始 X 坐标（像素）
            start_y (int): 螺旋轨迹的起始 Y 坐标（像素）
            cursor_code (int): 目标光标的特征码
                - 通过 dm.GetCursorShape() 获取
                - 不同光标有不同的特征码
            radius (float, optional): 初始螺旋半径（像素）
                - 默认: 1
                - 控制轨迹与起点的初始距离
            step (float, optional): 半径增长步长（像素）
                - 默认: 1
                - 每 20 度增加的半径值
                - 控制螺旋展开速度
            max_circles (int, optional): 最大螺旋圈数
                - 默认: 6
                - 控制轨迹覆盖范围
                - 防止无限循环

        Returns:
            bool: 查找结果
                - True: 找到目标光标并已点击
                - False: 遍历完所有圈数未找到

        Examples:
            查找手型光标（通常表示可点击元素）:
            >>> # 先获取目标光标的特征码
            >>> # 手动移动到目标位置，获取光标码
            >>> cursor_code = dm.GetCursorShape()
            >>> # 使用圆形渐开轨迹查找
            >>> found = dm.圆形渐开找鼠标(500, 500, cursor_code)
            >>> if found:
            ...     print('已找到并点击目标')

            自定义参数查找:
            >>> dm.圆形渐开找鼠标(start_x=800, start_y=600, cursor_code=65563, radius=2, step=2, max_circles=10)

        Note:
            - 每次移动间隔 1ms，防止移动过快
            - 使用极坐标转笛卡尔坐标计算位置
            - 每 20 度（每 2 次采样）增加半径
            - 每圈采样 36 个点（360° / 10°）
            - 找到目标后立即点击并返回
            - 适用于查找特定光标状态的UI元素

        See Also:
            - GetCursorShape: 获取当前光标特征码
            - 散点渐开找鼠标: 散点螺旋查找
            - 椭圆渐开找鼠标: 椭圆螺旋查找
            - 方形渐开找鼠标: 方形螺旋查找
        """
        # 1度对应的弧度值（用于角度转弧度计算）
        radian_per_degree = math.radians(1)

        # 外层循环控制螺旋圈数
        for _ in range(max_circles):
            # 内层循环以10度为步长遍历360度圆周（共36个采样点/圈）
            for angle in range(0, 360, 10):
                # 将角度转换为弧度（数学函数需要弧度制输入）
                current_radian = angle * radian_per_degree

                # 计算当前角度对应的螺旋坐标（极坐标转笛卡尔坐标）
                x = start_x + radius * math.cos(current_radian)
                y = start_y + radius * math.sin(current_radian)

                # 移动鼠标到计算出的坐标位置
                self.dm_instance.MoveTo(x, y)

                # 检查当前光标是否符合目标特征码
                if self.dm_instance.GetCursorShape() == cursor_code:
                    self.dm_instance.LeftClick()  # 找到目标后执行左键点击
                    return True  # 立即返回成功状态

                # 每20度（即每2次内层循环）增加半径，形成渐开效果
                if angle % 20 == 0:
                    radius += step

                # 控制鼠标移动节奏（1ms延迟防止过快移动）
                sleep(0.001)

        # 遍历完所有圈数未找到目标，返回失败
        return False

    def 散点渐开找鼠标(
        self,
        start_x: int,
        start_y: int,
        cursor_code: int,
        radius: float = 2,
        step: float = 0.6,
        max_iterations: int = 80,
    ) -> bool:
        """通过散点螺旋轨迹查找并点击特定光标

        使用散点螺旋算法移动鼠标，轨迹呈不规则螺旋状向外扩展，
        适合在不规则分布的UI元素中查找目标光标。

        轨迹特点：
            - 散点螺旋，非规则圆形
            - X = start_x + cos(r) + r * sin(r)
            - Y = start_y + sin(r) - r * cos(r)
            - 每次迭代增加 step

        Args:
            start_x (int): 起始 X 坐标（像素）
            start_y (int): 起始 Y 坐标（像素）
            cursor_code (int): 目标光标的特征码
            radius (float, optional): 初始半径参数
                - 默认: 2
                - 影响初始位置和轨迹形状
            step (float, optional): 半径增长步长
                - 默认: 0.6
                - 控制螺旋展开速度
            max_iterations (int, optional): 最大迭代次数
                - 默认: 80
                - 防止无限循环

        Returns:
            bool: 查找结果
                - True: 找到并已点击
                - False: 未找到

        Examples:
            使用散点螺旋查找:
            >>> found = dm.散点渐开找鼠标(600, 400, 65563)

            自定义参数:
            >>> dm.散点渐开找鼠标(start_x=500, start_y=500, cursor_code=65563, radius=3, step=0.8, max_iterations=100)

        Note:
            - 轨迹比圆形螺旋更不规则
            - 适合在密集UI元素中查找
            - 每次移动间隔 1ms
            - 找到后立即点击并返回

        See Also:
            - 圆形渐开找鼠标: 规则圆形螺旋
            - 椭圆渐开找鼠标: 椭圆螺旋
        """
        for _ in range(max_iterations):
            xzb = start_x + math.cos(radius) + radius * math.sin(radius)
            yzb = start_y + math.sin(radius) - radius * math.cos(radius)
            self.dm_instance.MoveTo(xzb, yzb)
            mouse_tz = self.dm_instance.GetCursorShape()
            if mouse_tz == cursor_code:
                self.dm_instance.LeftClick()
                return True
            radius += step
            sleep(0.001)
        return False

    def 椭圆渐开找鼠标(
        self,
        start_x: int,
        start_y: int,
        cursor_code: int,
        width_radius: float = 0.5,
        height_radius: float = 8,
        step: float = 0.5,
        max_circles: int = 6,
    ) -> bool:
        """通过椭圆螺旋轨迹查找并点击特定光标

        以椭圆螺旋轨迹移动鼠标，适合在横向或纵向分布较广的区域查找目标。

        轨迹特点：
            - 椭圆形螺旋，可自定义宽高比
            - X = start_x + width_radius * cos(angle)
            - Y = start_y + height_radius * sin(angle)
            - 每 20 度同时增加宽度和高度半径

        Args:
            start_x (int): 起始 X 坐标（像素）
            start_y (int): 起始 Y 坐标（像素）
            cursor_code (int): 目标光标的特征码
            width_radius (float, optional): 初始宽度半径
                - 默认: 0.5
                - 控制椭圆的横向尺寸
            height_radius (float, optional): 初始高度半径
                - 默认: 8
                - 控制椭圆的纵向尺寸
            step (float, optional): 半径增长步长
                - 默认: 0.5
                - 每 20 度同时增加到宽高半径
            max_circles (int, optional): 最大螺旋圈数
                - 默认: 6

        Returns:
            bool: 查找结果
                - True: 找到并已点击
                - False: 未找到

        Examples:
            纵向查找（高度大于宽度）:
            >>> dm.椭圆渐开找鼠标(500, 400, 65563, width_radius=1, height_radius=10)

            横向查找（宽度大于高度）:
            >>> dm.椭圆渐开找鼠标(500, 400, 65563, width_radius=10, height_radius=1)

            均衡查找:
            >>> dm.椭圆渐开找鼠标(start_x=600, start_y=500, cursor_code=65563, width_radius=5, height_radius=5, step=1, max_circles=8)

        Note:
            - 每圈采样 36 个点（360° / 10°）
            - 适合横向或纵向分布的UI元素
            - 可通过调整宽高半径适应不同布局
            - 每次移动间隔 1ms

        See Also:
            - 圆形渐开找鼠标: 规则圆形螺旋
            - 散点渐开找鼠标: 散点螺旋
            - 方形渐开找鼠标: 方形螺旋
        """
        seed = 3.1415926535897 / 180

        for _ in range(max_circles):
            for angle in range(0, 360, 10):
                xzb = start_x + width_radius * math.cos(angle * seed)
                yzb = start_y + height_radius * math.sin(angle * seed)
                self.dm_instance.MoveTo(xzb, yzb)
                sleep(0.001)
                mouse_tz = self.dm_instance.GetCursorShape()
                if mouse_tz == cursor_code:
                    self.dm_instance.LeftClick()
                    return True
                if angle % 20 == 0:
                    width_radius += step
                    height_radius += step
                sleep(0.001)
            sleep(0.001)
        return False

    def 方形渐开找鼠标(
        self,
        start_x: int,
        start_y: int,
        cursor_code: int,
        step: int = 10,
        max_circles: int = 6,
    ) -> bool:
        """通过方形螺旋轨迹查找并点击特定光标

        以方形螺旋轨迹移动鼠标，从中心向外呈方形扩展，
        适合在规则网格布局中查找目标。

        轨迹特点：
            - 方形螺旋，按矩形轨迹移动
            - 移动顺序: 右 → 上 → 左 → 下
            - 每圈边长逐渐增加
            - 适合网格状布局

        Args:
            start_x (int): 起始 X 坐标（像素）
            start_y (int): 起始 Y 坐标（像素）
            cursor_code (int): 目标光标的特征码
            step (int, optional): 移动步长（像素）
                - 默认: 10
                - 每次移动的距离
            max_circles (int, optional): 最大螺旋圈数
                - 默认: 6
                - 控制搜索范围

        Returns:
            bool: 查找结果
                - True: 找到并已点击
                - False: 未找到

        Examples:
            使用方形螺旋查找:
            >>> found = dm.方形渐开找鼠标(500, 500, 65563)

            自定义步长和圈数:
            >>> dm.方形渐开找鼠标(start_x=600, start_y=400, cursor_code=65563, step=15, max_circles=10)

            小步长精确查找:
            >>> dm.方形渐开找鼠标(400, 300, 65563, step=5, max_circles=8)

        Note:
            - 轨迹呈方形，适合网格布局
            - 每条边移动多次，每次移动 step 像素
            - 找到目标后立即点击并返回
            - 每圈结束后延迟 1ms
            - 移动顺序固定：右→上→左→下

        See Also:
            - 圆形渐开找鼠标: 圆形螺旋轨迹
            - 椭圆渐开找鼠标: 椭圆螺旋轨迹
            - 散点渐开找鼠标: 散点螺旋轨迹
        """
        m = 0
        xzb = start_x
        yzb = start_y
        for _ in range(max_circles):
            # 向右移动
            for _ in range(m):
                xzb += step
                self.dm_instance.MoveTo(xzb, yzb)
                mouse_tz = self.dm_instance.GetCursorShape()
                if mouse_tz == cursor_code:
                    self.dm_instance.LeftClick()
                    return True
            # 向上移动
            for _ in range(m + 6):
                yzb -= step
                self.dm_instance.MoveTo(xzb, yzb)
                mouse_tz = self.dm_instance.GetCursorShape()
                if mouse_tz == cursor_code:
                    self.dm_instance.LeftClick()
                    return True
            m += 1
            # 向左移动
            for _ in range(m):
                xzb -= step
                self.dm_instance.MoveTo(xzb, yzb)
                mouse_tz = self.dm_instance.GetCursorShape()
                if mouse_tz == cursor_code:
                    self.dm_instance.LeftClick()
                    return True
            # 向下移动
            for _ in range(m + 6):
                yzb += step
                self.dm_instance.MoveTo(xzb, yzb)
                mouse_tz = self.dm_instance.GetCursorShape()
                if mouse_tz == cursor_code:
                    self.dm_instance.LeftClick()
                    return True
            m += 1
            sleep(0.001)
        return False
