# T01选股策略系统Skill化设计文档

## 目标
将T01龙头战法选股系统打包成可复用的OpenClaw Skill，不包含硬编码token，以压缩包形式交付。

## 核心需求
1. **不包含硬编码token** - 所有API密钥通过环境变量或配置文件传入
2. **不安装skill** - 仅生成压缩包供手动下载
3. **完整功能保留** - 保留T日评分、T+1竞价分析、风控、消息推送等核心功能
4. **Phase 3功能可选** - ML进化、因子挖掘等高级功能作为可选模块

## 系统架构

### 核心模块（必需）
```
t01-dragon-strategy/
├── SKILL.md                    # Skill使用文档
├── config.yaml                 # 配置文件模板（无敏感信息）
├── config.example.yaml         # 配置示例
├── requirements.txt            # Python依赖
├── main.py                     # 主入口
├── limit_up_strategy.py        # 核心策略逻辑
├── scheduler.py                # 调度器
├── api_client.py               # API客户端（抽象层）
├── screener.py                 # 筛选器
├── strategy.py                 # 策略基类
├── output_formatter.py         # 输出格式化
├── integration.py              # 消息集成
├── data_storage.py             # 数据存储
├── performance_tracker.py      # 绩效跟踪
└── utils/
    ├── trading_calendar.py     # 交易日历
    └── feishu_sender.py        # 飞书发送器
```

### 可选模块（Phase 3 - 高级功能）
```
t01-dragon-strategy/
├── phase3/
│   ├── machine_learning.py     # 机器学习
│   ├── factor_mining.py        # 因子挖掘
│   ├── ic_monitor.py           # IC值监控
│   ├── evolution_trigger.py    # 进化触发器
│   ├── auto_closed_loop.py     # 自动闭环
│   └── ...                     # 其他Phase 3模块
```

### 脚本和工具
```
t01-dragon-strategy/
├── scripts/
│   ├── run_daily_scoring.sh    # T日评分脚本
│   ├── run_auction_analysis.sh # T+1竞价分析脚本
│   └── setup.sh                # 初始化脚本
└── tests/
    └── ...                     # 测试文件
```

## 敏感信息处理

### 需要移除/替换的内容
1. **Tushare Token** - 从config.yaml中移除，改为从环境变量读取
2. **飞书User ID** - 从配置中移除，改为配置项
3. **数据库密码** - 如有，改为环境变量
4. **日志中的敏感信息** - 清理历史日志

### 环境变量设计
```bash
# 必需
export TUSHARE_TOKEN="your_tushare_token_here"
export FEISHU_USER_ID="your_feishu_user_id"

# 可选（有默认值）
export T01_DATA_DIR="./data"
export T01_LOG_LEVEL="INFO"
export T01_NOTIFICATION_CHANNEL="feishu"
```

## 配置文件结构

### config.yaml（模板）
```yaml
version: "1.3.0"

# API配置（从环境变量读取）
api:
  tushare_token: ${TUSHARE_TOKEN}
  endpoint: http://api.tushare.pro
  timeout: 30

# 通知配置
notification:
  enabled: true
  channel: feishu
  feishu_user_id: ${FEISHU_USER_ID}

# 策略配置
strategy:
  schedule:
    daily_screening_time: "20:30"
    morning_review_time: "09:25"
    push_time: "09:30"
  risk_control:
    min_total_score: 60
    max_position_per_stock: 0.2

# 数据存储
data_storage:
  database:
    type: sqlite
    path: ./data/t01_database.db

# Phase 3功能开关
phase3:
  enabled: false  # 默认关闭，需要额外配置
```

## 实现计划

### Phase 1: 代码审计和清理
1. 扫描所有文件中的硬编码token
2. 识别所有敏感信息位置
3. 创建环境变量读取机制
4. 清理日志文件中的敏感信息

### Phase 2: 核心模块提取
1. 复制核心Python文件到新目录
2. 修改配置文件读取逻辑
3. 添加环境变量支持
4. 创建SKILL.md文档

### Phase 3: 可选模块处理
1. 将Phase 3功能移至单独目录
2. 添加功能开关机制
3. 确保核心功能不依赖Phase 3

### Phase 4: 打包和验证
1. 创建目录结构
2. 生成压缩包
3. 验证无敏感信息泄露
4. 测试基本功能

## 交付物

1. **t01-dragon-strategy.zip** - 完整skill压缩包
2. **SKILL.md** - 使用说明
3. **INSTALL.md** - 安装指南
4. **CHANGELOG.md** - 版本历史

## 验收标准

- [ ] 压缩包内无硬编码token
- [ ] 配置文件使用环境变量占位符
- [ ] 核心功能可独立运行
- [ ] 文档完整清晰
- [ ] 通过基本功能测试
