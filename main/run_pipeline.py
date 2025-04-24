#!/usr/bin/env python3
# run_pipeline.py
# 用于以不同模式运行pipeline的脚本
# 创建于2025-04-23，功能包括：
# - 支持从命令行启动pipeline
# - 提供详细参数配置选项
# - 支持只运行特定模块

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def main():
    """主函数，处理命令行参数并执行pipeline"""
    parser = argparse.ArgumentParser(description='运行餐饮数据管道')
    
    # 添加命令行参数
    parser.add_argument('--maintest', action='store_true', help='使用maintest.py而非main.py')
    parser.add_argument('--log-only', action='store_true', help='显示最新的日志文件内容')
    parser.add_argument('--time-stats', action='store_true', help='显示最新的执行时间统计')
    parser.add_argument('--module', type=str, choices=['all', 'dzdp', 'xhs', 'cleanup'], 
                        default='all', help='只运行特定模块')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示更多调试信息')
    
    args = parser.parse_args()
    
    # 获取脚本路径
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    log_dir = project_root / "logs"
    
    # 如果只是显示日志
    if args.log_only:
        show_latest_log(log_dir)
        return
    
    # 如果只是显示时间统计
    if args.time_stats:
        show_time_stats(script_dir / "timer_log.txt")
        return
    
    # 确定要运行的脚本
    script_name = "maintest.py" if args.maintest else "main.py"
    script_path = script_dir / script_name
    
    if not script_path.exists():
        print(f"错误: 脚本 {script_path} 不存在")
        return
    
    # 构建环境变量字典用于控制模块执行
    env = os.environ.copy()
    if args.module != 'all':
        env['RUN_MODULE'] = args.module
    
    if args.verbose:
        env['VERBOSE'] = '1'
    
    # 构建命令
    cmd = [sys.executable, str(script_path)]
    
    # 执行pipeline
    print(f"=== 开始执行 {script_name} ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模块: {args.module}")
    print(f"详细模式: {'是' if args.verbose else '否'}")
    
    try:
        process = subprocess.run(cmd, env=env, check=True)
        print(f"\n=== Pipeline 执行完成 ===")
        print(f"退出代码: {process.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"\n=== Pipeline 执行出错 ===")
        print(f"退出代码: {e.returncode}")
        sys.exit(e.returncode)

def show_latest_log(log_dir):
    """显示最新的日志文件内容"""
    log_path = log_dir / "pipeline.log"
    
    if not log_path.exists():
        print(f"错误: 日志文件 {log_path} 不存在")
        return
    
    print(f"=== 显示最新日志 {log_path} ===")
    with open(log_path, 'r', encoding='utf-8') as f:
        print(f.read())

def show_time_stats(timer_log_path):
    """显示最新的执行时间统计"""
    if not Path(timer_log_path).exists():
        print(f"错误: 时间统计文件 {timer_log_path} 不存在")
        return
    
    print(f"=== 显示执行时间统计 {timer_log_path} ===")
    with open(timer_log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 只显示最后一次运行的统计
    stats_start = -1
    for i, line in enumerate(reversed(lines)):
        if "===" in line and "模块执行时间统计" in line:
            stats_start = len(lines) - i - 1
            break
    
    if stats_start >= 0:
        for line in lines[stats_start-2:]:  # 包含前两行的时间戳
            print(line.strip())
    else:
        # 如果没找到详细统计，至少显示最后两条时间记录
        for line in lines[-2:]:
            print(line.strip())

if __name__ == "__main__":
    main() 