#!/usr/bin/env python3
"""
快速检查今天T01状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tushare as ts
from datetime import datetime, timedelta
import yaml

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
            return False
        return cal.iloc[0]['is_open'] == 1
    except Exception as e:
        print(f"检查交易日失败: {e}")
        return False

def main():
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    print(f"今天: {today}")
    print(f"昨天: {yesterday}")
    
    # 检查今天是否为交易日
    today_is_trading = check_trading_day(today)
    yesterday_is_trading = check_trading_day(yesterday)
    
    print(f"今天是交易日: {today_is_trading}")
    print(f"昨天是交易日: {yesterday_is_trading}")
    
    # 检查state目录
    state_dir = 'state'
    if os.path.exists(state_dir):
        files = os.listdir(state_dir)
        print(f"\nstate目录文件: {files}")
        
        # 查找候选文件
        candidate_files = [f for f in files if f.startswith('candidates_')]
        print(f"候选文件: {candidate_files}")
        
        if candidate_files:
            # 读取最新的候选文件
            latest = max(candidate_files, key=lambda x: os.path.getmtime(os.path.join(state_dir, x)))
            print(f"最新候选文件: {latest}")
            
            import json
            with open(os.path.join(state_dir, latest), 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"候选数据日期: T日={data.get('t_date')}, T+1日={data.get('t1_date')}")
                print(f"候选股票数量: {len(data.get('candidates', []))}")
    
    # 检查日志
    log_file = 'logs/t01_scheduler.log'
    if os.path.exists(log_file):
        import subprocess
        result = subprocess.run(['tail', '-10', log_file], capture_output=True, text=True)
        print(f"\n最近日志:\n{result.stdout}")
    
    # 建议操作
    print("\n" + "="*60)
    print("建议操作:")
    
    if not today_is_trading:
        print("❌ 今天不是交易日，无需运行T01")
        return
    
    if not candidate_files:
        print("1. 先运行T日评分:")
        print(f"   python3 scheduler.py --mode t-day")
    
    print("2. 运行T+1竞价分析:")
    print(f"   python3 scheduler.py --mode t1-auction")
    
    print("\n3. 启动调度器（长期运行）:")
    print(f"   python3 scheduler.py --mode run")

if __name__ == "__main__":
    main()