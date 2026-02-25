#!/usr/bin/env python3
"""
T01 中文财经新闻爬虫模块
使用 Playwright 爬取多个中文财经网站，增强舆情分析
"""

import os
import json
import re
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChineseNewsCrawler:
    """中文财经新闻爬虫 - 使用 Playwright 爬取多个网站"""
    
    def __init__(self, playwright_skill_dir: Optional[str] = None):
        """初始化爬虫"""
        # Playwright 技能目录
        if playwright_skill_dir:
            self.playwright_skill_dir = playwright_skill_dir
        else:
            # 默认路径
            self.playwright_skill_dir = "/root/.openclaw/workspace/skills/playwright-scraper-skill"
        
        # 检查 Playwright 技能是否可用
        self.playwright_available = self._check_playwright_availability()
        
        if not self.playwright_available:
            logger.warning("Playwright scraper skill not available")
        
        # 中文财经网站配置
        self.news_sites = {
            'sina': {
                'name': '新浪财经',
                'base_url': 'https://finance.sina.com.cn',
                'search_url': 'https://search.sina.com.cn/?q={query}&c=news&from=home&col=&range=all&source=&country=&size=10&stime={start_date}&etime={end_date}&sort=time',
                'search_pattern': 'title',
                'needs_stealth': True
            },
            'eastmoney': {
                'name': '东方财富',
                'base_url': 'https://www.eastmoney.com',
                'search_url': 'https://so.eastmoney.com/news/s?keyword={query}',
                'search_pattern': 'news-list',
                'needs_stealth': True
            },
            'cls': {
                'name': '财联社',
                'base_url': 'https://www.cls.cn',
                'search_url': 'https://www.cls.cn/search?keyword={query}&type=article',
                'search_pattern': 'article',
                'needs_stealth': True
            },
            'ths': {
                'name': '同花顺',
                'base_url': 'https://www.10jqka.com.cn',
                'search_url': 'https://so.10jqka.com.cn/index.php?keyword={query}&module=news',
                'search_pattern': 'news-list',
                'needs_stealth': True
            }
        }
        
        logger.info(f"ChineseNewsCrawler initialized with {len(self.news_sites)} news sites")
    
    def _check_playwright_availability(self) -> bool:
        """检查 Playwright 技能是否可用"""
        try:
            script_path = os.path.join(self.playwright_skill_dir, "scripts", "playwright-simple.js")
            return os.path.exists(script_path)
        except Exception as e:
            logger.warning(f"检查 Playwright 可用性失败: {e}")
            return False
    
    def _call_playwright_scraper(self, url: str, stealth: bool = True) -> Dict[str, Any]:
        """调用 Playwright 爬虫获取网页内容"""
        try:
            import subprocess
            import json
            
            # 选择脚本：stealth 模式或 simple 模式
            script_name = "playwright-stealth.js" if stealth else "playwright-simple.js"
            script_path = os.path.join(self.playwright_skill_dir, "scripts", script_name)
            
            if not os.path.exists(script_path):
                logger.error(f"Playwright 脚本不存在: {script_path}")
                return None
            
            # 运行 Playwright 脚本
            cmd = ["node", script_path, url]
            result = subprocess.run(
                cmd, 
                cwd=self.playwright_skill_dir,
                capture_output=True, 
                text=True, 
                timeout=60  # Playwright 可能需要更长时间
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.debug(f"解析 Playwright 输出失败: {e}")
                    # 返回原始输出
                    return {"raw": result.stdout, "error": "json_parse_failed"}
            else:
                logger.warning(f"Playwright 爬取失败: {result.stderr[:300]}")
                # 如果 stealth 模式失败，尝试 simple 模式（如果当前不是 simple 模式）
                if stealth:
                    logger.debug("⚠️ Stealth 模式失败，尝试 Simple 模式...")
                    return self._call_playwright_scraper(url, stealth=False)
                return None
        except subprocess.TimeoutExpired:
            logger.warning(f"Playwright 爬取超时 (60秒)")
            return None
        except Exception as e:
            logger.warning(f"调用 Playwright 异常: {e}")
            return None
    
    def search_stock_news(self, stock_name: str, stock_code: str, trade_date: str, 
                         days_back: int = 1) -> Dict[str, Any]:
        """
        搜索股票相关新闻 (多网站爬取)
        
        Args:
            stock_name: 股票名称
            stock_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD)
            days_back: 回溯天数
            
        Returns:
            新闻搜索结果
        """
        if not self.playwright_available:
            logger.warning("Playwright 不可用，跳过新闻爬取")
            return self._get_empty_result(stock_name, stock_code, trade_date)
        
        # 解析交易日期
        try:
            trade_date_obj = datetime.strptime(trade_date, "%Y%m%d")
            start_date = (trade_date_obj - timedelta(days=days_back)).strftime("%Y-%m-%d")
            end_date = trade_date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"日期解析失败: {e}")
            start_date = end_date = trade_date
        
        # 构建搜索查询
        market = "A股"
        if stock_code.endswith('.SH'):
            market = "沪市"
        elif stock_code.endswith('.SZ'):
            market = "深市"
        
        # 搜索词组合
        search_terms = [
            f"{stock_name} {stock_code}",  # 完整代码
            f"{stock_name} {market}",      # 名称+市场
            f"{stock_code[:-3]} {market}", # 简码+市场
            f"{stock_name} 涨停",           # 涨停相关
            f"{stock_name} 业绩",           # 业绩相关
            f"{stock_name} 公告",           # 公司公告
        ]
        
        all_news = []
        total_sites_processed = 0
        
        # 遍历所有新闻网站
        for site_key, site_config in self.news_sites.items():
            site_name = site_config['name']
            search_url_template = site_config.get('search_url')
            
            if not search_url_template:
                logger.debug(f"{site_name} 无搜索URL，跳过")
                continue
            
            for search_term in search_terms:
                try:
                    # 编码搜索词
                    encoded_term = quote_plus(search_term.encode('utf-8'))
                    
                    # 构造搜索URL（根据网站模板）
                    if '{start_date}' in search_url_template and '{end_date}' in search_url_template:
                        search_url = search_url_template.format(
                            query=encoded_term, 
                            start_date=start_date, 
                            end_date=end_date
                        )
                    else:
                        search_url = search_url_template.format(query=encoded_term)
                    
                    logger.debug(f"爬取 {site_name}: {search_url}")
                    
                    # 使用 Playwright 爬取
                    needs_stealth = site_config.get('needs_stealth', True)
                    result = self._call_playwright_scraper(search_url, stealth=needs_stealth)
                    
                    if result:
                        # 解析新闻内容（网站特定解析）
                        site_news = self._parse_news_from_site(site_key, result)
                        
                        # 添加股票信息
                        for news in site_news:
                            news['stock_name'] = stock_name
                            news['stock_code'] = stock_code
                            news['source_site'] = site_name
                            news['search_term'] = search_term
                        
                        all_news.extend(site_news)
                        logger.info(f"{site_name} - '{search_term}': 找到 {len(site_news)} 条新闻")
                    
                except Exception as e:
                    logger.warning(f"{site_name} 爬取失败 (查询: {search_term}): {e}")
                    continue
            
            total_sites_processed += 1
        
        # 去重
        unique_news = self._deduplicate_news(all_news)
        
        return {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'trade_date': trade_date,
            'total_news_count': len(unique_news),
            'news_results': unique_news[:15],  # 返回前15条
            'sites_searched': total_sites_processed,
            'search_terms': search_terms,
            'news_sources': list(self.news_sites.keys())
        }
    
    def _parse_news_from_site(self, site_key: str, playwright_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析特定网站的新闻内容"""
        news_list = []
        
        # 获取网页内容
        content = ""
        if "content" in playwright_result:
            content = playwright_result["content"]
        elif "raw" in playwright_result:
            content = playwright_result["raw"]
        else:
            logger.debug(f"{site_key}: Playwright 结果中没有内容字段")
            return news_list
        
        # 网站特定的解析逻辑
        if site_key == 'sina':
            news_list = self._parse_sina_news(content)
        elif site_key == 'eastmoney':
            news_list = self._parse_eastmoney_news(content)
        elif site_key == 'cls':
            news_list = self._parse_cls_news(content)
        elif site_key == 'ths':
            news_list = self._parse_ths_news(content)
        else:
            # 默认解析：尝试提取所有新闻链接和标题
            news_list = self._parse_generic_news(content)
        
        # 添加爬取时间戳
        crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for news in news_list:
            news['crawl_time'] = crawl_time
        
        return news_list
    
    def _parse_sina_news(self, content: str) -> List[Dict[str, Any]]:
        """解析新浪财经新闻"""
        news_list = []
        
        # 新浪新闻通常包含 class="r-info" 或包含新闻标题的 div
        # 使用正则表达式提取新闻条目
        import re
        
        # 模式1：新闻标题链接
        pattern1 = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        # 模式2：时间信息
        pattern2 = r'<span[^>]*class=".*?time.*?"[^>]*>(.*?)</span>'
        
        # 查找所有可能的新闻链接
        all_links = re.findall(pattern1, content, re.DOTALL)
        
        for url, title_html in all_links:
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            # 过滤：只保留包含财经、股票、公司等关键词的链接
            if not title:
                continue
            
            # 检查URL是否为新浪财经域名
            if 'finance.sina.com.cn' not in url and 'sina.com.cn' not in url:
                continue
            
            # 尝试提取时间
            time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', title_html)
            publish_time = time_match.group(1) if time_match else ""
            
            news_list.append({
                'title': title[:200],  # 限制标题长度
                'url': url,
                'publish_time': publish_time,
                'source': '新浪财经'
            })
        
        return news_list[:10]  # 限制数量
    
    def _parse_eastmoney_news(self, content: str) -> List[Dict[str, Any]]:
        """解析东方财富新闻"""
        news_list = []
        import re
        
        # 东方财富新闻通常有特定结构
        # 查找新闻条目
        news_pattern = r'<div[^>]*class=".*?news-item.*?"[^>]*>(.*?)</div>'
        news_items = re.findall(news_pattern, content, re.DOTALL)
        
        for item in news_items:
            # 提取标题和链接
            title_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', item, re.DOTALL)
            if not title_match:
                continue
            
            url = title_match.group(1)
            title_html = title_match.group(2)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            if not title:
                continue
            
            # 提取时间
            time_match = re.search(r'<span[^>]*class=".*?time.*?"[^>]*>(.*?)</span>', item, re.DOTALL)
            publish_time = time_match.group(1).strip() if time_match else ""
            
            news_list.append({
                'title': title[:200],
                'url': url,
                'publish_time': publish_time,
                'source': '东方财富'
            })
        
        return news_list[:10]
    
    def _parse_cls_news(self, content: str) -> List[Dict[str, Any]]:
        """解析财联社新闻"""
        news_list = []
        import re
        
        # 财联社新闻可能使用不同的结构
        # 尝试提取所有文章链接
        article_pattern = r'<article[^>]*>(.*?)</article>'
        articles = re.findall(article_pattern, content, re.DOTALL)
        
        for article in articles:
            # 提取标题
            title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', article, re.DOTALL)
            if not title_match:
                continue
            
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            # 提取链接
            link_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>', article, re.DOTALL)
            url = link_match.group(1) if link_match else ""
            
            # 提取时间
            time_match = re.search(r'<time[^>]*>(.*?)</time>', article, re.DOTALL)
            publish_time = time_match.group(1).strip() if time_match else ""
            
            if title:
                news_list.append({
                    'title': title[:200],
                    'url': url if url.startswith('http') else f"https://www.cls.cn{url}" if url else "",
                    'publish_time': publish_time,
                    'source': '财联社'
                })
        
        return news_list[:10]
    
    def _parse_ths_news(self, content: str) -> List[Dict[str, Any]]:
        """解析同花顺新闻"""
        news_list = []
        import re
        
        # 同花顺新闻
        # 查找新闻列表
        news_item_pattern = r'<li[^>]*class=".*?news-item.*?"[^>]*>(.*?)</li>'
        news_items = re.findall(news_item_pattern, content, re.DOTALL)
        
        for item in news_items:
            # 提取标题和链接
            title_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', item, re.DOTALL)
            if not title_match:
                continue
            
            url = title_match.group(1)
            title_html = title_match.group(2)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            # 提取时间
            time_match = re.search(r'<span[^>]*class=".*?time.*?"[^>]*>(.*?)</span>', item, re.DOTALL)
            publish_time = time_match.group(1).strip() if time_match else ""
            
            if title:
                news_list.append({
                    'title': title[:200],
                    'url': url if url.startswith('http') else f"https://www.10jqka.com.cn{url}" if url else "",
                    'publish_time': publish_time,
                    'source': '同花顺'
                })
        
        return news_list[:10]
    
    def _parse_generic_news(self, content: str) -> List[Dict[str, Any]]:
        """通用新闻解析（兜底方案）"""
        news_list = []
        import re
        
        # 提取所有链接和标题
        link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        all_links = re.findall(link_pattern, content, re.DOTALL)
        
        for url, title_html in all_links:
            title = re.sub(r'<[^>]+>', '', title_html).strip()[:100]
            
            # 过滤条件：标题长度、URL有效性
            if len(title) < 5 or len(title) > 200:
                continue
            
            # 检查是否是新闻相关URL
            if not any(keyword in url.lower() for keyword in ['news', 'article', 'report', '财经', '股票']):
                continue
            
            news_list.append({
                'title': title,
                'url': url,
                'publish_time': "",
                'source': '其他网站'
            })
        
        return news_list[:5]  # 限制数量
    
    def _deduplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重新闻（基于标题相似度）"""
        if not news_list:
            return []
        
        # 简单去重：基于URL和标题
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '').lower().strip()
            url = news.get('url', '').lower().strip()
            
            # 创建唯一标识符
            identifier = f"{title[:50]}_{url[:50]}"
            
            if identifier not in seen_titles:
                seen_titles.add(identifier)
                unique_news.append(news)
        
        return unique_news
    
    def _get_empty_result(self, stock_name: str, stock_code: str, trade_date: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'trade_date': trade_date,
            'total_news_count': 0,
            'news_results': [],
            'sites_searched': 0,
            'search_terms': [],
            'news_sources': []
        }


def test_crawler():
    """测试爬虫"""
    print("=== 中文新闻爬虫测试 ===")
    
    try:
        crawler = ChineseNewsCrawler()
        print("✅ ChineseNewsCrawler 初始化成功")
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
        
        # 搜索新闻（回溯1天）
        result = crawler.search_stock_news(
            stock['name'], stock['code'], stock['date'], days_back=1
        )
        
        print(f"   总新闻数: {result['total_news_count']}")
        print(f"   搜索网站: {', '.join(result['news_sources'])}")
        
        # 显示前3条新闻
        for i, news in enumerate(result['news_results'][:3], 1):
            print(f"   {i}. {news.get('source', '未知来源')}: {news.get('title', '无标题')[:50]}...")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_crawler()