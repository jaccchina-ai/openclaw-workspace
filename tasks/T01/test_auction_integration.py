#!/usr/bin/env python3
"""
测试竞价数据集成功能
"""

import sys
import yaml
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_auction_data_integration():
    """测试竞价数据集成"""
    print("🔍 测试竞价数据集成...")
    
    try:
        # 导入策略类
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 初始化策略
        strategy = LimitUpScoringStrategyV2(config)
        print("✅ 策略初始化成功")
        
        # 测试日期
        test_date = '20240222'  # 历史日期，应该有竞价数据
        test_stock = '000002.SZ'  # 万科
        
        print(f"\n📊 测试竞价数据获取:")
        print(f"   股票: {test_stock}")
        print(f"   日期: {test_date}")
        
        # 测试_get_real_auction_data方法
        auction_data = strategy._get_real_auction_data(test_stock, test_date)
        
        if auction_data:
            data_source = auction_data.get('data_source', 'unknown')
            open_change = auction_data.get('open_change_pct', 0)
            volume_ratio = auction_data.get('auction_volume_ratio', 1)
            amount = auction_data.get('auction_amount', 0)
            
            print(f"✅ 成功获取竞价数据 (来源: {data_source})")
            print(f"   开盘涨幅: {open_change:.2f}%")
            print(f"   竞价量比: {volume_ratio:.2f}")
            print(f"   竞价金额: {amount:.0f}元")
            
            # 测试竞价评分计算
            auction_score = strategy._calculate_auction_score(auction_data)
            print(f"   竞价评分: {auction_score:.1f}")
            
            return True
        else:
            print("❌ 无法获取竞价数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prev_trading_day():
    """测试前一个交易日获取"""
    print("\n🔍 测试前一个交易日获取...")
    
    try:
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 测试几个日期
        test_cases = [
            ('20240222', '20240221'),  # 周四的前一天是周三
            ('20240223', '20240222'),  # 周五的前一天是周四
        ]
        
        all_passed = True
        
        for test_date, expected_prev in test_cases:
            prev_date = strategy._get_prev_trading_day(test_date)
            
            if prev_date:
                status = "✅" if prev_date == expected_prev else "❌"
                print(f"{status} {test_date} → 前交易日: {prev_date} (预期: {expected_prev})")
                
                if prev_date != expected_prev:
                    all_passed = False
            else:
                print(f"❌ {test_date} → 无法获取前交易日")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_full_auction_analysis():
    """测试完整竞价分析流程"""
    print("\n🎯 测试完整竞价分析流程...")
    
    try:
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 创建模拟候选股票
        import pandas as pd
        mock_candidates = pd.DataFrame([
            {'ts_code': '000002.SZ', 'name': '万科A', 'trade_date': '20240221', 'total_score': 70.0},
            {'ts_code': '000001.SZ', 'name': '平安银行', 'trade_date': '20240221', 'total_score': 65.0},
        ])
        
        t1_date = '20240222'
        
        print(f"模拟候选股票: {len(mock_candidates)} 只")
        print(f"T+1日期: {t1_date}")
        
        # 运行竞价分析
        results = strategy.analyze_t1_auction(mock_candidates, t1_date)
        
        if not results.empty:
            print(f"✅ 竞价分析完成，生成 {len(results)} 条结果")
            
            for idx, row in results.iterrows():
                print(f"\n  {row['name']} ({row['ts_code']})")
                print(f"    T日评分: {row['t_day_score']:.1f}")
                print(f"    竞价评分: {row['auction_score']:.1f}")
                print(f"    最终评分: {row['final_score']:.1f}")
                
                auction_data = row['auction_data']
                data_source = auction_data.get('data_source', 'unknown')
                print(f"    数据来源: {data_source}")
                
                if 'recommendation' in row:
                    rec = row['recommendation']
                    print(f"    推荐: {rec.get('action', 'N/A')}, 仓位: {rec.get('position', 0)}, 置信度: {rec.get('confidence', 'N/A')}")
            
            return True
        else:
            print("❌ 竞价分析未生成结果")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("T01策略 - 竞价数据集成测试")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 竞价数据获取测试")
    print("2. 前一个交易日获取测试")
    print("3. 完整竞价分析流程测试")
    
    results = []
    
    # 运行测试
    tests = [
        ("竞价数据获取", test_auction_data_integration),
        ("前交易日获取", test_prev_trading_day),
        ("完整竞价分析", test_full_auction_analysis),
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
        print("\n🎉 竞价数据集成测试全部通过!")
        print("\n📋 下一步:")
        print("1. 运行完整策略测试: python3 test_v2.py")
        print("2. 验证T+1竞价评分流程")
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