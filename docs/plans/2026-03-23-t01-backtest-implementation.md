# T01策略回测自动化系统 - 实施计划

**日期**: 2026-03-23  
**版本**: 1.0  
**状态**: 已批准，开始实施

---

## 任务列表

### 任务1: 创建回测目录结构和基础文件
**预计时间**: 15分钟  
**TDD要求**: 先写测试 → 看失败 → 创建文件 → 看通过

1. 创建 `tasks/T01/backtest/` 目录
2. 创建 `__init__.py`
3. 创建 `tests/test_backtest.py` 基础测试框架
4. 验证目录结构正确

**验证命令**: `ls -la tasks/T01/backtest/`

---

### 任务2: 实现DataLoader类
**预计时间**: 30分钟  
**TDD要求**: 先写测试 → 看失败 → 实现 → 看通过

1. 编写 `test_data_loader.py` 测试用例
2. 实现 `data_loader.py`:
   - `DataLoader` 类
   - `load_limit_up_data(start_date, end_date)` 方法
   - `load_daily_price(ts_code, trade_date)` 方法
   - `load_auction_data(ts_code, trade_date)` 方法
3. 添加数据缓存机制
4. 运行测试验证

**验证命令**: `python3 -m pytest tests/test_data_loader.py -v`

---

### 任务3: 实现TradeSimulator类
**预计时间**: 45分钟  
**TDD要求**: 先写测试 → 看失败 → 实现 → 看通过

1. 编写 `test_trade_simulator.py` 测试用例
2. 实现 `trade_simulator.py`:
   - `TradeSimulator` 类
   - `simulate_day(trade_date, candidates)` 方法
   - `execute_buy(stock, price, amount)` 方法
   - `execute_sell(stock, price)` 方法
   - `get_portfolio_value()` 方法
   - 考虑滑点和手续费
3. 运行测试验证

**验证命令**: `python3 -m pytest tests/test_trade_simulator.py -v`

---

### 任务4: 实现MetricsCalculator类
**预计时间**: 30分钟  
**TDD要求**: 先写测试 → 看失败 → 实现 → 看通过

1. 编写 `test_metrics_calculator.py` 测试用例
2. 实现 `metrics_calculator.py`:
   - `MetricsCalculator` 类
   - `calculate_win_rate(trades)` 方法
   - `calculate_sharpe_ratio(returns)` 方法
   - `calculate_max_drawdown(equity_curve)` 方法
   - `calculate_profit_factor(trades)` 方法
   - `calculate_annual_return(total_return, days)` 方法
3. 运行测试验证

**验证命令**: `python3 -m pytest tests/test_metrics_calculator.py -v`

---

### 任务5: 实现BacktestEngine主类
**预计时间**: 45分钟  
**TDD要求**: 先写测试 → 看失败 → 实现 → 看通过

1. 编写 `test_backtest_engine.py` 测试用例
2. 实现 `backtest_engine.py`:
   - `BacktestEngine` 类
   - `__init__(config, start_date, end_date)`
   - `load_historical_data()` 方法
   - `run_backtest()` 方法 - 主回测循环
   - `calculate_metrics()` 方法
   - `generate_report()` 方法
3. 集成DataLoader、TradeSimulator、MetricsCalculator
4. 运行测试验证

**验证命令**: `python3 -m pytest tests/test_backtest_engine.py -v`

---

### 任务6: 实现ReportGenerator类
**预计时间**: 30分钟  
**TDD要求**: 先写测试 → 看失败 → 实现 → 看通过

1. 编写 `test_report_generator.py` 测试用例
2. 实现 `report_generator.py`:
   - `ReportGenerator` 类
   - `generate_text_report(metrics, trades)` 方法
   - `generate_json_report(metrics, trades)` 方法
   - `format_for_feishu(report)` 方法
3. 运行测试验证

**验证命令**: `python3 -m pytest tests/test_report_generator.py -v`

---

### 任务7: 更新config.yaml配置
**预计时间**: 15分钟  
**TDD要求**: 验证配置加载

1. 在 `config.yaml` 中添加 `backtest` 配置节
2. 配置项包括:
   - enabled: true
   - lookback_days: 252
   - initial_capital: 1000000
   - commission_rate: 0.0003
   - slippage: 0.005
   - position_size: 0.2
   - max_positions: 3
   - report_schedule: "weekly"
   - report_time: "06:00"
3. 编写测试验证配置加载
4. 运行测试验证

**验证命令**: `python3 -c "import yaml; config = yaml.safe_load(open('config.yaml')); print(config['backtest'])"`

---

### 任务8: 创建run_backtest.py入口脚本
**预计时间**: 20分钟  
**TDD要求**: 验证脚本可执行

1. 实现 `run_backtest.py`:
   - 命令行参数解析 (--start-date, --end-date, --config)
   - 加载配置
   - 初始化BacktestEngine
   - 执行回测
   - 生成并输出报告
   - 发送飞书消息（可选）
2. 添加shebang和可执行权限
3. 测试脚本运行

**验证命令**: `python3 run_backtest.py --help`

---

### 任务9: 添加cron定时任务
**预计时间**: 10分钟  
**TDD要求**: 验证cron格式正确

1. 在crontab中添加每周一回测任务:
   ```
   # T01策略回测报告 (每周一 06:00 北京时间)
   0 22 * * 0 cd /root/.openclaw/workspace/tasks/T01 && PATH=/root/.nvm/versions/node/v22.22.0/bin:$PATH /usr/bin/python3 run_backtest.py >> /root/.openclaw/workspace/tasks/T01/logs/backtest.log 2>&1
   ```
2. 创建logs目录
3. 验证cron格式

**验证命令**: `crontab -l | grep backtest`

---

### 任务10: 端到端集成测试
**预计时间**: 30分钟  
**TDD要求**: 完整流程测试

1. 运行完整回测流程（使用最近5天数据快速测试）
2. 验证报告生成
3. 验证所有指标计算正确
4. 验证飞书消息格式
5. 修复发现的问题

**验证命令**: `cd /root/.openclaw/workspace/tasks/T01 && python3 run_backtest.py --start-date $(date -d '5 days ago' +%Y%m%d) --end-date $(date +%Y%m%d)`

---

## 实施时间表

| 任务 | 预计时间 | 累计时间 |
|------|----------|----------|
| 任务1: 目录结构 | 15分钟 | 15分钟 |
| 任务2: DataLoader | 30分钟 | 45分钟 |
| 任务3: TradeSimulator | 45分钟 | 1.5小时 |
| 任务4: MetricsCalculator | 30分钟 | 2小时 |
| 任务5: BacktestEngine | 45分钟 | 2.75小时 |
| 任务6: ReportGenerator | 30分钟 | 3.25小时 |
| 任务7: 配置更新 | 15分钟 | 3.5小时 |
| 任务8: 入口脚本 | 20分钟 | 3.75小时 |
| 任务9: Cron任务 | 10分钟 | 3.9小时 |
| 任务10: 集成测试 | 30分钟 | 4.25小时 |

**总计**: 约4.5小时（含测试和审查时间）

---

## 依赖关系

```
任务1 (目录结构)
    ↓
任务2 (DataLoader) ──────┐
    ↓                    │
任务3 (TradeSimulator) ──┼──→ 任务5 (BacktestEngine)
    ↓                    │        ↓
任务4 (Metrics) ─────────┘   任务6 (ReportGenerator)
                                   ↓
                              任务8 (入口脚本)
                                   ↓
                              任务9 (Cron)
                                   ↓
                              任务10 (集成测试)

任务7 (配置) 可并行执行
```

---

## 审查检查点

每个任务完成后需要:
1. ✅ 所有测试通过
2. ✅ 代码符合项目规范
3. ✅ 文档字符串完整
4. ✅ 无硬编码，使用配置文件

---

**准备开始实施，将使用subagent驱动开发模式**
