import socket

def is_port_available(port):
    """
    检查端口是否可用
    
    参数:
        port (int): 要检查的端口号
        
    返回:
        bool: 端口是否可用
    """
    try:
        # 尝试绑定端口
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', port))
        test_socket.close()
        return True
    except socket.error:
        return False

def find_available_port(start_port=49152):
    """
    查找可用的端口
    
    参数:
        start_port (int): 起始端口号
        
    返回:
        int: 可用的端口号
    """
    port = start_port
    while port <= 65535:
        if is_port_available(port):
            return port
        port += 1
    
    # 如果所有端口都被占用，使用随机端口
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port