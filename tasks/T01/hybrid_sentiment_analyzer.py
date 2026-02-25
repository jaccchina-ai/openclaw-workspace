#!/usr/bin/env python3
"""
T01 混合舆情分析器
结合 Tavily API 和中文新闻爬虫，提供更全面的舆情分析
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridSentimentAnalyzer:
    """混合舆情分析器 - 结合 Tavily 和中文新闻爬虫"""
    
    def __init__(self, tavily_api_key: Optional[str] = None, 
                 playwright_skill_dir: Optional[str] = None):
        """初始化分析器"""
        # 尝试导入 Tavily 分析器
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from news_sentiment_test import NewsSentimentAnalyzer
            self.tavily_analyzer = NewsSentimentAnalyzer(tavily_api_key)
            self.tavily_available = True
            logger.info("Tavily 分析器初始化成功")
        except Exception as e:
            self.tavily_analyzer = None
            self.tavily_available = False
            logger.warning(f"Tavily 分析器初始化失败: {e}")
        
        # 尝试导入中文新闻爬虫
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from chinese_news_crawler import ChineseNewsCrawler
            self.chinese_crawler = ChineseNewsCrawler(playwright_skill_dir)
            self.chinese_crawler_available = self.chinese_crawler.playwright_available
            logger.info("中文新闻爬虫初始化成功")
        except Exception as e:
            self.chinese_crawler = None
            self.chinese_crawler_available = False
            logger.warning(f"中文新闻爬虫初始化失败: {e}")
        
        # 检查是否有可用的分析器
        if not self.tavily_available and not self.chinese_crawler_available:
            raise ValueError("No sentiment analyzer available (both Tavily and Chinese crawler failed)")
        
        logger.info(f"HybridSentimentAnalyzer 初始化完成 - "
                   f"Tavily: {self.tavily_available}, "
                   f"Chinese Crawler: {self.chinese_crawler_available}")
    
    def search_stock_news(self, stock_name: str, stock_code: str, trade_date: str, 
                         days_back: int = 1) -> Dict[str, Any]:
        """
        搜索股票相关新闻（混合来源）
        
        Args:
            stock_name: 股票名称
            stock_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            days_back: 回溯天数
            
        Returns:
            混合新闻搜索结果
        """
        all_news_results = []
        sources_used = []
        
        # 1. 使用 Tavily 搜索（如果可用）
        if self.tavily_available and self.tavily_analyzer:
            try:
                logger.info(f"使用 Tavily 搜索 {stock_name} ({stock_code}) 新闻...")
                tavily_result = self.tavily_analyzer.search_stock_news(
                    stock_name, stock_code, trade_date, days_back
                )
                
                if tavily_result and tavily_result.get('total_news_count', 0) > 0:
                    # 转换 Tavily 结果格式以匹配中文爬虫格式
                    converted_news = self._convert_tavily_news(tavily_result['news_results'])
                    all_news_results.extend(converted_news)
                    sources_used.append('tavily')
                    
                    logger.info(f"Tavily 找到 {tavily_result['total_news_count']} 条新闻")
                else:
                    logger.info("Tavily 未找到相关新闻")
            except Exception as e:
                logger.warning(f"Tavily 搜索失败: {e}")
        
        # 2. 使用中文新闻爬虫（如果可用）
        if self.chinese_crawler_available and self.chinese_crawler:
            try:
                logger.info(f"使用中文爬虫搜索 {stock_name} ({stock_code}) 新闻...")
                chinese_result = self.chinese_crawler.search_stock_news(
                    stock_name, stock_code, trade_date, days_back
                )
                
                if chinese_result and chinese_result.get('total_news_count', 0) > 0:
                    all_news_results.extend(chinese_result['news_results'])
                    sources_used.append('chinese_crawler')
                    
                    logger.info(f"中文爬虫找到 {chinese_result['total_news_count']} 条新闻")
                else:
                    logger.info("中文爬虫未找到相关新闻")
            except Exception as e:
                logger.warning(f"中文爬虫搜索失败: {e}")
        
        # 3. 去重合并结果
        unique_news = self._deduplicate_combined_news(all_news_results)
        
        return {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'trade_date': trade_date,
            'total_news_count': len(unique_news),
            'news_results': unique_news[:20],  # 最多返回20条
            'sources_used': sources_used,
            'search_completed': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _convert_tavily_news(self, tavily_news: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换 Tavily 新闻格式以匹配中文爬虫格式"""
        converted = []
        
        for news in tavily_news:
            converted_news = {
                'title': news.get('title', ''),
                'url': news.get('url', ''),
                'content': news.get('content', ''),
                'publish_time': '',  # Tavily 通常不提供发布时间
                'source': news.get('url', ''),  # 使用URL作为来源标识
                'original_format': 'tavily',
                'relevance_score': news.get('relevance_score', 0.5)
            }
            converted.append(converted_news)
        
        return converted
    
    def _deduplicate_combined_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重合并的新闻结果"""
        if not news_list:
            return []
        
        # 基于标题和URL去重
        seen_items = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '').lower().strip()
            url = news.get('url', '').lower().strip()
            
            # 创建唯一标识符
            if title:
                identifier = title[:100]
            elif url:
                identifier = url[:100]
            else:
                continue
            
            if identifier not in seen_items:
                seen_items.add(identifier)
                unique_news.append(news)
        
        return unique_news
    
    def analyze_sentiment(self, news_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        混合情感分析（结合中文和英文处理）
        
        注意：使用现有的情感分析逻辑，但优化中文处理
        """
        # 中文关键词（增强版）
        positive_keywords_cn = [
            '利好', '增长', '超预期', '突破', '创新高', '推荐', '买入', '看好', 
            '上涨', '强势', '业绩预增', '大涨', '龙头', '领涨', '资金流入',
            '机构推荐', '目标价', '增持', '买入评级', '优秀', '良好', '提升'
        ]
        
        negative_keywords_cn = [
            '利空', '下跌', '亏损', '风险', '减持', '卖出', '谨慎', '预警', 
            '暴跌', '调整', '业绩预减', '大跌', '跌停', '资金流出', '机构减持',
            '下调评级', '卖出评级', '警告', '问题', '下滑', '不及预期'
        ]
        
        # 英文关键词（保持原样）
        positive_keywords_en = [
            'positive', 'growth', 'beat', 'outperform', 'buy', 'bullish', 
            'upgrade', 'strong', 'gain', 'increase', 'improve', 'profit'
        ]
        
        negative_keywords_en = [
            'negative', 'decline', 'loss', 'risk', 'sell', 'bearish', 
            'downgrade', 'weak', 'drop', 'fall', 'decrease', 'warn'
        ]
        
        # 合并关键词
        positive_keywords = positive_keywords_cn + positive_keywords_en
        negative_keywords = negative_keywords_cn + negative_keywords_en
        
        total_score = 0
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        chinese_news_count = 0
        english_news_count = 0
        
        for news in news_results:
            # 获取新闻内容
            title = news.get('title', '')
            content = news.get('content', '')
            full_text = f"{title} {content}"
            
            # 判断是中文还是英文新闻
            is_chinese = self._is_chinese_text(full_text)
            if is_chinese:
                chinese_news_count += 1
            else:
                english_news_count += 1
            
            # 情感分析
            sentiment_result = self._analyze_single_news(
                full_text, positive_keywords, negative_keywords, is_chinese
            )
            
            sentiment = sentiment_result['sentiment']
            score = sentiment_result['score']
            
            # 统计
            if sentiment == 'positive':
                positive_count += 1
            elif sentiment == 'negative':
                negative_count += 1
            else:
                neutral_count += 1
            
            total_score += score
            
            # 保存结果到新闻对象
            news['sentiment'] = sentiment
            news['sentiment_score'] = score
            news['is_chinese'] = is_chinese
            news['keyword_matches'] = sentiment_result['matches']
        
        # 计算总体统计
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
        overall_score = self._calculate_overall_score(
            total_news, positive_count, negative_count, avg_sentiment,
            chinese_news_count, english_news_count
        )
        
        return {
            'total_news': total_news,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'avg_sentiment': avg_sentiment,
            'chinese_news_count': chinese_news_count,
            'english_news_count': english_news_count,
            'sentiment_category': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral',
            'overall_sentiment': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral',
            'overall_score': round(overall_score, 2)
        }
    
    def _is_chinese_text(self, text: str) -> bool:
        """判断文本是否是中文"""
        # 简单判断：如果包含中文字符，则认为是中文
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars) > 3  # 至少3个中文字符
    
    def _analyze_single_news(self, text: str, positive_keywords: List[str], 
                           negative_keywords: List[str], is_chinese: bool) -> Dict[str, Any]:
        """分析单条新闻的情感"""
        text_lower = text.lower()
        
        # 计算匹配次数
        pos_matches = 0
        neg_matches = 0
        
        for keyword in positive_keywords:
            if keyword.lower() in text_lower:
                pos_matches += 1
        
        for keyword in negative_keywords:
            if keyword.lower() in text_lower:
                neg_matches += 1
        
        # 决定情感
        if pos_matches > neg_matches:
            sentiment = 'positive'
            score = 1.0
        elif neg_matches > pos_matches:
            sentiment = 'negative'
            score = -1.0
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'matches': {'positive': pos_matches, 'negative': neg_matches}
        }
    
    def _calculate_overall_score(self, total_news: int, positive_count: int, 
                               negative_count: int, avg_sentiment: float,
                               chinese_news_count: int, english_news_count: int) -> float:
        """计算舆情综合评分 (0-10分)"""
        overall_score = 0
        
        if total_news > 0:
            # 基础分: 有新闻关注度
            overall_score += 2.0
            
            # 中文新闻额外加分（更相关）
            if chinese_news_count > 0:
                chinese_bonus = min(chinese_news_count * 0.3, 2.0)
                overall_score += chinese_bonus
            
            # 正面新闻加分
            if positive_count > 0:
                positive_bonus = min(positive_count * 0.6, 3.0)
                overall_score += positive_bonus
            
            # 情感得分映射 (-1到1映射到0到3分)
            sentiment_mapped = (avg_sentiment + 1) * 1.5  # -1->0, 0->1.5, 1->3
            overall_score += min(sentiment_mapped, 3.0)
            
            # 新闻数量加分 (上限2分)
            news_count_score = min(total_news * 0.15, 2.0)
            overall_score += news_count_score
        
        # 限制在0-10分
        overall_score = max(0, min(overall_score, 10))
        
        return overall_score
    
    def calculate_heat_index(self, news_count: int, avg_sentiment: float, 
                           recent_days: int = 3) -> float:
        """
        计算热度指数（复用原有逻辑）
        
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


def test_hybrid_analyzer():
    """测试混合分析器"""
    print("=== 混合舆情分析器测试 ===")
    
    try:
        analyzer = HybridSentimentAnalyzer()
        print("✅ HybridSentimentAnalyzer 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试样本股票
    test_stocks = [
        {"name": "宁德时代", "code": "300750.SZ", "date": "20260224"},
        {"name": "贵州茅台", "code": "600519.SH", "date": "20260224"},
    ]
    
    for stock in test_stocks:
        print(f"\n📊 测试股票: {stock['name']} ({stock['code']})")
        
        # 搜索新闻
        news_result = analyzer.search_stock_news(
            stock['name'], stock['code'], stock['date'], days_back=1
        )
        
        print(f"   总新闻数: {news_result['total_news_count']}")
        print(f"   来源: {', '.join(news_result['sources_used'])}")
        
        # 情感分析
        sentiment_result = analyzer.analyze_sentiment(news_result['news_results'])
        
        print(f"   正面新闻: {sentiment_result['positive_count']}")
        print(f"   负面新闻: {sentiment_result['negative_count']}")
        print(f"   中性新闻: {sentiment_result['neutral_count']}")
        print(f"   舆情评分: {sentiment_result['overall_score']}/10.0")
        print(f"   中文新闻数: {sentiment_result['chinese_news_count']}")
        print(f"   英文新闻数: {sentiment_result['english_news_count']}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_hybrid_analyzer()