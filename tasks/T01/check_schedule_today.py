#!/usr/bin/env python3
"""
检查今天调度器逻辑
验证今天(2/24)是否会被识别为交易日，今晚20:00是否运行T日评分
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
import yaml
from datetime import datetime, timedelta

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 设置token
ts.set_token(config['api']['api_key'])
pro = ts.pro_api()

def check_trading_day(date_str):
    """检查是否为交易日"""
    try:
        cal = pro.trade_cal(exchange='SSE', start_date=date_str, end_date=date_str)
        if cal.empty:
            print(f"日期 {date_str}: 日历查询返回空")
            return False
        is_open = cal.iloc[0]['is_open'] == 1
        print(f"日期 {date_str}: {'✅ 是交易日' if is_open else '❌ 不是交易日'}")
        return is_open
    except Exception as e:
        print(f"检查交易日失败 {date_str}: {e}")
        return False

def check_schedule_logic():
    """检查调度器逻辑"""
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    
    print("=== 调度器逻辑检查 ===")
    print(f"今天: {today} (2月24日，节后第一个交易日)")
    print(f"昨天: {yesterday} (2月23日，周日)")
    print(f"明天: {tomorrow} (2月25日，周二)")
    print()
    
    # 检查今天是否为交易日
    today_is_trading = check_trading_day(today)
    
    # 检查昨天是否为交易日
    yesterday_is_trading = check_trading_day(yesterday)
    
    print("\n=== 调度器预期行为 ===")
    
    if today_is_trading:
        print("✅ 今天是交易日 (2/24)")
        print("✅ 今晚20:00: 运行T日评分 (对今天2/24的涨停股评分)")
        print("✅ 明早09:25: 运行T+1竞价分析 (对今天2/24的涨停股在明天2/25的竞价分析)")
        print("✅ 明早09:30前: 飞书推送股票信息")
    else:
        print("❌ 今天不是交易日，调度器今晚20:00不会运行T日评分")
    
    print("\n=== 关键逻辑验证 ===")
    
    # 验证T日候选文件保存逻辑
    from scheduler import T01Scheduler
    scheduler = T01Scheduler('config.yaml')
    
    # 测试get_trade_date逻辑
    print(f"1. scheduler.get_trade_date(offset=-1): {scheduler.get_trade_date(offset=-1)}")
    print(f"2. scheduler.get_trade_date(offset=0): {scheduler.get_trade_date(offset=0)}")
    
    # 检查现有的候选文件
    state_dir = 'state'
    if os.path.exists(state_dir):
        import json
        files = os.listdir(state_dir)
        candidate_files = [f for f in files if f.startswith('candidates_')]
        
        if candidate_files:
            print(f"\n3. 现有候选文件: {candidate_files}")
            for file in candidate_files:
                with open(os.path.join(state_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"   - {file}: T日={data.get('t_date')}, T+1日={data.get('t1_date')}")
        else:
            print("\n3. 没有候选文件")
    
    print("\n=== 建议 ===")
    if today_is_trading:
        print("1. 等待今晚20:00自动运行T日评分")
        print("2. 明早09:30前检查飞书消息")
        print("3. 如未收到消息，查看日志: ./manage_t01.sh logs")
    else:
        print("1. 需要手动运行T日评分: python3 scheduler.py --mode t-day")
        print("2. 检查交易日历API是否正常工作")

if __name__ == "__main__":
    check_schedule_logic()