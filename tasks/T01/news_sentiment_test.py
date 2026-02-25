#!/usr/bin/env python3
"""
T01 舆情分析测试脚本
用于验证新闻舆情分析对涨停股热度持续性判断的价值
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    """新闻舆情分析器 - 使用Tavily API"""
    
    def __init__(self, tavily_api_key: Optional[str] = None):
        """初始化分析器"""
        self.api_key = tavily_api_key or os.environ.get('TAVILY_API_KEY')
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        self.tavily_script_path = "/root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs"
        if not os.path.exists(self.tavily_script_path):
            raise FileNotFoundError(f"Tavily script not found: {self.tavily_script_path}")
        
        logger.info("NewsSentimentAnalyzer initialized with Tavily API")
    
    def search_stock_news(self, stock_name: str, stock_code: str, trade_date: str, 
                         days_back: int = 1) -> Dict[str, Any]:
        """
        搜索股票相关新闻
        
        Args:
            stock_name: 股票名称
            stock_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            days_back: 回溯天数
            
        Returns:
            新闻搜索结果
        """
        # 构建搜索查询 - 优化版 (添加中文限定词和市场标识)
        # 提取市场标识
        market = "A股"
        if stock_code.endswith('.SH'):
            market = "沪市"
        elif stock_code.endswith('.SZ'):
            market = "深市"
        
        queries = [
            f"{stock_name} {stock_code} {market} 中国 A股 涨停板 涨停",  # 涨停相关
            f"{stock_name} {stock_code} {market} 中国 A股 利好 消息",  # 利好相关
            f"{stock_name} {stock_code} {market} 中国 A股 业绩 预告",  # 业绩相关
            f"{stock_name} {stock_code} {market} 中国 A股 公告 通知",  # 公司公告
        ]
        
        all_results = []
        for query in queries:
            try:
                result = self._call_tavily(query, days_back=days_back)
                if result and result.get('sources'):
                    all_results.extend(result['sources'])
                    logger.info(f"Query '{query}' returned {len(result.get('sources', []))} results")
            except Exception as e:
                logger.warning(f"Query '{query}' failed: {e}")
                continue
        
        # 去重
        unique_results = self._deduplicate_results(all_results)
        
        return {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'trade_date': trade_date,
            'total_news_count': len(unique_results),
            'news_results': unique_results[:10],  # 只返回前10条
            'search_queries': queries
        }
    
    def _call_tavily(self, query: str, days_back: int = 1) -> Dict[str, Any]:
        """调用Tavily API"""
        cmd = [
            'node', self.tavily_script_path,
            query,
            '--topic', 'news',
            '--days', str(days_back),
            '-n', '5'
        ]
        
        logger.debug(f"Executing Tavily command: {' '.join(cmd)}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['TAVILY_API_KEY'] = self.api_key
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=30  # 30秒超时
            )
            
            if result.returncode != 0:
                logger.error(f"Tavily command failed: {result.stderr}")
                return {'answer': '', 'sources': []}
            
            # 解析输出
            return self._parse_tavily_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.error("Tavily command timeout")
            return {'answer': '', 'sources': []}
        except Exception as e:
            logger.error(f"Tavily command error: {e}")
            return {'answer': '', 'sources': []}
    
    def _parse_tavily_output(self, output: str) -> Dict[str, Any]:
        """解析Tavily输出"""
        lines = output.strip().split('\n')
        
        answer = ""
        sources = []
        current_source = {}
        
        in_answer_section = False
        in_sources_section = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## Answer'):
                in_answer_section = True
                in_sources_section = False
                continue
            elif line.startswith('## Sources'):
                in_answer_section = False
                in_sources_section = True
                continue
            elif line.startswith('---'):
                in_answer_section = False
                continue
            
            if in_answer_section and line:
                answer += line + ' '
            elif in_sources_section:
                if line.startswith('- **'):
                    # 新来源开始
                    if current_source:
                        sources.append(current_source)
                    
                    # 提取标题和URL
                    import re
                    title_match = re.search(r'\*\*(.*?)\*\*', line)
                    url_match = re.search(r'https?://[^\s)]+', line)
                    score_match = re.search(r'\(relevance: (\d+)%\)', line)
                    
                    current_source = {
                        'title': title_match.group(1) if title_match else '',
                        'url': url_match.group(0) if url_match else '',
                        'relevance_score': int(score_match.group(1)) / 100 if score_match else 0.5
                    }
                elif line.startswith('http') or line.startswith('  http'):
                    # URL行 - 设置URL
                    url = line.strip()
                    if current_source:
                        current_source['url'] = url
                    # 不视为内容行，继续循环
                    continue
                elif line and current_source:
                    # 内容行
                    if 'content' not in current_source:
                        current_source['content'] = line
                    else:
                        current_source['content'] += ' ' + line
        
        # 添加最后一个来源
        if current_source:
            sources.append(current_source)
        
        return {
            'answer': answer.strip(),
            'sources': sources
        }
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重新闻结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def analyze_sentiment(self, news_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        简单情感分析（关键词匹配）
        
        注意：这是一个简单实现，实际应使用NLP模型
        """
        # 中文关键词
        positive_keywords_cn = ['利好', '增长', '超预期', '突破', '创新高', '推荐', '买入', '看好', '上涨', '强势']
        negative_keywords_cn = ['利空', '下跌', '亏损', '风险', '减持', '卖出', '谨慎', '预警', '暴跌', '调整']
        
        # 英文关键词
        positive_keywords_en = ['positive', 'growth', 'beat', 'outperform', 'buy', 'bullish', 'upgrade', 'strong', 'gain']
        negative_keywords_en = ['negative', 'decline', 'loss', 'risk', 'sell', 'bearish', 'downgrade', 'weak', 'drop', 'fall']
        
        # 合并关键词
        positive_keywords = positive_keywords_cn + positive_keywords_en
        negative_keywords = negative_keywords_cn + negative_keywords_en
        
        total_score = 0
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for news in news_results:
            content = f"{news.get('title', '')} {news.get('content', '')}"
            content_lower = content.lower()
            
            # 简单关键词匹配
            pos_matches = sum(1 for keyword in positive_keywords if keyword in content)
            neg_matches = sum(1 for keyword in negative_keywords if keyword in content)
            
            if pos_matches > neg_matches:
                sentiment = 'positive'
                positive_count += 1
                score = 1.0
            elif neg_matches > pos_matches:
                sentiment = 'negative'
                negative_count += 1
                score = -1.0
            else:
                sentiment = 'neutral'
                neutral_count += 1
                score = 0.0
            
            news['sentiment'] = sentiment
            news['sentiment_score'] = score
            total_score += score
        
        total_news = len(news_results)
        if total_news > 0:
            avg_sentiment = total_score / total_news
            positive_ratio = positive_count / total_news
            negative_ratio = negative_count / total_news
        else:
            avg_sentiment = 0
            positive_ratio = 0
            negative_ratio = 0
        
        # 计算舆情综合评分 (0-10分)
        # 基于: 新闻数量 + 情感倾向 + 正面新闻比例
        overall_score = 0
        if total_news > 0:
            # 基础分: 有新闻关注度
            overall_score += 2.0
            
            # 正面新闻加分
            if positive_count > 0:
                overall_score += min(positive_count * 0.5, 3.0)
            
            # 情感得分映射 (-1到1映射到0到3分)
            sentiment_mapped = (avg_sentiment + 1) * 1.5  # -1->0, 0->1.5, 1->3
            overall_score += min(sentiment_mapped, 3.0)
            
            # 新闻数量加分 (上限2分)
            news_count_score = min(total_news * 0.1, 2.0)
            overall_score += news_count_score
        
        # 限制在0-10分
        overall_score = max(0, min(overall_score, 10))
        
        return {
            'total_news': total_news,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'avg_sentiment': avg_sentiment,
            'sentiment_category': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral',
            'overall_sentiment': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral',
            'overall_score': round(overall_score, 2)
        }
    
    def calculate_heat_index(self, news_count: int, avg_sentiment: float, 
                           recent_days: int = 3) -> float:
        """
        计算热度指数
        
        公式: (新闻数量 × 情感得分 × 时间衰减因子)
        """
        # 时间衰减因子：越近的新闻权重越高
        time_factor = 1.0 / recent_days if recent_days > 0 else 1.0
        
        # 基础热度计算
        base_heat = news_count * (1 + avg_sentiment)  # avg_sentiment在-1到1之间
        
        # 应用时间衰减
        heat_index = base_heat * time_factor
        
        # 归一化到0-100范围（简单版本）
        normalized_heat = min(100, max(0, heat_index * 10))
        
        return round(normalized_heat, 2)


def test_with_sample_data():
    """使用样本数据测试"""
    print("=== T01 舆情分析模块测试 ===")
    
    # 初始化分析器
    try:
        analyzer = NewsSentimentAnalyzer()
        print("✅ NewsSentimentAnalyzer 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试样本：宁德时代（之前测试过的涨停股）
    test_cases = [
        {
            'name': '宁德时代',
            'code': '300750.SZ',
            'date': '20250224',
            'is_limit_up': True
        },
        {
            'name': '贵州茅台',
            'code': '600519.SH',
            'date': '20250224',
            'is_limit_up': False  # 对比非涨停股
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 测试股票: {test_case['name']} ({test_case['code']})")
        print(f"   交易日期: {test_case['date']}")
        print(f"   是否涨停: {'是' if test_case['is_limit_up'] else '否'}")
        
        # 搜索新闻
        print("   搜索相关新闻...")
        news_result = analyzer.search_stock_news(
            stock_name=test_case['name'],
            stock_code=test_case['code'],
            trade_date=test_case['date'],
            days_back=3
        )
        
        print(f"   找到 {news_result['total_news_count']} 条相关新闻")
        
        # 情感分析
        if news_result['total_news_count'] > 0:
            sentiment_result = analyzer.analyze_sentiment(news_result['news_results'])
            
            print(f"   情感分析:")
            print(f"     - 正面: {sentiment_result['positive_count']}条 ({sentiment_result['positive_ratio']*100:.1f}%)")
            print(f"     - 负面: {sentiment_result['negative_count']}条 ({sentiment_result['negative_ratio']*100:.1f}%)")
            print(f"     - 中性: {sentiment_result['neutral_count']}条")
            print(f"     - 平均情感: {sentiment_result['avg_sentiment']:.2f}")
            print(f"     - 情感分类: {sentiment_result['sentiment_category']}")
            
            # 热度指数
            heat_index = analyzer.calculate_heat_index(
                news_count=news_result['total_news_count'],
                avg_sentiment=sentiment_result['avg_sentiment']
            )
            
            print(f"   热度指数: {heat_index}/100")
            
            # T01评分建议
            if test_case['is_limit_up']:
                if heat_index > 60:
                    suggestion = "✅ 高热度，持续性强，建议重点关注"
                elif heat_index > 30:
                    suggestion = "⚠️ 中等热度，需结合技术指标判断"
                else:
                    suggestion = "❌ 低热度，警惕一日游"
                
                print(f"   T01建议: {suggestion}")
        
        # 显示前3条新闻
        if news_result['total_news_count'] > 0:
            print(f"\n   前3条新闻摘要:")
            for i, news in enumerate(news_result['news_results'][:3], 1):
                print(f"     {i}. {news.get('title', '无标题')}")
                if 'sentiment' in news:
                    print(f"        情感: {news['sentiment']}, 得分: {news['sentiment_score']}")
        
        print("-" * 50)
    
    print("\n=== 测试总结 ===")
    print("✅ 舆情分析模块基本功能测试完成")
    print("📈 后续开发方向:")
    print("   1. 集成到T01评分体系")
    print("   2. 优化情感分析算法（使用NLP模型）")
    print("   3. 增加更多数据源（社交媒体、论坛等）")
    print("   4. 实时监控和预警功能")


if __name__ == "__main__":
    # 检查Tavily API密钥
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        print("❌ 错误: TAVILY_API_KEY 环境变量未设置")
        print("请执行: export TAVILY_API_KEY=your_api_key")
        sys.exit(1)
    
    print(f"✅ TAVILY_API_KEY 已设置: {api_key[:15]}...")
    
    # 运行测试
    test_with_sample_data()