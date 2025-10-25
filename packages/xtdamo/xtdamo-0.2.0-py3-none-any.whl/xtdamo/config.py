# !/usr/bin/env python3
"""
==============================================================
Description  : 基础配置管理模块 - 提供默认配置和错误处理
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-18 22:00:00
Github       : https://github.com/sandorn/xtdamo

本模块提供以下核心功能:
- 默认配置管理 (延迟、相似度、超时等)
- 错误代码映射与处理
- 窗口绑定模式配置
- 配置验证与获取

主要特性:
- 统一的配置管理
- 详细的错误信息映射
- 灵活的绑定模式配置
- 配置验证机制
- 易于扩展的配置结构
==============================================================
"""

from __future__ import annotations

from typing import Any


class Config:
    """基础配置管理类 - 提供默认配置和错误处理"""

    # 默认延迟配置
    DEFAULT_MOUSE_DELAY: float = 0.05
    DEFAULT_KEYBOARD_DELAY: float = 0.05

    # 默认相似度配置
    DEFAULT_SIMILARITY: float = 0.9

    # 默认超时配置
    DEFAULT_TIMEOUT: float = 5.0

    # 大漠插件错误代码映射
    ERROR_CODES: dict[int, str] = {
        -1: '无法连接网络',
        -2: '进程没有以管理员方式运行，win7 win8 vista 2008 建议关闭uac)',
        0: '失败 (未知错误)',
        1: '成功',
        2: '余额不足',
        3: '绑定了本机器,但是账户余额不足50元.',
        4: '注册码错误',
        5: '你的机器或者IP在黑名单列表中或者不在白名单列表中.',
        6: '非法使用插件.',
        7: '你的帐号因为非法使用被封禁.',
        8: 'ver_info不在你设置的附加白名单中.',
        77: '机器码或者IP因为非法使用,而被封禁.',
        -8: '版本附加信息长度超过了20',
        -9: '版本附加信息里包含了非法字母.',
    }

    # 窗口绑定模式配置
    BIND_MODES = {
        'display': ['normal', 'gdi', 'gdi2', 'dx', 'dx2'],
        'mouse': ['normal', 'windows', 'windows2', 'windows3', 'dx', 'dx2'],
        'keypad': ['normal', 'windows', 'dx'],
        'mode': [0, 1, 2, 3, 4, 5, 6, 7, 101, 103],
    }

    # 默认绑定配置
    DEFAULT_BIND_CONFIG = {
        'display': 'gdi',
        'mouse': 'windows3',
        'keypad': 'windows',
        'mode': 101,
    }

    @classmethod
    def get_error_message(cls, error_code: int) -> str:
        """获取错误代码对应的错误信息

        Args:
            error_code: 错误代码

        Returns:
            str: 错误信息
        """
        return cls.ERROR_CODES.get(error_code, f'未知错误代码: {error_code}')

    @classmethod
    def get_bind_config(cls, **kwargs) -> dict[str, Any]:
        """获取窗口绑定配置

        只有非 None 的参数才会覆盖默认配置，并且会验证参数的有效性。

        Args:
            **kwargs: 自定义配置参数
                - display: 显示模式 (可选值见 BIND_MODES['display'])
                - mouse: 鼠标模式 (可选值见 BIND_MODES['mouse'])
                - keypad: 键盘模式 (可选值见 BIND_MODES['keypad'])
                - mode: 绑定模式 (可选值见 BIND_MODES['mode'])

        Returns:
            Dict[str, Any]: 绑定配置字典

        Raises:
            ValueError: 当提供的参数值不在有效范围内时

        Examples:
            使用默认配置:
            >>> config = Config.get_bind_config()
            >>> print(config)
            {'display': 'gdi', 'mouse': 'windows3', 'keypad': 'windows', 'mode': 101}

            部分自定义（其他使用默认）:
            >>> config = Config.get_bind_config(display='dx2')
            >>> print(config)
            {'display': 'dx2', 'mouse': 'windows3', 'keypad': 'windows', 'mode': 101}

            传入 None 不会覆盖默认值:
            >>> config = Config.get_bind_config(display=None, mouse='dx')
            >>> print(config)
            {'display': 'gdi', 'mouse': 'dx', 'keypad': 'windows', 'mode': 101}
        """
        config = cls.DEFAULT_BIND_CONFIG.copy()

        # 只更新非 None 的参数，并验证其有效性
        for key, value in kwargs.items():
            if value is not None:
                # 验证参数名是否有效
                if key not in cls.BIND_MODES:
                    raise ValueError(f'无效的配置参数: {key}. 有效参数: {list(cls.BIND_MODES.keys())}')

                # 验证参数值是否在有效范围内
                if not cls.validate_bind_mode(key, value):
                    raise ValueError(f'无效的 {key} 值: {value}. 有效值: {cls.BIND_MODES[key]}')

                config[key] = value

        return config

    @classmethod
    def validate_bind_mode(cls, mode_type: str, mode_value: str | int) -> bool:
        """验证绑定模式是否有效

        Args:
            mode_type (str): 模式类型 ("display", "mouse", "keypad", "mode")
            mode_value (str | int): 模式值
                - 对于 display/mouse/keypad: 字符串值
                - 对于 mode: 整数值

        Returns:
            bool: 是否有效

        Examples:
            验证显示模式:
            >>> Config.validate_bind_mode('display', 'gdi')
            True
            >>> Config.validate_bind_mode('display', 'invalid')
            False

            验证绑定模式:
            >>> Config.validate_bind_mode('mode', 101)
            True
            >>> Config.validate_bind_mode('mode', 999)
            False
        """
        if mode_type not in cls.BIND_MODES:
            return False

        return mode_value in cls.BIND_MODES[mode_type]
