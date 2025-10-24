
## 3. exelock/__init__.py

#```python
"""
exelock - 强大的单实例程序锁

使用混合锁机制（端口+文件锁）防止程序重复启动，即使在打包成 exe 后也能可靠工作。

基本用法:
    import exelock
    
    # 最简单的方式 - 无需参数
    exelock.ensure_exelock()
    
    # 您的程序代码
"""

from .core import ExeLock, exelock, ensure_exelock

__version__ = "1.0.2"
__author__ = "pengmin"
__all__ = ['ExeLock', 'exelock', 'ensure_exelock']