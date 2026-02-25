# 宏观数据源测试报告

**测试时间**: 2026-02-25 18:05:41
**测试模式**: stealth

## 测试摘要

- **总测试数**: 8
- **成功**: 5
- **部分成功**: 3
- **失败**: 0
- **错误**: 0
- **成功率**: 62.5%
- **总耗时**: 82.34秒

## 详细结果

| 数据源 | 状态 | 值 | 耗时(秒) | 备注 |
|--------|------|-----|----------|------|
| 美元兑人民币汇率 | ✅ success | 6.86851295 | 8.30 | 成功 |
| 布伦特原油价格 | ⚠️ partial_success | N/A | 9.58 | 数据解析失败，但网页访问成功 |
| 10年期美债收益率 | ⚠️ partial_success | N/A | 11.16 | 数据解析失败，但网页访问成功 |
| VIX恐慌指数 | ✅ success | 19.5 | 6.86 | 成功 |
| 黄金价格(人民币/克) | ⚠️ partial_success | N/A | 6.05 | 数据解析失败，但网页访问成功 |
| 新浪财经首页 | ✅ success | True | 16.73 | 成功 |
| 东方财富首页 | ✅ success | False | 15.13 | 成功 |
| 财联社首页 | ✅ success | False | 8.52 | 成功 |

## 改进建议

- 🔧 布伦特原油价格: 需要优化解析逻辑 - 数据解析失败，但网页访问成功
- 🔧 10年期美债收益率: 需要优化解析逻辑 - 数据解析失败，但网页访问成功
- 🔧 黄金价格(人民币/克): 需要优化解析逻辑 - 数据解析失败，但网页访问成功
- 🚨 整体成功率低于70%，建议检查网络连接和反爬虫策略

## 数据源详情

### 美元兑人民币汇率
- **描述**: XE.com 汇率转换器
- **URL**: https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CNY
- **预期模式**: `(\d+\.\d+)\s*(?:CNY|人民币|元)`
- **测试结果**: success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CNY
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013843478.png...

### 布伦特原油价格
- **描述**: Investing.com 原油价格
- **URL**: https://www.investing.com/commodities/brent-oil
- **预期模式**: `\$(\d+\.\d+)`
- **测试结果**: partial_success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.investing.com/commodities/brent-oil
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013853769.png

✅ 爬取完成！
{
  "title": ...

### 10年期美债收益率
- **描述**: Investing.com 美债收益率
- **URL**: https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield
- **预期模式**: `(\d+\.\d+)\s*%`
- **测试结果**: partial_success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.investing.com/rates-bonds/u.s.-10-year-bond-yield
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013865383.png

✅ 爬取完成！...

### VIX恐慌指数
- **描述**: CBOE官网 VIX指数
- **URL**: https://www.cboe.com/tradable_products/vix/
- **预期模式**: `(\d+\.\d+)\s*(?:VIX|指数)`
- **测试结果**: success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.cboe.com/tradable_products/vix/
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013878511.png

✅ 爬取完成！
{
  "title": "VIX...

### 黄金价格(人民币/克)
- **描述**: 黄金网 黄金价格
- **URL**: https://gold.cnfol.com/
- **预期模式**: `(\d+\.\d+)\s*元\s*[/每]?\s*克`
- **测试结果**: partial_success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://gold.cnfol.com/
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013887387.png

✅ 爬取完成！
{
  "title": "",
  "url": "chrome-error://chromewebdata/...

### 新浪财经首页
- **描述**: 新浪财经 (中文新闻源)
- **URL**: https://finance.sina.com.cn
- **预期模式**: `<title>.*?新浪财经.*?</title>`
- **测试结果**: success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://finance.sina.com.cn
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013895412.png

✅ 爬取完成！
{
  "title": "新浪财经_金融信息服务商",
  "u...

### 东方财富首页
- **描述**: 东方财富 (中文新闻源)
- **URL**: https://www.eastmoney.com
- **预期模式**: `<title>.*?东方财富.*?</title>`
- **测试结果**: success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.eastmoney.com
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013914173.png

✅ 爬取完成！
{
  "title": "东方财富手机APP官方下载-东方财富网",...

### 财联社首页
- **描述**: 财联社 (中文新闻源)
- **URL**: https://www.cls.cn
- **预期模式**: `<title>.*?财联社.*?</title>`
- **测试结果**: success
- **内容预览**: 🕷️  啟動 Playwright Stealth 爬蟲...
🔒 反爬模式: 無頭
📱 導航到: https://www.cls.cn
📡 HTTP Status: 200
⏳ 等待 5000ms 讓內容載入...
📸 截圖已儲存: ./screenshot-1772013931307.png

✅ 爬取完成！
{
  "title": "财联社",
  "url": "https://s.cl...

