# T01 龙头战法选股策略

A股涨停股评分与竞价分析系统

## 简介

T01龙头战法选股策略是一个基于Tushare Pro API的A股量化选股系统，主要功能包括：

- **T日评分**: 每日收盘后评分涨停股，选出观察标的
- **T+1竞价分析**: 次日竞价时段重新评分，生成买入建议
- **风控系统**: 融资融券风险监控、指数风控
- **绩效跟踪**: 自动跟踪推荐股票表现

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export TUSHARE_TOKEN="your_token"
export FEISHU_USER_ID="your_user_id"

# 3. 复制配置
cp config.example.yaml config.yaml

# 4. 运行
python3 main.py --mode t_day --date $(date +%Y%m%d)
```

## 文档

- [SKILL.md](SKILL.md) - 详细使用说明
- [INSTALL.md](INSTALL.md) - 安装指南
- [config.example.yaml](config.example.yaml) - 配置示例

## 功能特性

### 核心功能
- ✅ T日涨停股评分
- ✅ T+1竞价分析
- ✅ 风控模块
- ✅ 绩效跟踪
- ✅ 飞书消息推送

### Phase 3 高级功能（可选）
- 🤖 机器学习优化
- 🔍 因子挖掘
- 📊 IC值监控
- 🔄 自动闭环进化
- 🛡️ 安全部署管理

## 评分因子

### T日评分
- 首次涨停时间 (30分)
- 封成比 (20分)
- 封单金额/流通市值 (15分)
- 换手率相关 (10分)
- 主力净额/占比 (10分)
- 热点板块判断 (10分)
- 舆情分析 (5分)

### T+1竞价评分
- 开盘涨幅 (35分)
- 竞价成交量/T日成交量 (25分)
- 竞价量比 (20分)
- 竞价换手率 (20分)

## 系统架构

```
┌─────────────────────────────────────────┐
│              T01 Strategy               │
├─────────────────────────────────────────┤
│  Core Layer                             │
│  ├── limit_up_strategy.py (主策略)      │
│  ├── scheduler.py (调度器)              │
│  ├── api_client.py (API客户端)          │
│  └── data_storage.py (数据存储)         │
├─────────────────────────────────────────┤
│  Phase 3 Layer (Optional)               │
│  ├── machine_learning.py                │
│  ├── factor_mining.py                   │
│  └── evolution_trigger.py               │
├─────────────────────────────────────────┤
│  Utils Layer                            │
│  ├── trading_calendar.py                │
│  └── feishu_sender.py                   │
└─────────────────────────────────────────┘
```

## 版本历史

### v1.3.0 (2026-04-02)
- 打包为OpenClaw Skill
- 移除硬编码token
- 添加环境变量支持
- 分离Phase 3功能为可选模块

### v1.2.0
- 添加竞价成交量/T日成交量因子
- 添加连续无选股预警
- 添加进化阶段提醒

### v1.1.0
- 添加融资融券风控
- 添加交易日历本地缓存
- 优化飞书消息发送

### v1.0.0
- 初始版本发布
- T日评分功能
- T+1竞价分析

## 许可证

MIT License

## 免责声明

本策略仅供学习和研究使用，不构成投资建议。股市有风险，投资需谨慎。
