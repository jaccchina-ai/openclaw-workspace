# 问题：T100宏观监控系统原油数据获取失败

## 背景
T100宏观监控系统每日22:00（北京时间）生成宏观数据报告，需要获取布伦特原油价格作为国际数据的一部分。系统采用三层数据获取策略：
1. **第一层（优先）**: yfinance库获取Brent原油期货（BZ=F）或WTI原油（CL=F）
2. **第二层（备选）**: AKShare库获取上海国际能源交易中心原油期货（symbol="SC0", market="INE"）
3. **第三层（备用）**: 多种备用方案（Playwright爬取、免费API、web_fetch等）

## 当前问题
在2026-03-07 22:00的执行中，原油数据获取完全失败，报告显示"原油(布伦特): N/A"。具体错误链：

### 错误1：AKShare API失败
```
Crude oil error: list index out of range
```
这个错误发生在`ak.futures_zh_spot(symbol="SC0", market="INE")`调用中，表明API返回的数据结构异常或为空。

### 错误2：Playwright爬取失败
```
尝试 Playwright 爬取 Investing.com: https://www.investing.com/commodities/brent-oil
Playwright 结果中没有内容字段
Playwright 原油价格获取返回空值
```
Playwright爬虫未能从Investing.com提取到有效价格数据。

### 错误3：web_fetch命令未知
```
web_fetch 命令失败: error: unknown command 'web_fetch'
```
调用OpenClaw CLI的web_fetch工具时，命令未被识别。

### 问题复杂性
- **多层故障**：三个独立数据源同时失败，表明可能存在系统性问题
- **环境依赖**：cron执行环境与交互式shell环境可能存在差异
- **数据源稳定性**：免费数据源（AKShare、Investing.com）可能更改页面结构或API格式

## 当前代码架构

### 主获取逻辑（run_monitor.py 1540-1595行）
```python
# 首先尝试 yfinance
if YFINANCE_AVAILABLE:
    brent_ticker = yf.Ticker("BZ=F")
    brent_price = brent_ticker.info.get('regularMarketPrice')
    if brent_price is not None:
        results["crude_oil"] = float(brent_price)
    else:
        wti_ticker = yf.Ticker("CL=F")
        wti_price = wti_ticker.info.get('regularMarketPrice')
        if wti_price is not None:
            results["crude_oil"] = float(wti_price)

# 如果 yfinance 失败，尝试 akshare
df = ak.futures_zh_spot(symbol="SC0", market="INE")
if df is not None and not df.empty:
    latest = df.iloc[-1]
    results["crude_oil"] = float(latest.get("close", 0))

# 如果以上都失败，调用备用方案
fallback_oil = get_crude_oil_fallback()
```

### 备用方案函数（get_crude_oil_fallback）
三层备用方案：
1. **yfinance再次尝试**：BZ=F → CL=F
2. **Playwright爬取**：Investing.com布伦特原油页面
3. **web_fetch爬取**：通过OpenClaw CLI（当前失败）

## 已确认信息
1. **yfinance测试正常**：单独测试`yf.Ticker("BZ=F")`可成功获取价格92.69，但在cron环境中可能失败
2. **AKShare问题**：`futures_zh_spot("SC0", "INE")`返回数据结构异常（list index out of range）
3. **Playwright问题**：爬虫脚本返回空内容，可能是页面结构变化或反爬机制
4. **OpenClaw CLI**：`web_fetch`不是有效的openclaw子命令，可能是工具名称错误

## 分析要求

请进行系统性分析，提供：

### 1. 问题根因分析
- 为什么三层数据源会同时失败？
- 是环境问题、API变化、还是代码逻辑缺陷？
- 每个错误的具体技术原因是什么？

### 2. 3-5个可行解决方案
每个方案需要包含：
- **方案概述**：核心思路和技术路线
- **实施步骤**：具体可执行的操作步骤
- **预期效果**：问题解决程度和性能提升
- **优缺点**：优势、局限性、风险分析
- **复杂度评估**：实施难度和时间估计

### 3. 推荐实施步骤
- 根据当前上下文（T100宏观监控系统）推荐最优方案
- 提供具体代码修改建议和配置调整
- 包含测试验证方案和回滚计划

## 系统上下文
- **平台**：OpenClaw AI助手系统
- **环境**：Linux服务器，Python 3.x，Node.js 22.22.0
- **现有技能**：yfinance, AKShare, Playwright-scraper-skill
- **约束**：需要免费或低成本解决方案，系统稳定性优先

请提供深入、具体、可操作的分析。避免泛泛而谈，注重实际可行性。