# !/usr/bin/env python
"""
==============================================================
Description  : 大漠插件主入口模块 - 统一封装和管理所有功能组件
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2025-05-21 16:26:08
LastEditTime : 2025-10-25 22:00:00
FilePath     : xtdamo/damo.py
Github       : https://github.com/sandorn/xtdamo

本模块是 xtdamo 的核心入口，提供以下功能:
- 统一管理所有功能组件（CoreEngine, ApiProxy, Key, Mouse）
- 自动注册和注销大漠插件
- 智能方法路由和动态属性查找
- 分层架构的统一接口

主要类:
- DmExcute: 主入口类，管理所有组件的生命周期和方法路由

辅助函数:
- conv_to_rgb: 十六进制颜色转 RGB

架构说明:
    DmExcute (主入口)
        ├── CoreEngine (核心引擎) - 底层大漠方法封装
        ├── ApiProxy (高级接口) - 友好的中文 API
        ├── Key (键盘模块) - 键盘操作封装
        └── Mouse (鼠标模块) - 鼠标操作封装

使用示例:
    from xtdamo import DmExcute

    # 创建实例（自动注册插件）
    dm = DmExcute()

    # 使用高级接口
    hwnd = dm.FindWindow("", "窗口标题")
    dm.绑定窗口(hwnd)

    # 使用核心方法
    dm.MoveTo(100, 200)
    dm.LeftClick()

    # 程序结束时自动注销
==============================================================
"""

from __future__ import annotations

from typing import Any

from .apiproxy import ApiProxy
from .config import Config
from .coreengine import CoreEngine
from .key import Key
from .mouse import Mouse
from .regsvr import DmRegister
from .secure_config import dm_credentials


class DmExcute:
    """大漠插件主入口类 - 统一管理和路由所有功能

    DmExcute 是 xtdamo 的核心入口类，负责：
    1. 自动注册和注销大漠插件
    2. 创建和管理所有功能组件（CoreEngine, ApiProxy, Key, Mouse）
    3. 提供智能的方法路由机制（自动查找最合适的组件方法）
    4. 实现分层架构的统一访问接口

    Attributes:
        RegDM (DmRegister): 大漠插件注册器
        dm_instance: 大漠插件原生实例
        CoreEngine (CoreEngine): 核心引擎，提供底层大漠方法封装
        ApiProxy (ApiProxy): 高级接口，提供友好的中文 API
        Key (Key): 键盘模块，封装键盘操作
        Mouse (Mouse): 鼠标模块，封装鼠标操作

    方法查找顺序:
        1. 先在各个组件中查找（Key, Mouse, ApiProxy, CoreEngine）
        2. 如果找不到，再查找大漠原生方法
        3. 都找不到则抛出 AttributeError

    Examples:
        基本使用:
        >>> from xtdamo import DmExcute
        >>> dm = DmExcute()
        >>> print(dm.ver())  # 获取版本
        >>> print(dm.GetID())  # 获取ID

        窗口操作:
        >>> hwnd = dm.FindWindow('', '记事本')
        >>> if dm.绑定窗口(hwnd):  # 使用 ApiProxy 的方法
        ...     print('绑定成功')

        鼠标和键盘操作:
        >>> dm.MoveTo(100, 200)  # 自动路由到合适的组件
        >>> dm.LeftClick()
        >>> dm.KeyPressStr('Hello World')

        使用特定组件:
        >>> result = dm.CoreEngine.BindWindow(hwnd)  # 直接使用核心引擎
        >>> dm.Mouse.safe_click(100, 200)  # 直接使用鼠标模块

        指定大漠插件路径:
        >>> dm = DmExcute(dm_dirpath='C:/dm/dm.dll')

    Note:
        - 创建实例时会自动注册大漠插件
        - 对象销毁时会自动注销插件（__del__）
        - 推荐在测试中复用同一实例，避免频繁注册/注销
        - 如果注册失败会抛出 AssertionError

    Raises:
        AssertionError: 当大漠插件注册失败、组件初始化失败或授权失败时

    See Also:
        - CoreEngine: 底层核心方法封装
        - ApiProxy: 高级接口和中文 API
        - Key: 键盘操作模块
        - Mouse: 鼠标操作模块
    """

    def __init__(self, dm_dirpath: str | None = None):
        """初始化大漠插件主入口

        创建并初始化所有功能组件，自动注册大漠插件并进行授权验证。

        初始化流程:
            1. 注册大漠插件 (DmRegister)
            2. 创建核心引擎 (CoreEngine)
            3. 创建功能模块 (Key, Mouse, ApiProxy)
            4. 设置组件路由映射
            5. 验证所有组件初始化成功
            6. 获取认证信息并授权

        Args:
            dm_dirpath (str | None, optional): 大漠插件 dll 路径
                - None: 自动搜索系统中的 dm.dll（默认）
                - str: 指定 dm.dll 的完整路径

        Raises:
            AssertionError: 当以下情况发生时抛出:
                - 大漠插件实例初始化失败
                - 任何组件（Key, Mouse, CoreEngine, ApiProxy）初始化失败
                - 插件授权失败

        Examples:
            使用默认路径:
            >>> dm = DmExcute()

            指定插件路径:
            >>> dm = DmExcute(dm_dirpath='D:/tools/dm.dll')

            错误处理:
            >>> try:
            ...     dm = DmExcute()
            ... except AssertionError as e:
            ...     print(f'初始化失败: {e}')

        Note:
            - 插件注册需要有效的注册码和版本信息
            - 注册信息从 secure_config.py 的 dm_credentials 获取
            - 建议在应用中只创建一个实例并复用
            - 授权失败时会显示详细的错误信息
        """
        # 1. 注册大漠插件
        self.RegDM = DmRegister(dm_dirpath)
        self.dm_instance = self.RegDM.dm_instance

        # 2. 创建核心引擎（底层）
        self.CoreEngine = CoreEngine(self.dm_instance)

        # 3. 创建功能模块，ApiProxy 接收 CoreEngine 实例
        self.Key = Key(self.dm_instance)
        self.Mouse = Mouse(self.dm_instance)
        self.ApiProxy = ApiProxy(self.dm_instance, self.CoreEngine)

        # 4. 设置动态方法路由映射
        self._components = {
            'Key': self.Key,
            'Mouse': self.Mouse,
            'ApiProxy': self.ApiProxy,
            'CoreEngine': self.CoreEngine,
        }

        # 5. 验证所有组件初始化成功
        assert self.dm_instance is not None, '大漠插件实例初始化失败'
        assert all([self.Key, self.Mouse, self.CoreEngine, self.ApiProxy]), '模块初始化失败'

        # 6. 获取认证信息并授权
        reg_code, ver_info = dm_credentials.get_dm_credentials()
        tmp_ret = self.dm_instance.Reg(reg_code, ver_info)
        assert tmp_ret == 1, f'授权失败,错误代码：{tmp_ret} | 授权问题： {Config.get_error_message(tmp_ret)}'

    def __repr__(self) -> str:
        """返回对象的字符串表示

        提供有用的调试信息，包括大漠插件版本和 ID。

        Returns:
            str: 格式化的字符串，包含版本号和 ID
                成功: "版本：7.2129 , ID：xxxxx"
                失败: "获取版本和ID时出错: 错误信息"

        Examples:
            >>> dm = DmExcute()
            >>> print(dm)
            版本：7.2129 , ID：12345

            >>> repr(dm)
            '版本：7.2129 , ID：12345'
        """
        try:
            return f'版本：{self.ver()} , ID：{self.GetID()}'
        except Exception as e:
            return f'获取版本和ID时出错: {e}'

    def __getattr__(self, key: str) -> Any:
        """智能方法路由 - 自动查找并返回合适的方法或属性

        实现动态属性查找机制，按以下顺序查找方法：
        1. Key 模块 - 键盘相关方法
        2. Mouse 模块 - 鼠标相关方法
        3. ApiProxy 模块 - 高级接口和中文 API
        4. CoreEngine 模块 - 核心底层方法
        5. dm_instance - 大漠插件原生方法

        这使得用户可以直接通过 dm.方法名() 调用任何组件的方法，
        而不需要知道该方法属于哪个组件。

        Args:
            key (str): 要查找的属性或方法名

        Returns:
            Any: 找到的方法或属性

        Raises:
            AttributeError: 当所有组件都找不到该属性时

        Examples:
            自动路由到 ApiProxy:
            >>> dm = DmExcute()
            >>> hwnd = dm.FindWindow('', '记事本')
            >>> dm.绑定窗口(hwnd)  # 自动路由到 ApiProxy.绑定窗口

            自动路由到 Mouse:
            >>> dm.safe_click(100, 200)  # 自动路由到 Mouse.safe_click

            自动路由到 Key:
            >>> dm.KeyPressStr('Hello')  # 自动路由到 Key.KeyPressStr

            自动路由到 CoreEngine:
            >>> dm.MoveTo(100, 200)  # 自动路由到 CoreEngine.MoveTo

            自动路由到原生方法:
            >>> dm.ver()  # 自动路由到 dm_instance.ver

        Note:
            - 如果多个组件有同名方法，按查找顺序返回第一个找到的
            - 这是 Python 的魔术方法，会在访问不存在的属性时自动调用
            - 查找失败时抛出标准的 AttributeError，便于调试
        """
        # 按优先级在各组件中查找
        for _, component in self._components.items():
            if hasattr(component, key):
                return getattr(component, key)

        # 最后尝试大漠原生方法，确保dm_instance不为None
        if self.dm_instance is not None:
            try:
                return getattr(self.dm_instance, key)
            except AttributeError:
                pass

        # 所有地方都找不到，抛出标准错误
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    def __del__(self):
        """对象销毁时自动取消大漠插件注册

        Python 的析构函数，在对象被垃圾回收时自动调用。
        确保大漠插件正确注销，释放系统资源。

        Note:
            - 这是自动调用的，通常不需要手动调用
            - 在程序正常退出时会自动触发
            - 在异常退出时也会尝试调用
            - 建议不要在应用中频繁创建销毁实例

        Examples:
            正常退出（自动调用）:
            >>> dm = DmExcute()
            >>> # ... 使用 dm ...
            >>> # 程序结束时自动调用 __del__

            手动删除（触发 __del__）:
            >>> dm = DmExcute()
            >>> del dm  # 立即触发注销

            作用域结束（自动调用）:
            >>> def test():
            ...     dm = DmExcute()
            ...     # 函数结束时自动注销
            >>> test()
        """
        self.RegDM.unregister()


def conv_to_rgb(color: str) -> list[int]:
    """将十六进制颜色字符串转换为 RGB 列表

    将 6 位十六进制颜色代码（如 "RRGGBB"）转换为 [R, G, B] 整数列表。
    常用于颜色处理和图像识别相关功能。

    Args:
        color (str): 6 位十六进制颜色字符串
            - 格式: "RRGGBB"
            - 每个分量范围: 00-FF (0-255)
            - 不需要 # 前缀

    Returns:
        list[int]: RGB 值列表 [R, G, B]
            - 每个值范围: 0-255
            - 顺序: [红色, 绿色, 蓝色]

    Examples:
        纯红色:
        >>> conv_to_rgb('FF0000')
        [255, 0, 0]

        纯绿色:
        >>> conv_to_rgb('00FF00')
        [0, 255, 0]

        纯蓝色:
        >>> conv_to_rgb('0000FF')
        [0, 0, 255]

        白色:
        >>> conv_to_rgb('FFFFFF')
        [255, 255, 255]

        黑色:
        >>> conv_to_rgb('000000')
        [0, 0, 0]

        灰色:
        >>> conv_to_rgb('808080')
        [128, 128, 128]

        自定义颜色:
        >>> conv_to_rgb('3A7BD5')
        [58, 123, 213]

    Note:
        - 输入必须是 6 位十六进制字符串
        - 大小写不敏感（内部转换为整数）
        - 不验证输入格式，确保调用时格式正确

    See Also:
        - 大漠插件颜色相关方法通常使用十六进制格式
        - 可配合 FindColor、CmpColor 等方法使用
    """
    rgb_str = [color[:2], color[2:4], color[4:6]]
    return [int(i, 16) for i in rgb_str]
