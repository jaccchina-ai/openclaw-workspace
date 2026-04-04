# T01 龙头战法选股策略 Skill

A股涨停股评分与竞价分析系统 - 基于Tushare Pro API

## 功能特性

- **T日评分**: 每日收盘后评分涨停股，选出观察标的
- **T+1竞价分析**: 次日竞价时段重新评分，生成买入建议
- **风控系统**: 融资融券风险监控、指数风控
- **绩效跟踪**: 自动跟踪推荐股票表现
- **消息推送**: 飞书消息推送
- **Phase 3进化** (可选): 机器学习、因子挖掘、自动优化

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export TUSHARE_TOKEN="your_tushare_token_here"
export FEISHU_USER_ID="your_feishu_user_id"
```

### 3. 复制配置文件

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 调整策略参数
```

### 4. 运行策略

```bash
# T日评分（收盘后）
python3 main.py --mode t_day --date $(date +%Y%m%d)

# T+1竞价分析（次日9:25）
python3 main.py --mode t1_auction --date $(date +%Y%m%d)
```

## 配置文件说明

### config.yaml 主要配置项

```yaml
# API配置
api:
  tushare_token: ${TUSHARE_TOKEN}  # 从环境变量读取
  endpoint: http://api.tushare.pro
  timeout: 30

# 策略调度
strategy:
  schedule:
    daily_screening_time: "20:30"  # T日评分时间
    morning_review_time: "09:25"   # T+1竞价分析时间
    push_time: "09:30"             # 推送时间

# 风控配置
strategy:
  risk_control:
    min_total_score: 60            # 最低入选分数
    max_position_per_stock: 0.2    # 单股最大仓位

# 通知配置
notification:
  enabled: true
  channel: feishu
  feishu_user_id: ${FEISHU_USER_ID}

# Phase 3功能开关
phase3:
  enabled: false  # 默认关闭
```

## 目录结构

```
t01-dragon-strategy/
├── core/                       # 核心模块
│   ├── limit_up_strategy.py   # 主策略逻辑
│   ├── scheduler.py           # 调度器
│   ├── api_client.py          # API客户端
│   ├── screener.py            # 筛选器
│   ├── data_storage.py        # 数据存储
│   └── performance_tracker.py # 绩效跟踪
├── phase3/                     # Phase 3高级功能（可选）
│   ├── machine_learning.py
│   ├── factor_mining.py
│   └── ...
├── utils/                      # 工具函数
│   ├── trading_calendar.py
│   └── feishu_sender.py
├── scripts/                    # 运行脚本
│   ├── run_daily_scoring.sh
│   └── run_auction_analysis.sh
├── tests/                      # 测试文件
├── config.example.yaml         # 配置示例
├── requirements.txt            # 依赖列表
└── main.py                     # 主入口
```

## 评分因子

### T日评分因子
- 首次涨停时间 (30分)
- 封成比 (20分)
- 封单金额/流通市值 (15分)
- 换手率相关 (10分)
- 主力净额/占比 (10分)
- 热点板块判断 (10分)
- 舆情分析 (5分)

### T+1竞价评分因子
- 开盘涨幅 (35分)
- 竞价成交量/T日成交量 (25分)
- 竞价量比 (20分)
- 竞价换手率 (20分)

## 定时任务配置

### Cron示例

```bash
# T日评分（周一至周五 20:30 北京时间）
30 12 * * 1-5 /path/to/t01-dragon-strategy/scripts/run_daily_scoring.sh

# T+1竞价分析（周一至周五 09:25 北京时间）
25 1 * * 1-5 /path/to/t01-dragon-strategy/scripts/run_auction_analysis.sh
```

## Phase 3 高级功能

Phase 3包含机器学习、因子挖掘、自动优化等高级功能。

启用Phase 3:
```yaml
phase3:
  enabled: true
  machine_learning:
    enabled: true
    mode: reinforcement
```

## 数据存储

默认使用SQLite数据库，存储位置: `./data/t01_database.db`

数据表:
- `t01_recommendations` - 推荐记录
- `t01_trades` - 交易记录
- `t01_performance` - 绩效数据
- `t01_factors` - 因子数据
- `t01_learning_logs` - 学习日志

## 许可证

MIT License
