# 情绪指标预警系统

监控炸板率、连板高度等情绪指标，极端行情自动预警并建议仓位调整。

## 功能特性

### 监控指标

| 指标 | 说明 | 预警阈值 |
|------|------|----------|
| **炸板率** | 开板股票数 / 曾涨停数 | >50% 警告, >70% 极端 |
| **连板高度** | 市场最高连板数 | ≤2板 低迷, ≥6板 活跃 |
| **涨跌家数比** | 上涨家数 / 下跌家数 | <0.5 熊市, >2.0 牛市 |
| **涨跌停家数** | 涨停/跌停股票数量 | 跌停>30家 危险 |
| **昨日涨停溢价** | 昨日涨停股今日平均收益 | <-2% 极端负溢价 |
| **封板率** | 成功封板数 / 曾涨停数 | <60% 低封板率 |

### 仓位建议

| 市场状态 | 情绪评分 | 建议仓位 | 操作建议 |
|----------|----------|----------|----------|
| 🔴🔴🔴 极端熊市 | <20 | 0% | 清仓观望 |
| 🔴🔴 熊市 | 20-40 | 20% | 大幅减仓 |
| 🟡 谨慎 | 40-50 | 50% | 谨慎操作 |
| ⚪ 中性 | 50-70 | 70% | 正常操作 |
| 🟢🟢 牛市 | >70 | 100% | 积极操作 |

## 安装部署

### 1. 依赖安装

```bash
pip install tushare pandas numpy pyyaml
```

### 2. 配置文件

系统使用 `config.yaml` 中的配置，已自动添加 `sentiment_monitor` 配置段。

### 3. 添加定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（已包含在 sentiment_cron.txt 中）
# 开盘情绪监控 (北京时间 09:35)
35 1 * * 1-5 cd /root/.openclaw/workspace/tasks/T01 && python3 sentiment_alert.py >> ./logs/sentiment_cron.log 2>&1

# 收盘前情绪监控 (北京时间 14:55)
55 6 * * 1-5 cd /root/.openclaw/workspace/tasks/T01 && python3 sentiment_alert.py >> ./logs/sentiment_cron.log 2>&1
```

## 使用方法

### 命令行运行

```bash
# 分析当日情绪
cd /root/.openclaw/workspace/tasks/T01
python3 sentiment_monitor.py

# 分析指定日期
python3 sentiment_monitor.py --date 20250403

# 检查并发送预警
python3 sentiment_alert.py

# 强制发送报告
python3 sentiment_alert.py --force
```

### Python 调用

```python
from sentiment_monitor import MarketSentimentMonitor
import yaml

# 加载配置
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 创建监控器
monitor = MarketSentimentMonitor(config)

# 分析情绪
result = monitor.analyze_sentiment('20250403')

# 获取报告
report = monitor.format_report(result)
print(report)

# 检查预警
alert = monitor.check_alert(result)
if alert:
    print(f"预警: {alert['message']}")
```

## 报告示例

```
╔══════════════════════════════════════════════════════════╗
║          📊 市场情绪指标报告 - 20250403                  ║
╚══════════════════════════════════════════════════════════╝

【综合评分】30/100  🔴🔴🔴
【市场状态】extreme_bear
【操作建议】清仓观望 | 建议仓位: 0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 关键指标:

1️⃣ 炸板率: 39.6%
   └─ 涨停53家, 炸板21家

2️⃣ 连板高度: 1板
   └─ 分布: {1: 32}

3️⃣ 涨跌比: 0.66
   └─ 涨1200 / 跌1800 / 平200

4️⃣ 涨跌停: 涨停53家 / 跌停45家
   └─ 大涨(>5%): 120家 | 大跌(<-5%): 280家

5️⃣ 昨日涨停溢价: -1.5%
   └─ 统计48只股票

6️⃣ 封板率: 60.4%
   └─ 封板32家 / 曾涨停53家

💡 系统建议:
• 清仓观望
• 建议仓位控制在 0%
```

## 配置说明

在 `config.yaml` 中的 `sentiment_monitor` 段配置：

```yaml
sentiment_monitor:
  enabled: true
  alert_cooldown_minutes: 30  # 预警冷却时间
  thresholds:                 # 阈值配置
    explosion_rate:
      extreme_high: 0.7
      high: 0.5
      warning: 0.3
    # ... 其他阈值
  schedule:                   # 监控时间
    - time: "09:35"
      description: "开盘情绪监控"
    - time: "14:55"
      description: "收盘前情绪监控"
  notification:
    enabled: true
    channels:
      - feishu
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `sentiment_monitor.py` | 核心监控模块 |
| `sentiment_alert.py` | 飞书推送脚本 |
| `run_sentiment_monitor.sh` | 定时运行脚本 |
| `sentiment_cron.txt` | Cron 配置示例 |

## 日志

日志文件保存在 `./logs/sentiment_monitor.log` 和 `./logs/sentiment_cron.log`

## 注意事项

1. 仅在交易日运行，非交易日自动跳过
2. 预警有冷却时间（默认30分钟），避免重复预警
3. 需要配置 Tushare token（已从 config.yaml 读取）
4. 飞书推送需要配置 openclaw CLI
