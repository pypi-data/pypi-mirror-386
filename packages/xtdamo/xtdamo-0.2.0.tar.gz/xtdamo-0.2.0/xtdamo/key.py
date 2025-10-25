# !/usr/bin/env python3
"""键盘操作模块 - 提供完整的键盘控制功能

本模块是 xtdamo 键盘操作的核心实现，封装了大漠插件的所有键盘相关API，
提供统一、标准的键盘操作接口。

核心功能:
    - 单键操作：KeyPress, KeyDown, KeyUp
    - 字符输入：KeyPressChar, KeyPressStr
    - 按键检测：GetKeyState, WaitKey
    - 延迟控制：SetKeypadDelay
    - 组合键支持：Ctrl+C, Alt+Tab 等

架构说明:
    Key 类直接映射大漠插件的键盘API，所有方法名保持与大漠插件一致（大写开头），
    确保API的标准化和一致性。移除了重复的辅助方法，只保留标准API。

使用示例:
    基本按键:
        >>> from xtdamo import DmExcute
        >>> dm = DmExcute()
        >>> dm.Key.KeyPress(13)  # 按回车键（VK_RETURN）
        >>> dm.Key.KeyPressStr('Hello World')  # 输入文本

    组合键:
        >>> dm.Key.KeyDown(17)  # 按下Ctrl（VK_CONTROL）
        >>> dm.Key.KeyPress(67)  # 按C键
        >>> dm.Key.KeyUp(17)  # 释放Ctrl

    等待按键:
        >>> dm.Key.WaitKey(27, 5000)  # 等待ESC键，超时5秒

注意事项:
    - 所有虚拟键码参考 Windows VK_* 常量
    - 推荐使用 time_utils.VirtualKeys 获取常用键码
    - 窗口绑定后键盘操作作用于绑定窗口
    - 某些模式下的后台输入需要管理员权限

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
    - Windows虚拟键码表
    - xtdamo项目文档
==============================================================
"""

from __future__ import annotations

from typing import Any

from .config import Config


class Key:
    """键盘操作控制器

    提供完整的键盘操作功能，包括按键模拟、组合键、文本输入等。
    所有方法都是对大漠插件原生API的直接映射。

    Attributes:
        dm_instance: 大漠插件实例

    Examples:
        基本使用:
        >>> key = Key(dm_instance)
        >>> key.KeyPress(VirtualKeys.ENTER)  # 按回车键
        >>> key.KeyPressStr('Hello World')  # 输入文字

        组合键:
        >>> key.KeyDown(VirtualKeys.CTRL)  # 按下Ctrl
        >>> key.KeyPress(ord('C'))  # 按C键
        >>> key.KeyUp(VirtualKeys.CTRL)  # 释放Ctrl

    Note:
        - 直接使用大写开头的标准方法（如 KeyPress）
        - 使用 VirtualKeys 类获取虚拟键码常量
        - 所有方法都映射到大漠插件的原生API
    """

    def __init__(self, dm_instance: Any) -> None:
        """初始化键盘操作控制器

        Args:
            dm_instance: 大漠插件实例

        Raises:
            ValueError: 当 dm_instance 为 None 时抛出
        """
        if not dm_instance:
            raise ValueError('dmobject cannot be None')
        self.dm_instance = dm_instance

    # ==================== 标准键盘API方法 ====================

    def GetKeyState(self, vk_code: int) -> int:
        """获取按键状态

        检测指定虚拟键码的按键是否被按下。

        Args:
            vk_code (int): 虚拟键码（Virtual Key Code）
                - 可以使用 VirtualKeys 常量
                - 如 VirtualKeys.ENTER, VirtualKeys.ESC 等

        Returns:
            int: 按键状态
                - 0: 按键未按下
                - 1: 按键已按下

        Examples:
            检测回车键状态:
            >>> if dm.Key.GetKeyState(VirtualKeys.ENTER):
            ...     print('回车键被按下')

            检测Ctrl键状态:
            >>> from xtdamo.time_utils import VirtualKeys
            >>> if dm.Key.GetKeyState(VirtualKeys.CTRL):
            ...     print('Ctrl键被按下')

        Note:
            - 实时检测，不会阻塞
            - 可用于检测组合键状态
            - 虚拟键码定义在 VirtualKeys 类中

        See Also:
            - WaitKey: 等待按键按下
            - KeyPress: 模拟按键
        """
        return self.dm_instance.GetKeyState(vk_code)

    def SetKeypadDelay(
        self,
        type: str = 'dx',
        delay: float = Config.DEFAULT_KEYBOARD_DELAY,
    ) -> int:
        """设置键盘按键延迟

        配置键盘操作的延迟时间，影响所有键盘相关方法。

        Args:
            type (str, optional): 键盘模式
                - 'normal': 正常模式
                - 'windows': Windows消息模式
                - 'dx': DirectX模式，默认值
            delay (int, optional): 延迟时间（毫秒）
                - 默认: Config.DEFAULT_KEYBOARD_DELAY
                - 范围: 通常 10-1000ms

        Returns:
            int: 设置结果
                - 1: 设置成功
                - 0: 设置失败

        Examples:
            设置较短延迟（快速输入）:
            >>> dm.Key.SetKeypadDelay('dx', 10)

            设置较长延迟（模拟人工输入）:
            >>> dm.Key.SetKeypadDelay('windows', 100)

        Note:
            - 延迟时间影响按键操作的速度
            - 过短的延迟可能导致某些程序无法正确识别
            - 建议根据目标程序调整合适的延迟

        See Also:
            - KeyPressStr: 使用延迟输入字符串
            - Config.DEFAULT_KEYBOARD_DELAY: 默认延迟配置
        """
        return self.dm_instance.SetKeypadDelay(type, delay)

    def WaitKey(self, vk_code: int, timeout: int = 0) -> int:
        """等待按键按下

        等待指定的按键被按下，支持超时设置。

        Args:
            vk_code (int): 虚拟键码
                - 使用 VirtualKeys 常量
            timeout (int, optional): 超时时间（毫秒）
                - 0: 无限等待，默认值
                - >0: 等待指定毫秒数

        Returns:
            int: 等待结果
                - 1: 按键被按下
                - 0: 超时未检测到按键

        Examples:
            无限等待回车键:
            >>> dm.Key.WaitKey(VirtualKeys.ENTER)
            >>> print('用户按下了回车键')

            等待ESC键，超时5秒:
            >>> if dm.Key.WaitKey(VirtualKeys.ESC, 5000):
            ...     print('用户按下了ESC')
            ... else:
            ...     print('超时，用户未按键')

        Note:
            - 会阻塞执行直到按键或超时
            - 常用于需要用户确认的场景
            - 超时为0时会一直等待

        See Also:
            - GetKeyState: 非阻塞的按键状态检测
        """
        return self.dm_instance.WaitKey(vk_code, timeout)

    def KeyDown(self, vk_code: int) -> int:
        """按下按键（不释放）

        模拟按键按下动作，但不释放，需要配合 KeyUp 使用。

        Args:
            vk_code (int): 虚拟键码

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            模拟组合键 Ctrl+C:
            >>> dm.Key.KeyDown(VirtualKeys.CTRL)
            >>> dm.Key.KeyPress(ord('C'))
            >>> dm.Key.KeyUp(VirtualKeys.CTRL)

            长按某个键:
            >>> dm.Key.KeyDown(VirtualKeys.SPACE)
            >>> sleep(2)  # 按住2秒
            >>> dm.Key.KeyUp(VirtualKeys.SPACE)

        Note:
            - 必须配合 KeyUp 使用，否则按键一直处于按下状态
            - 常用于模拟组合键
            - 建议使用 down_up 方法替代手动调用

        See Also:
            - KeyUp: 释放按键
            - KeyPress: 完整的按下并释放
            - down_up: 封装的按下释放方法
        """
        return self.dm_instance.KeyDown(vk_code)

    def KeyDownChar(self, key_str: str) -> int:
        """按下字符键（不释放）

        按下指定字符对应的按键，但不释放。

        Args:
            key_str (str): 字符
                - 单个字符，如 'a', 'B', '1'

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            按下字符'a':
            >>> dm.Key.KeyDownChar('a')
            >>> sleep(1)
            >>> dm.Key.KeyUpChar('a')

        Note:
            - 必须配合 KeyUpChar 使用
            - 自动处理字符到键码的转换

        See Also:
            - KeyUpChar: 释放字符键
            - KeyPressChar: 完整的字符按键
        """
        return self.dm_instance.KeyDownChar(key_str)

    def KeyPress(self, vk_code: int) -> int:
        """按下并释放按键

        模拟完整的按键操作（按下后立即释放）。

        Args:
            vk_code (int): 虚拟键码

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            按回车键:
            >>> dm.Key.KeyPress(VirtualKeys.ENTER)

            按ESC键:
            >>> dm.Key.KeyPress(VirtualKeys.ESC)

        Note:
            - 这是最常用的按键方法
            - 自动完成按下和释放
            - 有默认的按键延迟

        See Also:
            - KeyDown: 只按下不释放
            - KeyUp: 只释放
            - press: 封装方法
        """
        return self.dm_instance.KeyPress(vk_code)

    def KeyPressChar(self, key_str: str) -> int:
        """按下并释放字符键

        模拟完整的字符按键操作。

        Args:
            key_str (str): 字符

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            按字符'a':
            >>> dm.Key.KeyPressChar('a')

            按数字'5':
            >>> dm.Key.KeyPressChar('5')

        Note:
            - 适用于单个字符输入
            - 自动处理字符转换
            - 输入多个字符请使用 KeyPressStr

        See Also:
            - KeyPressStr: 输入字符串
        """
        return self.dm_instance.KeyPressChar(key_str)

    def KeyPressStr(
        self,
        key_str: str,
        delay: float = Config.DEFAULT_KEYBOARD_DELAY,
    ) -> int:
        """输入字符串

        逐字符输入字符串，支持自定义延迟。

        Args:
            key_str (str): 要输入的字符串
            delay (float, optional): 字符间延迟（毫秒）
                - 默认: Config.DEFAULT_KEYBOARD_DELAY

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            输入文本:
            >>> dm.Key.KeyPressStr('Hello World')

            快速输入:
            >>> dm.Key.KeyPressStr('快速输入', delay=10)

            模拟人工输入:
            >>> dm.Key.KeyPressStr('慢速输入', delay=100)

        Note:
            - 适用于文本框、输入框等
            - delay 影响输入速度
            - 较长的延迟更像人工输入

        See Also:
            - KeyPressChar: 输入单个字符
            - SetKeypadDelay: 设置全局延迟
        """
        return self.dm_instance.KeyPressStr(key_str, delay)

    def KeyUp(self, vk_code: int) -> int:
        """释放按键

        释放之前按下的按键。

        Args:
            vk_code (int): 虚拟键码

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            配合 KeyDown 使用:
            >>> dm.Key.KeyDown(VirtualKeys.SHIFT)
            >>> dm.Key.KeyPress(ord('A'))  # 输入大写A
            >>> dm.Key.KeyUp(VirtualKeys.SHIFT)

        Note:
            - 必须与 KeyDown 配对使用
            - 释放的按键必须是之前按下的

        See Also:
            - KeyDown: 按下按键
            - up: 封装方法
        """
        return self.dm_instance.KeyUp(vk_code)

    def KeyUpChar(self, key_str: str) -> int:
        """释放字符键

        释放之前按下的字符键。

        Args:
            key_str (str): 字符

        Returns:
            int: 操作结果
                - 1: 成功
                - 0: 失败

        Examples:
            >>> dm.Key.KeyDownChar('a')
            >>> sleep(1)
            >>> dm.Key.KeyUpChar('a')

        Note:
            - 必须与 KeyDownChar 配对使用

        See Also:
            - KeyDownChar: 按下字符键
        """
        return self.dm_instance.KeyUpChar(key_str)
