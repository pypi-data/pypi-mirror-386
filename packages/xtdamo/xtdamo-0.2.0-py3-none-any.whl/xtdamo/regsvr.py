# !/usr/bin/env python3
"""
==============================================================
Description  : 大漠插件注册管理模块 - 提供COM组件注册、卸载、状态检测等功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-18 22:00:00
Github       : https://github.com/sandorn/xtdamo

本模块提供以下核心功能:
- COM组件注册 (regsvr32注册)
- COM组件卸载 (regsvr32卸载)
- 注册状态检测
- 管理员权限处理
- COM对象创建与管理

主要特性:
- 自动检测管理员权限
- 智能注册失败处理
- 支持多种注册方式
- 异常处理和错误恢复
- 注册状态实时监控
==============================================================
"""

from __future__ import annotations

import ctypes
import os
from typing import Any

from win32com.client import Dispatch
from xtlog import mylog


def _create_dm_object():
    """创建大漠插件COM对象

    尝试通过 win32com 创建大漠插件的 COM 对象实例。
    这是大漠插件正常工作的前提条件。

    Returns:
        Any | None: 大漠插件实例对象
            - 成功: 返回 dm.dmsoft COM 对象
            - 失败: 返回 None

    Examples:
        创建对象:
        >>> dm = _create_dm_object()
        >>> if dm:
        ...     print(dm.ver())  # 获取版本号

        处理失败:
        >>> dm = _create_dm_object()
        >>> if dm is None:
        ...     print('需要先注册大漠插件')

    Note:
        - 需要大漠插件已通过 regsvr32 注册到系统
        - 创建失败通常意味着插件未注册或注册损坏
        - 使用 win32com.client.Dispatch 创建 COM 对象
        - 失败时会记录详细的错误日志

    See Also:
        - DmRegister: 大漠插件注册管理类
        - _runas_admin: 以管理员权限执行命令
    """
    try:
        dm_instance = Dispatch('dm.dmsoft')
        mylog.success('创建大漠COM对象[dm.dmsoft]成功!')
        return dm_instance
    except Exception as e:
        mylog.error(f'--- 创建大漠COM对象[dm.dmsoft]失败 --- 错误: {e}')
        return None


def _runas_admin(cmd, ishide=False, waitsed=10):
    """以管理员权限运行命令

    使用 Windows ShellExecuteEx API 以管理员权限执行指定命令，
    并等待命令执行完成。支持隐藏命令窗口和自定义超时时间。

    Args:
        cmd (str): 要执行的命令字符串
            - 完整的命令行，如 "regsvr32.exe /s dm.dll"
        ishide (bool, optional): 是否隐藏命令窗口
            - True: 隐藏窗口 (nShow=1)
            - False: 显示窗口 (nShow=0)，默认值
        waitsed (int, optional): 等待命令完成的超时时间（秒）
            - 默认: 10 秒
            - 超时后会继续执行，不会阻止返回

    Returns:
        bool: 命令执行状态
            - True: 命令成功启动并完成
            - False: 命令启动失败或无法获取进程句柄

    Examples:
        注册 DLL（隐藏窗口）:
        >>> success = _runas_admin('regsvr32.exe /s dm.dll', ishide=True)
        >>> if success:
        ...     print('注册命令执行成功')

        执行命令（显示窗口，等待 5 秒）:
        >>> _runas_admin('reg delete HKEY...', ishide=False, waitsed=5)

        批处理命令:
        >>> _runas_admin('cmd /c "echo Test && pause"')

    Note:
        - 会弹出 UAC 提示框，需要用户确认管理员权限
        - 使用 ShellExecuteEx 代替 ShellExecuteW 以支持等待进程完成
        - SEE_MASK_NOCLOSEPROCESS (0x00000040) 保持进程句柄打开
        - 超时后会自动关闭进程句柄，防止资源泄漏
        - 如果用户拒绝 UAC 提示，命令不会执行

    See Also:
        - DmRegister.execute: 使用此函数进行注册
        - DmRegister.unregister: 使用此函数进行卸载
    """

    # ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {cmd}", None, 1)

    # 使用ShellExecuteEx 替代 ShellExecuteW ，以便等待进程完成
    # 结构体大小必须与ctypes.sizeof(SHELLEXECUTEINFO)一致
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_ulong),
            ('fMask', ctypes.c_ulong),
            ('hwnd', ctypes.c_void_p),
            ('lpVerb', ctypes.c_wchar_p),
            ('lpFile', ctypes.c_wchar_p),
            ('lpParameters', ctypes.c_wchar_p),
            ('lpDirectory', ctypes.c_wchar_p),
            ('nShow', ctypes.c_int),
            ('hInstApp', ctypes.c_void_p),
            ('lpIDList', ctypes.c_void_p),
            ('lpClass', ctypes.c_wchar_p),
            ('hKeyClass', ctypes.c_void_p),
            ('dwHotKey', ctypes.c_ulong),
            ('hIcon', ctypes.c_void_p),
            ('hProcess', ctypes.c_void_p),
        ]

    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    sei.hwnd = None
    sei.lpVerb = 'runas'
    sei.lpFile = 'cmd.exe'
    sei.lpParameters = f'/C {cmd}'
    sei.lpDirectory = None
    sei.nShow = 1 if ishide else 0  # SW_HIDE

    success = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))

    if success and sei.hProcess:
        # 等待进程完成，设置超时为10秒
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 1000 * waitsed)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)  # 关闭进程句柄
        return True
    return False


class DmRegister:
    """大漠插件注册管理器 - 自动化处理COM组件注册和对象创建

    DmRegister 提供完整的大漠插件生命周期管理，包括：
    1. 自动检测插件是否已注册
    2. 智能注册（自动处理管理员权限）
    3. COM对象创建和验证
    4. 插件卸载和清理

    Attributes:
        dll_path (str): 大漠插件 DLL 文件的完整路径
        dm_instance (Any | None): 大漠插件 COM 对象实例
            - 成功: dm.dmsoft 对象
            - 失败: None
        is_registered (bool): 插件注册状态标志
            - True: 已成功注册并创建对象
            - False: 注册失败或对象创建失败

    工作流程:
        1. 确定 DLL 路径（默认或自定义）
        2. 尝试创建 COM 对象（检测是否已注册）
        3. 如未注册，执行注册操作（自动提权）
        4. 再次尝试创建 COM 对象
        5. 验证注册状态

    Examples:
        使用默认路径:
        >>> dm_reg = DmRegister()
        >>> if dm_reg.is_registered:
        ...     print(dm_reg.dm_instance.ver())

        指定 DLL 目录:
        >>> dm_reg = DmRegister(dll_directory='D:/tools/dm')
        >>> print(dm_reg.dll_path)  # D:/tools/dm/dm.dll

        指定具体 DLL 文件:
        >>> dm_reg = DmRegister(dll_directory='C:/dm/dm.dll')

        使用后卸载:
        >>> dm_reg = DmRegister()
        >>> # ... 使用插件 ...
        >>> dm_reg.unregister()

    Note:
        - 默认路径: {当前模块目录}/.dm/dm.dll
        - 注册需要管理员权限，会自动提示 UAC
        - 注册失败不会抛出异常，但 is_registered 为 False
        - 建议在应用结束时调用 unregister()

    See Also:
        - _create_dm_object: COM 对象创建函数
        - _runas_admin: 管理员权限执行函数
        - execute: 注册执行方法
        - unregister: 卸载方法
    """

    def __init__(self, dll_directory: str | None = None):
        """初始化大漠插件注册器

        构建 DLL 路径并尝试注册/创建大漠插件对象。
        如果插件已注册，直接创建对象；否则执行注册流程。

        Args:
            dll_directory (str | None, optional): DLL 路径
                - None: 使用默认路径 {模块目录}/.dm/dm.dll
                - str (目录): 自动拼接 dm.dll，如 "D:/tools/dm"
                - str (文件): 直接使用，如 "D:/tools/dm/dm.dll"

        Examples:
            默认路径（推荐）:
            >>> dm_reg = DmRegister()
            >>> print(dm_reg.dll_path)
            # D:/CODES/xtdamo/xtdamo/.dm/dm.dll

            指定目录:
            >>> dm_reg = DmRegister(dll_directory='C:/dm')
            >>> print(dm_reg.dll_path)  # C:/dm/dm.dll

            指定文件:
            >>> dm_reg = DmRegister(dll_directory='C:/tools/dm.dll')
            >>> print(dm_reg.dll_path)  # C:/tools/dm.dll

            检查结果:
            >>> dm_reg = DmRegister()
            >>> if dm_reg.is_registered:
            ...     print('注册成功')
            ... else:
            ...     print('注册失败，检查日志')

        Note:
            - 默认路径是模块所在目录的 .dm 子目录
            - 如果提供目录路径，会自动拼接 dm.dll
            - 如果提供 .dll 文件，直接使用该路径
            - 初始化时会自动调用 execute() 方法
            - 可能会触发 UAC 提示（需要管理员权限）

        See Also:
            - execute: 执行注册流程
            - _create_dm_object: 创建 COM 对象
        """
        if not dll_directory:
            # 使用新的默认路径
            dll_directory = os.path.join(os.path.dirname(__file__), '.dm')
            dll_directory = os.path.abspath(dll_directory)

        # 构建dll文件路径
        self.dll_path = dll_directory if dll_directory.endswith('.dll') else os.path.join(dll_directory, 'dm.dll')

        # 构建注册命令
        register_command = f'regsvr32.exe /s "{self.dll_path}"'

        # 初始化时设为None，后续会被赋值为大漠插件对象
        self.dm_instance: Any | None = None
        self.is_registered: bool = False
        self.execute(register_command)

    def execute(self, register_command):
        """执行大漠插件注册流程

        智能注册流程：
        1. 首先尝试直接创建 COM 对象（检测是否已注册）
        2. 如果失败，执行注册命令（自动处理管理员权限）
        3. 注册后再次尝试创建 COM 对象
        4. 更新注册状态标志

        Args:
            register_command (str): regsvr32 注册命令
                - 格式: 'regsvr32.exe /s "DLL路径"'
                - /s 参数表示静默注册（无弹窗）

        Returns:
            Any | None: 大漠插件对象
                - 成功: dm.dmsoft COM 对象
                - 失败: None

        Examples:
            手动调用（通常不需要）:
            >>> dm_reg = DmRegister()
            >>> cmd = 'regsvr32.exe /s "D:/dm/dm.dll"'
            >>> result = dm_reg.execute(cmd)
            >>> if result:
            ...     print('注册成功')

        Note:
            - 此方法在 __init__ 中自动调用，通常不需要手动调用
            - 会自动检测当前用户是否有管理员权限
            - 有管理员权限: 直接使用 os.system 执行
            - 无管理员权限: 使用 _runas_admin 提权执行
            - 注册失败会记录日志，但不抛出异常
            - 更新 self.is_registered 和 self.dm_instance

        See Also:
            - _create_dm_object: 创建 COM 对象
            - _runas_admin: 管理员权限执行
            - unregister: 卸载注册
        """
        # 首先尝试直接创建大漠对象
        self.dm_instance = _create_dm_object()

        if self.dm_instance is not None:
            return self.dm_instance

        # 未注册时尝试注册
        mylog.info('尝试注册大漠插件...')
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()

        if is_admin:
            os.system(register_command)  # noqa: S605
            mylog.debug(f'注册大漠插件： {register_command} ')
        else:
            if _runas_admin(register_command):
                mylog.debug(f'以ShellExecuteEx注册大漠插件： {register_command} ')
            else:
                mylog.error('注册命令执行失败或无法获取进程句柄')

        # 注册后再次尝试创建大漠对象
        self.dm_instance = _create_dm_object()

        # 注册后仍然失败的情况
        if self.dm_instance is None:
            self.is_registered = False
            mylog.warning('警告: 无法创建大漠对象！')
        else:
            self.is_registered = True
            return self.dm_instance
        return None

    def unregister(self):
        """卸载大漠插件COM组件

        从系统注册表中移除大漠插件的 COM 注册信息，
        并清理对象引用。建议在应用程序结束时调用。

        卸载流程:
            1. 构造 regsvr32 卸载命令（/u 参数）
            2. 检测管理员权限并执行卸载
            3. 清除对象引用和状态标志

        Examples:
            基本使用:
            >>> dm_reg = DmRegister()
            >>> # ... 使用插件 ...
            >>> dm_reg.unregister()

            验证卸载:
            >>> dm_reg.unregister()
            >>> print(dm_reg.is_registered)  # False
            >>> print(dm_reg.dm_instance)  # None

            完整流程:
            >>> dm_reg = DmRegister()
            >>> if dm_reg.is_registered:
            ...     dm_reg.dm_instance.ver()
            ...     dm_reg.unregister()

        Note:
            - 卸载需要管理员权限，会触发 UAC 提示
            - /u 参数表示卸载，/s 参数表示静默执行
            - 卸载后 is_registered 设为 False
            - 卸载后 dm_instance 设为 None
            - 建议在应用退出时调用，但不是必须的
            - 卸载不影响其他使用大漠插件的程序

        See Also:
            - execute: 注册方法
            - _runas_admin: 管理员权限执行
        """
        # 构造取消注册命令
        unregister_command = f'regsvr32.exe /u /s "{self.dll_path}"'

        if ctypes.windll.shell32.IsUserAnAdmin():
            os.system(unregister_command)  # noqa: S605
            mylog.debug(f'已取消注册大漠插件： {unregister_command}')
        else:
            if _runas_admin(unregister_command):
                mylog.debug(f'以ShellExecuteEx取消注册大漠插件：{unregister_command}')
            else:
                mylog.error('取消注册命令执行失败或无法获取进程句柄')
        self.is_registered = False
        self.dm_instance = None  # 清除大漠对象引用

    def __repr__(self):
        """返回注册器的字符串表示

        提供详细的调试信息，包括注册状态、对象实例和 DLL 路径。

        Returns:
            str: 格式化的字符串，包含关键信息
                格式: "dm.dll注册状态:{状态} ,大漠对象:{对象} ,注册路径:{路径}"

        Examples:
            查看状态:
            >>> dm_reg = DmRegister()
            >>> print(dm_reg)
            dm.dll注册状态:True ,大漠对象:<COMObject dm.dmsoft> ,注册路径:D:/dm/dm.dll

            调试信息:
            >>> print(repr(dm_reg))
            dm.dll注册状态:True ,大漠对象:<COMObject dm.dmsoft> ,注册路径:D:/dm/dm.dll

        Note:
            - 用于调试和日志记录
            - 可以快速查看注册器的完整状态
        """
        return f'dm.dll注册状态:{self.is_registered} ,大漠对象:{self.dm_instance} ,注册路径:{self.dll_path}'


if __name__ == '__main__':
    try:
        dm_reg = DmRegister()
        mylog.info(
            dm_reg,
            '\n',
            dm_reg.dm_instance.ver() if dm_reg.dm_instance else 'dm_instance is None',
        )
    except Exception as e:
        mylog.error(f'发生错误: {e}')

    mylog.info('程序结束')
