#!/usr/bin/env python3
"""
测试交易日历修复
"""

import sys
import yaml
import pandas as pd
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_trade_cal_api():
    """直接测试trade_cal API"""
    print("🔍 直接测试trade_cal API...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        import tushare as ts
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 测试查询2024年2月的交易日历
        df = pro.trade_cal(
            exchange='SSE',
            start_date='20240201',
            end_date='20240229',
            fields='cal_date,is_open,pretrade_date'
        )
        
        if not df.empty:
            print(f"✅ 获取到 {len(df)} 条交易日历记录")
            
            # 显示前10条记录
            print("\n前10条记录:")
            print(df.head(10).to_string())
            
            # 检查特定日期
            test_date = '20240222'
            test_date2 = '20240223'
            
            date1 = df[df['cal_date'] == test_date]
            date2 = df[df['cal_date'] == test_date2]
            
            print(f"\n日期 {test_date} 的信息:")
            if not date1.empty:
                print(date1.to_string(index=False))
            else:
                print("未找到")
                
            print(f"\n日期 {test_date2} 的信息:")
            if not date2.empty:
                print(date2.to_string(index=False))
            else:
                print("未找到")
            
            return True
        else:
            print("❌ 未获取到交易日历数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prev_trading_day_fixed():
    """测试修复后的前交易日获取"""
    print("\n🔍 测试修复后的前交易日获取...")
    
    try:
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 测试几个日期
        test_cases = [
            ('20240222', '20240221'),  # 周四 → 周三
            ('20240223', '20240222'),  # 周五 → 周四
            ('20240226', '20240223'),  # 周一 → 上周五
        ]
        
        all_passed = True
        
        for test_date, expected_prev in test_cases:
            prev_date = strategy._get_prev_trading_day(test_date)
            
            if prev_date:
                status = "✅" if prev_date == expected_prev else "❌"
                print(f"{status} {test_date} → 前交易日: {prev_date} (预期: {expected_prev})")
                
                if prev_date != expected_prev:
                    all_passed = False
                    print(f"  实际返回值: {prev_date}")
            else:
                print(f"❌ {test_date} → 无法获取前交易日")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("交易日历修复测试")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 直接测试trade_cal API")
    print("2. 测试修复后的前交易日获取")
    
    results = []
    
    # 运行测试
    tests = [
        ("trade_cal API测试", test_trade_cal_api),
        ("前交易日获取测试", test_prev_trading_day_fixed),
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
        print("\n🎉 交易日历修复测试全部通过!")
        return True
    else:
        print("\n⚠️  测试失败，需要进一步调试")
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