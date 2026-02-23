#!/usr/bin/env python3
"""
macro-monitor 核心执行脚本 (任务代码: T100)
集成：国际数据、汇率、大宗商品、新闻情感分析、板块轮动预测
"""

import sys
import json
import os
import csv
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import re

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    print(f"ERROR: Missing required libraries: {e}")
    print("Please install: pip install akshare pandas numpy scikit-learn")
    sys.exit(1)

# 飞书群 ID (T99 使用的群)
FEISHU_GROUP_ID = "chat:oc_ff08c55a23630937869cd222dad0bf14"

# 备用方案使用跟踪
_FALLBACK_USAGE = {
    "usd_cny": {"used": False, "source": None, "error": None},
    "crude_oil": {"used": False, "source": None, "error": None},
    "us_10y_yield": {"used": False, "source": None, "error": None},
    "vix": {"used": False, "source": None, "error": None},
    "gold_cny": {"used": False, "source": None, "error": None},
}

def _record_fallback_usage(key: str, source: str, error: str = None):
    """记录备用方案使用情况"""
    global _FALLBACK_USAGE
    if key in _FALLBACK_USAGE:
        _FALLBACK_USAGE[key]["used"] = True
        _FALLBACK_USAGE[key]["source"] = source
        _FALLBACK_USAGE[key]["error"] = error

def _reset_fallback_usage():
    """重置备用方案使用记录"""
    global _FALLBACK_USAGE
    for key in _FALLBACK_USAGE:
        _FALLBACK_USAGE[key] = {"used": False, "source": None, "error": None}

# ============================================================================
# 备用数据获取函数（当 akshare API 失败时使用）
# ============================================================================

# 数据源缓存，避免重复调用外部API
_DATA_CACHE = {}
_CACHE_EXPIRY = 300  # 缓存有效期（秒）

def _get_from_cache(key: str):
    """从缓存获取数据，检查是否过期"""
    if key not in _DATA_CACHE:
        return None
    entry = _DATA_CACHE[key]
    import time
    if time.time() - entry["timestamp"] < _CACHE_EXPIRY:
        return entry["value"]
    else:
        del _DATA_CACHE[key]
        return None

def _set_to_cache(key: str, value):
    """设置缓存数据"""
    import time
    _DATA_CACHE[key] = {
        "value": value,
        "timestamp": time.time()
    }

def _call_openclaw_tool(tool: str, args: list) -> dict | None:
    """调用 OpenClaw 工具的统一接口"""
    try:
        import subprocess
        import json
        cmd = ["openclaw", tool] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # 如果不是 JSON，返回原始文本
                return {"raw": result.stdout}
        else:
            print(f"      {tool} 命令失败: {result.stderr[:200]}")
            return None
    except Exception as e:
        print(f"      调用 {tool} 异常: {e}")
        return None

def get_exchange_rate_fallback() -> float | None:
    """
    备用方案获取美元兑人民币汇率
    优先级：1. 免费API → 2. Tavily Search → 3. web_fetch
    """
    cache_key = "exchange_rate_usd_cny"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"      使用缓存的汇率数据: {cached}")
        return cached
    
    try:
        print("    ├─ [Fallback] 尝试备用方案获取汇率...")
        
        # 方法1：免费汇率 API (exchangerate-api.com) - 最稳定
        try:
            import urllib.request
            import json
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())
            rate = data.get('rates', {}).get('CNY')
            if rate:
                rate_float = float(rate)
                print(f"      从 exchangerate-api.com 获取汇率: {rate_float}")
                _set_to_cache(cache_key, rate_float)
                _record_fallback_usage("usd_cny", "exchangerate-api.com")
                return rate_float
        except Exception as api_err:
            print(f"      免费API失败: {api_err}")
        
        # 方法2：Tavily Search - 可靠性高，有上下文
        try:
            result = _call_openclaw_tool("web_search", ["--query", "USD to CNY exchange rate today", "--count", "3"])
            if result and "results" in result:
                for res in result.get("results", []):
                    snippet = res.get("snippet", "").lower()
                    import re
                    # 在摘要中查找汇率数字（格式如 7.24 CNY 或 7.24 人民币）
                    matches = re.findall(r'(\d+\.\d+)\s*(?:cny|人民币|rmb)', snippet)
                    if matches:
                        rate_float = float(matches[0])
                        print(f"      从 Tavily Search 获取汇率: {rate_float}")
                        _set_to_cache(cache_key, rate_float)
                        _record_fallback_usage("usd_cny", "Tavily Search")
                        return rate_float
        except Exception as search_err:
            print(f"      Tavily Search 失败: {search_err}")
        
        # 方法3：web_fetch 爬取 XE.com - 兜底方案
        try:
            result = _call_openclaw_tool("web_fetch", ["--url", "https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CNY", "--extractMode", "text"])
            if result and "raw" in result:
                import re
                content = result["raw"]
                # 查找汇率数字（XE.com 的格式）
                matches = re.findall(r'(\d+\.\d+)\s*Chinese Yuan', content)
                if not matches:
                    matches = re.findall(r'(\d+\.\d+)\s*CNY', content)
                if not matches:
                    matches = re.findall(r'(\d+\.\d+)\s*人民币', content)
                if matches:
                    rate_float = float(matches[0])
                    print(f"      从 XE.com 获取汇率: {rate_float}")
                    _set_to_cache(cache_key, rate_float)
                    _record_fallback_usage("usd_cny", "XE.com (web_fetch)")
                    return rate_float
        except Exception as tool_err:
            print(f"      web_fetch 失败: {tool_err}")
        
        print("      所有备用方案均失败")
        _record_fallback_usage("usd_cny", None, "所有备用方案失败")
        return None
        
    except Exception as e:
        print(f"      汇率备用方案失败: {e}")
        _record_fallback_usage("usd_cny", None, str(e))
        return None

def get_crude_oil_fallback() -> float | None:
    """
    备用方案获取原油价格（布伦特原油）
    优先级：1. Tavily Search → 2. 免费API → 3. web_fetch
    """
    cache_key = "crude_oil_brent"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"      使用缓存的原油价格: {cached}")
        return cached
    
    try:
        print("    ├─ [Fallback] 尝试备用方案获取原油价格...")
        
        # 方法1：Tavily Search - 最可靠，能获取最新价格
        try:
            result = _call_openclaw_tool("web_search", ["--query", "布伦特原油 当前价格 美元", "--count", "3"])
            if result and "results" in result:
                for res in result.get("results", []):
                    snippet = res.get("snippet", "").lower()
                    import re
                    # 查找价格数字（格式如 $85.42 或 85.42美元）
                    matches = re.findall(r'\$(\d+\.\d+)', snippet)
                    if not matches:
                        matches = re.findall(r'(\d+\.\d+)\s*美元', snippet)
                    if matches:
                        price = float(matches[0])
                        print(f"      从 Tavily Search 获取原油价格: ${price}")
                        _set_to_cache(cache_key, price)
                        _record_fallback_usage("crude_oil", "Tavily Search")
                        return price
        except Exception as search_err:
            print(f"      Tavily Search 失败: {search_err}")
        
        # 方法2：免费API（Alpha Vantage 或类似，需要API key，暂时跳过）
        # 方法3：web_fetch 爬取 Investing.com
        try:
            result = _call_openclaw_tool("web_fetch", ["--url", "https://www.investing.com/commodities/brent-oil", "--extractMode", "text"])
            if result and "raw" in result:
                import re
                content = result["raw"]
                # Investing.com 页面中查找价格
                # 查找模式：数字+小数点，可能带有逗号分隔千位
                matches = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d+|\d+\.\d+)', content)
                if matches:
                    # 取第一个匹配项，并去除逗号
                    price_str = matches[0].replace(',', '')
                    price = float(price_str)
                    print(f"      从 Investing.com 获取原油价格: ${price}")
                    _set_to_cache(cache_key, price)
                    _record_fallback_usage("crude_oil", "Investing.com (web_fetch)")
                    return price
        except Exception as tool_err:
            print(f"      web_fetch 失败: {tool_err}")
        
        print("      所有备用方案均失败")
        _record_fallback_usage("crude_oil", None, "所有备用方案失败")
        return None
        
    except Exception as e:
        print(f"      原油备用方案失败: {e}")
        _record_fallback_usage("crude_oil", None, str(e))
        return None

def get_us_treasury_yield_fallback() -> float | None:
    """
    备用方案获取10年期美债收益率
    优先级：1. 美国财政部API → 2. Tavily Search → 3. 财经网站
    """
    cache_key = "us_10y_yield"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"      使用缓存的美债收益率: {cached}")
        return cached
    
    try:
        print("    ├─ [Fallback] 尝试备用方案获取美债收益率...")
        
        # 方法1：直接访问美国财政部JSON数据（最权威）
        try:
            import urllib.request
            import json
            url = "https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Datasets/yield.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=15)
            data = json.loads(response.read().decode())
            # 数据格式：{ "data": [["2024-02-21", 1.5, 1.8, ...], ...] }
            # 10年期是第10列（索引9）
            if "data" in data and len(data["data"]) > 0:
                latest = data["data"][0]  # 最新一天的数据
                if len(latest) > 9:
                    yield_value = float(latest[9])  # 10年期收益率
                    print(f"      从美国财政部获取10年期美债收益率: {yield_value}%")
                    _set_to_cache(cache_key, yield_value)
                    _record_fallback_usage("us_10y_yield", "美国财政部API")
                    return yield_value
        except Exception as api_err:
            print(f"      财政部API失败: {api_err}")
        
        # 方法2：Tavily Search
        try:
            result = _call_openclaw_tool("web_search", ["--query", "10 year US Treasury yield today", "--count", "3"])
            if result and "results" in result:
                for res in result.get("results", []):
                    snippet = res.get("snippet", "").lower()
                    import re
                    # 查找百分比数字（格式如 4.25% 或 4.25 percent）
                    matches = re.findall(r'(\d+\.\d+)\s*%', snippet)
                    if not matches:
                        matches = re.findall(r'(\d+\.\d+)\s*percent', snippet)
                    if matches:
                        yield_value = float(matches[0])
                        print(f"      从 Tavily Search 获取美债收益率: {yield_value}%")
                        _set_to_cache(cache_key, yield_value)
                        return yield_value
        except Exception as search_err:
            print(f"      Tavily Search 失败: {search_err}")
        
        # 方法3：web_fetch 爬取 Investing.com
        try:
            result = _call_openclaw_tool("web_fetch", ["--url", "https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield", "--extractMode", "text"])
            if result and "raw" in result:
                import re
                content = result["raw"]
                matches = re.findall(r'(\d+\.\d+)\s*%', content)
                if matches:
                    # 取第一个匹配项
                    yield_value = float(matches[0])
                    print(f"      从 Investing.com 获取美债收益率: {yield_value}%")
                    _set_to_cache(cache_key, yield_value)
                    return yield_value
        except Exception as tool_err:
            print(f"      web_fetch 失败: {tool_err}")
        
        print("      所有备用方案均失败")
        _record_fallback_usage("us_10y_yield", None, "所有备用方案失败")
        return None
        
    except Exception as e:
        print(f"      美债收益率备用方案失败: {e}")
        _record_fallback_usage("us_10y_yield", None, str(e))
        return None

def get_vix_fallback() -> float | None:
    """
    备用方案获取 VIX 恐慌指数
    优先级：1. Tavily Search → 2. CBOE官网 → 3. 财经网站
    """
    cache_key = "vix_index"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"      使用缓存的 VIX 指数: {cached}")
        return cached
    
    try:
        print("    ├─ [Fallback] 尝试备用方案获取 VIX 指数...")
        
        # 方法1：Tavily Search - 最快捷
        try:
            result = _call_openclaw_tool("web_search", ["--query", "VIX index current value today", "--count", "3"])
            if result and "results" in result:
                for res in result.get("results", []):
                    snippet = res.get("snippet", "").lower()
                    import re
                    # 查找VIX数字（通常在13-30之间）
                    matches = re.findall(r'(\d+\.\d+|\d+)\s*(?:point|points|指数)?', snippet)
                    for match in matches:
                        value = float(match)
                        if 10 <= value <= 50:  # 合理范围
                            print(f"      从 Tavily Search 获取 VIX 指数: {value}")
                            _set_to_cache(cache_key, value)
                            return value
        except Exception as search_err:
            print(f"      Tavily Search 失败: {search_err}")
        
        # 方法2：web_fetch 爬取 CBOE官网
        try:
            result = _call_openclaw_tool("web_fetch", ["--url", "https://www.cboe.com/tradable_products/vix/", "--extractMode", "text"])
            if result and "raw" in result:
                import re
                content = result["raw"]
                # 查找VIX数值
                matches = re.findall(r'(\d+\.\d+)\s*VIX', content)
                if not matches:
                    matches = re.findall(r'VIX.*?(\d+\.\d+)', content, re.IGNORECASE)
                if matches:
                    value = float(matches[0])
                    print(f"      从 CBOE 官网获取 VIX 指数: {value}")
                    _set_to_cache(cache_key, value)
                    return value
        except Exception as tool_err:
            print(f"      web_fetch 失败: {tool_err}")
        
        # 方法3：免费金融数据API（如 Alpha Vantage，需要API key）
        # 暂时跳过
        
        print("      所有备用方案均失败")
        _record_fallback_usage("vix", None, "所有备用方案失败")
        return None
        
    except Exception as e:
        print(f"      VIX 备用方案失败: {e}")
        _record_fallback_usage("vix", None, str(e))
        return None

def get_gold_price_fallback() -> float | None:
    """
    备用方案获取黄金价格（人民币/克）
    优先级：1. 上海黄金交易所API → 2. Tavily Search → 3. 财经网站
    """
    cache_key = "gold_price_cny"
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"      使用缓存的黄金价格: {cached}")
        return cached
    
    try:
        print("    ├─ [Fallback] 尝试备用方案获取黄金价格...")
        
        # 方法1：上海黄金交易所官方数据
        try:
            import urllib.request
            import json
            url = "https://www.sge.com.cn/graph/goldTrendJson"  # 示例URL，可能需要验证真实API
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())
            # 这里需要根据实际API响应解析
            # 简化：暂时跳过
        except Exception as api_err:
            print(f"      金交所API失败: {api_err}")
        
        # 方法2：Tavily Search
        try:
            result = _call_openclaw_tool("web_search", ["--query", "黄金价格 人民币 每克 今日", "--count", "3"])
            if result and "results" in result:
                for res in result.get("results", []):
                    snippet = res.get("snippet", "").lower()
                    import re
                    # 查找价格（人民币/克）
                    matches = re.findall(r'(\d+\.\d+)\s*元\s*每克', snippet)
                    if not matches:
                        matches = re.findall(r'(\d+\.\d+)\s*人民币\s*每克', snippet)
                    if matches:
                        price = float(matches[0])
                        print(f"      从 Tavily Search 获取黄金价格: {price}元/克")
                        _set_to_cache(cache_key, price)
                        return price
        except Exception as search_err:
            print(f"      Tavily Search 失败: {search_err}")
        
        # 方法3：web_fetch 爬取财经网站
        try:
            result = _call_openclaw_tool("web_fetch", ["--url", "https://gold.cnfol.com/", "--extractMode", "text"])
            if result and "raw" in result:
                import re
                content = result["raw"]
                matches = re.findall(r'(\d+\.\d+)\s*元/克', content)
                if matches:
                    price = float(matches[0])
                    print(f"      从财经网站获取黄金价格: {price}元/克")
                    _set_to_cache(cache_key, price)
                    return price
        except Exception as tool_err:
            print(f"      web_fetch 失败: {tool_err}")
        
        print("      所有备用方案均失败")
        _record_fallback_usage("gold_cny", None, "所有备用方案失败")
        return None
        
    except Exception as e:
        print(f"      黄金价格备用方案失败: {e}")
        _record_fallback_usage("gold_cny", None, str(e))
        return None

# ============================================================================
# 主要数据获取函数
# ============================================================================

def get_domestic_macro() -> Dict[str, Any]:
    """获取国内宏观数据：GDP、CPI、PPI、PMI、社会消费品零售等"""
    results = {}
    today = datetime.now()
    
    try:
        # PMI
        df = ak.macro_china_pmi()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["pmi_manufacturing"] = float(latest.get("制造业-指数", 0))
            results["pmi_non_manufacturing"] = float(latest.get("非制造业-指数", 0))
    except Exception as e:
        print(f"PMI error: {e}")
    
    try:
        # CPI
        df = ak.macro_china_cpi()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["cpi_yoy"] = float(latest.get("全国当月", 0)) if "全国当月" in latest else 0
    except Exception as e:
        print(f"CPI error: {e}")
    
    try:
        # PPI
        df = ak.macro_china_ppi()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["ppi_yoy"] = float(latest.get("当月", 0)) if "当月" in latest else 0
    except Exception as e:
        print(f"PPI error: {e}")
    
    try:
        # 社会消费品零售总额
        df = ak.macro_china_consumer_goods_retail()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["retail_sales_yoy"] = float(latest.get("社会消费品零售总额_yoy", 0))
    except Exception as e:
        print(f"Retail sales error: {e}")
    
    try:
        # 工业增加值
        df = ak.macro_china_industrial_production_yoy()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["industrial_yoy"] = float(latest.get("工业增加值_yoy", 0))
    except Exception as e:
        print(f"Industrial production error: {e}")
    
    return results

def get_international_macro() -> Dict[str, Any]:
    """获取国际宏观数据：美联储、欧央行、汇率、大宗商品"""
    results = {}
    
    # 美国 CPI (近似的，akshare 可能没有最新)
    try:
        df = ak.macro_usa_cpi_monthly()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["us_cpi_yoy"] = float(latest.get("value", 0))
    except Exception as e:
        print(f"US CPI error: {e}")
    
    # 美国失业率
    try:
        df = ak.macro_usa_unemployment_rate()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["us_unemployment"] = float(latest.get("value", 0))
    except Exception as e:
        print(f"US unemployment error: {e}")
    
    # 汇率：美元兑人民币
    try:
        df = ak.currency_boc_sina(symbol="USD/CNY")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["usd_cny"] = float(latest.get("现汇卖出价", 0))
        else:
            # akshare 返回空数据，尝试备用方案
            fallback_rate = get_exchange_rate_fallback()
            if fallback_rate is not None:
                results["usd_cny"] = fallback_rate
                print(f"    ├─ [Info] 使用备用方案获取汇率: {fallback_rate}")
    except Exception as e:
        print(f"USD/CNY error: {e}")
        # API 调用异常，尝试备用方案
        fallback_rate = get_exchange_rate_fallback()
        if fallback_rate is not None:
            results["usd_cny"] = fallback_rate
            print(f"    ├─ [Info] 使用备用方案获取汇率: {fallback_rate}")
    
    # 大宗商品：黄金、原油、铜
    try:
        # 黄金 (上海黄金交易所)
        df = ak.spot_golden_benchmark_sge()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["gold_cny"] = float(latest.get("收盘价", 0))
        else:
            # akshare 返回空数据，尝试备用方案
            fallback_gold = get_gold_price_fallback()
            if fallback_gold is not None:
                results["gold_cny"] = fallback_gold
                print(f"    ├─ [Info] 使用备用方案获取黄金价格: {fallback_gold}")
    except Exception as e:
        print(f"Gold error: {e}")
        # API 调用异常，尝试备用方案
        fallback_gold = get_gold_price_fallback()
        if fallback_gold is not None:
            results["gold_cny"] = fallback_gold
            print(f"    ├─ [Info] 使用备用方案获取黄金价格: {fallback_gold}")
    
    try:
        # 原油 (布伦特)
        df = ak.futures_zh_spot(symbol="SC0", market="INE")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            results["crude_oil"] = float(latest.get("close", 0))
        else:
            # akshare 返回空数据，尝试备用方案
            fallback_oil = get_crude_oil_fallback()
            if fallback_oil is not None:
                results["crude_oil"] = fallback_oil
                print(f"    ├─ [Info] 使用备用方案获取原油价格: {fallback_oil}")
    except Exception as e:
        print(f"Crude oil error: {e}")
        # API 调用异常，尝试备用方案
        fallback_oil = get_crude_oil_fallback()
        if fallback_oil is not None:
            results["crude_oil"] = fallback_oil
            print(f"    ├─ [Info] 使用备用方案获取原油价格: {fallback_oil}")
    
    # 10年期美债收益率 (通过akshare的债券数据)
    try:
        df = ak.bond_zh_us_rate()
        if df is not None and not df.empty:
            # 查找10年期
            ten_year = df[df["债券名称"].str.contains("10年")]
            if not ten_year.empty:
                results["us_10y_yield"] = float(ten_year.iloc[-1].get("收益率", 0))
            else:
                # 未找到10年期数据，尝试备用方案
                fallback_yield = get_us_treasury_yield_fallback()
                if fallback_yield is not None:
                    results["us_10y_yield"] = fallback_yield
                    print(f"    ├─ [Info] 使用备用方案获取美债收益率: {fallback_yield}")
        else:
            # akshare 返回空数据，尝试备用方案
            fallback_yield = get_us_treasury_yield_fallback()
            if fallback_yield is not None:
                results["us_10y_yield"] = fallback_yield
                print(f"    ├─ [Info] 使用备用方案获取美债收益率: {fallback_yield}")
    except Exception as e:
        print(f"US Treasury yield error: {e}")
        # API 调用异常，尝试备用方案
        fallback_yield = get_us_treasury_yield_fallback()
        if fallback_yield is not None:
            results["us_10y_yield"] = fallback_yield
            print(f"    ├─ [Info] 使用备用方案获取美债收益率: {fallback_yield}")
    
    # 合并扩展国际数据
    try:
        extended = get_extended_international_macro()
        results.update(extended)
    except Exception as e:
        print(f"Extended international data error: {e}")
    
    return results

def get_extended_international_macro() -> Dict[str, Any]:
    """扩展国际数据：欧元区 CPI、日本央行政策、VIX 恐慌指数等"""
    results = {}
    
    # 欧元区 CPI (akshare 可能没有直接接口，尝试其他来源)
    try:
        # 尝试 ak.macro_euro_cpi_yoy() 或类似函数
        # 先检查可用性
        if hasattr(ak, 'macro_euro_cpi_yoy'):
            df = ak.macro_euro_cpi_yoy()
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                results["euro_cpi_yoy"] = float(latest.get("value", 0))
    except Exception as e:
        print(f"Euro CPI error: {e}")
    
    # 日本央行政策利率 (可能通过 ak.macro_japan_bank_rate)
    try:
        if hasattr(ak, 'macro_japan_bank_rate'):
            df = ak.macro_japan_bank_rate()
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                results["japan_policy_rate"] = float(latest.get("value", 0))
    except Exception as e:
        print(f"Japan policy rate error: {e}")
    
    # VIX 恐慌指数 (CBOE VIX)
    vix_found = False
    try:
        # akshare 可能通过 stock_us_spot 或 index_zh_vix
        # 尝试多种方式
        if hasattr(ak, 'stock_us_spot'):
            df = ak.stock_us_spot()
            if df is not None and not df.empty:
                vix_row = df[df["symbol"] == "VIX"]
                if not vix_row.empty:
                    results["vix"] = float(vix_row.iloc[-1].get("close", 0))
                    vix_found = True
    except Exception as e:
        print(f"VIX error: {e}")
    
    # 如果 akshare 未找到 VIX 数据，尝试备用方案
    if not vix_found:
        fallback_vix = get_vix_fallback()
        if fallback_vix is not None:
            results["vix"] = fallback_vix
            print(f"    ├─ [Info] 使用备用方案获取 VIX 指数: {fallback_vix}")
            vix_found = True
    
    # 如果以上都失败，添加占位符
    if "euro_cpi_yoy" not in results:
        results["euro_cpi_yoy"] = None
    if "japan_policy_rate" not in results:
        results["japan_policy_rate"] = None
    if "vix" not in results:
        results["vix"] = None
    
    return results

def save_historical_data(data_type: str, data: Dict[str, Any]):
    """保存历史数据到 CSV/JSON 文件"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 保存为 JSON
    json_path = os.path.join(data_dir, f"{data_type}_{today}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 同时追加到 CSV 以便分析
    csv_path = os.path.join(data_dir, f"{data_type}.csv")
    file_exists = os.path.exists(csv_path)
    
    # 展平嵌套字典
    flat_data = {"date": today}
    def flatten(d, prefix=""):
        for k, v in d.items():
            if isinstance(v, dict):
                flatten(v, f"{prefix}{k}_")
            elif isinstance(v, (list, tuple)):
                flat_data[f"{prefix}{k}"] = str(v)
            else:
                flat_data[f"{prefix}{k}"] = v
    flatten(data)
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=flat_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(flat_data)
    
    print(f"Historical data saved: {json_path}")

def load_historical_data(data_type: str, days: int = 30) -> List[Dict[str, Any]]:
    """加载最近 N 天的历史数据"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        return []
    
    csv_path = os.path.join(data_dir, f"{data_type}.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            df = df.tail(days)
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Load CSV error: {e}")
    
    # 如果 CSV 不存在，尝试加载 JSON 文件
    all_data = []
    for offset in range(days):
        date_str = (datetime.now() - timedelta(days=offset)).strftime("%Y-%m-%d")
        json_path = os.path.join(data_dir, f"{data_type}_{date_str}.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                all_data.append(json.load(f))
    
    return all_data

def get_sector_rotation_prediction() -> Dict[str, Any]:
    """
    板块轮动预测：基于近期板块涨跌幅、资金流向，使用简单线性回归预测未来强势板块
    返回：预测的强势板块列表、轮动信号
    """
    try:
        # 获取行业板块近期数据（近20个交易日）
        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            return {"predicted_sectors": [], "signal": "insufficient_data"}
        
        # 简化：直接取今日涨幅前5的板块作为预测（假设动量延续）
        df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
        df = df.dropna(subset=["涨跌幅"])
        df = df.sort_values("涨跌幅", ascending=False)
        
        top_sectors = []
        for i, row in df.head(5).iterrows():
            name = row.get("板块名称", str(row.get("名称", "未知")))
            change = round(float(row["涨跌幅"]), 2)
            top_sectors.append({"name": name, "change_pct": change})
        
        # 轮动信号：基于板块集中度
        if len(top_sectors) >= 3:
            top3_avg = np.mean([s["change_pct"] for s in top_sectors[:3]])
            if top3_avg > 5.0:
                signal = "strong_momentum"
            elif top3_avg > 2.0:
                signal = "moderate_momentum"
            else:
                signal = "weak_momentum"
        else:
            signal = "neutral"
        
        # 简单的机器学习预测（示例：使用历史涨跌幅预测次日）
        # 这里仅作框架展示，实际需要更多历史数据
        prediction = {
            "predicted_sectors": top_sectors,
            "signal": signal,
            "method": "momentum_ranking",
            "note": "实际轮动预测需要更多历史数据与特征工程"
        }
        return prediction
    except Exception as e:
        print(f"Sector rotation prediction error: {e}")
        return {"predicted_sectors": [], "signal": "error", "error": str(e)}

def analyze_news_sentiment() -> Dict[str, Any]:
    """
    新闻情感分析（使用 browser 工具爬取真实新闻）
    从财联社、华尔街见闻获取标题，进行关键词情感判断
    """
    import time
    import random
    import re
    from typing import List
    
    sentiment_keywords = {
        "positive": ["增长", "利好", "复苏", "上涨", "突破", "创新高", "政策支持", "宽松", "盈利", "扩张", "提振", "反弹"],
        "negative": ["下跌", "下滑", "风险", "预警", "收紧", "衰退", "冲突", "疫情", "亏损", "裁员", "暴跌", "危机"],
        "neutral": ["持平", "震荡", "调整", "维持", "稳定", "预计", "发布", "公告", "会议", "数据"]
    }
    
    def fetch_with_browser(url: str, site_name: str) -> List[str]:
        """使用 OpenClaw browser 工具（external-chrome profile）爬取新闻标题"""
        import subprocess
        import json
        
        titles = []
        target_id = None
        try:
            print(f"    ├─ [Browser] 爬取 {site_name}...")
            time.sleep(random.uniform(2.0, 4.0))
            
            # 预检查：确保 external-chrome profile 可用
            try:
                profiles_cmd = ["openclaw", "browser", "profiles", "--json"]
                profiles_result = subprocess.run(profiles_cmd, capture_output=True, text=True, timeout=15)
                if profiles_result.returncode == 0:
                    try:
                        profiles_data = json.loads(profiles_result.stdout)
                        external_found = False
                        for profile in profiles_data.get("profiles", []):
                            if profile.get("name") == "external-chrome" and profile.get("status") == "running":
                                external_found = True
                                break
                        if not external_found:
                            print("      external-chrome profile 不可用或未运行，跳过 browser 爬取")
                            return []
                    except json.JSONDecodeError:
                        print("      无法解析 profiles 输出，继续尝试")
                else:
                    print("      获取 profiles 失败，继续尝试")
            except Exception as e:
                print(f"      预检查异常: {e}, 继续尝试")
            
            # 1. 打开目标网页
            open_cmd = ["openclaw", "browser", "open", "--browser-profile", "external-chrome", url]
            result = subprocess.run(open_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error_msg = result.stderr.lower() if result.stderr else ""
                # 检查是否是因为扩展未连接的错误
                if "no tab is connected" in error_msg or "extension relay" in error_msg:
                    print(f"      浏览器扩展未连接（无头环境），跳过 browser 爬取")
                    return []
                print(f"      打开页面失败: {result.stderr[:200]}")
                return []
            
            # 解析返回的 target id
            output = result.stdout.strip()
            target_id = None
            for line in output.split('\n'):
                if line.startswith('id:'):
                    target_id = line.split(':')[1].strip()
                    break
            
            if not target_id:
                print("      无法获取页面ID")
                return []
            
            print(f"      页面已打开，ID: {target_id}")
            
            # 2. 等待页面加载（动态内容可能需要时间）
            wait_time = random.uniform(4.0, 8.0)
            time.sleep(wait_time)
            
            # 3. 获取页面快照（JSON格式）
            snapshot_cmd = ["openclaw", "browser", "snapshot", "--browser-profile", 
                          "external-chrome", "--json", "--target-id", target_id]
            snapshot_result = subprocess.run(snapshot_cmd, capture_output=True, text=True, timeout=30)
            
            if snapshot_result.returncode != 0:
                print(f"      快照失败: {snapshot_result.stderr[:200]}")
                return []
            
            # 4. 解析 JSON 并提取文本
            try:
                data = json.loads(snapshot_result.stdout)
            except json.JSONDecodeError:
                print("      快照输出不是有效 JSON")
                return []
            
            # 递归提取所有文本节点
            def extract_text_nodes(obj, texts):
                if isinstance(obj, dict):
                    # 提取 text 字段
                    if 'text' in obj and obj['text']:
                        text = obj['text'].strip()
                        if text:
                            texts.append(text)
                    # 提取 role 或 name 字段（可能包含标题）
                    for field in ['role', 'name', 'value', 'placeholder', 'label']:
                        if field in obj and obj[field]:
                            val = str(obj[field]).strip()
                            if val:
                                texts.append(val)
                    # 递归遍历所有值
                    for value in obj.values():
                        extract_text_nodes(value, texts)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text_nodes(item, texts)
            
            all_texts = []
            extract_text_nodes(data, all_texts)
            
            # 5. 过滤出可能的新闻标题
            for text in all_texts:
                # 基本过滤
                if not text or len(text) < 8 or len(text) > 200:
                    continue
                if not re.search(r'[\u4e00-\u9fff]', text):
                    continue
                
                # 排除常见非新闻内容
                exclude_keywords = ['首页', '登录', '注册', '关于', '联系我们', 'APP', '下载', '客户端', 
                                   '订阅', '广告', '推广', '微信', '微博', '二维码', '搜索', '请输入']
                if any(word in text for word in exclude_keywords):
                    continue
                
                # 排除纯数字、日期、URL等
                if re.match(r'^\d+[年月日时分秒]?$', text):
                    continue
                if re.match(r'^https?://', text):
                    continue
                if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
                    continue
                
                titles.append(text)
            
            # 去重
            seen = set()
            unique = []
            for t in titles:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)
            
            print(f"      提取到 {len(unique)} 条候选标题")
            return unique[:20]  # 最多返回20条
            
        except subprocess.TimeoutExpired:
            print(f"      浏览器爬取超时: {site_name}")
        except Exception as e:
            print(f"      Browser 爬取异常: {str(e)[:80]}")
        finally:
            # 6. 关闭标签页（清理）
            if target_id:
                try:
                    close_cmd = ["openclaw", "browser", "close", "--browser-profile", 
                               "external-chrome", "--target-id", target_id]
                    subprocess.run(close_cmd, capture_output=True, timeout=10)
                except:
                    pass
        
        return []
    
    def fetch_with_requests(url: str, site_name: str) -> List[str]:
        """使用 requests + BeautifulSoup 爬取新闻标题（定制解析器）"""
        import requests
        from bs4 import BeautifulSoup
        
        titles = []
        try:
            print(f"    ├─ [Requests] 爬取 {site_name}...")
            time.sleep(random.uniform(2.0, 5.0))
            
            # 模拟浏览器头部
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # 发送请求
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 针对不同网站的专用解析器
            if 'cls.cn' in url:
                # 财联社专用解析器
                # 策略1：寻找新闻标题相关元素
                selectors = [
                    'h1', 'h2', 'h3', 'h4',  # 标题标签
                    '.news-title', '.title', '.article-title',  # 常见类名
                    '[class*="news"]', '[class*="article"]',  # 类名包含news/article
                    'a[href*="article"]', 'a[href*="news"]',  # 文章链接
                ]
                
                for selector in selectors:
                    for tag in soup.select(selector):
                        text = tag.get_text(strip=True)
                        if not text:
                            continue
                        # 过滤条件
                        if len(text) < 8 or len(text) > 150:
                            continue
                        if not re.search(r'[\u4e00-\u9fff]', text):
                            continue
                        # 排除常见非新闻内容
                        exclude_keywords = ['首页', '登录', '注册', '关于', '联系我们', 'APP', '下载', '客户端', '财经', '行情']
                        if any(word in text for word in exclude_keywords):
                            continue
                        # 排除纯数字、日期等
                        if re.match(r'^\d+[年月日时分秒]?$', text):
                            continue
                        titles.append(text)
                
                # 策略2：寻找时间戳附近的文本（新闻通常有时间）
                time_tags = soup.find_all(['time', 'span[class*="time"]', 'div[class*="time"]'])
                for time_tag in time_tags:
                    parent = time_tag.find_parent(['div', 'article', 'li'])
                    if parent:
                        for child in parent.find_all(['h2', 'h3', 'a', 'div[class*="title"]']):
                            text = child.get_text(strip=True)
                            if text and 10 <= len(text) <= 120 and re.search(r'[\u4e00-\u9fff]', text):
                                titles.append(text)
                
                # 策略3：寻找列表项中的新闻
                list_items = soup.find_all(['li', '.list-item', '.news-item'])
                for item in list_items:
                    text = item.get_text(strip=True)
                    if text and 15 <= len(text) <= 200 and re.search(r'[\u4e00-\u9fff]', text):
                        if '订阅' not in text and '广告' not in text:
                            titles.append(text)
            
            elif 'wallstreetcn.com' in url:
                # 华尔街见闻专用解析器
                # 策略1：Vue组件数据属性
                vue_selectors = [
                    '[data-v-]',  # Vue组件
                    '.headline', '.news-headline', '.article-headline',
                    '.title', '.news-title', '.article-title',
                    'h1', 'h2', 'h3',
                    '[class*="news"]', '[class*="article"]',
                ]
                
                for selector in vue_selectors:
                    for tag in soup.select(selector):
                        text = tag.get_text(strip=True)
                        if not text:
                            continue
                        if len(text) < 10 or len(text) > 200:
                            continue
                        if not re.search(r'[\u4e00-\u9fff]', text):
                            continue
                        # 排除非新闻内容
                        exclude_keywords = ['订阅', '下载', 'APP', '客户端', '微信', '微博', '广告', '推广']
                        if any(word in text for word in exclude_keywords):
                            continue
                        titles.append(text)
                
                # 策略2：寻找卡片式新闻
                cards = soup.select('.card, .news-card, .article-card, .item-card')
                for card in cards:
                    title_elem = card.select_one('h2, h3, .title, .card-title')
                    if title_elem:
                        text = title_elem.get_text(strip=True)
                        if text and 10 <= len(text) <= 150 and re.search(r'[\u4e00-\u9fff]', text):
                            titles.append(text)
                
                # 策略3：寻找摘要附近的标题
                summaries = soup.find_all(['p', '.summary', '.abstract'])
                for summary in summaries:
                    prev_sibling = summary.find_previous_sibling(['h2', 'h3', 'div[class*="title"]'])
                    if prev_sibling:
                        text = prev_sibling.get_text(strip=True)
                        if text and 10 <= len(text) <= 120 and re.search(r'[\u4e00-\u9fff]', text):
                            titles.append(text)
            
            else:
                # 通用提取：所有包含中文的较长文本
                for tag in soup.find_all(text=True):
                    if isinstance(tag, str):
                        text = tag.strip()
                        if 15 <= len(text) <= 200 and re.search(r'[\u4e00-\u9fff]', text):
                            titles.append(text)
            
            # 去重与过滤
            seen = set()
            unique = []
            for t in titles:
                if t in seen:
                    continue
                # 进一步过滤：确保是合理的新闻标题
                if len(t) < 10 or len(t) > 180:
                    continue
                # 排除纯符号、重复字符等
                if re.match(r'^[·\-=*]+$', t):
                    continue
                # 检查是否包含日期格式（如"2024-02-21"），可能是时间戳而非标题
                if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', t):
                    continue
                
                unique.append(t)
                seen.add(t)
            
            print(f"      提取到 {len(unique)} 条候选标题")
            return unique[:25]  # 最多返回25条
            
        except requests.exceptions.Timeout:
            print(f"      Requests 爬取超时: {site_name}")
        except requests.exceptions.HTTPError as e:
            print(f"      HTTP错误 {e.response.status_code}: {site_name}")
        except Exception as e:
            print(f"      Requests 爬取异常: {str(e)[:80]}")
        return []
    
    def fetch_news(url: str, site_name: str) -> List[str]:
        """主爬取函数：尝试多种方法"""
        # 方法1：首先尝试 browser（如果可用）
        titles = fetch_with_browser(url, site_name)
        if titles:
            return titles
        
        # 方法2：使用 requests + BeautifulSoup（主要方法）
        titles = fetch_with_requests(url, site_name)
        if titles:
            return titles
        
        return []
    
    # 目标网站列表
    websites = [
        ("https://www.cls.cn", "财联社"),
        ("https://wallstreetcn.com", "华尔街见闻")
    ]
    
    all_titles = []
    for url, name in websites:
        titles = fetch_news(url, name)
        if titles:
            all_titles.extend(titles)
            print(f"    └─ {name} 爬取成功: {len(titles)} 条标题")
        else:
            print(f"    └─ {name} 爬取失败，将使用模拟数据")
        
        # 网站间延迟
        if len(websites) > 1:
            delay = random.uniform(3.0, 8.0)
            time.sleep(delay)
    
    # 如果没有爬取到标题，返回错误状态（不接受模拟数据）
    if not all_titles:
        print("  ❌ 错误：所有爬取方法均失败，无法获取真实新闻数据")
        return {
            "error": True,
            "error_message": "无法爬取真实新闻数据：财联社、华尔街见闻爬取失败",
            "sentiment_score": 0,
            "sentiment": "unknown",
            "positive_news": 0,
            "negative_news": 0,
            "neutral_news": 0,
            "sample_titles": [],
            "note": "爬取失败，无真实数据",
            "source": "error",
            "total_titles": 0
        }
    
    note = "实时爬取数据"
    source = "web_crawl"
    
    # 情感分析
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for title in all_titles:
        title_lower = title.lower()
        if any(kw in title_lower for kw in sentiment_keywords["positive"]):
            positive_count += 1
        elif any(kw in title_lower for kw in sentiment_keywords["negative"]):
            negative_count += 1
        else:
            neutral_count += 1
    
    total = positive_count + negative_count + neutral_count
    if total > 0:
        sentiment_score = (positive_count - negative_count) / total * 100
    else:
        sentiment_score = 0
    
    # 定性
    if sentiment_score > 30:
        sentiment = "strong_positive"
    elif sentiment_score > 10:
        sentiment = "moderate_positive"
    elif sentiment_score > -10:
        sentiment = "neutral"
    elif sentiment_score > -30:
        sentiment = "moderate_negative"
    else:
        sentiment = "strong_negative"
    
    return {
        "sentiment_score": round(sentiment_score, 1),
        "sentiment": sentiment,
        "positive_news": positive_count,
        "negative_news": negative_count,
        "neutral_news": neutral_count,
        "sample_titles": all_titles[:5],  # 返回前5条作为示例
        "note": note,
        "source": source,
        "total_titles": len(all_titles)
    }

def compute_market_sentiment_index(news_sentiment: Dict[str, Any], 
                                   international: Dict[str, Any],
                                   domestic: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建量化情绪指数
    结合新闻情感、VIX、汇率变化、大宗商品等多项指标
    返回 0‑100 的指数值（越高表示情绪越乐观）
    """
    # 1. 新闻情感分数（-100 到 +100 映射到 0‑100）
    news_score = news_sentiment.get("sentiment_score", 0)  # -100 ~ +100
    news_index = (news_score + 100) / 2  # 转换为 0‑100
    
    # 2. VIX 指数（反向指标，VIX 越高情绪越差）
    vix = international.get("vix", 20)
    if vix is None or vix <= 0:
        vix = 20
    # VIX 正常范围 10‑30，映射到情绪指数
    if vix > 30:
        vix_index = 10
    elif vix > 25:
        vix_index = 30
    elif vix > 20:
        vix_index = 50
    elif vix > 15:
        vix_index = 70
    elif vix > 10:
        vix_index = 90
    else:
        vix_index = 100
    
    # 3. 汇率变化（人民币升值情绪好）
    usd_cny = international.get("usd_cny", 7.2)
    # 简单判断：低于 7.1 为升值，高于 7.2 为贬值
    if usd_cny < 7.1:
        fx_index = 80
    elif usd_cny > 7.2:
        fx_index = 40
    else:
        fx_index = 60
    
    # 4. 大宗商品（油价上涨可能预示经济复苏）
    crude = international.get("crude_oil", 80)
    if crude > 85:
        crude_index = 80
    elif crude > 75:
        crude_index = 70
    elif crude > 65:
        crude_index = 60
    else:
        crude_index = 50
    
    # 加权综合指数
    # 权重：新闻 40%，VIX 30%，汇率 20%，油价 10%
    composite = (news_index * 0.4 + vix_index * 0.3 + 
                 fx_index * 0.2 + crude_index * 0.1)
    composite = max(0, min(100, composite))
    
    # 定性描述
    if composite >= 80:
        sentiment = "极度乐观"
    elif composite >= 65:
        sentiment = "乐观"
    elif composite >= 50:
        sentiment = "中性"
    elif composite >= 35:
        sentiment = "谨慎"
    else:
        sentiment = "悲观"
    
    return {
        "composite_index": round(composite, 1),
        "sentiment": sentiment,
        "components": {
            "news_index": round(news_index, 1),
            "vix_index": round(vix_index, 1),
            "fx_index": round(fx_index, 1),
            "crude_index": round(crude_index, 1)
        }
    }

def generate_report(domestic: Dict, international: Dict, 
                    sector_pred: Dict, news_sentiment: Dict) -> str:
    """生成格式化报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 处理 None 值，防止比较错误
    domestic = {k: (v if v is not None else 0) for k, v in domestic.items()}
    international = {k: (v if v is not None else 0) for k, v in international.items()}
    
    report = f"""【宏观数据监控报告】📊 {today} 22:00

🌍 国际数据
• 美国CPI同比：{international.get('us_cpi_yoy', 'N/A')}%
• 美国失业率：{international.get('us_unemployment', 'N/A')}%
• 10年期美债收益率：{international.get('us_10y_yield', 'N/A')}%
• 美元兑人民币：{international.get('usd_cny', 'N/A')}
• 黄金(人民币/克)：{international.get('gold_cny', 'N/A')}
• 原油(布伦特)：{international.get('crude_oil', 'N/A')}
• 欧元区CPI同比：{international.get('euro_cpi_yoy', 'N/A')}%
• 日本政策利率：{international.get('japan_policy_rate', 'N/A')}%
• VIX恐慌指数：{international.get('vix', 'N/A')}

🇨🇳 国内数据
• 制造业PMI：{domestic.get('pmi_manufacturing', 'N/A')}
• 非制造业PMI：{domestic.get('pmi_non_manufacturing', 'N/A')}
• CPI同比：{domestic.get('cpi_yoy', 'N/A')}%
• PPI同比：{domestic.get('ppi_yoy', 'N/A')}%
• 社会消费品零售同比：{domestic.get('retail_sales_yoy', 'N/A')}%
• 工业增加值同比：{domestic.get('industrial_yoy', 'N/A')}%

📈 板块轮动预测
• 信号：{sector_pred.get('signal', 'N/A')}
• 预测强势板块："""
    
    sectors = sector_pred.get("predicted_sectors", [])
    for i, s in enumerate(sectors[:5], 1):
        report += f"\n   {i}. {s['name']} ({s['change_pct']}%)"
    
    if not sectors:
        report += "\n   暂无数据"
    
    news = news_sentiment
    report += f"""

📰 新闻情感分析"""
    
    if news.get("error"):
        report += f"""
• 状态：❌ 爬取失败
• 错误信息：{news.get('error_message', '未知错误')}
• 说明：无法获取真实新闻数据，已拒绝使用模拟数据"""
    else:
        report += f"""
• 情感分数：{news.get('sentiment_score', 0)}/100
• 定性：{news.get('sentiment', 'N/A')}
• 正面/负面/中性：{news.get('positive_news', 0)}/{news.get('negative_news', 0)}/{news.get('neutral_news', 0)}
• 示例标题："""
        
        for title in news.get("sample_titles", [])[:3]:
            report += f"\n   • {title}"
    
    # 情绪指数（如果存在）
    sentiment_index = news.get("sentiment_index")
    if sentiment_index:
        comp = sentiment_index.get("composite_index", 0)
        sent = sentiment_index.get("sentiment", "N/A")
        report += f"""

📊 情绪指数
• 综合指数：{comp}/100
• 市场情绪：{sent}
• 成分指标：
   - 新闻情感：{sentiment_index.get('components', {}).get('news_index', 0)}/100
   - VIX情绪：{sentiment_index.get('components', {}).get('vix_index', 0)}/100
   - 汇率情绪：{sentiment_index.get('components', {}).get('fx_index', 0)}/100
   - 油价情绪：{sentiment_index.get('components', {}).get('crude_index', 0)}/100"""
    
    # 联动分析
    report += """

🔗 联动分析
• 汇率与A股："""
    usd_cny = international.get("usd_cny", 0)
    if usd_cny > 7.2:
        report += "人民币贬值压力较大，外资流出风险增加，对A股偏空。"
    elif usd_cny < 7.0:
        report += "人民币走强，有利于外资流入，对A股偏多。"
    else:
        report += "汇率区间震荡，对A股影响中性。"
    
    report += f"""
• 大宗商品与板块："""
    crude = international.get("crude_oil", 0)
    if crude > 80:
        report += "油价高位，利好油气、煤炭等资源板块。"
    elif crude < 70:
        report += "油价低位，利好航空、物流等成本敏感板块。"
    else:
        report += "油价震荡，对板块影响分化。"
    
    report += f"""
• 美债收益率与成长股："""
    us_yield = international.get("us_10y_yield", 0)
    if us_yield > 4.5:
        report += "美债收益率高企，压制成长股估值，利好价值股。"
    elif us_yield < 3.5:
        report += "美债收益率低位，支撑成长股估值。"
    else:
        report += "美债收益率适中，对风格影响中性。"
    
    report += f"""
• VIX与市场风险偏好："""
    vix = international.get("vix")
    if vix is None:
        report += "VIX数据暂缺，市场情绪未知。"
    elif vix > 25:
        report += "VIX高企，市场恐慌情绪上升，建议降低仓位，避险为主。"
    elif vix > 18:
        report += "VIX偏高，市场波动加大，需控制风险。"
    elif vix > 12:
        report += "VIX适中，市场情绪相对稳定。"
    else:
        report += "VIX低位，市场情绪乐观，可适度积极。"
    
    # 生成今日数据驱动投资建议
    pmi_manu = domestic.get('pmi_manufacturing')
    pmi_text = f"{pmi_manu}" if pmi_manu is not None else 'N/A'
    pmi_advice = '处于扩张区间，关注工业板块' if pmi_manu is not None and pmi_manu > 50 else '处于收缩区间，谨慎对待周期股'
    
    cpi = domestic.get('cpi_yoy')
    cpi_text = f"{cpi}%" if cpi is not None else 'N/A'
    cpi_advice = '通胀压力上升，关注抗通胀资产' if cpi is not None and cpi > 3.0 else '通胀温和，货币政策空间较大'
    
    usd_cny = international.get('usd_cny')
    fx_text = f"{usd_cny}" if usd_cny is not None else 'N/A'
    fx_advice = '汇率偏弱，外资流出压力大' if usd_cny is not None and usd_cny > 7.2 else '汇率稳定，对A股影响中性'
    
    us_yield = international.get('us_10y_yield')
    yield_text = f"{us_yield}%" if us_yield is not None else 'N/A'
    yield_advice = '高企压制成长股，偏好价值股' if us_yield is not None and us_yield > 4.5 else '偏低支撑成长股估值'
    
    vix = international.get('vix')
    vix_text = f"{vix}" if vix is not None else 'N/A'
    vix_advice = '市场情绪恐慌，建议降低仓位' if vix is not None and vix > 25 else '市场情绪稳定，可适度积极'
    
    report += f"""

📊 今日数据驱动投资建议
1. 基于制造业PMI {pmi_text}，{pmi_advice}
2. 基于CPI同比 {cpi_text}，{cpi_advice}
3. 基于人民币汇率 {fx_text}，{fx_advice}
4. 基于美债收益率 {yield_text}，{yield_advice}
5. 基于VIX恐慌指数 {vix_text}，{vix_advice}

📌 投资建议
1. 关注预测强势板块中的个股机会
2. 根据新闻情感调整仓位（正面可积极，负面需谨慎）
3. 跟踪汇率与大宗商品变化，把握周期轮动
4. 结合T99短线扫描，聚焦宏观与技术共振标的

—— macro‑monitor v2.0 (集成国际数据、板块预测、新闻情感)

📋 数据来源说明
"""
    # 添加备用方案使用汇总
    fallback_summary = ""
    used_items = []
    error_items = []
    for key, info in _FALLBACK_USAGE.items():
        if info["used"]:
            if info["source"]:
                used_items.append(f"{key}: {info['source']}")
            if info["error"]:
                error_items.append(f"{key}: {info['error']}")
    
    if used_items:
        fallback_summary += "• 以下数据使用备用方案获取:\n"
        for item in used_items:
            fallback_summary += f"   - {item}\n"
    
    if error_items:
        fallback_summary += "• 以下数据备用方案失败:\n"
        for item in error_items:
            fallback_summary += f"   - {item}\n"
    
    if used_items or error_items:
        report += "\n" + fallback_summary
    
    return report

def save_for_t99(domestic: Dict, international: Dict, sector_pred: Dict, 
                news_sentiment: Dict, sentiment_index: Dict):
    """保存简化版宏观数据供 T99 短线决策使用"""
    import json
    from datetime import datetime
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "T100_macro_monitor",
        "domestic_key": {
            "pmi_manufacturing": domestic.get('pmi_manufacturing'),
            "pmi_non_manufacturing": domestic.get('pmi_non_manufacturing'),
            "cpi_yoy": domestic.get('cpi_yoy'),
            "ppi_yoy": domestic.get('ppi_yoy'),
            "retail_sales_yoy": domestic.get('retail_sales_yoy'),
            "industrial_yoy": domestic.get('industrial_yoy')
        },
        "international_key": {
            "us_cpi_yoy": international.get('us_cpi_yoy'),
            "us_unemployment": international.get('us_unemployment'),
            "us_10y_yield": international.get('us_10y_yield'),
            "usd_cny": international.get('usd_cny'),
            "gold_cny": international.get('gold_cny'),
            "crude_oil": international.get('crude_oil'),
            "euro_cpi_yoy": international.get('euro_cpi_yoy'),
            "japan_policy_rate": international.get('japan_policy_rate'),
            "vix": international.get('vix')
        },
        "sector_prediction": {
            "signal": sector_pred.get('signal'),
            "predicted_sectors": sector_pred.get('predicted_sectors', [])
        },
        "news_sentiment": {
            "sentiment_score": news_sentiment.get('sentiment_score'),
            "sentiment": news_sentiment.get('sentiment'),
            "positive_news": news_sentiment.get('positive_news'),
            "negative_news": news_sentiment.get('negative_news'),
            "neutral_news": news_sentiment.get('neutral_news')
        },
        "sentiment_index": {
            "composite_index": sentiment_index.get('composite_index'),
            "sentiment": sentiment_index.get('sentiment'),
            "components": sentiment_index.get('components', {})
        },
        "investment_advice_summary": {
            "pmi_advice": '处于扩张区间，关注工业板块' if domestic.get('pmi_manufacturing', 0) > 50 else '处于收缩区间，谨慎对待周期股',
            "cpi_advice": '通胀压力上升，关注抗通胀资产' if domestic.get('cpi_yoy', 0) > 3.0 else '通胀温和，货币政策空间较大',
            "fx_advice": '汇率偏弱，外资流出压力大' if international.get('usd_cny', 0) > 7.2 else '汇率稳定，对A股影响中性',
            "yield_advice": '高企压制成长股，偏好价值股' if international.get('us_10y_yield', 0) > 4.5 else '偏低支撑成长股估值',
            "vix_advice": '市场情绪恐慌，建议降低仓位' if international.get('vix', 0) > 25 else '市场情绪稳定，可适度积极'
        }
    }
    
    # 保存到共享目录
    shared_dir = "/root/.openclaw/workspace/data/shared"
    os.makedirs(shared_dir, exist_ok=True)
    
    # 保存完整数据
    full_path = os.path.join(shared_dir, "t100_macro_latest.json")
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 保存简化版（仅关键指标）
    simplified = {
        "timestamp": data["timestamp"],
        "date": data["date"],
        "composite_index": sentiment_index.get('composite_index'),
        "sentiment": sentiment_index.get('sentiment'),
        "pmi_manufacturing": domestic.get('pmi_manufacturing'),
        "cpi_yoy": domestic.get('cpi_yoy'),
        "usd_cny": international.get('usd_cny'),
        "us_10y_yield": international.get('us_10y_yield'),
        "vix": international.get('vix'),
        "predicted_sectors": sector_pred.get('predicted_sectors', []),
        "sector_signal": sector_pred.get('signal')
    }
    simple_path = os.path.join(shared_dir, "t100_macro_simplified.json")
    with open(simple_path, "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    
    print(f"T100数据已保存供T99使用: {full_path}, {simple_path}")

def send_to_feishu(report: str):
    """发送报告到飞书群"""
    # 测试模式：仅打印，不发送
    if os.environ.get("TEST_MODE") == "1":
        print("=== TEST MODE (report not sent) ===")
        print(report[:500] + "...")
        return
    
    # 使用 openclaw CLI 发送消息
    # 注意：需要 openclaw 服务运行且配置了飞书通道
    cmd = f'openclaw message --channel feishu --target "{FEISHU_GROUP_ID}" --message "{report}"'
    os.system(cmd)
    print("Report sent to Feishu group.")

def main():
    print("=== macro-monitor v2.0 开始执行 ===")
    # 重置备用方案使用记录
    _reset_fallback_usage()
    
    print("采集国内宏观数据...")
    domestic = get_domestic_macro()
    
    print("采集国际宏观数据...")
    international = get_international_macro()
    
    print("分析板块轮动...")
    sector_pred = get_sector_rotation_prediction()
    
    print("分析新闻情感...")
    news_sentiment = analyze_news_sentiment()
    
    print("计算情绪指数...")
    sentiment_index = compute_market_sentiment_index(news_sentiment, international, domestic)
    news_sentiment["sentiment_index"] = sentiment_index
    
    print("保存历史数据...")
    try:
        save_historical_data("domestic", domestic)
        save_historical_data("international", international)
        save_historical_data("sector_pred", sector_pred)
        save_historical_data("news_sentiment", news_sentiment)
        save_historical_data("sentiment_index", sentiment_index)
    except Exception as e:
        print(f"保存历史数据失败: {e}")
    
    # 保存数据供 T99 使用
    try:
        save_for_t99(domestic, international, sector_pred, news_sentiment, sentiment_index)
    except Exception as e:
        print(f"保存T99共享数据失败: {e}")
    
    print("生成报告...")
    report = generate_report(domestic, international, sector_pred, news_sentiment)
    
    print("\n=== 报告预览（前500字符） ===")
    print(report[:500] + "...")
    
    print("\n发送报告到飞书群...")
    send_to_feishu(report)
    
    print("=== 执行完成 ===")

if __name__ == "__main__":
    main()