#!/usr/bin/env python3
"""
为T01候选股运行舆情分析
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# 导入舆情分析模块
sys.path.insert(0, str(Path(__file__).parent))
from news_sentiment_test import NewsSentimentAnalyzer

def load_candidates() -> List[Dict[str, Any]]:
    """加载候选股票"""
    candidates_file = Path("state/candidates_20260224_to_20260225.json")
    if not candidates_file.exists():
        print(f"错误: 候选股文件不存在: {candidates_file}")
        return []
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('candidates', [])

def analyze_stock_sentiment(analyzer: NewsSentimentAnalyzer, stock: Dict[str, Any]) -> Dict[str, Any]:
    """分析单只股票的舆情"""
    name = stock.get('name', '未知')
    code = stock.get('ts_code', '未知')
    trade_date = stock.get('trade_date', '20260224')
    
    print(f"📊 分析 {name} ({code})...")
    
    try:
        # 搜索新闻 (回溯2天)
        news_result = analyzer.search_stock_news(name, code, trade_date, days_back=2)
        
        # 情感分析
        sentiment_result = analyzer.analyze_sentiment(news_result['news_results'])
        
        # 计算舆情评分 (0-10分)
        # 基于: 新闻数量、情感得分、相关新闻比例
        total_news = news_result['total_news_count']
        pos_count = sentiment_result.get('positive_count', 0)
        neg_count = sentiment_result.get('negative_count', 0)
        neutral_count = sentiment_result.get('neutral_count', 0)
        
        # 相关新闻 (相关性评分>0.1)
        relevant_news = [
            n for n in news_result['news_results'] 
            if n.get('relevance_score', 0) > 0.1
        ]
        
        # 舆情评分逻辑
        sentiment_score = 0
        if total_news > 0:
            # 基础分: 有新闻关注度
            sentiment_score += 2.0
            
            # 正面新闻加分
            if pos_count > 0:
                sentiment_score += min(pos_count * 1.0, 3.0)
            
            # 相关新闻加分
            if len(relevant_news) > 0:
                sentiment_score += min(len(relevant_news) * 0.5, 3.0)
            
            # 负面新闻扣分
            if neg_count > 0:
                sentiment_score -= min(neg_count * 1.5, 4.0)
        
        # 限制在0-10分
        sentiment_score = max(0, min(sentiment_score, 10))
        
        return {
            'stock_name': name,
            'stock_code': code,
            'trade_date': trade_date,
            'total_news': total_news,
            'positive_news': pos_count,
            'negative_news': neg_count,
            'neutral_news': neutral_count,
            'relevant_news': len(relevant_news),
            'sentiment_score': round(sentiment_score, 2),
            'sentiment_summary': sentiment_result.get('overall_sentiment', 'neutral'),
            'news_samples': relevant_news[:3],  # 取前3条相关新闻
            'search_queries': news_result.get('search_queries', []),
            'success': True
        }
        
    except Exception as e:
        print(f"❌ 分析 {name} ({code}) 失败: {e}")
        return {
            'stock_name': name,
            'stock_code': code,
            'trade_date': trade_date,
            'error': str(e),
            'success': False
        }

def generate_report(results: List[Dict[str, Any]]) -> str:
    """生成舆情分析报告"""
    report_parts = []
    report_parts.append("📰 **T01候选股舆情分析报告 (2026-02-24)**")
    report_parts.append("="*50)
    report_parts.append("")
    
    successful_results = [r for r in results if r.get('success')]
    failed_results = [r for r in results if not r.get('success')]
    
    # 汇总统计
    if successful_results:
        total_news = sum(r.get('total_news', 0) for r in successful_results)
        avg_sentiment = sum(r.get('sentiment_score', 0) for r in successful_results) / len(successful_results)
        
        report_parts.append("📊 **汇总统计**")
        report_parts.append(f"分析股票: {len(successful_results)} 只")
        report_parts.append(f"总新闻数: {total_news} 条")
        report_parts.append(f"平均舆情评分: {avg_sentiment:.2f}/10.0")
        report_parts.append("")
    
    # 每只股票详情
    report_parts.append("🎯 **详细分析**")
    report_parts.append("")
    
    for i, result in enumerate(successful_results, 1):
        name = result['stock_name']
        code = result['stock_code']
        total = result['total_news']
        pos = result['positive_news']
        neg = result['negative_news']
        rel = result['relevant_news']
        score = result['sentiment_score']
        sentiment = result['sentiment_summary']
        
        report_parts.append(f"### #{i} {name} ({code})")
        report_parts.append(f"**舆情评分**: {score}/10.0 | **情感倾向**: {sentiment}")
        report_parts.append(f"**新闻统计**: 总数{total}条 | 正面{pos}条 | 负面{neg}条 | 相关{rel}条")
        
        # 相关新闻示例
        if result.get('news_samples'):
            report_parts.append("**相关新闻示例**:")
            for j, news in enumerate(result['news_samples'][:2], 1):
                title = news.get('title', '无标题')
                url = news.get('url', '')
                relevance = news.get('relevance_score', 0) * 100
                
                # 缩短标题
                if len(title) > 60:
                    title = title[:57] + "..."
                
                report_parts.append(f"  {j}. {title}")
                if url:
                    report_parts.append(f"     [链接]({url}) ({relevance:.0f}%相关)")
        else:
            report_parts.append("**相关新闻**: 无")
        
        report_parts.append("")
    
    # 失败分析
    if failed_results:
        report_parts.append("❌ **分析失败**")
        for result in failed_results:
            report_parts.append(f"- {result['stock_name']} ({result['stock_code']}): {result.get('error', '未知错误')}")
        report_parts.append("")
    
    # 局限性说明
    report_parts.append("⚠️ **局限性说明**")
    report_parts.append("1. **新闻相关性**: Tavily返回大量英文新闻，中文关键词匹配度低")
    report_parts.append("2. **情感分析**: 基于简单关键词匹配，对英文新闻无效")
    report_parts.append("3. **时间范围**: 仅回溯2天，可能遗漏早期新闻")
    report_parts.append("4. **查询优化**: 需要添加中文过滤和更精准查询词")
    report_parts.append("")
    
    # 建议
    report_parts.append("💡 **优化建议**")
    report_parts.append("1. **查询优化**: 添加'中国'、'A股'、'沪市'、'深市'等限定词")
    report_parts.append("2. **语言过滤**: 优先中文新闻源或添加语言检测")
    report_parts.append("3. **NLP升级**: 使用深度学习模型进行情感分析")
    report_parts.append("4. **集成方案**: 作为T01独立模块，权重可配置 (建议5-15分)")
    report_parts.append("")
    
    report_parts.append("⏰ **生成时间**: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    
    return "\n".join(report_parts)

def main():
    """主函数"""
    print("🚀 开始T01候选股舆情分析")
    
    # 加载候选股
    candidates = load_candidates()
    if not candidates:
        print("❌ 无候选股数据，退出")
        return
    
    print(f"📈 找到 {len(candidates)} 只候选股")
    
    # 初始化舆情分析器
    try:
        analyzer = NewsSentimentAnalyzer()
    except Exception as e:
        print(f"❌ 初始化舆情分析器失败: {e}")
        return
    
    # 分析每只股票
    results = []
    for i, stock in enumerate(candidates, 1):
        print(f"\n[{i}/{len(candidates)}] ", end="")
        result = analyze_stock_sentiment(analyzer, stock)
        results.append(result)
        time.sleep(2)  # 避免API限制
    
    print("\n" + "="*50)
    print("✅ 舆情分析完成，生成报告...")
    
    # 生成报告
    report = generate_report(results)
    
    # 保存报告到文件
    output_file = Path("output/sentiment_report_20260224.txt")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 报告已保存: {output_file}")
    print("\n" + "="*50)
    print("📋 报告预览 (前500字符):")
    print("="*50)
    print(report[:500] + "..." if len(report) > 500 else report)
    
    # 返回报告内容
    return report

if __name__ == "__main__":
    report = main()
    if report:
        # 保存报告到变量，供外部调用
        with open("sentiment_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)