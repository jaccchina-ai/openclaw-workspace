#!/usr/bin/env python3
"""
T01系统机器学习集成演示
展示数据存储、胜率统计、机器学习优化的完整流程
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主演示函数"""
    print("="*70)
    print("🤖 T01系统机器学习集成演示")
    print("="*70)
    print("演示功能:")
    print("1. 📊 数据存储模块 - 本地化存储选股数据")
    print("2. 📈 绩效跟踪模块 - 统计胜率和绩效指标")
    print("3. 🤖 机器学习模块 - 因子优化和自我进化")
    print("4. 🔄 完整工作流程 - 从选股到优化的闭环")
    print("="*70)
    
    try:
        # 1. 初始化模块
        print("\n1️⃣ 初始化系统模块...")
        from data_storage import T01DataStorage
        from performance_tracker import PerformanceTracker
        from machine_learning import T01MachineLearning
        
        storage = T01DataStorage()
        tracker = PerformanceTracker()
        ml = T01MachineLearning()
        
        print("✅ 模块初始化完成")
        
        # 2. 演示数据存储
        print("\n2️⃣ 演示数据存储功能...")
        
        # 检查现有数据
        print("📊 检查现有数据...")
        factors_df = storage.get_factor_data()
        if not factors_df.empty:
            print(f"✅ 数据库中有 {len(factors_df)} 个因子")
            print("   权重最高的5个因子:")
            top_factors = factors_df.sort_values('weight', ascending=False).head(5)
            for _, row in top_factors.iterrows():
                print(f"     {row['factor_name']}: {row['weight']:.1f}")
        else:
            print("⚠️  数据库中没有因子数据")
        
        # 3. 演示绩效跟踪
        print("\n3️⃣ 演示绩效跟踪功能...")
        
        # 计算绩效统计
        print("📈 计算绩效统计...")
        performance = tracker.calculate_portfolio_performance()
        
        if performance.get('summary', {}).get('total_trades', 0) > 0:
            summary = performance['summary']
            print(f"✅ 绩效统计完成:")
            print(f"   总交易: {summary['total_trades']}")
            print(f"   胜率: {summary['win_rate_pct']:.1f}%")
            print(f"   平均收益率: {summary['avg_return_pct']:.2f}%")
            print(f"   盈亏因子: {summary['profit_factor']:.2f}")
        else:
            print("⚠️  暂无完成交易的记录，跳过绩效统计")
        
        # 生成绩效报告
        print("\n📋 生成绩效报告...")
        report = tracker.generate_performance_report()
        print(report[:500] + "..." if len(report) > 500 else report)
        
        # 4. 演示机器学习优化
        print("\n4️⃣ 演示机器学习优化功能...")
        
        # 检查数据充足性
        print("🔍 检查数据充足性...")
        sufficient, message = ml.check_data_sufficiency()
        print(f"   数据充足: {'✅ 是' if sufficient else '❌ 否'}")
        print(f"   详情: {message}")
        
        if sufficient:
            # 分析因子重要性
            print("\n🔬 分析因子重要性...")
            factor_result = ml.analyze_factor_importance()
            
            if factor_result.get('success'):
                print("✅ 因子重要性分析完成")
                if 'feature_importance' in factor_result:
                    print("   最重要的5个因子:")
                    for factor, importance in list(factor_result['feature_importance'].items())[:5]:
                        print(f"     {factor}: {importance:.4f}")
            else:
                print(f"⚠️  因子重要性分析失败: {factor_result.get('message', '未知错误')}")
            
            # 发现新因子
            print("\n🔎 尝试发现新因子...")
            discovery_result = ml.discover_new_factors()
            
            if discovery_result.get('success'):
                print(f"✅ 发现 {discovery_result.get('new_factors_saved', 0)} 个新因子")
            else:
                print(f"⚠️  因子发现失败: {discovery_result.get('message', '未知错误')}")
            
            # 生成优化报告
            print("\n📋 生成优化报告...")
            optimization_report = ml.generate_optimization_report()
            print(optimization_report[:600] + "..." if len(optimization_report) > 600 else optimization_report)
        
        # 5. 完整工作流程演示
        print("\n5️⃣ 完整工作流程演示...")
        
        # 模拟一个交易流程
        print("🔄 模拟交易流程:")
        print("  1. T日涨停股评分 → 生成候选股票")
        print("  2. T+1竞价分析 → 生成买入推荐")
        print("  3. T+2卖出 → 记录交易结果")
        print("  4. 绩效统计 → 计算胜率")
        print("  5. 机器学习优化 → 改进策略")
        
        # 演示如何手动记录交易
        print("\n📝 演示如何手动记录交易:")
        
        # 创建一个模拟推荐记录
        test_recommendation = {
            'trade_date': '20260224',
            't1_date': '20260225',
            'ts_code': '000859.SZ',
            'name': '国风新材',
            'total_score': 151.0,
            't_day_score': 151.0,
            'auction_score': 85.5,
            'auction_data': {
                'open_change_pct': 2.5,
                'data_source': 'realtime'
            },
            'seal_ratio': 0.043,
            'seal_to_mv': 0.00707,
            'turnover_ratio': 0.0,
            'is_hot_sector': False,
            'pct_chg': 10.02
        }
        
        try:
            # 保存推荐记录
            rec_id = storage.save_recommendation(test_recommendation)
            print(f"  ✅ 保存推荐记录: {rec_id}")
            
            # 记录买入交易
            buy_trade = {
                'trade_type': 'buy',
                'trade_date': '20260225',
                'trade_time': '09:30',
                'price': 10.25,
                'quantity': 1000,
                'notes': 'T+1开盘买入',
                'status': 'completed'
            }
            
            buy_id = storage.record_trade(rec_id, buy_trade)
            print(f"  ✅ 记录买入交易: {buy_id} @ 10.25元")
            
            # 记录卖出交易
            sell_trade = {
                'trade_type': 'sell',
                'trade_date': '20260226',
                'trade_time': '15:00',
                'price': 10.75,
                'quantity': 1000,
                'notes': 'T+2收盘卖出',
                'status': 'completed'
            }
            
            sell_id = storage.record_trade(rec_id, sell_trade)
            print(f"  ✅ 记录卖出交易: {sell_id} @ 10.75元")
            
            # 计算绩效
            perf_data = {
                'buy_date': '20260225',
                'buy_price': 10.25,
                'sell_date': '20260226',
                'sell_price': 10.75,
                'holding_days': 1,
                'return_pct': 4.88,  # (10.75-10.25)/10.25*100
                'win_loss': 1,  # 盈利
                'max_drawdown': 0.5,
                'sharpe_ratio': 2.5
            }
            
            perf_id = storage.record_performance(rec_id, perf_data)
            print(f"  ✅ 记录绩效数据: {perf_id} (收益率: 4.88%)")
            
            print("\n🎯 交易流程演示完成!")
            print("   买入价: 10.25元, 卖出价: 10.75元, 收益率: 4.88%")
            
        except Exception as e:
            print(f"  ⚠️  模拟交易失败: {e}")
        
        # 6. 系统维护演示
        print("\n6️⃣ 系统维护功能演示...")
        
        # 数据库备份
        print("💾 数据库备份...")
        try:
            storage.backup_database()
            print("  ✅ 数据库备份完成")
        except Exception as e:
            print(f"  ⚠️  备份失败: {e}")
        
        # 数据清理
        print("🧹 数据清理...")
        try:
            storage.cleanup_old_data()
            print("  ✅ 旧数据清理完成")
        except Exception as e:
            print(f"  ⚠️  清理失败: {e}")
        
        # 7. 总结和后续步骤
        print("\n" + "="*70)
        print("🎉 演示完成!")
        print("="*70)
        
        print("\n📋 已演示的核心功能:")
        print("  ✅ 数据存储 - 本地化存储交易数据")
        print("  ✅ 绩效跟踪 - 胜率统计和绩效分析")
        print("  ✅ 机器学习 - 因子优化和自我进化")
        print("  ✅ 系统维护 - 备份和清理")
        
        print("\n🚀 后续操作建议:")
        print("  1. 运行T01策略积累真实交易数据")
        print("  2. 当数据达到100条时，启动机器学习优化")
        print("  3. 定期查看绩效报告，监控策略表现")
        print("  4. 使用机器学习发现的因子改进策略")
        
        print("\n🔧 可用命令:")
        print("  # 查看绩效报告")
        print("  python performance_tracker.py")
        print("\n  # 运行机器学习优化")
        print("  python machine_learning.py --generate-report")
        print("\n  # 分析因子重要性")
        print("  python machine_learning.py --analyze-factors")
        print("\n  # 发现新因子")
        print("  python machine_learning.py --discover-factors")
        
        print("\n📈 胜率统计标准:")
        print("  T+1日开盘价买入，T+2日收盘价卖出后有盈利算成功")
        print("  最少需要20笔交易才开始统计，95%置信区间")
        
        print("\n🤖 机器学习优化目标:")
        print("  1. 最大化胜率")
        print("  2. 最大化夏普比率")
        print("  3. 最小化最大回撤")
        print("  4. 自动发现有效因子")
        
        print("\n🔄 自我进化周期: 每30天自动优化一次")
        
        print("\n" + "="*70)
        print("💡 提示: 系统现在可以自动学习并改进策略!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())