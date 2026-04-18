---
name: a-stock-midterm
description: 整合的中线投资分析技能，专注于 A 股基本面、宏观、研报和股东持仓分析。将 Wind 数据逻辑迁移至 Tushare API。涵盖财务分析、研报预测、宏观数据和股东持仓等 11 个核心模块。
---

# A 股中线投资分析 (a-stock-midterm)

## 🎯 技能定位
专注于 **A 股中线投资逻辑与数据深度分析**，通过整合 11 个专业子模块，构建从宏观到行业再到个股的完整投研框架。

## 📚 核心模块
1. **宏观分析 (macro-analysis)**: 全球宏观、货币/财政政策。
2. **市场分析 (market-analysis)**: A 股收盘市场综述、龙虎榜、大宗交易。
3. **个股分析 (stock-analysis)**: 投资逻辑梳理、基本面、财务报表分析。
4. **研报共识分析 (research-consensus)**: 盈利预测、评级变化、预期差分析。
5. **周期股景气拐点**: 行业景气度评估、周期位置判断。
6. **宏观行业个股传导**: 政策到行业的映射逻辑。
7. **个股投资逻辑研究**: 深度护城河拆解与财务健康评估。
8. **反身性与泡沫识别**: 情绪面与估值极端博弈分析。
9. **政策解读受益映射**: 实时政策对板块的驱动。
10. **每日投研简报/盘后复盘**: 核心数据与大盘情绪总结。

## 📊 数据源集成 (Tushare)
本技能已全面迁移至 Tushare 数据接口（Token: 870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab）。

### 迁移对照表
- **财务数据**: 原 `wind_financial_data` → Tushare `income`, `balancesheet`, `cashflow`, `fina_indicator`
- **研报预测**: 原 `wind_financial_data` (共识) → Tushare `report_rc` (研报盈利预测)
- **宏观数据**: 原 `wind_macro` → Tushare `cn_gdp`, `cn_cpi`, `cn_m2` 等宏观接口
- **大股东持仓**: 原 `wind_shareholders` → Tushare `top10_holders` / `top10_floatholders`
- **每日指标**: 原 `wind_daily_basic` → Tushare `daily_basic` (PE, PB, 换手率, 总市值)

## 🔧 使用工作流
1. **确定范围**: 用户提到宏观、行业、个股、财务、研报、持仓等。
2. **选择逻辑插件**: 匹配 `logic_plugins/` 下的对应逻辑框架。
3. **调用 Tushare**: 使用 `scripts/tushare_adapter.py` 获取核心数据。
4. **整合输出**: 根据逻辑框架，结合最新数据，输出高质量分析报告。

## 📅 定时任务
- **盘前 (9:00)**: 宏观环境概览、个股评级变化、重要政策映射。
- **盘后 (17:30)**: A 股收盘市场综述、个股财报/研报更新、龙虎榜分析。
- **周末**: 组合深度体检、中线投资逻辑修正。

---
**版本**: v1.0 (2026-03-23)
**数据驱动**: Tushare Pro
