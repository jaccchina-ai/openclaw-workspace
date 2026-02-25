#!/usr/bin/env python3
"""
宏观数据源测试套件
验证所有宏观数据网站的可访问性和数据提取功能
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataSourceTestSuite:
    """数据源测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        # 宏观数据源列表
        self.macro_data_sources = {
            'exchange_rate': {
                'name': '美元兑人民币汇率',
                'url': 'https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CNY',
                'parser': self._parse_exchange_rate,
                'expected_pattern': r'(\d+\.\d+)\s*(?:CNY|人民币|元)',
                'description': 'XE.com 汇率转换器'
            },
            'crude_oil': {
                'name': '布伦特原油价格',
                'url': 'https://www.investing.com/commodities/brent-oil',
                'parser': self._parse_crude_oil,
                'expected_pattern': r'\$(\d+\.\d+)',
                'description': 'Investing.com 原油价格'
            },
            'treasury_yield': {
                'name': '10年期美债收益率',
                'url': 'https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield',
                'parser': self._parse_treasury_yield,
                'expected_pattern': r'(\d+\.\d+)\s*%',
                'description': 'Investing.com 美债收益率'
            },
            'vix_index': {
                'name': 'VIX恐慌指数',
                'url': 'https://www.cboe.com/tradable_products/vix/',
                'parser': self._parse_vix_index,
                'expected_pattern': r'(\d+\.\d+)\s*(?:VIX|指数)',
                'description': 'CBOE官网 VIX指数'
            },
            'gold_price': {
                'name': '黄金价格(人民币/克)',
                'url': 'https://gold.cnfol.com/',
                'parser': self._parse_gold_price,
                'expected_pattern': r'(\d+\.\d+)\s*元\s*[/每]?\s*克',
                'description': '黄金网 黄金价格'
            },
            'sina_finance': {
                'name': '新浪财经首页',
                'url': 'https://finance.sina.com.cn',
                'parser': self._parse_news_site,
                'expected_pattern': r'<title>.*?新浪财经.*?</title>',
                'description': '新浪财经 (中文新闻源)'
            },
            'eastmoney': {
                'name': '东方财富首页',
                'url': 'https://www.eastmoney.com',
                'parser': self._parse_news_site,
                'expected_pattern': r'<title>.*?东方财富.*?</title>',
                'description': '东方财富 (中文新闻源)'
            },
            'cls': {
                'name': '财联社首页',
                'url': 'https://www.cls.cn',
                'parser': self._parse_news_site,
                'expected_pattern': r'<title>.*?财联社.*?</title>',
                'description': '财联社 (中文新闻源)'
            }
        }
        
        # Playwright 技能目录
        self.playwright_skill_dir = "/root/.openclaw/workspace/skills/playwright-scraper-skill"
        
        logger.info(f"数据源测试套件初始化完成，包含 {len(self.macro_data_sources)} 个数据源")
    
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
    
    def _parse_exchange_rate(self, content: str) -> Optional[float]:
        """解析汇率数据"""
        import re
        matches = re.findall(r'(\d+\.\d+)\s*(?:CNY|人民币|元)', content)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None
    
    def _parse_crude_oil(self, content: str) -> Optional[float]:
        """解析原油价格"""
        import re
        # 尝试多种模式匹配价格
        # 模式1：带美元符号的数字，如 $85.42
        matches = re.findall(r'\$(\d+\.\d+)', content)
        if not matches:
            # 模式2：数字后跟"USD"或"美元"
            matches = re.findall(r'(\d+\.\d+)\s*(?:USD|美元)', content, re.IGNORECASE)
        if not matches:
            # 模式3：仅数字（可能带逗号），在合理范围内（原油价格通常在50-150美元）
            all_numbers = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d+|\d+\.\d+)', content)
            matches = [n for n in all_numbers if 20 <= float(n.replace(',', '')) <= 200]
        if not matches:
            # 模式4：尝试在"Brent"或"布伦特"附近查找数字
            brent_section = re.search(r'(?i)(brent|布伦特).*?(\d+\.\d+)', content)
            if brent_section:
                matches = [brent_section.group(2)]
        
        if matches:
            # 取第一个匹配项，去除逗号
            price_str = matches[0].replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None
    
    def _parse_treasury_yield(self, content: str) -> Optional[float]:
        """解析美债收益率"""
        import re
        # 尝试多种模式匹配收益率
        # 模式1：百分比符号，如 4.25%
        matches = re.findall(r'(\d+\.\d+)\s*%', content)
        if not matches:
            # 模式2：数字后跟"percent"或"收益率"或"yield"
            matches = re.findall(r'(\d+\.\d+)\s*(?:percent|收益率|yield)', content, re.IGNORECASE)
        if not matches:
            # 模式3：仅数字，在合理范围内（美债收益率通常在0.5-10.0%）
            all_numbers = re.findall(r'(\d{1,2}\.\d+)', content)
            matches = [n for n in all_numbers if 0.5 <= float(n) <= 10.0]
        if not matches:
            # 模式4：尝试在"10-year"或"十年期"附近查找数字
            ten_year_section = re.search(r'(?i)(10.?year|十年期|10年期).*?(\d+\.\d+)', content)
            if ten_year_section:
                matches = [ten_year_section.group(2)]
        
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None
    
    def _parse_vix_index(self, content: str) -> Optional[float]:
        """解析VIX指数"""
        import re
        matches = re.findall(r'VIX.*?(\d+\.\d+)', content, re.IGNORECASE)
        if not matches:
            matches = re.findall(r'(\d+\.\d+)\s*VIX', content, re.IGNORECASE)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None
    
    def _parse_gold_price(self, content: str) -> Optional[float]:
        """解析黄金价格"""
        import re
        # 尝试多种模式匹配黄金价格
        # 模式1：元/克 格式
        matches = re.findall(r'(\d+\.\d+)\s*元\s*[/每]?\s*克', content)
        if not matches:
            # 模式2：人民币/克 格式
            matches = re.findall(r'(\d+\.\d+)\s*人民币\s*[/每]?\s*克', content)
        if not matches:
            # 模式3：元/盎司 格式 (转换为元/克: 1盎司=31.1035克)
            oz_matches = re.findall(r'(\d+\.\d+)\s*元\s*[/每]?\s*盎司', content)
            if oz_matches:
                try:
                    oz_price = float(oz_matches[0])
                    # 转换为元/克
                    gram_price = oz_price / 31.1035
                    return round(gram_price, 2)
                except ValueError:
                    pass
        if not matches:
            # 模式4：仅数字，在合理范围内（黄金价格通常在300-600元/克）
            all_numbers = re.findall(r'(\d{3}\.\d+|\d{3})', content)
            matches = [n for n in all_numbers if 300 <= float(n) <= 600]
        if not matches:
            # 模式5：尝试在"黄金"或"金价"附近查找数字
            gold_section = re.search(r'(?i)(黄金|金价).*?(\d{3}\.\d+|\d{3})', content)
            if gold_section:
                num = gold_section.group(2)
                if 300 <= float(num) <= 600:
                    matches = [num]
        
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None
    
    def _parse_news_site(self, content: str) -> bool:
        """解析新闻网站首页（验证可访问性）"""
        import re
        # 检查是否包含网站名称或标题
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).lower()
            # 简单验证：页面有标题即可
            return len(title) > 10
        return len(content) > 1000  # 有足够的内容
    
    def test_single_source(self, source_key: str, use_stealth: bool = True) -> Dict[str, Any]:
        """测试单个数据源"""
        if source_key not in self.macro_data_sources:
            return {
                'source_key': source_key,
                'status': 'error',
                'error': f"未知数据源: {source_key}"
            }
        
        source = self.macro_data_sources[source_key]
        url = source['url']
        parser = source['parser']
        
        logger.info(f"测试数据源: {source['name']} ({source['description']})")
        logger.info(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            # 使用 Playwright 爬取
            result = self._call_playwright_scraper(url, stealth=use_stealth)
            
            if not result:
                return {
                    'source_key': source_key,
                    'name': source['name'],
                    'url': url,
                    'status': 'failed',
                    'error': 'Playwright 爬取返回空结果',
                    'elapsed_time': time.time() - start_time
                }
            
            # 获取网页内容
            content = ""
            if "content" in result:
                content = result["content"]
            elif "raw" in result:
                content = result["raw"]
            else:
                return {
                    'source_key': source_key,
                    'name': source['name'],
                    'url': url,
                    'status': 'failed',
                    'error': 'Playwright 结果中没有内容字段',
                    'elapsed_time': time.time() - start_time
                }
            
            # 使用特定解析器解析内容
            parsed_value = parser(content)
            
            elapsed_time = time.time() - start_time
            
            if parsed_value is not None:
                return {
                    'source_key': source_key,
                    'name': source['name'],
                    'url': url,
                    'status': 'success',
                    'value': parsed_value,
                    'elapsed_time': elapsed_time,
                    'content_preview': content[:500] if content else "",
                    'parser_used': parser.__name__
                }
            else:
                # 解析失败，但网页访问成功
                return {
                    'source_key': source_key,
                    'name': source['name'],
                    'url': url,
                    'status': 'partial_success',
                    'error': '数据解析失败，但网页访问成功',
                    'elapsed_time': elapsed_time,
                    'content_preview': content[:500] if content else "",
                    'parser_used': parser.__name__
                }
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                'source_key': source_key,
                'name': source['name'],
                'url': url,
                'status': 'error',
                'error': str(e),
                'elapsed_time': elapsed_time
            }
    
    def run_comprehensive_test(self, source_keys: List[str] = None, 
                             use_stealth: bool = True) -> Dict[str, Any]:
        """运行全面测试"""
        if source_keys is None:
            source_keys = list(self.macro_data_sources.keys())
        
        logger.info(f"开始全面测试 {len(source_keys)} 个数据源")
        logger.info(f"使用模式: {'Stealth' if use_stealth else 'Simple'}")
        
        results = {}
        success_count = 0
        partial_count = 0
        failed_count = 0
        error_count = 0
        
        for source_key in source_keys:
            logger.info(f"\n{'='*60}")
            result = self.test_single_source(source_key, use_stealth)
            results[source_key] = result
            
            if result['status'] == 'success':
                success_count += 1
                logger.info(f"✅ {source_key}: 成功 - 值: {result.get('value')}")
            elif result['status'] == 'partial_success':
                partial_count += 1
                logger.info(f"⚠️ {source_key}: 部分成功 - 错误: {result.get('error')}")
            elif result['status'] == 'failed':
                failed_count += 1
                logger.info(f"❌ {source_key}: 失败 - 错误: {result.get('error')}")
            else:
                error_count += 1
                logger.info(f"🚨 {source_key}: 错误 - 错误: {result.get('error')}")
            
            # 避免请求过于频繁
            time.sleep(2)
        
        # 计算统计信息
        total_tests = len(source_keys)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'success_count': success_count,
            'partial_success_count': partial_count,
            'failed_count': failed_count,
            'error_count': error_count,
            'success_rate': round(success_rate, 2),
            'test_mode': 'stealth' if use_stealth else 'simple',
            'test_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'elapsed_time_total': sum(r.get('elapsed_time', 0) for r in results.values()),
            'results': results
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("测试摘要:")
        logger.info(f"  总测试数: {total_tests}")
        logger.info(f"  成功: {success_count}")
        logger.info(f"  部分成功: {partial_count}")
        logger.info(f"  失败: {failed_count}")
        logger.info(f"  错误: {error_count}")
        logger.info(f"  成功率: {success_rate:.2f}%")
        logger.info(f"  总耗时: {summary['elapsed_time_total']:.2f}秒")
        
        return summary
    
    def generate_report(self, test_results: Dict[str, Any], 
                       output_file: str = "data_source_test_report.json") -> str:
        """生成测试报告"""
        report = {
            'test_summary': {
                'total_tests': test_results['total_tests'],
                'success_count': test_results['success_count'],
                'partial_success_count': test_results['partial_success_count'],
                'failed_count': test_results['failed_count'],
                'error_count': test_results['error_count'],
                'success_rate': test_results['success_rate'],
                'test_mode': test_results['test_mode'],
                'test_time': test_results['test_time'],
                'elapsed_time_total': test_results['elapsed_time_total']
            },
            'detailed_results': test_results['results'],
            'recommendations': self._generate_recommendations(test_results)
        }
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成简洁的Markdown报告
        md_file = output_file.replace('.json', '.md')
        self._generate_markdown_report(report, md_file)
        
        logger.info(f"JSON报告已保存: {output_file}")
        logger.info(f"Markdown报告已保存: {md_file}")
        
        return output_file
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        results = test_results['results']
        
        for source_key, result in results.items():
            if result['status'] in ['failed', 'error']:
                source_name = self.macro_data_sources.get(source_key, {}).get('name', source_key)
                recommendations.append(f"⚠️ {source_name}: 需要修复 - {result.get('error', '未知错误')}")
            elif result['status'] == 'partial_success':
                source_name = self.macro_data_sources.get(source_key, {}).get('name', source_key)
                recommendations.append(f"🔧 {source_name}: 需要优化解析逻辑 - {result.get('error', '解析失败')}")
        
        # 整体建议
        if test_results['success_rate'] < 70:
            recommendations.append("🚨 整体成功率低于70%，建议检查网络连接和反爬虫策略")
        elif test_results['success_rate'] < 90:
            recommendations.append("⚠️ 整体成功率低于90%，建议优化失败的数据源")
        
        if not recommendations:
            recommendations.append("✅ 所有数据源工作正常，无需改进")
        
        return recommendations
    
    def _generate_markdown_report(self, report: Dict[str, Any], output_file: str):
        """生成Markdown格式报告"""
        summary = report['test_summary']
        results = report['detailed_results']
        recommendations = report['recommendations']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 宏观数据源测试报告\n\n")
            f.write(f"**测试时间**: {summary['test_time']}\n")
            f.write(f"**测试模式**: {summary['test_mode']}\n\n")
            
            f.write("## 测试摘要\n\n")
            f.write(f"- **总测试数**: {summary['total_tests']}\n")
            f.write(f"- **成功**: {summary['success_count']}\n")
            f.write(f"- **部分成功**: {summary['partial_success_count']}\n")
            f.write(f"- **失败**: {summary['failed_count']}\n")
            f.write(f"- **错误**: {summary['error_count']}\n")
            f.write(f"- **成功率**: {summary['success_rate']}%\n")
            f.write(f"- **总耗时**: {summary['elapsed_time_total']:.2f}秒\n\n")
            
            f.write("## 详细结果\n\n")
            f.write("| 数据源 | 状态 | 值 | 耗时(秒) | 备注 |\n")
            f.write("|--------|------|-----|----------|------|\n")
            
            for source_key, result in results.items():
                source_name = self.macro_data_sources.get(source_key, {}).get('name', source_key)
                status_emoji = {'success': '✅', 'partial_success': '⚠️', 'failed': '❌', 'error': '🚨'}.get(result['status'], '❓')
                value = result.get('value', 'N/A')
                elapsed = f"{result.get('elapsed_time', 0):.2f}"
                note = result.get('error', '成功')[:50]
                
                f.write(f"| {source_name} | {status_emoji} {result['status']} | {value} | {elapsed} | {note} |\n")
            
            f.write("\n## 改进建议\n\n")
            for rec in recommendations:
                f.write(f"- {rec}\n")
            
            f.write("\n## 数据源详情\n\n")
            for source_key, source_info in self.macro_data_sources.items():
                f.write(f"### {source_info['name']}\n")
                f.write(f"- **描述**: {source_info['description']}\n")
                f.write(f"- **URL**: {source_info['url']}\n")
                f.write(f"- **预期模式**: `{source_info.get('expected_pattern', 'N/A')}`\n")
                if source_key in results:
                    result = results[source_key]
                    f.write(f"- **测试结果**: {result['status']}\n")
                    if result.get('content_preview'):
                        f.write(f"- **内容预览**: {result['content_preview'][:200]}...\n")
                f.write("\n")
        
        logger.info(f"Markdown报告已生成: {output_file}")


def run_test_suite():
    """运行测试套件"""
    print("=== 宏观数据源测试套件 ===")
    
    try:
        test_suite = DataSourceTestSuite()
        print("✅ 测试套件初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 选择要测试的数据源
    source_keys = [
        'exchange_rate',      # 汇率
        'crude_oil',         # 原油价格
        'treasury_yield',    # 美债收益率
        'vix_index',         # VIX指数
        'gold_price',        # 黄金价格
        'sina_finance',      # 新浪财经
        'eastmoney',         # 东方财富
        'cls'                # 财联社
    ]
    
    print(f"测试 {len(source_keys)} 个数据源...")
    
    # 运行测试 (使用Stealth模式)
    test_results = test_suite.run_comprehensive_test(source_keys, use_stealth=True)
    
    # 生成报告
    report_file = test_suite.generate_report(
        test_results, 
        output_file=f"data_source_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    print(f"\n✅ 测试完成，报告已保存: {report_file}")
    
    # 显示关键指标
    summary = test_results
    print(f"\n📊 关键指标:")
    print(f"   成功率: {summary['success_rate']:.2f}%")
    print(f"   成功数: {summary['success_count']}/{summary['total_tests']}")
    print(f"   总耗时: {summary['elapsed_time_total']:.2f}秒")
    
    return test_results


if __name__ == "__main__":
    run_test_suite()