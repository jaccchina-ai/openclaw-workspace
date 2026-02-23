#!/usr/bin/env python3
"""
T01策略 - 明日测试脚本
测试筛选规则、热点板块判断、资金流接口
"""

import sys
import yaml
import pandas as pd
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_config():
    """测试配置文件"""
    print("🔍 测试配置文件...")
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ 配置文件加载成功")
        print(f"   API Token: {config['api'].get('api_key', '')[:10]}...")
        
        # 检查策略配置
        if 'strategy' in config:
            print(f"✅ 策略配置存在")
            t_day = config['strategy'].get('t_day_scoring', {})
            print(f"   T日评分权重: {len(t_day)} 个因子")
            
        return config
        
    except Exception as e:
        print(f"❌ 配置文件错误: {e}")
        return None

def test_screening_logic():
    """测试筛选逻辑 (不调用API)"""
    print("\n🎯 测试筛选逻辑...")
    
    # 模拟数据
    test_data = [
        {'ts_code': '000001.SZ', 'name': '平安银行', 'industry': '银行'},
        {'ts_code': '000002.SZ', 'name': 'ST万科', 'industry': '房地产'},  # ST股票
        {'ts_code': '830999.BJ', 'name': '北交所股票', 'industry': '测试'},  # 北交所
        {'ts_code': '688001.SH', 'name': '科创板股票', 'industry': '科技'},  # 科创板
        {'ts_code': '600000.SH', 'name': '浦发银行', 'industry': '银行'},
    ]
    
    df = pd.DataFrame(test_data)
    print(f"原始数据: {len(df)} 条记录")
    
    # 应用筛选规则
    # 1. 剔除ST股票
    non_st_mask = ~df['name'].str.contains('ST')
    df_filtered = df[non_st_mask]
    st_count = len(df) - len(df_filtered)
    
    # 2. 剔除北交所股票
    non_bj_mask = ~df_filtered['ts_code'].str.startswith('8')
    df_filtered = df_filtered[non_bj_mask]
    bj_count = len(df) - st_count - len(df_filtered)
    
    # 3. 剔除科创板股票
    non_kc_mask = ~df_filtered['ts_code'].str.startswith('688')
    df_filtered = df_filtered[non_kc_mask]
    kc_count = len(df) - st_count - bj_count - len(df_filtered)
    
    print(f"✅ 筛选结果:")
    print(f"   剔除ST股票: {st_count} 只")
    print(f"   剔除北交所股票: {bj_count} 只")
    print(f"   剔除科创板股票: {kc_count} 只")
    print(f"   剩余股票: {len(df_filtered)} 只")
    
    if len(df_filtered) == 2:
        print("✅ 筛选逻辑测试通过!")
        return True
    else:
        print(f"❌ 筛选逻辑测试失败，预期2只，实际{len(df_filtered)}只")
        return False

def test_hot_sector_threshold():
    """测试热点板块阈值逻辑"""
    print("\n🔥 测试热点板块阈值...")
    
    # 测试用例
    test_cases = [
        {
            'name': '理想热点板块',
            'pct_change': 5.0,  # ≥3%
            'net_amount': 60000000,  # ≥5000万 (6000万)
            'rank': 5,  # ≤10
            'limit_count': 4,  # ≥3
            'expected': True
        },
        {
            'name': '涨幅不足',
            'pct_change': 2.5,  # <3%
            'net_amount': 60000000,
            'rank': 5,
            'limit_count': 4,
            'expected': False
        },
        {
            'name': '净流入不足',
            'pct_change': 5.0,
            'net_amount': 40000000,  # <5000万
            'rank': 5,
            'limit_count': 4,
            'expected': False
        },
        {
            'name': '排名靠后',
            'pct_change': 5.0,
            'net_amount': 60000000,
            'rank': 15,  # >10
            'limit_count': 4,
            'expected': False
        },
        {
            'name': '涨停数不足',
            'pct_change': 5.0,
            'net_amount': 60000000,
            'rank': 5,
            'limit_count': 2,  # <3
            'expected': False
        },
    ]
    
    all_passed = True
    
    for case in test_cases:
        condition1 = case['pct_change'] >= 3.0
        condition2 = case['net_amount'] >= 50000000
        condition3 = case['rank'] <= 10
        condition4 = case['limit_count'] >= 3
        
        result = condition1 and condition2 and condition3 and condition4
        passed = (result == case['expected'])
        
        status = "✅" if passed else "❌"
        print(f"{status} {case['name']}: 预期{case['expected']}, 实际{result}")
        
        if not passed:
            all_passed = False
            print(f"   条件: 涨幅{condition1}, 净流入{condition2}, 排名{condition3}, 涨停数{condition4}")
    
    if all_passed:
        print("✅ 热点板块阈值测试通过!")
    else:
        print("❌ 热点板块阈值测试失败")
    
    return all_passed

def test_unit_conversion():
    """测试单位转换"""
    print("\n📏 测试单位转换...")
    
    # 测试万元转元
    test_cases = [
        {'wan': 100.0, 'expected_yuan': 1000000.0},
        {'wan': 0.0, 'expected_yuan': 0.0},
        {'wan': 5000.0, 'expected_yuan': 50000000.0},  # 5000万元
    ]
    
    all_passed = True
    
    for case in test_cases:
        yuan = case['wan'] * 10000
        passed = abs(yuan - case['expected_yuan']) < 0.01
        
        status = "✅" if passed else "❌"
        print(f"{status} {case['wan']}万元 = {yuan:.0f}元 (预期: {case['expected_yuan']:.0f}元)")
        
        if not passed:
            all_passed = False
    
    if all_passed:
        print("✅ 单位转换测试通过!")
    else:
        print("❌ 单位转换测试失败")
    
    return all_passed

def main():
    """主测试函数"""
    print("="*60)
    print("T01策略 - 明日测试准备")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 配置文件检查")
    print("2. 筛选逻辑测试")
    print("3. 热点板块阈值测试")
    print("4. 单位转换测试")
    print("5. API接口测试 (需要网络)")
    
    print("\n⚠️  注意: 实际API测试需要:")
    print("  - 有效的tushare token")
    print("  - 网络连接")
    print("  - API调用权限")
    
    # 运行测试
    config = test_config()
    if not config:
        print("❌ 配置文件测试失败，终止测试")
        return False
    
    tests = [
        ("筛选逻辑", test_screening_logic),
        ("热点板块阈值", test_hot_sector_threshold),
        ("单位转换", test_unit_conversion),
    ]
    
    results = []
    
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
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed_count += 1
    
    print(f"\n📊 结果: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        print("🎉 所有离线测试通过!")
        print("\n📋 下一步:")
        print("1. 运行实际API测试: python3 test_v2.py")
        print("2. 检查筛选规则效果")
        print("3. 验证热点板块判断")
        return True
    else:
        print("⚠️  部分测试失败，请检查代码")
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