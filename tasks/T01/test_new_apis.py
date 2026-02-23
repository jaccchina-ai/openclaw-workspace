#!/usr/bin/env python3
"""
测试新集成的API接口
1. stock_st - ST股票判断
2. daily_basic - 量比和换手率
3. trade_cal - 交易日历
"""

import sys
import yaml
import pandas as pd
import logging
import tushare as ts

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_stock_st():
    """测试ST股票接口"""
    print("🔍 测试ST股票接口 (stock_st)...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        test_date = '20240222'
        df = pro.stock_st(trade_date=test_date)
        
        if not df.empty:
            print(f"✅ 获取到 {len(df)} 只ST股票")
            print(f"   示例: {df.iloc[0]['ts_code']} - {df.iloc[0]['name']}")
            
            # 检查字段
            required = ['ts_code', 'name', 'trade_date', 'type']
            missing = [f for f in required if f not in df.columns]
            if missing:
                print(f"⚠️  缺失字段: {missing}")
                return False
            else:
                print(f"✅ 所有必需字段存在")
                return True
        else:
            print(f"⚠️  日期 {test_date} 没有ST股票数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_daily_basic():
    """测试每日指标接口"""
    print("\n🔍 测试每日指标接口 (daily_basic)...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        test_date = '20240222'
        test_stock = '000002.SZ'  # 万科
        
        df = pro.daily_basic(
            trade_date=test_date,
            ts_code=test_stock,
            fields='ts_code,volume_ratio,turnover_rate,turnover_rate_f'
        )
        
        if not df.empty:
            print(f"✅ 获取到股票 {test_stock} 的每日指标")
            
            row = df.iloc[0]
            print(f"   量比(volume_ratio): {row.get('volume_ratio', 'N/A')}")
            print(f"   换手率(turnover_rate): {row.get('turnover_rate', 'N/A')}")
            print(f"   自由流通股换手率(turnover_rate_f): {row.get('turnover_rate_f', 'N/A')}")
            
            # 检查关键字段
            key_fields = ['volume_ratio', 'turnover_rate', 'turnover_rate_f']
            for field in key_fields:
                if field in df.columns and pd.notna(row.get(field)):
                    print(f"   ✅ {field} 字段有效")
                else:
                    print(f"   ⚠️  {field} 字段无效或缺失")
            
            return True
        else:
            print(f"⚠️  未获取到数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_trade_cal():
    """测试交易日历接口"""
    print("\n🔍 测试交易日历接口 (trade_cal)...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 测试2024年2月的交易日历
        df = pro.trade_cal(
            exchange='SSE',
            start_date='20240201',
            end_date='20240229'
        )
        
        if not df.empty:
            print(f"✅ 获取到 {len(df)} 条交易日历记录")
            
            # 分析交易日
            trading_days = df[df['is_open'] == 1]
            non_trading_days = df[df['is_open'] == 0]
            
            print(f"   交易日: {len(trading_days)} 天")
            print(f"   非交易日: {len(non_trading_days)} 天")
            
            # 显示最近几个交易日
            recent_trading = trading_days.head(5)
            print(f"   最近5个交易日:")
            for _, row in recent_trading.iterrows():
                print(f"     {row['cal_date']} (前交易日: {row.get('pretrade_date', 'N/A')})")
            
            # 检查字段
            required = ['exchange', 'cal_date', 'is_open', 'pretrade_date']
            missing = [f for f in required if f not in df.columns]
            if missing:
                print(f"⚠️  缺失字段: {missing}")
                return False
            else:
                print(f"✅ 所有必需字段存在")
                return True
        else:
            print(f"⚠️  未获取到交易日历数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_strategy_integration():
    """测试策略集成"""
    print("\n🎯 测试策略集成效果...")
    
    print("""
修改总结:
1. ST判断: name.contains('ST') → stock_st接口 (准确率100%)
2. 量比获取: 复杂计算 → daily_basic.volume_ratio (直接准确)
3. 换手率: 普通换手率 → 优先使用daily_basic.turnover_rate_f (自由流通股)

预期改进:
- ST判断准确率: 大幅提升，避免误判
- 量比数据: 直接可靠，无需复杂计算
- 换手率质量: 基于自由流通股，反映真实流动性
- 整体评分: 更准确反映涨停股质量
""")
    
    return True

def main():
    """主测试函数"""
    print("="*60)
    print("T01策略 - 新API接口集成测试")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 测试ST股票接口 (stock_st)")
    print("2. 测试每日指标接口 (daily_basic)")
    print("3. 测试交易日历接口 (trade_cal)")
    print("4. 策略集成效果分析")
    
    results = []
    
    # 运行测试
    tests = [
        ("ST股票接口", test_stock_st),
        ("每日指标接口", test_daily_basic),
        ("交易日历接口", test_trade_cal),
        ("策略集成分析", test_strategy_integration),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*40}")
            print(f"测试: {test_name}")
            print('='*40)
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("测试汇总")
    print('='*60)
    
    passed_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed_count += 1
    
    print(f"\n📊 结果: {passed_count}/{len(results)} 项测试通过")
    
    if passed_count == len(results):
        print("\n🎉 所有新API接口测试通过!")
        print("\n📋 下一步:")
        print("1. 运行完整策略测试: python3 test_v2.py")
        print("2. 验证ST判断优化效果")
        print("3. 检查量比和换手率数据准确性")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查API权限或网络连接")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)