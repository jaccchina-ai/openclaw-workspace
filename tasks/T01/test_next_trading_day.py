#!/usr/bin/env python3
"""
测试下一个交易日获取逻辑
"""

import sys
import yaml

print("🔍 测试下一个交易日获取逻辑...")

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sys.path.insert(0, '.')
    from limit_up_strategy_new import LimitUpScoringStrategyV2
    
    strategy = LimitUpScoringStrategyV2(config)
    print("✅ 策略初始化成功")
    
    # 测试用例
    test_cases = [
        ('20260213', '20260224'),  # 节前最后一个交易日 → 节后第一个交易日
        ('20260224', '20260225'),  # 节后第一个交易日 → 下一个交易日
        ('20260210', '20260211'),  # 正常交易日 → 下一个交易日
    ]
    
    print("\n📅 测试下一个交易日计算:")
    
    all_passed = True
    for t_date, expected_next in test_cases:
        next_date = strategy._get_next_trading_day(t_date)
        
        if next_date:
            status = "✅" if next_date == expected_next else "❌"
            print(f"{status} {t_date} → 下一个交易日: {next_date} (预期: {expected_next})")
            
            if next_date != expected_next:
                all_passed = False
        else:
            print(f"❌ {t_date} → 无法获取下一个交易日")
            all_passed = False
    
    print("\n📅 测试前一个交易日计算:")
    
    # 也测试一下前一个交易日逻辑
    prev_test_cases = [
        ('20260224', '20260213'),  # 节后第一个交易日 → 节前最后一个交易日
        ('20260225', '20260224'),  # 正常交易日 → 前一个交易日
        ('20260211', '20260210'),  # 正常交易日 → 前一个交易日
    ]
    
    for t_date, expected_prev in prev_test_cases:
        prev_date = strategy._get_prev_trading_day(t_date)
        
        if prev_date:
            status = "✅" if prev_date == expected_prev else "❌"
            print(f"{status} {t_date} → 前交易日: {prev_date} (预期: {expected_prev})")
            
            if prev_date != expected_prev:
                all_passed = False
        else:
            print(f"❌ {t_date} → 无法获取前交易日")
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()