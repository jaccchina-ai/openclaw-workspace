#!/usr/bin/env python3
"""
手动运行T日评分任务 - 基于2月13日数据
生成候选股票列表，为2月24日实时测试做准备
"""

import sys
import yaml
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.WARNING)

def main():
    print("🚀 手动运行T日评分任务 (基于2月13日数据)")
    print("="*60)
    
    try:
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 导入策略类
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        # 初始化策略
        strategy = LimitUpScoringStrategyV2(config)
        
        # T日: 2月13日 (交易日)
        t_date = '20260213'
        
        print(f"📈 获取涨停股票 (日期: {t_date})...")
        
        # 获取涨停股票
        limit_up_stocks = strategy.get_limit_up_stocks(t_date)
        
        if limit_up_stocks.empty:
            print("❌ 没有涨停股票")
            return False
        
        print(f"✅ 获取到 {len(limit_up_stocks)} 只涨停股票")
        
        # 显示涨停股票信息
        print(f"\n📋 涨停股票统计:")
        print(f"  总数量: {len(limit_up_stocks)}")
        
        # 按行业统计
        if 'industry' in limit_up_stocks.columns:
            industry_counts = limit_up_stocks['industry'].value_counts().head(5)
            print(f"  热门行业 (前5):")
            for industry, count in industry_counts.items():
                print(f"    {industry}: {count}只")
        
        # 计算评分 (只评分前15只，加快速度)
        max_score = min(15, len(limit_up_stocks))
        print(f"\n📊 开始评分 (前{max_score}只)...")
        
        scored_stocks = strategy.calculate_t_day_score(limit_up_stocks.head(max_score), t_date)
        
        if scored_stocks.empty:
            print("❌ 评分失败")
            return False
        
        print(f"✅ 成功评分 {len(scored_stocks)} 只股票")
        
        # 选择前5名候选
        top_n = config['strategy']['output'].get('top_n_candidates', 5)
        candidates = scored_stocks.head(top_n).copy()
        
        print(f"\n🎖️  T日候选股票 (前{top_n}名):")
        print("="*60)
        
        # 保存详细候选信息
        candidates_details = []
        
        for i in range(len(candidates)):
            stock = candidates.iloc[i]
            name = stock.get('name', '未知')
            code = stock.get('ts_code', '未知')
            total_score = stock.get('total_score', 0)
            
            # 收集详细指标
            details = {
                'name': name,
                'ts_code': code,
                'total_score': total_score,
                'pct_chg': stock.get('pct_chg', 0),
                'first_time': stock.get('first_time', ''),
                'fd_amount': stock.get('fd_amount', 0),
                'amount': stock.get('amount', 0),
                'float_mv': stock.get('float_mv', 0),
                'turnover_ratio': stock.get('turnover_ratio', 0),
                'is_hot_sector': stock.get('is_hot_sector', False),
                'industry': stock.get('industry', ''),
                'first_limit_time_score': stock.get('first_limit_time_score', 0),
                'order_quality_score': stock.get('order_quality_score', 0),
                'liquidity_score': stock.get('liquidity_score', 0),
                'money_flow_score': stock.get('money_flow_score', 0),
                'sector_score': stock.get('sector_score', 0),
                'dragon_list_score': stock.get('dragon_list_score', 0)
            }
            
            # 计算衍生指标
            if details['amount'] > 0:
                details['seal_ratio'] = details['fd_amount'] / details['amount']
            else:
                details['seal_ratio'] = 0
            
            if details['float_mv'] > 0:
                details['seal_to_mv'] = details['fd_amount'] / details['float_mv']
            else:
                details['seal_to_mv'] = 0
            
            # 确保所有值都是JSON可序列化的
            cleaned_details = {}
            for key, value in details.items():
                if pd.isna(value):  # 处理NaN值
                    cleaned_details[key] = None
                elif isinstance(value, (bool, np.bool_)):
                    cleaned_details[key] = bool(value)  # 转换numpy bool为Python bool
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    cleaned_details[key] = int(value)  # 转换numpy整数为Python整数
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    cleaned_details[key] = float(value)  # 转换numpy浮点数为Python浮点数
                else:
                    cleaned_details[key] = value
            
            candidates_details.append(cleaned_details)
            
            # 显示
            print(f"\n#{i+1} {name} ({code}) - 总分: {total_score:.1f}")
            print(f"  涨幅: {details['pct_chg']}% | 行业: {details['industry']}")
            
            if details['first_time']:
                try:
                    time_str = f"{details['first_time'][:2]}:{details['first_time'][2:4]}:{details['first_time'][4:6]}"
                    print(f"  首次涨停: {time_str}")
                except:
                    print(f"  首次涨停: {details['first_time']}")
            
            print(f"  封成比: {details['seal_ratio']:.3f} | 封单/流通: {details['seal_to_mv']*10000:.2f}bp")
            print(f"  换手率: {details['turnover_ratio']:.2f}%")
            print(f"  热点板块: {'是' if details['is_hot_sector'] else '否'}")
            
            # 评分详情
            print(f"  评分详情: 涨停时间({details['first_limit_time_score']:.1f}) + "
                  f"封单质量({details['order_quality_score']:.1f}) + "
                  f"流动性({details['liquidity_score']:.1f}) + "
                  f"资金流({details['money_flow_score']:.1f}) + "
                  f"热点板块({details['sector_score']:.1f}) + "
                  f"龙虎榜({details['dragon_list_score']:.1f})")
        
        # 保存候选股票
        state_dir = Path("state")
        state_dir.mkdir(exist_ok=True)
        
        # 获取T+1日日期
        try:
            t1_date = strategy._get_next_trading_day(t_date)
            if not t1_date:
                # 如果无法获取，使用2月24日作为节后第一个交易日
                t1_date = '20260224'
        except Exception as e:
            print(f"⚠️  获取T+1日失败: {e}")
            t1_date = '20260224'
        
        result = {
            'success': True,
            'trade_date': t_date,
            't1_date': t1_date,
            'generated_at': datetime.now().isoformat(),
            'candidates': candidates_details,
            'summary': {
                'total_limit_up': len(limit_up_stocks),
                'total_scored': len(scored_stocks),
                'top_n_selected': len(candidates),
                'top_score': candidates.iloc[0]['total_score'] if not candidates.empty else 0
            }
        }
        
        filename = state_dir / f"candidates_{t_date}_to_{t1_date}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 候选股票已保存: {filename}")
        print(f"📅 T+1日: {t1_date} (用于2月24日竞价测试)")
        
        # 生成简单消息预览
        print(f"\n📋 消息推送预览 (简化版):")
        print("="*40)
        
        # 简单显示，不调用复杂的scheduler
        print(f"📊 **T01策略候选股票 - {t_date}**")
        print("="*40)
        print(f"**市场状况**: 正常 (基于{t_date}数据)")
        print(f"**风险等级**: 待评估")
        print(f"**建议**: 等待2月24日竞价测试")
        print("="*40)
        
        print(f"**🎯 候选股票 ({len(candidates_details)}只)**")
        for i, details in enumerate(candidates_details, 1):
            print(f"\n#{i} **{details['name']}** ({details['ts_code']})")
            print(f"  评分: {details['total_score']:.1f}")
            print(f"  涨幅: {details['pct_chg']}% | 行业: {details['industry']}")
            
            if details['first_time']:
                try:
                    time_str = f"{details['first_time'][:2]}:{details['first_time'][2:4]}:{details['first_time'][4:6]}"
                    print(f"  首次涨停: {time_str}")
                except:
                    print(f"  首次涨停: {details['first_time']}")
            
            print(f"  封成比: {details['seal_ratio']:.3f} | 封单/流通: {details['seal_to_mv']*10000:.2f}bp")
            print(f"  换手率: {details['turnover_ratio']:.2f}%")
            print(f"  热点板块: {'是' if details['is_hot_sector'] else '否'}")
            
            # 显示各维度评分
            print(f"  评分详情:")
            print(f"    涨停时间: {details['first_limit_time_score']:.1f}")
            print(f"    封单质量: {details['order_quality_score']:.1f}")
            print(f"    流动性: {details['liquidity_score']:.1f}")
            print(f"    资金流: {details['money_flow_score']:.1f}")
            print(f"    热点板块: {details['sector_score']:.1f}")
            print(f"    龙虎榜: {details['dragon_list_score']:.1f}")
        
        print("\n" + "="*40)
        print("**📋 注意事项**")
        print("1. 以上为T日评分结果，基于2月13日数据")
        print("2. 等待2月24日竞价测试验证")
        print("3. 实际操作需结合竞价数据重新评分")
        print("\n**⏰ 数据来源**: 历史数据分析")
        
        print(f"\n✅ T日评分任务完成!")
        print(f"   候选股票已保存，准备用于2月24日竞价测试")
        
        return True
        
    except Exception as e:
        print(f"❌ T日评分任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)