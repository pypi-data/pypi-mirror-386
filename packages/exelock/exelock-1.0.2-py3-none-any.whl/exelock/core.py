import socket
import os
import sys
import atexit
import hashlib
import time
import portalocker  # 用于跨平台文件锁

class ExeLock:
    """
    单实例程序锁类
    
    使用混合锁机制（端口+文件锁）确保同一时间只有一个程序实例在运行
    """
    
    def __init__(self, program_name=None, port=None, silent=False):
        """
        初始化单实例锁
        
        参数:
            program_name (str, optional): 程序名称，用于标识锁。如果为 None，则使用当前执行的文件名。
            port (int, optional): 用于锁定的端口号。如果为 None，则基于程序名自动生成。
            silent (bool): 是否静默模式。如果为 True，检测到已有实例时不显示 GUI 警告。
        """
        if program_name is None:
            program_name = os.path.basename(sys.argv[0])
        
        self.program_name = program_name
        self.port = port or self._generate_port(program_name)
        self.silent = silent
        self.lock_socket = None
        
        # 文件锁路径
        import tempfile
        lock_name = program_name.replace('.exe', '').replace('.py', '').replace(' ', '_') + '.lock'
        self.lock_file = os.path.join(tempfile.gettempdir(), lock_name)
        
        # 确保文件锁目录存在
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        
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
        检查程序是否已在运行 - 混合检测方法
        
        返回:
            bool: 程序是否已在运行
        """
        # 方法1: 端口检测
        port_in_use = False
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(0.5)
            result = test_socket.connect_ex(('localhost', self.port))
            test_socket.close()
            port_in_use = (result == 0)  # 0表示连接成功，端口在使用中
        except:
            pass
        
        # 方法2: 文件锁检测
        file_lock_in_use = False
        try:
            if os.path.exists(self.lock_file):
                # 检查锁文件是否"新鲜"（最近修改）
                file_age = time.time() - os.path.getmtime(self.lock_file)
                if file_age < 60:  # 60秒内的锁文件认为有效
                    file_lock_in_use = True
                else:
                    # 锁文件太旧，可能是异常退出留下的，删除它
                    try:
                        os.remove(self.lock_file)
                    except:
                        pass
        except:
            pass
        
        # 如果任一检测方法表明程序在运行，则返回True
        return port_in_use or file_lock_in_use
    
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
            # 获取端口锁
            self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.lock_socket.bind(('localhost', self.port))
            self.lock_socket.listen(1)  # 开始监听，这样其他实例能检测到端口被占用
            
            # 获取文件锁
            self.lock_handle = open(self.lock_file, 'w')
            self.lock_handle.write(f"{os.getpid()}:{time.time()}")
            self.lock_handle.flush()
            
            # 锁定文件
            portalocker.lock(self.lock_handle, portalocker.LOCK_EX)
            
            # 注册退出时清理函数
            atexit.register(self.release)
            
            return True
        except Exception as e:
            # 获取锁失败，清理资源
            self._cleanup()
            return False
    
    def release(self):
        """
        释放程序锁
        """
        self._cleanup()
    
    def _cleanup(self):
        """
        清理所有锁资源
        """
        # 释放端口锁
        if self.lock_socket:
            try:
                self.lock_socket.close()
            except:
                pass
            self.lock_socket = None
        
        # 释放文件锁
        if hasattr(self, 'lock_handle') and self.lock_handle:
            try:
                portalocker.unlock(self.lock_handle)
                self.lock_handle.close()
            except:
                pass
            self.lock_handle = None
        
        # 删除锁文件
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except:
            pass
    
    def _show_warning_message(self):
        """
        显示警告消息
        """
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
            # 其他异常，使用控制台输出
            print(f"警告: '{self.program_name}' 已经在运行，请不要重复启动！")
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        if not self.acquire():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.release()


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