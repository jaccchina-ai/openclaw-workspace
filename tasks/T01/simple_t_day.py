#!/usr/bin/env python3
"""
极简T日评分 - 直接调用Tushare API
"""
import sys
import pandas as pd
import tushare as ts
from datetime import datetime
import json
from pathlib import Path

def simple_t_day_scoring(trade_date="20260226"):
    """极简T日评分"""
    print(f"=== 极简T日评分 ({trade_date}) ===")
    
    # Tushare token
    TOKEN = "870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab"
    pro = ts.pro_api(TOKEN)
    
    print("1. 获取涨停股列表...")
    limit_up_df = pro.limit_list_d(trade_date=trade_date, limit_type='U')
    print(f"   获取到 {len(limit_up_df)} 只涨停股")
    
    if limit_up_df.empty:
        print("⚠️  无涨停股数据")
        return []
    
    # 简单评分规则
    print("2. 进行极简评分...")
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
        
        scored_stocks.append({
            'ts_code': row['ts_code'],
            'name': row['name'],
            'industry': row.get('industry', ''),
            'total_score': round(score, 2),
            'seal_ratio': round(fd_amount / amount if amount > 0 else 0, 4),
            'turnover_rate': round(turnover_rate, 2),
            'first_time': first_time
        })
    
    # 按评分排序
    scored_stocks.sort(key=lambda x: x['total_score'], reverse=True)
    
    print(f"3. 评分完成，最高分: {scored_stocks[0]['total_score'] if scored_stocks else 0}")
    
    return scored_stocks[:5]  # 返回前5名

def save_candidates(candidates, t_date="20260226", t1_date="20260227"):
    """保存候选股票"""
    print("4. 保存候选股票...")
    
    candidates_file = f"candidates_{t_date}_to_{t1_date}.json"
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    
    state_file = state_dir / candidates_file
    symlink_file = Path(candidates_file)
    
    # 保存数据
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump({
            "t_date": t_date,
            "t1_date": t1_date,
            "generated_at": datetime.now().isoformat(),
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

def main():
    print("🚀 开始手动完成今晚选股")
    
    try:
        # 执行极简评分
        candidates = simple_t_day_scoring("20260226")
        
        if not candidates:
            print("❌ 未生成候选股票")
            return False
        
        print("\n🎯 生成的候选股票:")
        for i, stock in enumerate(candidates, 1):
            print(f"{i}. {stock['ts_code']} {stock['name']} - 评分: {stock['total_score']}")
            print(f"   封成比: {stock['seal_ratio']}, 换手率: {stock['turnover_rate']}%, 首次涨停: {stock['first_time']}")
        
        # 保存结果
        save_candidates(candidates)
        
        print("\n✅ 手动选股完成！")
        return True
        
    except Exception as e:
        print(f"❌ 手动选股失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)