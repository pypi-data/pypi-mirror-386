import socket
import sys
import atexit
import os
import hashlib
import logging

# 设置日志
logger = logging.getLogger(__name__)

class ExeLock:
    """
    单实例程序锁类
    
    使用端口绑定方法确保同一时间只有一个程序实例在运行
    """
    
    def __init__(self, program_name=None, port=None, silent=False):
        """
        初始化单实例锁
        
        参数:
            program_name (str): 程序名称，用于标识锁和生成默认端口
            port (int, optional): 用于锁定的端口号，默认基于程序名生成
            silent (bool): 是否静默模式，如果为True，检测到已有实例时不显示GUI警告
        """
        if program_name is None:
            # 如果没有提供程序名，使用当前执行的文件名
            program_name = os.path.basename(sys.argv[0])
        
        self.program_name = program_name
        self.port = port or self._generate_port(program_name)
        self.silent = silent
        self.lock_socket = None
        self._acquired = False
        
        logger.debug(f"初始化单实例锁: {self.program_name}, 端口: {self.port}")
    
    def _generate_port(self, program_name):
        """
        基于程序名生成端口号
        
        参数:
            program_name (str): 程序名称
            
        返回:
            int: 49152-65535范围内的端口号
        """
        # 使用MD5哈希生成端口
        hash_obj = hashlib.md5(program_name.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # 将哈希前4位转换为端口号 (49152-65535)
        port = 49152 + (int(hash_hex[:4], 16) % 16384)
        return port
    
    def is_running(self):
        """
        检查程序是否已在运行
        
        返回:
            bool: 程序是否已在运行
        """
        try:
            # 尝试连接锁端口
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(0.5)  # 设置超时避免长时间阻塞
            test_socket.connect(('localhost', self.port))
            test_socket.close()
            logger.debug(f"检测到程序已在运行: {self.program_name}")
            return True
        except (socket.timeout, ConnectionRefusedError, socket.error):
            # 连接失败，说明程序未运行
            logger.debug(f"程序未运行: {self.program_name}")
            return False
    
    def acquire(self):
        """
        获取程序锁
        
        返回:
            bool: 是否成功获取锁
        """
        if self.is_running():
            if not self.silent:
                self._show_warning_message()
            return False
        
        try:
            self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.lock_socket.bind(('localhost', self.port))
            # 不调用listen()，这样其他socket无法连接
            self._acquired = True
            
            # 注册退出时清理函数
            atexit.register(self.release)
            
            logger.debug(f"成功获取程序锁: {self.program_name}")
            return True
            
        except Exception as e:
            logger.error(f"获取程序锁失败: {self.program_name}, 错误: {e}")
            if self.lock_socket:
                self.lock_socket.close()
                self.lock_socket = None
            return False
    
    def release(self):
        """
        释放程序锁
        """
        if self.lock_socket:
            try:
                self.lock_socket.close()
                logger.debug(f"释放程序锁: {self.program_name}")
            except Exception as e:
                logger.error(f"释放程序锁失败: {self.program_name}, 错误: {e}")
            finally:
                self.lock_socket = None
                self._acquired = False
        
        # 从atexit中移除
        try:
            if self.release in atexit._exithandlers:
                atexit.unregister(self.release)
        except:
            pass
    
    def _show_warning_message(self):
        """显示警告消息"""
        try:
            import tkinter.messagebox
            import tkinter as tk
            
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)
            
            tkinter.messagebox.showwarning(
                "程序已在运行", 
                f"'{self.program_name}' 已经在运行，请不要重复启动！",
                parent=root
            )
            
            root.destroy()
        except ImportError:
            # 如果没有tkinter，使用控制台输出
            print(f"警告: '{self.program_name}' 已经在运行，请不要重复启动！")
        except Exception as e:
            logger.error(f"显示警告消息失败: {e}")
            print(f"警告: '{self.program_name}' 已经在运行，请不要重复启动！")
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self.acquire():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()
    
    @property
    def acquired(self):
        """是否已获取锁"""
        return self._acquired


def exelock(program_name=None, port=None, silent=False):
    """
    创建并获取单实例锁的便捷函数
    
    参数:
        program_name (str, optional): 程序名称，默认使用当前文件名
        port (int, optional): 用于锁定的端口号
        silent (bool): 是否静默模式
        
    返回:
        bool: 是否成功获取锁（True=成功，False=已有实例在运行）
    """
    lock = ExeLock(program_name=program_name, port=port, silent=silent)
    return lock.acquire()


def ensure_exelock(program_name=None, port=None, silent=False):
    """
    确保单实例运行的便捷函数
    
    如果程序已在运行，会显示警告并退出程序
    
    参数:
        program_name (str, optional): 程序名称，默认使用当前文件名
        port (int, optional): 用于锁定的端口号
        silent (bool): 是否静默模式
    """
    if not exelock(program_name, port, silent):
        sys.exit(1)