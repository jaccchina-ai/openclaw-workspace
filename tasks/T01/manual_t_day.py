#!/usr/bin/env python3
"""
手动T日评分脚本 - 简化版
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 配置简单日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def main():
    print("=== 手动T日评分 (2026-02-26) ===")
    
    try:
        # 导入策略
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        import yaml
        
        # 加载配置
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 创建策略实例
        strategy = LimitUpScoringStrategyV2(config)
        print("✅ 策略初始化完成")
        
        # 执行T日评分
        print("📊 开始T日涨停股评分...")
        
        # 1. 获取涨停股
        limit_up_stocks = strategy.get_limit_up_stocks(trade_date="20260226")
        print(f"📈 获取到 {len(limit_up_stocks) if limit_up_stocks is not None else 0} 只涨停股")
        
        # 2. 计算T日评分
        scored_stocks = strategy.calculate_t_day_score(limit_up_stocks, trade_date="20260226")
        print(f"📊 完成 {len(scored_stocks) if scored_stocks is not None else 0} 只股票评分")
        
        # 3. 获取前5名作为候选
        if scored_stocks is not None and not scored_stocks.empty:
            # 按总分排序
            scored_stocks = scored_stocks.sort_values('total_score', ascending=False)
            candidates = scored_stocks.head(5).to_dict('records')
        else:
            candidates = []
        
        print(f"✅ 评分完成！候选股票数量: {len(candidates)}")
        
        if candidates:
            print("\n🎯 前5名候选股票:")
            for i, stock in enumerate(candidates[:5], 1):
                print(f"{i}. {stock.get('ts_code', 'N/A')} - 评分: {stock.get('total_score', 0):.2f}")
        
        # 保存到文件
        import json
        import os
        from datetime import datetime
        
        t_date = "20260226"
        t1_date = "20260227"  # 明天
        
        candidates_file = f"candidates_{t_date}_to_{t1_date}.json"
        state_dir = Path("state")
        state_dir.mkdir(exist_ok=True)
        
        state_file = state_dir / candidates_file
        symlink_file = Path(candidates_file)
        
        # 保存到state目录
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
        symlink_file.symlink_to(state_file)
        
        print(f"💾 候选股票已保存: {state_file}")
        print(f"🔗 符号链接已创建: {symlink_file} -> {state_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 手动评分失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)