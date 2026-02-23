#!/usr/bin/env python3
"""
快速测试交易日数据 - 只测试关键接口
"""

import sys
import yaml
import tushare as ts

print("🔍 快速测试交易日关键接口...")

try:
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化tushare
    ts.set_token(config['api']['api_key'])
    pro = ts.pro_api()
    
    test_date = '20260213'  # 交易日
    print(f"测试日期: {test_date}")
    
    # 1. 测试涨停股数据 (关键)
    print("\n1. 📈 涨停股数据测试...")
    try:
        limit_df = pro.limit_list_d(trade_date=test_date, limit_type='U', fields='ts_code,name,pct_chg')
        if not limit_df.empty:
            print(f"✅ 成功: {len(limit_df)} 只涨停股")
            print(f"   样例: {limit_df.iloc[0]['name']} ({limit_df.iloc[0]['ts_code']}) {limit_df.iloc[0]['pct_chg']}%")
        else:
            print("❌ 失败: 涨停股数据为空")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 2. 测试融资融券数据 (关键)
    print("\n2. 💰 融资融券数据测试...")
    try:
        margin_df = pro.margin(trade_date=test_date)
        if not margin_df.empty:
            financing = margin_df['rzye'].sum()
            margin = margin_df['rqye'].sum()
            print(f"✅ 成功: 融资余额={financing/1e12:.2f}万亿, 融券余额={margin/1e9:.2f}亿")
        else:
            print("❌ 失败: 融资融券数据为空")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 3. 测试日线数据 (简单验证)
    print("\n3. 📊 日线数据测试...")
    try:
        daily_df = pro.daily(trade_date=test_date, fields='ts_code,close', limit=5)
        if not daily_df.empty:
            print(f"✅ 成功: {len(daily_df)} 条日线数据")
        else:
            print("❌ 失败: 日线数据为空")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 4. 测试交易日历
    print("\n4. 📅 交易日历测试...")
    try:
        cal_df = pro.trade_cal(start_date=test_date, end_date=test_date)
        if not cal_df.empty:
            is_open = cal_df.iloc[0]['is_open']
            print(f"✅ 成功: 日期{test_date}是{'交易日' if is_open == 1 else '非交易日'}")
        else:
            print("❌ 失败: 交易日历数据为空")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("\n" + "="*60)
    print("快速测试完成")
    
except Exception as e:
    print(f"❌ 测试初始化失败: {e}")
    import traceback
    traceback.print_exc()