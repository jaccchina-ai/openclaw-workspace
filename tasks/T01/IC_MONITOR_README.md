# T01 IC监控模块 (ic_monitor.py)

## 概述

IC监控模块用于监控T01策略中各因子的有效性，通过计算因子IC值（信息系数）来识别失效因子并发出预警。

## IC值定义

**IC (Information Coefficient)**：因子值与次日收益率的Spearman秩相关系数

- **IC值范围**: -1 到 1
- **|IC| > 0.1**: 强预测能力
- **0.03 < |IC| < 0.1**: 中等预测能力  
- **|IC| < 0.03**: 弱预测能力（失效因子）

## 监控因子列表

1. `seal_ratio` - 封成比
2. `seal_to_mv` - 封单/流通市值
3. `turnover_rate` - 换手率
4. `turnover_20ma_ratio` - 换手率/20日均量
5. `volume_ratio` - 量比
6. `first_limit_time` - 首次涨停时间
7. `main_net_ratio` - 主力净流入比例
8. `medium_net_ratio` - 中单净流入比例
9. `dragon_score` - 龙头得分
10. `is_hot_sector` - 是否热点板块

## 功能特性

### 1. 每日IC值计算
- 计算各因子的当日IC值
- 使用Spearman秩相关系数
- 需要至少30个样本进行计算

### 2. 滚动窗口IC值
- 20日滚动IC均值
- 60日滚动IC均值
- 反映因子长期稳定性

### 3. 失效因子预警
- 当|IC| < 0.03时标记为"失效因子"
- 飞书消息推送预警
- 记录到IC历史数据

### 4. IC趋势分析
- 检测IC值持续下降趋势
- 连续5天下降触发预警
- 帮助提前识别因子衰减

### 5. 飞书消息推送
- 每日IC监控报告
- 失效因子警告
- 趋势下降预警

## 使用方法

### 命令行运行

```bash
# 运行今日IC监控
python3 ic_monitor.py

# 指定日期运行
python3 ic_monitor.py --date 20260326

# 测试模式（生成模拟数据）
python3 ic_monitor.py --test

# 运行并发送到飞书
python3 ic_monitor.py --send-feishu
```

### 通过Scheduler运行

```bash
# 运行IC监控一次
python3 scheduler.py --mode ic-monitor

# 指定日期运行
python3 scheduler.py --mode ic-monitor --date 20260326

# 运行完整调度器（包含IC监控定时任务）
python3 scheduler.py --mode run
```

### 定时任务

IC监控任务已集成到scheduler中，每天收盘后**15:30**自动运行。

## 数据存储

### IC历史数据
- 文件路径: `data/ic_monitor/ic_history.json`
- 格式: JSON
- 内容: 每个因子的历史IC值记录

### IC监控报告
- 文件路径: `data/ic_monitor/ic_report_YYYYMMDD.json`
- 格式: JSON
- 内容: 每日IC监控完整报告

## 报告格式

### 飞书消息示例

```
📊 **T01因子IC监控报告 (20260326)**
========================================
**监控因子数**: 10
**有效因子数**: 8
**失效因子数**: 2 ⚠️
**预警因子数**: 1
**因子有效率**: 80.0%

🚨 **失效因子警告** (|IC| < 0.03)
  • turnover_rate: IC=0.0200
  • volume_ratio: IC=0.0150

⚠️ **IC下降趋势预警**
  • seal_ratio: 连续下降5天

**因子IC值详情**
```
因子名称                 当日IC       20日IC      60日IC      状态      
----------------------------------------------------------------------
seal_ratio           0.1500     0.1200     0.1000     ✅       
turnover_rate        0.0200     0.0500     0.0800     ❌       
volume_ratio         0.0150     0.0400     0.0600     ❌       
```

**说明**:
• IC值: 因子与次日收益率的Spearman秩相关系数
• |IC| ≥ 0.03: 因子有效 ✅
• |IC| < 0.03: 因子失效 ❌
• 20日/60日IC: 滚动窗口平均IC值

⏰ 生成时间: 2026-03-26T15:30:00
```

## 配置参数

### 失效阈值
```python
IC_INVALID_THRESHOLD = 0.03  # |IC| < 0.03 视为失效
```

### 趋势预警阈值
```python
TREND_DAYS_THRESHOLD = 5  # 连续5天下降触发预警
```

## 单元测试

```bash
# 运行单元测试
python3 test_ic_monitor.py

# 运行集成测试
python3 test_ic_integration.py
```

## 集成说明

IC监控模块已集成到T01调度器中：

1. **初始化**: 在`T01Scheduler.__init__`中自动初始化IC监控器
2. **定时任务**: 每天15:30自动运行IC监控
3. **手动运行**: 支持通过命令行参数`--mode ic-monitor`手动运行
4. **飞书推送**: 自动发送IC监控报告到飞书

## 注意事项

1. **数据依赖**: 需要Tushare Pro API权限获取历史数据
2. **计算时间**: 首次运行需要下载历史数据，可能需要较长时间
3. **样本数量**: 每个因子至少需要30个样本才能计算IC值
4. **交易日**: 只在交易日运行，非交易日自动跳过

## 故障排除

### IC值计算失败
- 检查Tushare API token是否有效
- 确认是否为交易日
- 检查网络连接

### 飞书发送失败
- 检查飞书用户ID配置
- 确认openclaw CLI可用
- 检查环境变量PATH设置

## 更新日志

### v1.0.0 (2026-03-26)
- 初始版本发布
- 实现IC值计算和监控
- 集成到T01调度器
- 支持飞书消息推送
