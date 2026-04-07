#!/usr/bin/env python3
"""
演示sentiment_monitor.py的新功能：API重试机制和缓存机制
"""

import sys
import os
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sentiment_monitor import MarketSentimentMonitor, safe_api_call


def demo_safe_api_call():
    """演示API重试机制"""
    print("=" * 60)
    print("演示1: API重试机制 (safe_api_call)")
    print("=" * 60)
    
    # 示例1: 成功调用
    def successful_api():
        return "API调用成功!"
    
    result = safe_api_call(successful_api)
    print(f"✅ 成功调用: {result}")
    
    # 示例2: 失败2次后成功
    call_count = [0]
    def flaky_api():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception(f"临时错误 #{call_count[0]}")
        return f"第{call_count[0]}次尝试成功!"
    
    call_count[0] = 0
    result = safe_api_call(flaky_api, max_retries=3, retry_delay=0.5)
    print(f"✅ 重试后成功: {result}")
    
    # 示例3: 全部失败
    def always_fails():
        raise Exception("持续错误")
    
    try:
        safe_api_call(always_fails, max_retries=2, retry_delay=0.3)
    except Exception as e:
        print(f"✅ 捕获预期异常: {e}")
    
    print()


def demo_cache_mechanism():
    """演示缓存机制"""
    print("=" * 60)
    print("演示2: 缓存机制 (MarketSentimentMonitor)")
    print("=" * 60)
    
    # 创建监控器实例
    monitor = MarketSentimentMonitor(config={})
    
    # 演示缓存键生成
    key1 = monitor._get_cache_key("test_method", ("arg1", "arg2"), {"kwarg": "value"})
    key2 = monitor._get_cache_key("test_method", ("arg1", "arg2"), {"kwarg": "value"})
    print(f"✅ 缓存键生成: {key1}")
    print(f"✅ 相同参数生成相同键: {key1 == key2}")
    
    # 演示设置和获取缓存
    test_data = {"sentiment": 75, "status": "bull", "indicators": {"limit_up": 100}}
    monitor._set_cached_result("test_key", test_data)
    cached = monitor._get_cached_result("test_key")
    print(f"✅ 设置缓存: {test_data}")
    print(f"✅ 获取缓存: {cached}")
    
    # 演示缓存过期 (使用1秒TTL)
    monitor._set_cached_result("expire_key", "临时数据", ttl=1)
    print(f"✅ 设置1秒TTL缓存: 临时数据")
    time.sleep(1.1)
    expired = monitor._get_cached_result("expire_key")
    print(f"✅ 1秒后获取过期缓存: {expired} (应为None)")
    
    print()


def demo_backward_compatibility():
    """演示向后兼容性"""
    print("=" * 60)
    print("演示3: 向后兼容性")
    print("=" * 60)
    
    monitor = MarketSentimentMonitor(config={})
    
    # 模拟缓存损坏，验证功能仍然正常
    original_cache = monitor._cache
    monitor._cache = None  # 破坏缓存
    
    # 尝试获取缓存（应返回None而不崩溃）
    result = monitor._get_cached_result("any_key")
    print(f"✅ 缓存损坏时获取: {result} (应为None)")
    
    # 尝试设置缓存（应记录警告而不崩溃）
    monitor._set_cached_result("key", "value")
    print(f"✅ 缓存损坏时设置: 已记录警告")
    
    # 恢复缓存
    monitor._cache = original_cache
    print(f"✅ 向后兼容: 缓存失败不影响正常功能")
    
    print()


if __name__ == '__main__':
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "sentiment_monitor.py 新功能演示" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    demo_safe_api_call()
    demo_cache_mechanism()
    demo_backward_compatibility()
    
    print("=" * 60)
    print("✨ 所有演示完成!")
    print("=" * 60)
    print("\n新功能总结:")
    print("  1. safe_api_call(): API调用自动重试机制 (最大3次, 1秒间隔)")
    print("  2. _cache字典: 结果缓存机制 (TTL: 5分钟)")
    print("  3. 向后兼容: 缓存失败时不影响正常功能")
    print()
