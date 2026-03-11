#!/usr/bin/env python3
"""
T99超时机制修复脚本
问题：signal.alarm(5)在某些环境下失效，导致Tushare API调用无限期等待
解决方案：使用threading.Timer实现更可靠的超时机制
"""

import os
import sys
import json
import threading
import traceback
from datetime import datetime

def add_timeout_fix_to_market_data():
    """为market_data.py中的Tushare API调用添加可靠的超时机制"""
    market_data_path = "/root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py"
    
    if not os.path.exists(market_data_path):
        print(f"❌ 文件不存在: {market_data_path}")
        return False
    
    # 读取文件内容
    with open(market_data_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找get_sector_rotation函数中的Tushare API调用部分
    if "signal.alarm(5)" not in content:
        print("⚠️ 未找到signal.alarm(5)调用，可能已修复或代码结构不同")
        return True
    
    # 定义新的超时辅助函数
    timeout_helper = '''
# ====== 可靠的超时机制辅助函数 ======
import threading
import _thread

class TimeoutException(Exception):
    """超时异常"""
    pass

def run_with_timeout(func, timeout_seconds=5, default_result=None):
    """使用threading.Timer运行函数，超时返回默认值
    
    Args:
        func: 要执行的函数
        timeout_seconds: 超时时间（秒）
        default_result: 超时时的默认返回值
        
    Returns:
        func的返回值或default_result
    """
    result_container = []
    exception_container = []
    
    def worker():
        try:
            result = func()
            result_container.append(result)
        except Exception as e:
            exception_container.append(e)
    
    # 启动工作线程
    thread = threading.Thread(target=worker)
    thread.daemon = True  # 设置为守护线程，主线程退出时会强制结束
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        # 线程仍在运行，说明超时
        print(f"[TIMEOUT] 函数执行超时 ({timeout_seconds}秒)，返回默认值")
        return default_result
    
    # 线程正常结束
    if exception_container:
        raise exception_container[0]
    
    return result_container[0] if result_container else default_result

def safe_tushare_call(api_call_func, timeout_seconds=5, default_result=None):
    """安全的Tushare API调用，带超时保护"""
    try:
        return run_with_timeout(api_call_func, timeout_seconds, default_result)
    except Exception as e:
        print(f"[ERROR] Tushare API调用异常: {e}")
        return default_result
# ====== 超时机制结束 ======
'''
    
    # 查找signal导入位置，在它后面添加新的超时机制
    if "import signal" in content:
        # 在import signal后添加新的超时机制
        new_content = content.replace(
            "import signal",
            "import signal\n\n" + timeout_helper
        )
    else:
        # 在文件开头的导入部分后添加
        imports_end = content.find("\n\n")  # 找到第一个空行
        if imports_end > 0:
            new_content = content[:imports_end] + "\n\n" + timeout_helper + content[imports_end:]
        else:
            print("❌ 无法确定导入部分结束位置")
            return False
    
    # 替换signal.alarm调用为safe_tushare_call
    # 首先查找industry_data = pro.moneyflow_ind_dc(...)调用
    tushare_patterns = [
        ("industry_data = pro.moneyflow_ind_dc", "industry_data = safe_tushare_call(lambda: pro.moneyflow_ind_dc"),
        ("concept_data = pro.moneyflow_ind_dc", "concept_data = safe_tushare_call(lambda: pro.moneyflow_ind_dc")
    ]
    
    for old_pattern, new_pattern in tushare_patterns:
        if old_pattern in new_content:
            # 找到具体的API调用行
            lines = new_content.split('\n')
            for i, line in enumerate(lines):
                if old_pattern in line and "signal.alarm" in lines[i-2:i+5]:  # 检查附近是否有signal.alarm
                    # 替换该行
                    lines[i] = line.replace(old_pattern, new_pattern)
                    # 添加闭合括号
                    if line.strip().endswith(')'):
                        lines[i] = lines[i] + ", timeout_seconds=5, default_result=None)"
                    break
            new_content = '\n'.join(lines)
    
    # 备份原文件
    backup_path = market_data_path + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 原文件已备份到: {backup_path}")
    
    # 写入新文件
    with open(market_data_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ market_data.py已更新，添加了可靠的超时机制")
    return True

def test_fix():
    """测试修复后的代码"""
    print("\n=== 测试修复后的代码 ===")
    
    # 先测试模块导入
    test_script = '''
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/a-share-short-decision')

try:
    from tools.market_data import get_sector_rotation, run_with_timeout, safe_tushare_call
    print("✅ 模块导入成功")
    
    # 测试超时机制
    print("\\n测试超时机制...")
    def long_running_task():
        import time
        time.sleep(10)  # 这个任务应该超时
        return "不应到达这里"
    
    result = run_with_timeout(long_running_task, timeout_seconds=2, default_result="超时默认值")
    print(f"超时测试结果: {result}")
    if result == "超时默认值":
        print("✅ 超时机制工作正常")
    else:
        print("❌ 超时机制可能有问题")
    
    # 测试get_sector_rotation（不实际调用API）
    print("\\n测试get_sector_rotation导入（不执行）...")
    print("✅ get_sector_rotation导入成功")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
'''
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if result.stderr:
            print("标准错误:", result.stderr)
    except subprocess.TimeoutExpired:
        print("❌ 测试超时，超时机制可能有问题")
    finally:
        os.unlink(test_file)

def main():
    print("=== T99超时机制修复脚本 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("问题: signal.alarm(5)在某些环境下失效，导致API调用无限期等待")
    print("解决方案: 使用threading.Timer实现更可靠的超时机制")
    
    # 1. 添加超时机制
    print("\n1. 添加可靠的超时机制到market_data.py...")
    if not add_timeout_fix_to_market_data():
        print("❌ 修复失败")
        return 1
    
    # 2. 测试修复
    print("\n2. 测试修复...")
    test_fix()
    
    # 3. 验证明天的交易日判断
    print("\n3. 验证交易日判断...")
    try:
        from tools.market_data import is_trading_day_local
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_str = tomorrow.strftime("%Y%m%d")
        is_trading = is_trading_day_local(tomorrow_str)
        print(f"明天({tomorrow_str})是否为交易日: {is_trading}")
        
        if is_trading:
            print("✅ 明天是交易日，14:30扫描将正常执行")
        else:
            print("⚠️ 明天不是交易日，14:30扫描将跳过")
    except Exception as e:
        print(f"❌ 交易日判断测试失败: {e}")
    
    print("\n=== 修复完成 ===")
    print("建议: 明天14:30前运行一次测试，确保扫描正常工作")
    
    # 构建测试命令（避免f-string转义问题）
    today_str = datetime.now().strftime('%Y-%m-%d')
    test_cmd = f"cd /root/.openclaw/workspace/skills/a-share-short-decision && timeout 30 python3 -c \\\"from tools.market_data import get_sector_rotation; result = get_sector_rotation(analysis_date='{today_str}', debug=True); print('测试成功:', result.get('data_source', 'unknown'))\\\""
    print(f"测试命令: {test_cmd}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())