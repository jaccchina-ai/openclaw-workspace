#!/usr/bin/env python3
"""
快速T日评分 - 基于2月13日数据，生成候选股票
"""

import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime

# 禁用详细日志
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('tushare').setLevel(logging.WARNING)

def main():
    print("🚀 快速T日评分 (基于2月13日数据)")
    print("="*50)
    
    try:
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 导入策略类
        sys.path.insert(0, '.')
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        # 初始化策略
        print("初始化策略...")
        strategy = LimitUpScoringStrategyV2(config)
        
        # T日: 2月13日 (交易日)
        t_date = '20260213'
        
        print(f"获取涨停股票 (日期: {t_date})...")
        
        # 获取涨停股票 (限制数量)
        limit_up_stocks = strategy.get_limit_up_stocks(t_date)
        
        if limit_up_stocks.empty:
            print("❌ 没有涨停股票")
            return False
        
        print(f"✅ 获取到 {len(limit_up_stocks)} 只涨停股票")
        
        # 只取前10只进行评分
        score_count = min(10, len(limit_up_stocks))
        print(f"评分前{score_count}只股票...")
        
        scored_stocks = strategy.calculate_t_day_score(limit_up_stocks.head(score_count), t_date)
        
        if scored_stocks.empty:
            print("❌ 评分失败")
            return False
        
        print(f"✅ 成功评分 {len(scored_stocks)} 只股票")
        
        # 选择前3名候选
        top_n = min(3, len(scored_stocks))
        candidates = scored_stocks.head(top_n)
        
        print(f"\n🎖️  T日候选股票 (前{top_n}名):")
        print("="*50)
        
        candidates_list = []
        
        for i in range(top_n):
            stock = candidates.iloc[i]
            name = stock.get('name', '未知')
            code = stock.get('ts_code', '未知')
            total_score = float(stock.get('total_score', 0))
            
            # 收集关键指标
            candidate_data = {
                'name': str(name),
                'ts_code': str(code),
                'total_score': total_score,
                't_day_score': total_score,  # 用于T+1消息
                'pct_chg': float(stock.get('pct_chg', 0)),
                'first_time': str(stock.get('first_time', '')),
                'fd_amount': float(stock.get('fd_amount', 0)),
                'amount': float(stock.get('amount', 0)),
                'float_mv': float(stock.get('float_mv', 0)),
                'turnover_ratio': float(stock.get('turnover_ratio', 0)),
                'is_hot_sector': bool(stock.get('is_hot_sector', False)),
                'industry': str(stock.get('industry', '')),
                'first_limit_time_score': float(stock.get('first_limit_time_score', 0)),
                'order_quality_score': float(stock.get('order_quality_score', 0)),
                'liquidity_score': float(stock.get('liquidity_score', 0)),
                'money_flow_score': float(stock.get('money_flow_score', 0)),
                'sector_score': float(stock.get('sector_score', 0)),
                'dragon_list_score': float(stock.get('dragon_list_score', 0))
            }
            
            # 计算衍生指标
            amount = candidate_data['amount']
            float_mv = candidate_data['float_mv']
            fd_amount = candidate_data['fd_amount']
            
            candidate_data['seal_ratio'] = fd_amount / amount if amount > 0 else 0.0
            candidate_data['seal_to_mv'] = fd_amount / float_mv if float_mv > 0 else 0.0
            
            candidates_list.append(candidate_data)
            
            # 显示
            print(f"\n#{i+1} {name} ({code})")
            print(f"  总分: {total_score:.1f}")
            print(f"  涨幅: {candidate_data['pct_chg']}% | 行业: {candidate_data['industry']}")
            
            if candidate_data['first_time']:
                try:
                    time_str = f"{candidate_data['first_time'][:2]}:{candidate_data['first_time'][2:4]}:{candidate_data['first_time'][4:6]}"
                    print(f"  首次涨停: {time_str}")
                except:
                    print(f"  首次涨停: {candidate_data['first_time']}")
            
            print(f"  封成比: {candidate_data['seal_ratio']:.3f}")
            print(f"  封单/流通: {candidate_data['seal_to_mv']*10000:.2f}bp")
            print(f"  换手率: {candidate_data['turnover_ratio']:.2f}%")
            print(f"  热点板块: {'是' if candidate_data['is_hot_sector'] else '否'}")
        
        # 保存候选股票
        state_dir = Path("state")
        state_dir.mkdir(exist_ok=True)
        
        # 获取T+1日 (2月24日，节后第一个交易日)
        t1_date = '20260224'
        
        result = {
            'success': True,
            'trade_date': t_date,
            't1_date': t1_date,
            'generated_at': datetime.now().isoformat(),
            'candidates': candidates_list,
            'summary': {
                'total_limit_up': int(len(limit_up_stocks)),
                'total_scored': int(len(scored_stocks)),
                'top_n_selected': top_n,
                'top_score': float(candidates.iloc[0]['total_score']) if top_n > 0 else 0.0
            }
        }
        
        filename = state_dir / f"candidates_{t_date}_to_{t1_date}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 候选股票已保存: {filename}")
        print(f"📅 T+1日: {t1_date} (用于2月24日竞价测试)")
        
        # 显示消息格式示例
        print(f"\n📋 消息推送指标示例:")
        print("="*50)
        print(f"股票: {candidates_list[0]['name']} ({candidates_list[0]['ts_code']})")
        print(f"  总分: {candidates_list[0]['total_score']:.1f}")
        print(f"  涨停涨幅: {candidates_list[0]['pct_chg']}%")
        print(f"  首次涨停时间: {candidates_list[0]['first_time']}")
        print(f"  封成比: {candidates_list[0]['seal_ratio']:.3f}")
        print(f"  封单/流通市值: {candidates_list[0]['seal_to_mv']*10000:.2f}bp")
        print(f"  换手率: {candidates_list[0]['turnover_ratio']:.2f}%")
        print(f"  热点板块: {'是' if candidates_list[0]['is_hot_sector'] else '否'}")
        print(f"  行业: {candidates_list[0]['industry']}")
        
        print(f"\n✅ T日评分完成! 候选股票已保存，准备用于2月24日竞价测试")
        
        return True
        
    except Exception as e:
        print(f"❌ T日评分失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)