#!/usr/bin/env python3
"""诊断T99短期信号引擎超时问题"""

import time
import sys
import traceback
from datetime import datetime

# 添加技能路径到sys.path
sys.path.insert(0, '/root/.openclaw/workspace/skills/a-share-short-decision')
sys.path.insert(0, '/root/.openclaw/workspace/skills/a-share-short-decision/tools')

def timed_call(func_name, func, *args, **kwargs):
    """带计时器的函数调用"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始执行: {func_name}")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 完成: {func_name} - {elapsed:.2f}秒")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: {func_name} - {elapsed:.2f}秒 - {e}")
        traceback.print_exc()
        return None

def main():
    print("=== T99短期信号引擎诊断开始 ===")
    print(f"当前时间: {datetime.now()}")
    print(f"Python路径: {sys.executable}")
    
    # 导入所需模块
    try:
        from tools.fusion_engine import short_term_signal_engine
        from tools.market_data import get_market_sentiment, get_sector_rotation, scan_strong_stocks
        from tools.money_flow import analyze_capital_flow
        from tools.risk_control import check_market_trend, short_term_risk_control
        from tools.settings import get_screener_config
        
        print("✓ 模块导入成功")
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        traceback.print_exc()
        return
    
    # 测试日期（使用今天）
    test_date = "2026-02-28"
    
    # 1. 测试交易日历
    print("\n--- 测试交易日历 ---")
    import akshare as ak
    timed_call("akshare.tool_trade_date_hist_sina", ak.tool_trade_date_hist_sina)
    
    # 2. 测试配置获取
    print("\n--- 测试配置获取 ---")
    config = timed_call("get_screener_config", get_screener_config)
    if config:
        print(f"配置加载成功，策略: {config.get('strategy', {}).keys()}")
    
    # 3. 测试市场情绪
    print("\n--- 测试市场情绪 ---")
    sentiment = timed_call("get_market_sentiment", get_market_sentiment, test_date, True)
    
    # 4. 测试板块轮动
    print("\n--- 测试板块轮动 ---")
    sector_info = timed_call("get_sector_rotation", get_sector_rotation, 5, test_date, True)
    
    # 5. 测试大盘趋势
    print("\n--- 测试大盘趋势 ---")
    market_trend = timed_call("check_market_trend", check_market_trend, "sh000001", 5)
    
    # 6. 获取板块名称
    sector_names = []
    if sector_info and sector_info.get("top_sectors"):
        sector_names = [x["name"] for x in sector_info.get("top_sectors", [])]
        print(f"板块名称: {sector_names[:5]}")
    
    # 检查宏观板块配置
    if config:
        macro_sectors = config.get("strategy", {}).get("macro", {}).get("sectors", [])
        if macro_sectors and isinstance(macro_sectors, list) and len(macro_sectors) > 0:
            sector_names = macro_sectors
            print(f"使用宏观板块: {sector_names}")
    
    # 7. 测试强势股扫描（这是最可能卡住的地方）
    print("\n--- 测试强势股扫描 ---")
    stocks = timed_call("scan_strong_stocks", scan_strong_stocks, sector_names, 10, test_date, True)
    
    # 8. 测试资金流分析
    target_symbol = stocks[0]["code"] if stocks else None
    if target_symbol:
        print(f"\n--- 测试资金流分析 ({target_symbol}) ---")
        capital = timed_call("analyze_capital_flow", analyze_capital_flow, target_symbol, test_date, True)
    else:
        print("\n⚠ 无目标股票，跳过资金流分析")
    
    # 9. 测试完整引擎（设置超时）
    print("\n=== 测试完整短期信号引擎（300秒超时） ===")
    import signal
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException("函数执行超时")
    
    # 设置超时处理器
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5分钟超时
    
    try:
        start = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始执行完整引擎...")
        result = short_term_signal_engine(analysis_date=test_date, debug=True)
        elapsed = time.time() - start
        signal.alarm(0)  # 取消超时
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 引擎执行成功 - {elapsed:.2f}秒")
        print(f"结果: score={result.get('score')}, signal={result.get('signal')}")
    except TimeoutException:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ 引擎执行超时（300秒）")
        print("问题: 函数在5分钟后仍未完成")
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 引擎执行错误 - {elapsed:.2f}秒")
        print(f"错误: {e}")
        traceback.print_exc()
    finally:
        signal.alarm(0)  # 确保取消超时
    
    print("\n=== 诊断完成 ===")

if __name__ == "__main__":
    main()