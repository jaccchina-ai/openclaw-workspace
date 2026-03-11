#!/usr/bin/env python3
"""
生成前10名候选股票的T日评分
"""
import sys
import pandas as pd
import tushare as ts
from datetime import datetime
import json
from pathlib import Path

def top10_t_day_scoring(trade_date="20260226", top_n=10):
    """前10名T日评分"""
    print(f"=== T日评分 ({trade_date}) - 前{top_n}名 ===")
    
    # Tushare token
    TOKEN = "870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab"
    pro = ts.pro_api(TOKEN)
    
    print("1. 获取涨停股列表...")
    limit_up_df = pro.limit_list_d(trade_date=trade_date, limit_type='U')
    print(f"   获取到 {len(limit_up_df)} 只涨停股")
    
    if limit_up_df.empty:
        print("⚠️  无涨停股数据")
        return []
    
    # 改进的评分规则
    print(f"2. 进行评分 (选取前{top_n}名)...")
    scored_stocks = []
    
    for idx, row in limit_up_df.iterrows():
        score = 0
        
        # 评分规则1: 封成比 (封单金额/成交金额) 越高越好
        fd_amount = row.get('fd_amount', 0)
        amount = row.get('amount', 1)
        if amount > 0:
            seal_ratio = fd_amount / amount
            score += min(seal_ratio * 10, 30)  # 最多30分
        
        # 评分规则2: 换手率适中 (3-15%较好)
        turnover_rate = row.get('turnover_rate', 0)
        if 3 <= turnover_rate <= 15:
            score += 20
        elif turnover_rate < 3:
            score += 10
        elif turnover_rate <= 25:
            score += 5
        
        # 评分规则3: 首次涨停时间越早越好
        first_time = row.get('first_time', '')
        if first_time:
            hour = int(first_time[:2]) if len(first_time) >= 2 else 15
            if hour <= 10:
                score += 25
            elif hour <= 11:
                score += 20
            elif hour <= 13:
                score += 15
            elif hour <= 14:
                score += 10
            else:
                score += 5
        
        # 评分规则4: 连板数越多越好 (limit_times)
        limit_times = row.get('limit_times', 1)
        score += min(limit_times * 5, 15)  # 最多15分
        
        # 评分规则5: 封单金额/流通市值 (fd_amount/float_mv)
        fd_amount_val = row.get('fd_amount', 0)
        float_mv = row.get('float_mv', 1)
        if float_mv > 0:
            fd_to_mv = fd_amount_val / float_mv
            score += min(fd_to_mv * 1000, 20)  # 最多20分
        
        scored_stocks.append({
            'ts_code': row['ts_code'],
            'name': row['name'],
            'industry': row.get('industry', ''),
            'total_score': round(score, 2),
            'seal_ratio': round(fd_amount / amount if amount > 0 else 0, 4),
            'turnover_rate': round(turnover_rate, 2),
            'first_time': first_time,
            'limit_times': limit_times,
            'fd_amount': fd_amount_val,
            'float_mv': float_mv,
            'amount': amount
        })
    
    # 按评分排序
    scored_stocks.sort(key=lambda x: x['total_score'], reverse=True)
    
    print(f"3. 评分完成，最高分: {scored_stocks[0]['total_score'] if scored_stocks else 0}")
    
    return scored_stocks[:top_n]  # 返回前top_n名

def save_candidates(candidates, t_date="20260226", t1_date="20260227"):
    """保存候选股票"""
    print(f"4. 保存候选股票 ({len(candidates)} 只)...")
    
    candidates_file = f"candidates_{t_date}_to_{t1_date}.json"
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    
    state_file = state_dir / candidates_file
    symlink_file = Path(candidates_file)
    
    # 备份旧文件
    if state_file.exists():
        backup_file = state_file.with_suffix('.json.backup')
        import shutil
        shutil.copy2(state_file, backup_file)
        print(f"📦 已备份旧文件: {backup_file}")
    
    # 保存数据
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump({
            "t_date": t_date,
            "t1_date": t1_date,
            "generated_at": datetime.now().isoformat(),
            "candidates_count": len(candidates),
            "candidates": candidates
        }, f, indent=2, ensure_ascii=False)
    
    # 创建符号链接
    if symlink_file.exists():
        symlink_file.unlink()
    try:
        symlink_file.symlink_to(state_file)
        print(f"💾 候选股票已保存: {state_file}")
        print(f"🔗 符号链接已创建: {symlink_file} -> {state_file}")
    except Exception as e:
        print(f"⚠️  创建符号链接失败: {e}")
    
    return state_file

def print_candidate_table(candidates):
    """打印候选股票表格"""
    print("\n" + "="*80)
    print(f"🎯 前{len(candidates)}名候选股票 (按评分排序)")
    print("="*80)
    print(f"{'排名':<4} {'股票代码':<10} {'股票名称':<10} {'行业':<12} {'评分':<8} {'封成比':<8} {'换手率':<6} {'连板':<4} {'首次涨停'}")
    print("-"*80)
    
    for i, stock in enumerate(candidates, 1):
        print(f"{i:<4} {stock['ts_code']:<10} {stock['name']:<10} "
              f"{stock['industry'][:10]:<12} {stock['total_score']:<8.2f} "
              f"{stock['seal_ratio']:<8.3f} {stock['turnover_rate']:<6.1f}% "
              f"{stock['limit_times']:<4} {stock['first_time']}")
    
    print("="*80)

def main():
    print("🚀 根据新配置重新生成候选股票 (前10名)")
    
    try:
        # 读取配置确认top_n值
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        top_n = config.get('strategy', {}).get('output', {}).get('top_n_candidates', 10)
        print(f"📋 配置文件中的候选股数量: {top_n}")
        
        # 执行评分 (取前10名)
        candidates = top10_t_day_scoring("20260226", top_n=top_n)
        
        if not candidates:
            print("❌ 未生成候选股票")
            return False
        
        # 打印表格
        print_candidate_table(candidates)
        
        # 保存结果
        save_candidates(candidates)
        
        print(f"\n✅ 候选股票重新生成完成！已保存前{len(candidates)}名候选股。")
        return True
        
    except Exception as e:
        print(f"❌ 重新生成候选股失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)