#!/usr/bin/env python3
"""
调试下一个交易日获取问题
"""

import sys
import yaml
import pandas as pd

print("🔍 调试_next_trading_day方法...")

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    import tushare as ts
    ts.set_token(config['api']['api_key'])
    pro = ts.pro_api()
    
    # 测试日期
    test_date = '20260213'
    
    # 模拟_get_next_trading_day方法中的查询
    from datetime import datetime, timedelta
    
    current_dt = datetime.strptime(test_date, '%Y%m%d')
    start_date = test_date
    end_date = (current_dt + timedelta(days=30)).strftime('%Y%m%d')
    
    print(f"查询日期范围: {start_date} - {end_date}")
    
    cal_df = pro.trade_cal(
        exchange='SSE',
        start_date=start_date,
        end_date=end_date,
        fields='cal_date,is_open'
    )
    
    if cal_df.empty:
        print("❌ 交易日历查询返回空数据")
    else:
        print(f"✅ 获取到 {len(cal_df)} 条交易日历记录")
        
        # 按日期升序排序
        cal_df = cal_df.sort_values('cal_date', ascending=True)
        
        print("\n前10条记录:")
        print(cal_df.head(10).to_string())
        
        # 找到当前日期的索引
        current_idx = -1
        for i, row in cal_df.iterrows():
            if row['cal_date'] == test_date:
                current_idx = i
                print(f"\n✅ 找到日期 {test_date}，索引: {current_idx}")
                print(f"   是否为交易日: {row['is_open'] == 1}")
                break
        
        if current_idx == -1:
            print(f"\n❌ 在交易日历中未找到日期: {test_date}")
        else:
            # 向后查找下一个交易日
            print(f"\n🔍 从索引 {current_idx + 1} 开始查找下一个交易日...")
            found = False
            for i in range(current_idx + 1, len(cal_df)):
                if cal_df.iloc[i]['is_open'] == 1:
                    next_date = cal_df.iloc[i]['cal_date']
                    print(f"✅ 找到下一个交易日: {next_date} (索引: {i})")
                    found = True
                    break
            
            if not found:
                print(f"❌ 未找到下一个交易日，检查了 {len(cal_df) - current_idx - 1} 条记录")
                print(f"   最后几条记录:")
                print(cal_df.tail(5).to_string())
    
except Exception as e:
    print(f"❌ 调试失败: {e}")
    import traceback
    traceback.print_exc()