# !/usr/bin/env python
"""xtdamo - 基于大漠插件的Python自动化封装库

本库提供对大漠插件的完整封装，支持窗口管理、鼠标控制、键盘模拟、
图像识别、文本查找等自动化操作。

核心模块:
    - DmExcute: 主入口类，统一的调用接口
    - ApiProxy: 高级接口层，中文友好API
    - CoreEngine: 核心引擎层，底层功能封装
    - Key: 键盘操作模块
    - Mouse: 鼠标操作模块

架构特性:
    - 分层架构设计，职责清晰
    - 智能方法路由，自动选择最佳实现
    - 完整的参数验证和错误处理
    - 向后兼容，支持旧版本代码

版本信息:
    Version      : 0.2.0
    Author       : sandorn <sandorn@live.cn>
    Github       : https://github.com/sandorn/xtdamo
    LastEditTime : 2025-10-25
    License      : MIT

使用示例:
    >>> from xtdamo import DmExcute
    >>> dm = DmExcute()
    >>> print(dm.ver())
    >>> hwnd = dm.FindWindow('', '记事本')
    >>> dm.绑定窗口(hwnd)
==============================================================
"""

from __future__ import annotations

from .config import Config
from .damo import DmExcute
from .dependencies import CRYPTO_AVAILABLE, WIN32_AVAILABLE, WIN32GUI_AVAILABLE, DependencyChecker, check_dependency, get_available_dependencies, get_missing_dependencies
from .enum_wind import get_windows_by_criteria
from .secure_config import DmCredentials, dm_credentials

__version__ = '0.2.0'
__author__ = 'sandorn'
__email__ = 'sandorn@live.cn'
__license__ = 'MIT'
__url__ = 'https://github.com/sandorn/xtdamo'

__all__ = (
    'CRYPTO_AVAILABLE',
    'WIN32GUI_AVAILABLE',
    'WIN32_AVAILABLE',
    'Config',
    'DependencyChecker',
    'DmCredentials',
    'DmExcute',
    '__author__',
    '__email__',
    '__license__',
    '__url__',
    '__version__',
    'check_dependency',
    'dm_credentials',
    'get_available_dependencies',
    'get_missing_dependencies',
    'get_windows_by_criteria',
)
