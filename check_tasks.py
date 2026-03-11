#!/usr/bin/env python3
"""监控T99和T100任务状态"""

import os
import sys
import subprocess
import datetime
import json
from pathlib import Path

def check_t99():
    """检查T99扫描状态"""
    print("\n=== T99复盘扫描检查 ===")
    
    # 检查扫描日志
    scan_log = "/root/.openclaw/workspace/skills/a-share-short-decision/scan.log"
    if not os.path.exists(scan_log):
        print("❌ 扫描日志不存在")
        return False
    
    # 获取日志最后修改时间
    mtime = os.path.getmtime(scan_log)
    last_modified = datetime.datetime.fromtimestamp(mtime)
    now = datetime.datetime.now()
    
    print(f"日志最后修改: {last_modified}")
    print(f"当前时间: {now}")
    
    # 检查今天是否有扫描
    with open(scan_log, 'r') as f:
        lines = f.readlines()
    
    today_str = now.strftime("%Y-%m-%d")
    has_today_scan = any(today_str in line for line in lines[-50:])
    
    # 检查交易日
    try:
        import tushare as ts
        ts.set_token('870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab')
        pro = ts.pro_api()
        
        today_cal = pro.trade_cal(
            exchange='SSE', 
            start_date=now.strftime('%Y%m%d'),
            end_date=now.strftime('%Y%m%d')
        )
        
        if not today_cal.empty:
            is_trading_day = today_cal.iloc[0]['is_open'] == 1
            print(f"今天是交易日: {'是' if is_trading_day else '否'}")
            
            if is_trading_day and not has_today_scan:
                print("⚠️ 今天是交易日但无扫描记录")
                return False
            elif not is_trading_day and has_today_scan:
                print("⚠️ 今天非交易日但有扫描记录")
                return False
            else:
                print("✅ 扫描状态正常")
                return True
    except Exception as e:
        print(f"交易日检查错误: {e}")
    
    return True

def check_t100():
    """检查T100宏观监控状态"""
    print("\n=== T100宏观监控检查 ===")
    
    # 检查监控日志
    monitor_log = "/root/.openclaw/workspace/skills/macro-monitor/monitor.log"
    if not os.path.exists(monitor_log):
        print("❌ 监控日志不存在")
        return False
    
    # 获取日志最后修改时间
    mtime = os.path.getmtime(monitor_log)
    last_modified = datetime.datetime.fromtimestamp(mtime)
    now = datetime.datetime.now()
    
    print(f"日志最后修改: {last_modified}")
    print(f"当前时间: {now}")
    
    # 检查cron配置
    cron_result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if cron_result.returncode == 0:
        has_t100 = 'macro-monitor' in cron_result.stdout
        has_test_mode = 'TEST_MODE=0' in cron_result.stdout
        
        print(f"Cron中有T100任务: {'是' if has_t100 else '否'}")
        print(f"Cron中设置TEST_MODE=0: {'是' if has_test_mode else '否'}")
        
        if not has_t100:
            print("❌ Cron中无T100任务")
            return False
    else:
        print("❌ 无法读取crontab")
        return False
    
    # 检查最后报告时间（应该是昨晚22:00左右）
    # 北京时间22:00 = UTC 14:00
    expected_time = datetime.datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    if last_modified.date() == now.date() and last_modified.hour >= 14:
        print("✅ 今日报告已生成")
        return True
    elif last_modified.date() == (now - datetime.timedelta(days=1)).date() and last_modified.hour >= 14:
        print("✅ 昨日报告已生成")
        return True
    else:
        print(f"⚠️ 报告可能未按时生成")
        return False

def check_errors():
    """检查错误日志"""
    print("\n=== 错误状态检查 ===")
    
    errors_file = "/root/.openclaw/workspace/.learnings/ERRORS.md"
    if os.path.exists(errors_file):
        with open(errors_file, 'r') as f:
            content = f.read()
        
        pending_count = content.count('**Status**: pending')
        in_progress_count = content.count('**Status**: in_progress')
        
        print(f"Pending错误: {pending_count}")
        print(f"In-progress错误: {in_progress_count}")
        
        if pending_count > 1:  # 模板中有一个pending
            print("⚠️ 有待处理的错误")
            return False
    else:
        print("❌ 错误文件不存在")
    
    return True

def main():
    print(f"任务状态检查 - {datetime.datetime.now()}")
    print("=" * 50)
    
    all_ok = True
    
    # 检查T99
    if not check_t99():
        all_ok = False
    
    # 检查T100
    if not check_t100():
        all_ok = False
    
    # 检查错误
    if not check_errors():
        all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ 所有任务状态正常")
    else:
        print("⚠️ 发现需要关注的问题")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())