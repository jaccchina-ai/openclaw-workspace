#!/usr/bin/env python3
"""
测试LimitUpScoringStrategyV2
"""

import sys
import yaml
import pandas as pd
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 导入新策略类
sys.path.insert(0, '.')
from limit_up_strategy_new import LimitUpScoringStrategyV2

def test_basic():
    """基础测试"""
    print("🔍 测试LimitUpScoringStrategyV2...")
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化策略
    strategy = LimitUpScoringStrategyV2(config)
    print("✅ 策略初始化成功")
    
    # 测试数据获取
    test_date = '20240222'  # 有数据的日期
    print(f"\n📅 获取涨停股票数据 (日期: {test_date})...")
    
    limit_up_stocks = strategy.get_limit_up_stocks(test_date)
    print(f"✅ 获取到 {len(limit_up_stocks)} 只涨停股票")
    
    if limit_up_stocks.empty:
        print("❌ 没有涨停股票数据")
        return False
    
    # 显示前3只股票信息
    print("\n📋 前3只涨停股票信息:")
    for i in range(min(3, len(limit_up_stocks))):
        row = limit_up_stocks.iloc[i]
        print(f"\n#{i+1} {row['name']} ({row['ts_code']})")
        print(f"  涨幅: {row['pct_chg']:.2f}%")
        print(f"  封单金额: {row.get('fd_amount', 0):.0f}元")
        print(f"  成交金额: {row.get('amount', 0):.0f}元")
        print(f"  流通市值: {row.get('float_mv', 0):.0f}元")
        print(f"  换手率: {row.get('turnover_ratio', 0):.2f}%")
        
        # 计算封成比和封单/流通市值
        fd_amount = row.get('fd_amount', 0)
        amount = row.get('amount', 1)
        float_mv = row.get('float_mv', 1)
        
        seal_ratio = fd_amount / amount if amount > 0 else 0
        seal_to_mv = fd_amount / float_mv if float_mv > 0 else 0
        
        print(f"  封成比: {seal_ratio:.3f}")
        print(f"  封单/流通市值: {seal_to_mv:.6f}")
    
    # 测试评分 (只评前2只，避免耗时)
    print("\n🎯 测试评分功能 (前2只股票)...")
    test_stocks = limit_up_stocks.head(2).copy()
    
    # 简化测试：跳过耗时的历史数据计算
    # 临时修改策略，跳过某些API调用
    scored_stocks = strategy.calculate_t_day_score(test_stocks, test_date)
    
    if not scored_stocks.empty:
        print(f"✅ 成功评分 {len(scored_stocks)} 只股票")
        print("\n📊 评分结果:")
        for idx, row in scored_stocks.iterrows():
            print(f"\n{row['name']} ({row['ts_code']})")
            print(f"  总分: {row['total_score']:.1f}")
            print(f"  封成比: {row.get('seal_ratio', 0):.3f}")
            print(f"  封单/流通市值: {row.get('seal_to_mv', 0):.6f}")
            print(f"  换手率: {row.get('turnover_rate', 0):.2f}%")
            
            # 显示各维度分数
            details = row.get('score_details', {})
            if details:
                print("  各维度分数:")
                for key, score in details.items():
                    print(f"    {key}: {score:.1f}")
    else:
        print("❌ 评分失败")
        return False
    
    return True

def test_config():
    """测试配置"""
    print("\n⚙️ 检查配置...")
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查关键配置
    required = ['api', 'strategy']
    for req in required:
        if req not in config:
            print(f"❌ 缺失配置: {req}")
            return False
    
    print(f"✅ API Token: {config['api'].get('api_key', '')[:10]}...")
    
    # 检查评分权重
    t_day_weights = config['strategy'].get('t_day_scoring', {})
    if t_day_weights:
        print("✅ T日评分权重配置正常")
        for key, weight in t_day_weights.items():
            print(f"  {key}: {weight}")
    else:
        print("⚠️  T日评分权重未配置")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("T01策略V2测试")
    print("="*60)
    
    try:
        # 测试配置
        if not test_config():
            sys.exit(1)
        
        # 测试基础功能
        if test_basic():
            print("\n" + "="*60)
            print("✅ 测试通过!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ 测试失败")
            print("="*60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)