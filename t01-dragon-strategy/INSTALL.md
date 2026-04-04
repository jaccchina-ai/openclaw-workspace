# T01 龙头战法选股策略 - 安装指南

## 系统要求

- Python 3.8+
- pip
- Linux/macOS/Windows

## 安装步骤

### 1. 解压压缩包

```bash
unzip t01-dragon-strategy.zip
cd t01-dragon-strategy
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件或在 shell 中设置：

```bash
# 必需配置
export TUSHARE_TOKEN="your_tushare_token_here"
export FEISHU_USER_ID="your_feishu_user_id"

# 可选配置
export T01_DATA_DIR="./data"
export T01_LOG_LEVEL="INFO"
```

获取Tushare Token:
- 访问 https://tushare.pro
- 注册账号并获取Token

获取飞书User ID:
- 在飞书开发者后台查看
- 或联系管理员获取

### 4. 复制配置文件

```bash
cp config.example.yaml config.yaml
```

根据需要编辑 `config.yaml` 调整策略参数。

### 5. 创建必要目录

```bash
mkdir -p data output logs
```

### 6. 测试运行

```bash
# 测试T日评分
python3 main.py --mode t_day --date $(date +%Y%m%d)

# 测试T+1竞价分析
python3 main.py --mode t1_auction --date $(date +%Y%m%d)
```

## 配置定时任务

### Linux/macOS (Cron)

```bash
# 编辑crontab
crontab -e

# 添加以下行（北京时间）
# T日评分（周一至周五 20:30）
30 12 * * 1-5 /path/to/t01-dragon-strategy/scripts/run_daily_scoring.sh

# T+1竞价分析（周一至周五 09:25）
25 1 * * 1-5 /path/to/t01-dragon-strategy/scripts/run_auction_analysis.sh
```

### Windows (任务计划程序)

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器为每周一至周五
4. 设置操作为启动程序
5. 程序路径选择 `python3`，参数为 `main.py --mode t_day --date %date:~0,4%%date:~5,2%%date:~8,2%`

## 启用Phase 3高级功能（可选）

Phase 3包含机器学习、因子挖掘、自动优化等高级功能。

### 1. 安装额外依赖

```bash
pip install scikit-learn xgboost shap
```

### 2. 修改配置

编辑 `config.yaml`:

```yaml
phase3:
  enabled: true
  
machine_learning:
  enabled: true
  mode: reinforcement
```

### 3. 运行进化系统

```bash
python3 phase3/evolution_trigger.py
```

## 故障排除

### 问题1: "TUSHARE_TOKEN未设置"

**解决方案**: 确保环境变量已正确设置
```bash
echo $TUSHARE_TOKEN
```

### 问题2: "无法连接到Tushare API"

**解决方案**: 检查网络连接和Token有效性
```bash
python3 -c "import tushare as ts; ts.set_token('your_token'); pro = ts.pro_api(); print(pro.trade_cal(exchange='SSE', start_date='20260101', end_date='20260131'))"
```

### 问题3: "飞书消息发送失败"

**解决方案**: 检查FEISHU_USER_ID和openclaw CLI
```bash
# 测试飞书发送
openclaw message send --channel feishu --target "user:your_user_id" --message "测试消息"
```

## 目录结构说明

```
t01-dragon-strategy/
├── core/              # 核心模块（必需）
├── phase3/            # 高级功能（可选）
├── utils/             # 工具函数
├── scripts/           # 运行脚本
├── data/              # 数据存储目录
├── output/            # 输出目录
├── logs/              # 日志目录
├── config.yaml        # 配置文件
└── main.py            # 主程序
```

## 升级说明

### 从旧版本升级

1. 备份 `config.yaml` 和 `data/` 目录
2. 解压新版本压缩包
3. 恢复配置文件和数据
4. 检查配置文件是否有新增配置项

## 技术支持

如有问题，请查看:
- SKILL.md - 使用说明
- docs/ - 详细文档
- logs/ - 日志文件
