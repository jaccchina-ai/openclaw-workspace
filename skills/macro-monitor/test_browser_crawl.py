#!/usr/bin/env python3
"""快速测试 browser 爬取功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 导入必要的函数
from run_monitor import analyze_news_sentiment
import json

print("=== 快速测试 browser 爬取（仅财联社） ===")
print("预计时间：15-20秒")

# 临时修改 analyze_news_sentiment 函数，只测试一个网站
import run_monitor
original_websites = run_monitor.analyze_news_sentiment.__code__

# 由于函数复杂，直接调用内部函数
from run_monitor import analyze_news_sentiment

# 运行完整函数（会爬取两个网站）
result = analyze_news_sentiment()

print("\n=== 结果 ===")
if result.get("error"):
    print(f"❌ 爬取失败: {result.get('error_message')}")
else:
    print(f"✅ 成功获取 {result.get('total_titles', 0)} 条标题")
    print(f"   情感分数: {result.get('sentiment_score')}")
    print(f"   数据源: {result.get('source')}")
    print(f"   备注: {result.get('note')}")
    
    if result.get("sample_titles"):
        print("\n   示例标题:")
        for i, title in enumerate(result["sample_titles"][:3], 1):
            print(f"     {i}. {title}")

# 保存结果到临时文件
with open('/tmp/crawl_test.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n结果已保存到 /tmp/crawl_test.json")