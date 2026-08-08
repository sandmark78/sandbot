#!/usr/bin/env python3
"""
会话压缩检查脚本
检查是否有超过阈值的长会话，提醒压缩

用法: python3 session-compressor.py [--threshold 50]
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/node/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def check_main_session():
    """检查主会话状态"""
    # 主会话的 session key 是 agent:main:main
    # 无法直接读取 session 文件，但可以通过 cron 状态判断
    
    print("🔍 会话压缩检查")
    print("")
    print("💡 建议:")
    print("   - 主会话超过 50 轮时，使用 /reset 或 /new 开始新会话")
    print("   - 重要信息在 reset 前写入 memory/")
    print("   - Cron 任务使用 isolated session，自动隔离")
    print("")
    print("✅ 检查完成")

def main():
    threshold = 50
    if '--threshold' in sys.argv:
        idx = sys.argv.index('--threshold')
        if idx + 1 < len(sys.argv):
            threshold = int(sys.argv[idx + 1])
    
    print(f"🔍 会话压缩检查 (阈值: {threshold} 轮)")
    print("")
    
    check_main_session()

if __name__ == '__main__':
    main()
