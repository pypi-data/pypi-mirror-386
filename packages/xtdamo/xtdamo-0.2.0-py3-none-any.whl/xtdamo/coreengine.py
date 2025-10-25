# !/usr/bin/env python3
"""
==============================================================
Description  : 核心引擎模块 - 提供大漠插件核心功能封装，包括图像识别、文本识别、窗口操作等
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-18 22:00:00
Github       : https://github.com/sandorn/xtdamo

本模块提供以下核心功能:
- 图像识别与查找 (FindPic, FindPicEx)
- 文本识别与查找 (FindStr, FindStrEx)
- 颜色识别与查找 (FindColor, FindColorEx)
- 窗口操作与管理 (FindWindow, EnumWindow)
- 屏幕截图与图像处理
- 内存操作与数据查找

主要特性:
- 支持多种图像格式识别
- 智能相似度匹配算法
- 高性能窗口枚举
- 内存数据查找功能
- 异常处理和错误恢复
==============================================================
"""

from __future__ import annotations

from typing import Any

from .config import Config


class CoreEngine:
    def __init__(self, dm_instance: Any) -> None:
        """核心功能封装
        Args:
            dm_instance: 大漠插件实例
        """
        if not dm_instance:
            raise ValueError('dmobject cannot be None')
        self.dm_instance = dm_instance

    def __repr__(self):
        return f'版本： {self.ver()} ID：{self.GetID()}'

    def GetDmCount(self):
        return self.dm_instance.GetDmCount()

    def GetID(self):
        return self.dm_instance.GetID()

    def ver(self):
        return self.dm_instance.ver()

    def GetDir(self, types: int = 0):
        """
        0 : 获取当前路径
        1 : 获取系统路径(system32路径)
        2 : 获取windows路径(windows所在路径)
        3 : 获取临时目录路径(temp)
        4 : 获取当前进程(exe)所在的路径
        """
        return self.dm_instance.GetDir(types)

    def GetBasePath(self):
        return self.dm_instance.GetBasePath()

    def GetPath(self):
        return self.dm_instance.GetPath()

    def SetDisplayInput(self, mode):
        return self.dm_instance.SetDisplayInput(mode)

    def SetShowErrorMsg(self, show):
        return self.dm_instance.SetShowErrorMsg(show)

    def Capture(self, x1, y1, x2, y2, file):
        return self.dm_instance.Capture(x1, y1, x2, y2, file)

    def FindPic(
        self,
        x1,
        y1,
        x2,
        y2,
        pic_name,
        delta_color='101010',
        sim=Config.DEFAULT_SIMILARITY,
        dir=0,
        # intX=0,
        # intY=0,
    ):
        return self.dm_instance.FindPic(x1, y1, x2, y2, pic_name, delta_color=delta_color, sim=sim, dir=dir)

    def FindColor(self, x1, y1, x2, y2, color, sim, dir, intX, intY):
        # _, x0, y0 = dm.FindColor(0, 0, 1200, 800, color = "757575", sim = 1.0, dir = 1,  intX = 0, intY = 0)
        return self.dm_instance.FindColor(x1, y1, x2, y2, color, sim, dir, intX, intY)

    def LoadPic(self, pic_name):
        return self.dm_instance.LoadPic(pic_name)

    def FreePic(self, pic_name):
        return self.dm_instance.FreePic(pic_name)

    def GetColor(self, x, y):
        return self.dm_instance.GetColor(x, y)

    def GetPicSize(self, pic_name):
        return self.dm_instance.GetPicSize(pic_name)

    def GetColorBGR(self, x, y):
        return self.dm_instance.GetColorBGR(x, y)

    def BGR2RGB(self, bgr_color):
        return self.dm_instance.BGR2RGB(bgr_color)

    def CmpColor(self, x, y, color, sim):
        return self.dm_instance.CmpColor(x, y, color, sim)

    def BindWindow(
        self,
        hwnd: int,
        display: str | None = None,
        mouse: str | None = None,
        keypad: str | None = None,
        public: str = 'dx.public.fake.window.min|dx.public.hack.speed',
        mode: int | None = None,
    ) -> int:
        """绑定指定的窗口（核心方法）

        将大漠插件的操作绑定到指定窗口，支持多种绑定模式。
        这是底层绑定方法，通常由高级接口调用。

        Args:
            hwnd (int): 窗口句柄
                - 可通过 FindWindow 等方法获取
                - 必须是有效的窗口句柄

            display (str | None, optional): 显示模式，默认使用Config配置 ('gdi')
                - 'normal': 正常模式，前台可视，速度较慢
                - 'gdi': GDI模式，兼容性好，推荐使用
                - 'gdi2': GDI增强模式，速度更快
                - 'dx': DirectX模式，速度快但兼容性差
                - 'dx2': DirectX增强模式

            mouse (str | None, optional): 鼠标模式，默认使用Config配置 ('windows3')
                - 'normal': 正常模式，前台可视
                - 'windows': Windows消息模式
                - 'windows2': Windows增强模式
                - 'windows3': Windows兼容模式，推荐使用
                - 'dx': DirectX模式
                - 'dx2': DirectX增强模式

            keypad (str | None, optional): 键盘模式，默认使用Config配置 ('windows')
                - 'normal': 正常模式，前台可视
                - 'windows': Windows消息模式，推荐使用
                - 'dx': DirectX模式

            public (str, optional): 公共参数，默认为后台最小化和加速
                - 'dx.public.fake.window.min': 伪装窗口最小化
                - 'dx.public.hack.speed': 提升运行速度
                - 多个参数用 '|' 分隔

            mode (int | None, optional): 绑定模式，默认使用Config配置 (101)
                - 0: 推荐模式，前台前台
                - 1-7: 不同的兼容性模式
                - 101: 推荐后台模式，兼容性好
                - 103: 另一种后台模式

        Returns:
            int: 绑定结果
                - 1: 绑定成功
                - 0: 绑定失败

        Examples:
            使用默认配置绑定:
            >>> hwnd = dm.FindWindow('', '窗口标题')
            >>> result = dm.BindWindow(hwnd)
            >>> if result == 1:
            ...     print('绑定成功')

            自定义绑定模式:
            >>> result = dm.BindWindow(hwnd, display='dx2', mouse='windows3', keypad='windows', mode=101)

            前台绑定（适用于调试）:
            >>> result = dm.BindWindow(hwnd, display='normal', mouse='normal', keypad='normal', public='', mode=0)

        Note:
            - 绑定前请确保窗口句柄有效
            - 后台模式需要管理员权限
            - 不同游戏/程序可能需要不同的绑定模式组合
            - 绑定失败时可通过 GetLastError() 获取错误信息
            - 使用完毕后应调用 UnBindWindow() 解绑

        See Also:
            - UnBindWindow: 解绑窗口
            - IsBind: 检查窗口是否已绑定
            - Config.DEFAULT_BIND_CONFIG: 默认绑定配置
        """
        # 使用Config中的默认配置
        bind_config = Config.get_bind_config(
            display=display,
            mouse=mouse,
            keypad=keypad,
            mode=mode,
        )

        return self.dm_instance.BindWindowEx(
            hwnd,
            bind_config['display'],
            bind_config['mouse'],
            bind_config['keypad'],
            public,
            bind_config['mode'],
        )

    def UnBindWindow(self) -> int:
        """解绑窗口（核心方法）

        解除当前窗口的绑定状态，释放底层资源。
        这是底层解绑方法，通常由高级接口调用。

        Returns:
            int: 解绑结果
                - 1: 解绑成功
                - 0: 解绑失败

        Examples:
            基本使用:
            >>> result = dm.UnBindWindow()
            >>> if result == 1:
            ...     print('解绑成功')

            配合 BindWindow 使用:
            >>> hwnd = dm.FindWindow('', '窗口标题')
            >>> dm.BindWindow(hwnd)
            >>> # ... 执行操作 ...
            >>> dm.UnBindWindow()

        Note:
            - 这是底层方法，高级接口应使用 ApiProxy.解绑窗口
            - 即使未绑定窗口也可以调用，不会报错
            - 程序退出前应该解绑所有已绑定的窗口

        See Also:
            - BindWindow: 绑定窗口
            - IsBind: 检查窗口是否已绑定
        """
        return self.dm_instance.UnBindWindow()

    def IsBind(self, hwnd):
        return self.dm_instance.IsBind(hwnd)

    def MoveWindow(self, hwnd, x, y):
        return self.dm_instance.MoveWindow(hwnd, x, y)

    def FindWindow(self, class_name='', title_name=''):
        return self.dm_instance.FindWindow(class_name, title_name)

    def ClientToScreen(self, hwnd, x, y):
        return self.dm_instance.ClientToScreen(hwnd, x, y)

    def ScreenToClient(self, hwnd, x, y):
        return self.dm_instance.ScreenToClient(hwnd, x, y)

    def FindWindowByProcess(self, process_name, class_name, title_name):
        return self.dm_instance.FindWindowByProcess(process_name, class_name, title_name)

    def FindWindowByProcessId(self, process_id, class_, title):
        return self.dm_instance.FindWindowByProcessId(process_id, class_, title)

    def GetClientRect(self, hwnd, x1, y1, x2, y2):
        return self.dm_instance.GetClientRect(hwnd, x1, y1, x2, y2)

    def GetClientSize(self, hwnd, width, height):
        return self.dm_instance.GetClientSize(hwnd, width, height)

    def GetWindowRect(self, hwnd, x1, y1, x2, y2):
        return self.dm_instance.GetWindowRect(hwnd, x1, y1, x2, y2)

    def GetWindow(self, hwnd, flag):
        return self.dm_instance.GetWindow(hwnd, flag)

    def GetWindowProcessPath(self, hwnd):
        return self.dm_instance.GetWindowProcessPath(hwnd)

    def SetWindowSize(self, hwnd, width, height):
        return self.dm_instance.SetWindowSize(hwnd, width, height)

    def SetWindowState(self, hwnd, flag):
        return self.dm_instance.SetWindowState(hwnd, flag)

    def SetWindowText(self, hwnd, title):
        return self.dm_instance.SetWindowText(hwnd, title)

    def SetWindowTransparent(self, hwnd, trans):
        return self.dm_instance.SetWindowTransparent(hwnd, trans)

    def EnumWindow(self, parent, title, class_name, filter):
        return self.dm_instance.EnumWindow(parent, title, class_name, filter)

    def EnumWindowByProcess(self, process_name, title, class_name, filter):
        return self.dm_instance.EnumWindowByProcess(process_name, title, class_name, filter)

    def EnumWindowSuper(self, spec1, flag1, type1, spec2, flag2, type2, sort):
        return self.dm_instance.EnumWindowSuper(spec1, flag1, type1, spec2, flag2, type2, sort)

    def FindData(self, hwnd, addr_range, data):
        return self.dm_instance.FindData(hwnd, addr_range, data)

    def FindDataEx(self, hwnd, addr_range, data, step, multi_thread, mode):
        return self.dm_instance.FindDataEx(hwnd, addr_range, data, step, multi_thread, mode)

    def DoubleToData(self, value):
        return self.dm_instance.DoubleToData(value)

    def FloatToData(self, value):
        return self.dm_instance.FloatToData(value)

    def GetModuleBaseAddr(self, hwnd, module):
        return self.dm_instance.GetModuleBaseAddr(hwnd, module)

    def IntToData(self, value, type):
        return self.dm_instance.IntToData(value, type)

    def ReadData(self, hwnd, addr, len):
        return self.dm_instance.ReadData(hwnd, addr, len)

    def ReadDouble(self, hwnd, addr):
        return self.dm_instance.ReadDouble(hwnd, addr)

    def ReadFloat(self, hwnd, addr):
        return self.dm_instance.ReadFloat(hwnd, addr)

    def ReadInt(self, hwnd, addr, type):
        return self.dm_instance.ReadInt(hwnd, addr, type)

    def ReadString(self, hwnd, addr, type, len):
        return self.dm_instance.ReadString(hwnd, addr, type, len)

    def StringToData(self, value, type):
        return self.dm_instance.StringToData(value, type)

    def WriteData(self, hwnd, addr, data):
        return self.dm_instance.WriteData(hwnd, addr, data)

    def WriteDouble(self, hwnd, addr, v):
        return self.dm_instance.WriteDouble(hwnd, addr, v)

    def WriteFloat(self, hwnd, addr, v):
        return self.dm_instance.WriteFloat(hwnd, addr, v)

    def WriteInt(self, hwnd, addr, type, v):
        return self.dm_instance.WriteInt(hwnd, addr, type, v)

    def WriteString(self, hwnd, addr, type, v):
        return self.dm_instance.WriteString(hwnd, addr, type, v)

    def CopyFile(self, src_file, dst_file, over):
        return self.dm_instance.CopyFile(src_file, dst_file, over)

    def CreateFolder(self, folder):
        return self.dm_instance.CreateFolder(folder)

    def DecodeFile(self, file, pwd):
        return self.dm_instance.DecodeFile(file, pwd)

    def DeleteFile(self, file):
        return self.dm_instance.DeleteFile(file)

    def DeleteFolder(self, folder):
        return self.dm_instance.DeleteFolder(folder)

    def DeleteIni(self, section, key, file):
        return self.dm_instance.DeleteIni(section, key, file)

    def DeleteIniPwd(self, section, key, file, pwd):
        return self.dm_instance.DeleteIniPwd(section, key, file, pwd)

    def DownloadFile(self, url, save_file, timeout):
        return self.dm_instance.DownloadFile(url, save_file, timeout)

    def EncodeFile(self, file, pwd):
        return self.dm_instance.EncodeFile(file, pwd)

    def GetFileLength(self, file):
        return self.dm_instance.GetFileLength(file)

    def IsFileExist(self, file):
        return self.dm_instance.IsFileExist(file)

    def MoveFile(self, src_file, dst_file):
        return self.dm_instance.MoveFile(src_file, dst_file)

    def ReadFile(self, file):
        return self.dm_instance.ReadFile(file)

    def ReadIni(self, section, key, file):
        return self.dm_instance.ReadIni(section, key, file)

    def ReadIniPwd(self, section, key, file, pwd):
        return self.dm_instance.ReadIniPwd(section, key, file, pwd)

    def SelectDirectory(self):
        return self.dm_instance.SelectDirectory()

    def SelectFile(self):
        return self.dm_instance.SelectFile()

    def WriteFile(self, file, content):
        return self.dm_instance.WriteFile(file, content)

    def WriteIni(self, section, key, value, file):
        return self.dm_instance.WriteIni(section, key, value, file)

    def WriteIniPwd(self, section, key, value, file, pwd):
        return self.dm_instance.WriteIniPwd(section, key, value, file, pwd)

    def GetNetTime(self):
        return self.dm_instance.GetNetTime()

    def GetOsType(self):
        return self.dm_instance.GetOsType()

    def GetScreenHeight(self):
        return self.dm_instance.GetScreenHeight()

    def GetScreenWidth(self):
        return self.dm_instance.GetScreenWidth()

    def GetTime(self):
        return self.dm_instance.GetTime()

    def Is64Bit(self):
        return self.dm_instance.Is64Bit()

    def RunApp(self, app_path, mode):
        return self.dm_instance.RunApp(app_path, mode)

    def Play(self, media_file):
        return self.dm_instance.Play(media_file)

    def Stop(self, id):
        return self.dm_instance.Stop(id)

    def Delay(self, mis):
        return self.dm_instance.Delay(mis)

    def ExitOs(self, type):
        return self.dm_instance.ExitOs(type)

    def Beep(self, duration=1000, f=800):
        return self.dm_instance.Beep(f, duration)
