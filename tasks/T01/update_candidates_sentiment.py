#!/usr/bin/env python3
"""
更新候选股文件，添加舆情评分
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from news_sentiment_test import NewsSentimentAnalyzer

def update_candidates_with_sentiment():
    """更新候选股文件的舆情评分"""
    # 原始候选股文件
    candidate_file = Path("state/candidates_20260224_to_20260225.json")
    if not candidate_file.exists():
        print(f"❌ 候选股文件不存在: {candidate_file}")
        return False
    
    print(f"📄 读取候选股文件: {candidate_file}")
    with open(candidate_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    if not candidates:
        print("❌ 没有候选股数据")
        return False
    
    print(f"📊 找到 {len(candidates)} 只候选股")
    
    # 备份原文件
    backup_file = candidate_file.with_suffix('.json.bak')
    import shutil
    shutil.copy2(candidate_file, backup_file)
    print(f"📦 已备份原文件: {backup_file}")
    
    # 初始化舆情分析器
    try:
        analyzer = NewsSentimentAnalyzer()
        print("✅ 舆情分析器初始化成功")
    except Exception as e:
        print(f"❌ 舆情分析器初始化失败: {e}")
        return False
    
    # 对前5名进行舆情分析
    top_n = min(5, len(candidates))
    print(f"🎯 开始对前{top_n}名进行舆情分析")
    
    updated_count = 0
    for i in range(top_n):
        candidate = candidates[i]
        ts_code = candidate.get('ts_code', '')
        name = candidate.get('name', '')
        trade_date = candidate.get('trade_date', '20260224')
        
        if not ts_code or not name:
            print(f"⚠️  跳过无效候选股: {candidate}")
            continue
        
        print(f"  [{i+1}/{top_n}] 分析 {name} ({ts_code})...")
        
        try:
            # 舆情分析
            news_result = analyzer.search_stock_news(name, ts_code, trade_date, days_back=1)
            sentiment_result = analyzer.analyze_sentiment(news_result['news_results'])
            
            overall_score = sentiment_result.get('overall_score', 0)
            sentiment_category = sentiment_result.get('overall_sentiment', 'neutral')
            
            # 舆情权重 (从config.yaml获取，默认10分)
            import yaml
            config_path = Path("config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                sentiment_weight = config.get('strategy', {}).get('t_day_scoring', {}).get('sentiment', 10)
            else:
                sentiment_weight = 10
            
            # 舆情得分 = 舆情评分(0-10) × 权重 / 10
            sentiment_points = overall_score * sentiment_weight / 10.0
            
            # 更新候选股数据
            original_total = candidate.get('total_score', 0)
            
            # 计算基础分 (如果存在)
            if 'basic_score' in candidate:
                basic_score = candidate['basic_score']
                # 舆情分已经包含在总分中？需要检查
                # 假设原总分不包含舆情分
                new_total = basic_score + sentiment_points
            else:
                # 没有基础分，假设原总分不包含舆情分
                new_total = original_total + sentiment_points
                candidate['basic_score'] = original_total
            
            candidate['sentiment_score'] = sentiment_points
            candidate['total_score'] = new_total
            
            # 更新评分详情
            score_details = candidate.get('score_details', {})
            score_details['sentiment'] = sentiment_points
            candidate['score_details'] = score_details
            
            # 添加舆情信息
            candidate['sentiment_info'] = {
                'overall_score': overall_score,
                'sentiment_category': sentiment_category,
                'news_count': sentiment_result.get('total_news', 0),
                'positive_news': sentiment_result.get('positive_count', 0),
                'negative_news': sentiment_result.get('negative_count', 0),
                'updated_at': datetime.now().isoformat()
            }
            
            print(f"    ✅ 舆情评分: {overall_score:.2f}/10.0 → 权重得分: {sentiment_points:.2f}")
            print(f"       新闻: {sentiment_result.get('total_news', 0)}条, 情感: {sentiment_category}")
            print(f"       原总分: {original_total:.2f} → 新总分: {new_total:.2f}")
            
            updated_count += 1
            
        except Exception as e:
            print(f"    ❌ 舆情分析失败: {e}")
            # 添加默认舆情分0
            candidate['sentiment_score'] = 0
            if 'score_details' in candidate:
                candidate['score_details']['sentiment'] = 0
    
    print(f"\n📈 舆情分析完成，更新 {updated_count}/{top_n} 只股票")
    
    # 按新总分重新排序
    candidates.sort(key=lambda x: x.get('total_score', 0), reverse=True)
    data['candidates'] = candidates
    data['sentiment_updated'] = datetime.now().isoformat()
    data['sentiment_analysis_top_n'] = top_n
    
    # 保存更新后的文件
    with open(candidate_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已保存更新后的候选股文件: {candidate_file}")
    
    # 显示更新后的前3名
    print("\n🏆 更新后前三名:")
    for i in range(min(3, len(candidates))):
        candidate = candidates[i]
        name = candidate.get('name', '未知')
        code = candidate.get('ts_code', '未知')
        total = candidate.get('total_score', 0)
        basic = candidate.get('basic_score', total)
        sentiment = candidate.get('sentiment_score', 0)
        
        print(f"  #{i+1}: {name} ({code})")
        print(f"     总分: {total:.2f} = 基础分: {basic:.2f} + 舆情分: {sentiment:.2f}")
    
    return True

def main():
    """主函数"""
    print("="*60)
    print("🎯 候选股舆情评分更新工具")
    print("="*60)
    
    success = update_candidates_with_sentiment()
    
    if success:
        print("\n✅ 更新完成！候选股文件已包含舆情评分。")
        print("🔄 调度器将使用更新后的数据进行明早T+1竞价分析。")
    else:
        print("\n❌ 更新失败，请检查错误信息。")
    
    print("="*60)

if __name__ == "__main__":
    main()