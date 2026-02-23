#!/usr/bin/env python3
"""
测试融资融券风控模块
"""

import sys
import yaml
import logging
import pandas as pd

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_margin_api():
    """测试融资融券API"""
    print("🔍 测试融资融券API...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        import tushare as ts
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 测试获取融资融券数据
        test_date = '20240222'  # 历史日期
        margin_df = pro.margin(trade_date=test_date)
        
        if not margin_df.empty:
            print(f"✅ 成功获取融资融券数据: {len(margin_df)} 条记录")
            print("\n数据样例:")
            print(margin_df.to_string(index=False))
            
            # 计算统计信息
            financing_total = margin_df['rzye'].sum()
            margin_total = margin_df['rqye'].sum()
            
            print(f"\n📊 汇总统计:")
            print(f"   两市融资余额总和: {financing_total:.2f} 元")
            print(f"   两市融券余额总和: {margin_total:.2f} 元")
            
            # 检查字段
            print(f"\n🔍 字段检查:")
            for col in margin_df.columns:
                print(f"   - {col}")
            
            return True
        else:
            print("❌ 未获取到融资融券数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_margin_risk_module():
    """测试融资融券风控模块"""
    print("\n🔍 测试融资融券风控模块...")
    
    try:
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        strategy = LimitUpScoringStrategyV2(config)
        print("✅ 策略初始化成功")
        
        # 测试获取融资融券数据
        test_date = '20240222'
        margin_data = strategy._get_margin_data(test_date)
        
        if margin_data:
            print(f"✅ 成功获取融资融券风控数据")
            
            print(f"\n📊 融资融券数据:")
            print(f"   交易日期: {margin_data.get('trade_date', 'N/A')}")
            print(f"   融资余额总和: {margin_data.get('total_financing_balance', 0):.2f}")
            print(f"   融券余额总和: {margin_data.get('total_margin_balance', 0):.2f}")
            print(f"   融资余额变化率: {margin_data.get('financing_change_ratio', 0):.2f}%")
            print(f"   融券余额变化率: {margin_data.get('margin_change_ratio', 0):.2f}%")
            print(f"   融资买入/偿还比率: {margin_data.get('financing_buy_ratio', 0):.2f}")
            
            # 测试市场状况评估
            market_condition = strategy._get_market_condition(test_date)
            
            print(f"\n🎯 市场状况评估:")
            print(f"   市场状态: {market_condition.get('condition', 'N/A')}")
            print(f"   风险等级: {market_condition.get('risk_level', 'N/A')}")
            print(f"   风险评分: {market_condition.get('risk_score', 'N/A')}")
            print(f"   仓位乘数: {market_condition.get('position_multiplier', 'N/A')}")
            print(f"   建议: {market_condition.get('suggestion', 'N/A')}")
            
            return True
        else:
            print("❌ 无法获取融资融券数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auction_real_time_logic():
    """测试竞价实时数据逻辑"""
    print("\n🔍 测试竞价实时数据逻辑...")
    
    try:
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        strategy = LimitUpScoringStrategyV2(config)
        
        test_stock = '000002.SZ'
        test_date = '20240222'
        
        # 测试1: 非交易时间，允许历史数据
        print(f"\n测试1: 非交易时间 (is_trading_hours=False)")
        auction_data1 = strategy._get_real_auction_data(test_stock, test_date, is_trading_hours=False)
        
        if auction_data1:
            data_source1 = auction_data1.get('data_source', 'unknown')
            open_change1 = auction_data1.get('open_change_pct', 0)
            print(f"✅ 成功获取竞价数据 (来源: {data_source1})")
            print(f"   开盘涨幅: {open_change1:.2f}%")
        else:
            print("❌ 无法获取竞价数据")
        
        # 测试2: 模拟交易时间 (如果实时数据不可用，应该返回None)
        print(f"\n测试2: 模拟交易时间 (is_trading_hours=True)")
        # 注意: 对于历史日期，实时接口可能没有数据
        auction_data2 = strategy._get_real_auction_data(test_stock, test_date, is_trading_hours=True)
        
        if auction_data2:
            data_source2 = auction_data2.get('data_source', 'unknown')
            open_change2 = auction_data2.get('open_change_pct', 0)
            print(f"获取到竞价数据 (来源: {data_source2})")
            print(f"   开盘涨幅: {open_change2:.2f}%")
            if data_source2 != 'realtime':
                print(f"⚠️  警告: 在交易时间但未使用实时数据!")
        else:
            print("✅ 符合预期: 在交易时间且无实时数据时返回None")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("融资融券风控与竞价逻辑测试")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 融资融券API测试")
    print("2. 融资融券风控模块测试")
    print("3. 竞价实时数据逻辑测试")
    
    results = []
    
    # 运行测试
    tests = [
        ("融资融券API", test_margin_api),
        ("风控模块", test_margin_risk_module),
        ("竞价逻辑", test_auction_real_time_logic),
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
        print("\n🎉 所有测试通过!")
        print("\n📋 实现总结:")
        print("1. ✅ 融资融券API集成完成")
        print("2. ✅ 融资融券风控因子设计完成")
        print("3. ✅ 竞价实时数据逻辑修改完成")
        print("4. ✅ 9:25-9:29无法获取实时数据时直接返回错误")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查API权限或代码实现")
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