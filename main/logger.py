#!/usr/bin/env python3
# logger.py
# 用于记录pipeline执行过程中的所有控制台输出到日志文件
# 创建于2025-04-23，功能包括：
# - 将所有stdout和stderr输出同时记录到文件
# - 支持日志轮转，防止日志文件过大
# - 时间戳记录，便于追踪问题

import os
import sys
import time
from datetime import datetime
from pathlib import Path

class Logger:
    """将标准输出和标准错误输出重定向到文件的类"""
    
    def __init__(self, log_file_path, max_log_files=5, max_log_size_mb=10):
        """
        初始化Logger
        
        参数:
            log_file_path: 日志文件路径
            max_log_files: 最大保留的日志文件数量
            max_log_size_mb: 单个日志文件的最大大小（MB）
        """
        self.log_file_path = Path(log_file_path)
        self.max_log_files = max_log_files
        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024
        self.terminal_stdout = sys.stdout
        self.terminal_stderr = sys.stderr
        
        # 创建日志目录
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置日志文件轮转
        self._rotate_logs_if_needed()
        
        # 打开日志文件
        self.log_file = open(self.log_file_path, 'a', encoding='utf-8')
        
        # 记录启动信息
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_file.write(f"\n{'='*50}\n")
        self.log_file.write(f"=== 日志开始: {start_time} ===\n")
        self.log_file.write(f"{'='*50}\n\n")
        self.log_file.flush()
    
    def _rotate_logs_if_needed(self):
        """检查并执行日志文件轮转"""
        if self.log_file_path.exists() and self.log_file_path.stat().st_size >= self.max_log_size_bytes:
            # 轮转现有日志文件
            for i in range(self.max_log_files - 1, 0, -1):
                old_log = self.log_file_path.with_suffix(f'.{i}')
                new_log = self.log_file_path.with_suffix(f'.{i+1}')
                if old_log.exists():
                    if i == self.max_log_files - 1 and new_log.exists():
                        new_log.unlink()  # 删除最老的日志
                    old_log.rename(new_log)
            
            # 重命名当前日志文件
            if self.log_file_path.exists():
                self.log_file_path.rename(self.log_file_path.with_suffix('.1'))
    
    def write_to_stdout(self, message):
        """写入到标准输出和日志文件"""
        self.terminal_stdout.write(message)
        self.log_file.write(message)
        self.log_file.flush()
    
    def write_to_stderr(self, message):
        """写入到标准错误和日志文件"""
        self.terminal_stderr.write(message)
        self.log_file.write(f"[ERROR] {message}")
        self.log_file.flush()
    
    def start_logging(self):
        """开始日志记录，重定向stdout和stderr"""
        sys.stdout = self
        sys.stderr = self
        return self
    
    def stop_logging(self):
        """停止日志记录，恢复stdout和stderr"""
        sys.stdout = self.terminal_stdout
        sys.stderr = self.terminal_stderr
        
        # 记录结束信息
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_file.write(f"\n{'='*50}\n")
        self.log_file.write(f"=== 日志结束: {end_time} ===\n")
        self.log_file.write(f"{'='*50}\n\n")
        
        # 关闭日志文件
        if not self.log_file.closed:
            self.log_file.close()
    
    def __del__(self):
        """析构函数，确保日志文件被关闭"""
        self.stop_logging()
    
    def write(self, message):
        """实现write方法以模拟文件对象行为"""
        self.write_to_stdout(message)
    
    def flush(self):
        """实现flush方法以模拟文件对象行为"""
        self.terminal_stdout.flush()
        self.log_file.flush()

# 使用示例
def setup_logger(log_file_path="logs/pipeline.log"):
    """设置日志记录器"""
    logger = Logger(log_file_path)
    return logger.start_logging()

# 如果直接运行该脚本，则进行简单测试
if __name__ == "__main__":
    logger = setup_logger()
    try:
        print("这是一条测试日志消息")
        print("这条消息将同时输出到终端和日志文件")
        print("=== 错误测试 ===", file=sys.stderr)
    finally:
        logger.stop_logging()
        print("日志记录已停止，这条消息只会输出到终端") 