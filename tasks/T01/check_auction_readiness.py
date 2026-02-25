#!/usr/bin/env python3
"""
T01竞价分析准备检查
检查实时竞价分析所需的所有条件
"""

import sys
import os
import json
import yaml
import tushare as ts
from datetime import datetime, timedelta
import pandas as pd

def load_config():
    """加载配置文件"""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_beijing_time():
    """获取北京时间 (UTC+8)"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def check_tushare_connection():
    """检查Tushare连接"""
    try:
        config = load_config()
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        # 简单测试连接
        cal = pro.trade_cal(exchange='SSE', start_date='20260225', end_date='20260225')
        return True, "Tushare连接正常"
    except Exception as e:
        return False, f"Tushare连接失败: {e}"

def check_candidate_file():
    """检查候选股文件"""
    expected_file = "state/candidates_20260224_to_20260225.json"
    if not os.path.exists(expected_file):
        return False, f"候选股文件不存在: {expected_file}"
    
    try:
        with open(expected_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        candidate_count = len(data.get('candidates', []))
        return True, f"候选股文件正常，包含 {candidate_count} 只股票"
    except Exception as e:
        return False, f"候选股文件读取失败: {e}"

def check_scheduler_process():
    """检查调度器进程"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and 'scheduler.py' in ' '.join(proc.info['cmdline']):
                return True, f"调度器进程运行中 (PID: {proc.info['pid']})"
        return False, "调度器进程未找到"
    except Exception as e:
        return False, f"进程检查失败: {e}"

def check_trading_hours():
    """检查交易时间（北京时间）"""
    beijing_time = get_beijing_time()
    current_time_str = beijing_time.strftime("%H:%M")
    current_date_str = beijing_time.strftime("%Y%m%d")
    
    # 竞价窗口：09:25-09:29
    auction_start = datetime.strptime("09:25", "%H:%M").time()
    auction_end = datetime.strptime("09:29", "%H:%M").time()
    current_time = beijing_time.time()
    
    in_auction_window = auction_start <= current_time <= auction_end
    
    if in_auction_window:
        time_left = (datetime.combine(beijing_time.date(), auction_end) - beijing_time).total_seconds()
        minutes_left = int(time_left // 60)
        seconds_left = int(time_left % 60)
        return True, f"在竞价窗口内 (09:25-09:29), 剩余 {minutes_left}分{seconds_left}秒"
    else:
        # 计算距离下次窗口的时间
        if current_time < auction_start:
            target_datetime = datetime.combine(beijing_time.date(), auction_start)
        else:
            # 明天
            tomorrow = beijing_time.date() + timedelta(days=1)
            target_datetime = datetime.combine(tomorrow, auction_start)
        
        time_until = target_datetime - beijing_time
        hours_until = int(time_until.total_seconds() // 3600)
        minutes_until = int((time_until.total_seconds() % 3600) // 60)
        
        return False, f"不在竞价窗口内，距离下次窗口: {hours_until}小时{minutes_until}分钟"

def check_real_time_auction():
    """尝试获取实时竞价数据（仅在窗口内）"""
    beijing_time = get_beijing_time()
    current_time = beijing_time.time()
    auction_start = datetime.strptime("09:25", "%H:%M").time()
    auction_end = datetime.strptime("09:29", "%H:%M").time()
    
    if not (auction_start <= current_time <= auction_end):
        return False, "不在实时竞价窗口内 (09:25-09:29)"
    
    try:
        config = load_config()
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 尝试获取实时竞价数据
        today_str = beijing_time.strftime("%Y%m%d")
        auction_data = pro.stk_auction(trade_date=today_str)
        
        if auction_data is not None and not auction_data.empty:
            record_count = len(auction_data)
            return True, f"实时竞价接口正常，获取到 {record_count} 条记录"
        else:
            return False, "实时竞价接口返回空数据"
    except Exception as e:
        return False, f"实时竞价接口调用失败: {e}"

def check_historical_auction():
    """检查历史竞价数据接口"""
    try:
        config = load_config()
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 测试昨天的数据
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
        auction_data = pro.stk_auction_o(trade_date=yesterday)
        
        if auction_data is not None and not auction_data.empty:
            record_count = len(auction_data)
            return True, f"历史竞价接口正常，获取到 {record_count} 条记录"
        else:
            return False, "历史竞价接口返回空数据"
    except Exception as e:
        return False, f"历史竞价接口调用失败: {e}"

def main():
    """主函数"""
    beijing_time = get_beijing_time()
    print("="*70)
    print("🔍 T01竞价分析准备检查")
    print("="*70)
    print(f"当前时间 (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前时间 (北京时间): {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        ("Tushare连接", check_tushare_connection),
        ("候选股文件", check_candidate_file),
        ("调度器进程", check_scheduler_process),
        ("交易时间窗口", check_trading_hours),
        ("历史竞价接口", check_historical_auction),
        ("实时竞价接口", check_real_time_auction),
    ]
    
    results = []
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            results.append((check_name, status, passed, message))
            if not passed:
                all_passed = False
        except Exception as e:
            status = "⚠️"
            results.append((check_name, status, False, f"检查异常: {e}"))
            all_passed = False
    
    # 打印结果
    for check_name, status, passed, message in results:
        print(f"{status} {check_name}: {message}")
    
    print()
    print("="*70)
    
    # 总体状态
    if all_passed:
        print("🎉 所有检查通过！系统已准备好进行竞价分析")
    else:
        print("⚠️  部分检查未通过，请查看上方详细信息")
    
    # 具体建议
    beijing_time = get_beijing_time()
    current_time = beijing_time.time()
    auction_start = datetime.strptime("09:25", "%H:%M").time()
    auction_end = datetime.strptime("09:29", "%H:%M").time()
    
    print()
    print("📋 建议:")
    
    if auction_start <= current_time <= auction_end:
        print("1. 🚨 当前在竞价窗口内 (09:25-09:29)")
        print("2. 立即运行 T+1 竞价分析:")
        print("   python3 main.py t1-auction --date 20260225 --candidates state/candidates_20260224_to_20260225.json")
        print("3. 结果将自动推送到飞书")
    else:
        print("1. 等待竞价窗口 (09:25-09:29 北京时间)")
        print("2. 窗口内运行上述命令")
        print("3. 如实时接口失败，系统将明确报错")
    
    print()
    print("🔄 调度器状态:")
    print("   调度器应持续运行，自动处理每日任务")
    print("   手动运行: python3 scheduler.py --mode run")
    
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())