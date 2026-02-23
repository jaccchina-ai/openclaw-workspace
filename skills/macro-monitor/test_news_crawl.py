#!/usr/bin/env python3
"""测试新闻爬取解析器"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from run_monitor import analyze_news_sentiment
import json

print("=== 测试新闻爬取解析器 ===")
print("注意：这可能会触发真实网络请求，耗时约15-30秒")
print()

# 运行新闻情感分析函数
result = analyze_news_sentiment()

print("\n=== 爬取结果 ===")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 分析结果
if result.get("error"):
    print(f"\n❌ 爬取失败: {result.get('error_message')}")
    print("  源网站可能反爬或网络不通")
else:
    print(f"\n✅ 爬取成功")
    print(f"  获取标题数: {result.get('total_titles', 0)}")
    print(f"  正面/负面/中性: {result.get('positive_news')}/{result.get('negative_news')}/{result.get('neutral_news')}")
    print(f"  情感分数: {result.get('sentiment_score')}")
    print(f"  数据源: {result.get('source', 'unknown')}")
    print(f"  备注: {result.get('note', '')}")
    
    if result.get("sample_titles"):
        print("\n  示例标题:")
        for i, title in enumerate(result["sample_titles"][:5], 1):
            print(f"    {i}. {title}")