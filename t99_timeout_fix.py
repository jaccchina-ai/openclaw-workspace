#!/usr/bin/env python3
"""
T99扫描超时修复补丁
为get_sector_rotation函数添加双重超时保护和错误隔离
"""

import signal
import time
import threading
from functools import wraps
from typing import Any, Callable, Optional
import sys

class EnhancedTimeoutError(Exception):
    """增强超时异常"""
    pass

def enhanced_timeout(seconds: int = 10, fallback_value: Any = None, fallback_func: Optional[Callable] = None):
    """
    增强超时装饰器：信号超时 + 线程超时 + 优雅降级
    
    Args:
        seconds: 超时时间（秒）
        fallback_value: 超时后返回的默认值
        fallback_func: 超时后调用的回退函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            completed = [False]
            
            # 目标函数包装
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
                finally:
                    completed[0] = True
            
            # 创建并启动线程
            thread = threading.Thread(target=target)
            thread.daemon = True  # 守护线程，主线程退出时自动结束
            
            # 启动线程
            thread.start()
            
            # 等待线程完成或超时
            thread.join(timeout=seconds)
            
            if not completed[0]:
                # 线程未完成（超时）
                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception:
                        return fallback_value
                else:
                    return fallback_value
            elif exception[0] is not None:
                # 函数执行异常
                raise exception[0]
            else:
                # 函数正常完成
                return result[0]
        
        return wrapper
    return decorator

def with_signal_timeout(seconds: int = 5):
    """
    信号超时装饰器（适用于main线程）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"信号超时（{seconds}秒）")
            
            # 设置信号超时
            original_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                return func(*args, **kwargs)
            finally:
                # 恢复信号设置
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)
        
        return wrapper
    return decorator

def isolated_api_call(api_func, timeout: int = 8, default_return: Any = None):
    """
    隔离的API调用：超时后返回默认值，不影响整体流程
    
    Args:
        api_func: API调用函数
        timeout: 超时时间（秒）
        default_return: 超时后返回的默认值
    """
    result = [default_return]
    completed = [False]
    
    def target():
        try:
            result[0] = api_func()
        except Exception:
            pass  # 忽略异常，使用默认值
        finally:
            completed[0] = True
    
    # 启动线程
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    
    # 等待超时
    thread.join(timeout=timeout)
    
    return result[0]

def create_fixed_get_sector_rotation():
    """
    创建修复版的get_sector_rotation函数
    """
    print("=== T99超时修复补丁 ===")
    print("问题：get_sector_rotation函数在非交易日API调用挂起")
    print("解决方案：增强超时机制 + 错误隔离")
    
    # 读取原始函数
    try:
        import sys
        sys.path.insert(0, '/root/.openclaw/workspace/skills/a-share-short-decision')
        from tools.market_data import get_sector_rotation as original_func
        
        print("✅ 成功导入原始函数")
        
        # 创建修复版函数
        @enhanced_timeout(seconds=15, fallback_func=lambda *args, **kwargs: {
            "date": kwargs.get('analysis_date', '2026-03-03'),
            "top_sectors": [],
            "data_source": "timeout_fallback",
            "error": "api_timeout_15s"
        })
        @with_signal_timeout(seconds=10)
        def fixed_get_sector_rotation(top_n: int = 5, analysis_date: str | None = None, debug: bool = False):
            """
            修复版的get_sector_rotation函数
            添加双重超时保护
            """
            # 调用原始函数（已在装饰器中受到保护）
            return original_func(top_n=top_n, analysis_date=analysis_date, debug=debug)
        
        print("✅ 创建修复版函数成功")
        return fixed_get_sector_rotation
        
    except Exception as e:
        print(f"❌ 创建修复版函数失败: {e}")
        return None

def test_fix():
    """测试修复效果"""
    print("\n=== 测试修复效果 ===")
    
    # 模拟长时间运行的函数
    def long_running_api(duration: int = 20):
        print(f"  模拟API调用，预计运行{duration}秒...")
        time.sleep(duration)
        print("  API调用完成（不应该到达这里）")
        return {"data": "success"}
    
    # 使用增强超时装饰器
    @enhanced_timeout(seconds=5, fallback_value={"data": "timeout_fallback"})
    def test_function():
        return long_running_api(20)
    
    print("测试超时机制（5秒超时，20秒运行时间）...")
    start_time = time.time()
    
    try:
        result = test_function()
        elapsed = time.time() - start_time
        print(f"结果: {result}")
        print(f"耗时: {elapsed:.2f}秒")
        
        if "timeout_fallback" in str(result):
            print("✅ 超时机制工作正常：在5秒内返回回退值")
            return True
        else:
            print("❌ 超时机制失败：未按预期返回回退值")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def apply_fix():
    """
    应用修复到实际文件
    注意：需要备份原始文件
    """
    print("\n=== 应用修复到market_data.py ===")
    
    source_file = "/root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py"
    backup_file = source_file + ".backup"
    
    try:
        # 读取原始文件
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        import shutil
        shutil.copy2(source_file, backup_file)
        print(f"✅ 创建备份: {backup_file}")
        
        # 查找get_sector_rotation函数定义
        import re
        pattern = r'def get_sector_rotation\(top_n: int = 5, analysis_date: str \| None = None, debug: bool = False\) -> dict\[str, Any\]:'
        
        if re.search(pattern, content):
            print("✅ 找到get_sector_rotation函数定义")
            
            # 简单修复：在函数开头添加快速返回检查（非交易日）
            # 实际修复需要更复杂的逻辑，这里先记录
            print("⚠️  注意：实际修复需要修改函数内部逻辑")
            print("建议的修复步骤：")
            print("1. 添加交易日检查，非交易日直接返回空数据")
            print("2. 为所有API调用添加独立超时")
            print("3. 确保单点失败不影响整体")
            
            return True
        else:
            print("❌ 未找到get_sector_rotation函数定义")
            return False
            
    except Exception as e:
        print(f"❌ 应用修复失败: {e}")
        return False

if __name__ == "__main__":
    print("T99扫描超时修复工具")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    
    # 创建修复版函数
    fixed_func = create_fixed_get_sector_rotation()
    
    # 测试修复
    if test_fix():
        print("\n✅ 超时机制测试通过")
        
        # 询问是否应用修复
        print("\n是否应用修复到实际文件？")
        print("输入 'yes' 继续，其他任意输入取消:")
        user_input = input().strip().lower()
        
        if user_input == 'yes':
            apply_fix()
        else:
            print("取消应用修复")
    else:
        print("\n❌ 超时机制测试失败，请检查代码")