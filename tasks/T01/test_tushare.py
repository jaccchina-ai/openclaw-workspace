#!/usr/bin/env python3
"""
测试tushare API连接和基础功能
"""

import tushare as ts
import yaml
import pandas as pd
from datetime import datetime, timedelta
import json

def test_connection():
    """测试tushare连接"""
    print("🔍 测试tushare API连接...")
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    token = config['api']['api_key']
    print(f"Token: {token[:10]}...")
    
    # 设置token
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 测试基础API
    try:
        # 测试交易日历
        print("\n📅 测试交易日历...")
        cal = pro.trade_cal(exchange='SSE', start_date='20240201', end_date='20240228')
        print(f"交易日历获取成功: {len(cal)} 条记录")
        print("最近5个交易日:")
        print(cal[['cal_date', 'is_open']].head())
        
        # 测试日线数据
        print("\n📈 测试日线数据...")
        daily = pro.daily(trade_date='20240222', fields='ts_code,trade_date,close,pct_chg')
        print(f"日线数据获取成功: {len(daily)} 条记录")
        if not daily.empty:
            print("示例数据:")
            print(daily.head())
        
        # 测试股票基本信息
        print("\n🏢 测试股票基本信息...")
        stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry,list_date')
        print(f"股票基本信息获取成功: {len(stock_basic)} 只股票")
        
        # 测试涨停板数据
        print("\n🚀 测试涨停板数据...")
        try:
            limit_list = pro.limit_list(trade_date='20240222', limit_type='U')
            print(f"涨停板数据获取成功: {len(limit_list)} 条记录")
            if not limit_list.empty:
                print("涨停股票示例:")
                print(limit_list[['ts_code', 'name', 'close', 'pct_chg']].head())
        except Exception as e:
            print(f"涨停板数据获取失败: {e}")
            print("尝试备选方法...")
        
        # 测试资金流数据
        print("\n💰 测试资金流数据...")
        try:
            moneyflow = pro.moneyflow(trade_date='20240222')
            print(f"资金流数据获取成功: {len(moneyflow)} 条记录")
            if not moneyflow.empty:
                print("资金流字段:", moneyflow.columns.tolist())
        except Exception as e:
            print(f"资金流数据获取失败: {e}")
        
        # 测试指数数据
        print("\n📊 测试指数数据...")
        index_daily = pro.index_daily(ts_code='000001.SH', start_date='20240201', end_date='20240222')
        print(f"上证指数数据获取成功: {len(index_daily)} 条记录")
        if not index_daily.empty:
            print("最新数据:")
            print(index_daily[['trade_date', 'close', 'pct_chg']].tail())
        
        print("\n✅ tushare API测试完成")
        return True
        
    except Exception as e:
        print(f"❌ tushare API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_available_apis():
    """检查可用API接口"""
    print("\n🔍 检查可用API接口...")
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    token = config['api']['api_key']
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 列出可能有用的接口
    useful_apis = [
        'daily', 'daily_basic', 'fina_indicator', 'balance_sheet',
        'income', 'cashflow', 'forecast', 'express',
        'dividend', 'fina_audit', 'fina_mainbz',
        'disclosure_date', 'margin', 'margin_detail',
        'top10_holders', 'top10_floatholders',
        'holder_trade', 'repurchase', 'concept', 'concept_detail',
        'ths_index', 'ths_daily', 'ths_member',
        'stk_limit', 'stk_rewards', 'stk_holdertrade',
        'moneyflow', 'moneyflow_hsgt', 'hsgt_top10',
        'ggt_top10', 'margin', 'margin_detail',
        'top_inst', 'index_basic', 'index_daily',
        'index_weight', 'index_classify',
        'limit_list', 'bak_basic', 'adj_factor',
        'suspend', 'suspend_d', 'fund_basic',
        'fund_nav', 'fund_div', 'fund_portfolio',
        'fund_adj', 'future_basic', 'future_daily',
        'opt_basic', 'opt_daily', 'shibor', 'shibor_quote',
        'libor', 'hibor', 'wz_index', 'wz_data'
    ]
    
    print("可能对策略有用的API接口:")
    for api in useful_apis:
        if hasattr(pro, api):
            print(f"  ✅ {api}")
        else:
            print(f"  ❌ {api} (不可用)")
    
    return True

def test_strategy_framework():
    """测试策略框架"""
    print("\n🧪 测试策略框架...")
    
    try:
        # 导入策略类
        from limit_up_strategy import LimitUpScoringStrategy
        
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 初始化策略
        strategy = LimitUpScoringStrategy(config)
        print("✅ 策略类初始化成功")
        
        # 获取最近一个交易日
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 获取最近交易日
        today = datetime.now().strftime('%Y%m%d')
        cal = pro.trade_cal(exchange='SSE', start_date='20240201', end_date=today)
        trade_dates = cal[cal['is_open'] == 1]['cal_date'].tolist()
        
        if trade_dates:
            last_trade_date = trade_dates[-1]
            print(f"📅 使用最近交易日: {last_trade_date}")
            
            # 测试获取涨停股票
            limit_up_stocks = strategy.get_limit_up_stocks(last_trade_date)
            print(f"📈 获取到涨停股票: {len(limit_up_stocks)} 只")
            
            if not limit_up_stocks.empty:
                # 测试评分
                scored_stocks = strategy.calculate_t_day_score(limit_up_stocks.head(3), last_trade_date)
                print(f"🎯 成功评分: {len(scored_stocks)} 只股票")
                
                if not scored_stocks.empty:
                    print("\n📋 评分结果示例:")
                    for idx, row in scored_stocks.head(2).iterrows():
                        print(f"  股票: {row.get('name', 'N/A')} ({row['ts_code']})")
                        print(f"  总分: {row['total_score']:.1f}")
                        print(f"  涨幅: {row.get('pct_chg', 0):.2f}%")
                        print()
        
        print("✅ 策略框架测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 策略框架测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("T01 涨停股策略 - API测试")
    print("="*60)
    
    # 测试连接
    connection_ok = test_connection()
    
    if connection_ok:
        # 检查可用API
        check_available_apis()
        
        # 测试策略框架
        test_strategy_framework()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)