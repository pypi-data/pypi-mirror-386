"""
exelock - 单实例程序锁

提供防止程序重复启动的功能，使用端口绑定方法确保同一时间只有一个程序实例在运行。

使用方式:
    import exelock
    
    # 方式1: 使用便捷函数
    if not exelock.exelock('我的程序', 12345):
        exit(1)  # 程序已在运行
    
    # 方式2: 使用确保函数（失败会自动退出）
    exelock.ensure_exelock('我的程序', 12345)
    
    # 方式3: 使用上下文管理器
    with exelock.ExeLock('我的程序', 12345):
        # 您的程序代码
        pass
"""

from .core import ExeLock, exelock, ensure_exelock
from .utils import is_port_available, find_available_port

__version__ = "1.0.1"
__author__ = "pengmin"
__all__ = [
    'ExeLock',
    'exelock',
    'ensure_exelock',
    'is_port_available',
    'find_available_port'
]