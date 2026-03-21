# T01 数据库升级计划 - PostgreSQL + TimescaleDB 时间旅行支持

**创建日期**: 2026-03-21  
**目标**: 将 T01 系统从 SQLite 迁移到 PostgreSQL + TimescaleDB，支持完整数据保存和时间旅行查询  
**部署方式**: 本地 Docker  
**数据保留**: 永久保留所有历史数据

---

## 背景与目标

### 当前问题
1. SQLite 数据库缺少 T日晚间风控指标（融资融券数据）
2. T+1日竞价阶段完整指标未保存
3. T+1日竞价阶段风控指标未保存
4. 不支持时间旅行查询（无法查询历史时间点的精确状态）

### 新架构目标
1. **完整数据保存**: T日所有指标 + T日晚间风控 + T+1日竞价指标 + T+1日竞价风控
2. **时间旅行查询**: 使用 TimescaleDB 的 `AS OF SYSTEM TIME` 支持任意时间点的数据查询
3. **时序优化**: 利用 Hypertable 自动分区，优化时序数据查询性能
4. **连续聚合**: 自动计算日/周/月级别的统计指标
5. **数据完整性**: 为机器学习优化策略提供完整的数据基础

---

## 技术架构

### 数据库选型
- **PostgreSQL 15+**: 关系型数据库，支持 JSONB、窗口函数、CTE
- **TimescaleDB 2.11+**: PostgreSQL 扩展，专为时序数据优化
  - Hypertable 自动分区
  - 连续聚合 (Continuous Aggregates)
  - 数据保留策略 (Retention Policies)
  - 时间旅行查询 (AS OF SYSTEM TIME)

### Docker 部署架构
```yaml
# docker-compose.yml 结构
version: '3.8'
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: t01_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: t01_strategy
    volumes:
      - timescale_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
```

---

## 数据库 Schema 设计

### 1. 股票推荐主表 (Hypertable)
```sql
CREATE TABLE stock_recommendations (
    time TIMESTAMPTZ NOT NULL,
    trade_date DATE NOT NULL,
    t1_date DATE NOT NULL,
    ts_code TEXT NOT NULL,
    name TEXT,
    industry TEXT,
    
    -- T日基础数据
    close_price DOUBLE PRECISION,
    pct_chg DOUBLE PRECISION,
    
    -- T日评分指标
    t_day_score DOUBLE PRECISION,
    total_score DOUBLE PRECISION,
    basic_score DOUBLE PRECISION,
    auction_score DOUBLE PRECISION DEFAULT 0,
    
    -- T日技术指标 (评分细节)
    first_limit_time_score DOUBLE PRECISION,
    order_quality_score DOUBLE PRECISION,
    liquidity_score DOUBLE PRECISION,
    money_flow_score DOUBLE PRECISION,
    sector_score DOUBLE PRECISION,
    dragon_list_score DOUBLE PRECISION,
    sentiment_score DOUBLE PRECISION,
    
    -- T日原始指标
    first_limit_time TEXT,
    seal_ratio DOUBLE PRECISION,
    seal_to_mv DOUBLE PRECISION,
    fd_amount DOUBLE PRECISION,
    amount DOUBLE PRECISION,
    float_mv DOUBLE PRECISION,
    turnover_rate DOUBLE PRECISION,
    turnover_20ma_ratio DOUBLE PRECISION,
    volume_ratio DOUBLE PRECISION,
    main_net_amount DOUBLE PRECISION,
    main_net_ratio DOUBLE PRECISION,
    medium_net_amount DOUBLE PRECISION,
    is_hot_sector BOOLEAN,
    
    -- T日晚间风控指标 (新增)
    market_financing_balance DOUBLE PRECISION,
    market_margin_balance DOUBLE PRECISION,
    market_total_balance DOUBLE PRECISION,
    financing_change_ratio DOUBLE PRECISION,
    margin_change_ratio DOUBLE PRECISION,
    financing_buy_ratio DOUBLE PRECISION,
    market_risk_level TEXT,
    market_risk_score INTEGER,
    position_multiplier DOUBLE PRECISION,
    
    -- T+1日竞价指标 (新增)
    auction_open_price DOUBLE PRECISION,
    auction_open_change_pct DOUBLE PRECISION,
    auction_volume_ratio DOUBLE PRECISION,
    auction_turnover_rate DOUBLE PRECISION,
    auction_amount DOUBLE PRECISION,
    auction_vol DOUBLE PRECISION,
    pre_close DOUBLE PRECISION,
    
    -- T+1日竞价风控 (新增)
    auction_risk_level TEXT,
    auction_risk_score INTEGER,
    auction_position_adjustment DOUBLE PRECISION,
    final_recommendation TEXT,
    suggested_position DOUBLE PRECISION,
    
    -- 完整原始数据 (JSONB)
    t_day_raw_data JSONB,
    risk_control_raw_data JSONB,
    auction_raw_data JSONB,
    
    -- 元数据
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (time, ts_code)
);

-- 转换为 Hypertable，按时间自动分区
SELECT create_hypertable('stock_recommendations', 'time', 
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- 创建索引
CREATE INDEX idx_stock_recommendations_trade_date ON stock_recommendations(trade_date);
CREATE INDEX idx_stock_recommendations_ts_code ON stock_recommendations(ts_code);
CREATE INDEX idx_stock_recommendations_total_score ON stock_recommendations(total_score DESC);
CREATE INDEX idx_stock_recommendations_risk_level ON stock_recommendations(risk_level);
```

### 2. 因子权重历史表 (Hypertable)
```sql
CREATE TABLE factor_weights_history (
    time TIMESTAMPTZ NOT NULL,
    factor_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_type TEXT, -- technical/fundamental/market/sentiment/auction
    
    -- 权重信息
    weight DOUBLE PRECISION,
    previous_weight DOUBLE PRECISION,
    weight_change_pct DOUBLE PRECISION,
    
    -- 效果评估
    correlation_with_win DOUBLE PRECISION,
    importance_score DOUBLE PRECISION,
    ic_value DOUBLE PRECISION, -- Information Coefficient
    
    -- 有效性标记
    is_active BOOLEAN DEFAULT TRUE,
    is_effective BOOLEAN DEFAULT TRUE, -- IC >= 0.03
    
    -- 元数据
    calculation_period TEXT, -- 计算周期，如 "2026-01-01_to_2026-03-01"
    sample_size INTEGER,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    
    PRIMARY KEY (time, factor_id)
);

SELECT create_hypertable('factor_weights_history', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_factor_weights_factor_id ON factor_weights_history(factor_id);
CREATE INDEX idx_factor_weights_active ON factor_weights_history(is_active) WHERE is_active = TRUE;
```

### 3. 交易记录表 (Hypertable)
```sql
CREATE TABLE trade_records (
    time TIMESTAMPTZ NOT NULL,
    trade_id TEXT NOT NULL,
    recommendation_id TEXT NOT NULL,
    
    ts_code TEXT NOT NULL,
    name TEXT,
    trade_date DATE NOT NULL,
    
    trade_type TEXT NOT NULL, -- buy/sell
    trade_time TEXT,
    price DOUBLE PRECISION NOT NULL,
    quantity INTEGER,
    amount DOUBLE PRECISION,
    commission DOUBLE PRECISION DEFAULT 0.0,
    
    status TEXT DEFAULT 'pending', -- pending/completed/cancelled
    notes TEXT,
    
    -- 与推荐记录的关联
    entry_score DOUBLE PRECISION, -- 买入时的评分
    exit_score DOUBLE PRECISION,  -- 卖出时的评分
    
    PRIMARY KEY (time, trade_id)
);

SELECT create_hypertable('trade_records', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_trade_records_recommendation ON trade_records(recommendation_id);
CREATE INDEX idx_trade_records_ts_code ON trade_records(ts_code);
CREATE INDEX idx_trade_records_status ON trade_records(status);
```

### 4. 表现统计表 (Hypertable)
```sql
CREATE TABLE performance_stats (
    time TIMESTAMPTZ NOT NULL,
    performance_id TEXT NOT NULL,
    recommendation_id TEXT NOT NULL,
    
    ts_code TEXT NOT NULL,
    name TEXT,
    
    -- 买入信息
    buy_date DATE NOT NULL,
    buy_price DOUBLE PRECISION NOT NULL,
    buy_time TEXT,
    
    -- 卖出信息
    sell_date DATE,
    sell_price DOUBLE PRECISION,
    sell_time TEXT,
    
    -- 持有统计
    holding_days INTEGER,
    return_pct DOUBLE PRECISION,
    annualized_return_pct DOUBLE PRECISION,
    
    -- 风险指标
    max_drawdown DOUBLE PRECISION,
    max_profit_pct DOUBLE PRECISION,
    max_loss_pct DOUBLE PRECISION,
    
    -- 盈亏标记
    win_loss INTEGER, -- 1:盈利, 0:亏损, -1:未完成
    profit_amount DOUBLE PRECISION,
    
    -- 成功标准 (T+2收盘价/T+1开盘价 > 1.03%)
    success_threshold_met BOOLEAN,
    t1_open_price DOUBLE PRECISION,
    t2_close_price DOUBLE PRECISION,
    t2_return_pct DOUBLE PRECISION,
    
    PRIMARY KEY (time, performance_id)
);

SELECT create_hypertable('performance_stats', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_performance_recommendation ON performance_stats(recommendation_id);
CREATE INDEX idx_performance_win_loss ON performance_stats(win_loss);
CREATE INDEX idx_performance_success ON performance_stats(success_threshold_met);
```

### 5. 机器学习日志表 (Hypertable)
```sql
CREATE TABLE ml_learning_logs (
    time TIMESTAMPTZ NOT NULL,
    session_id TEXT NOT NULL,
    
    model_type TEXT NOT NULL,
    model_version TEXT,
    
    -- 训练数据
    training_start_date DATE,
    training_end_date DATE,
    training_data_size INTEGER,
    test_data_size INTEGER,
    
    -- 评估指标 (JSONB)
    metrics JSONB,
    -- 包含: accuracy, precision, recall, f1_score, auc_roc, 
    --       win_rate, avg_return, sharpe_ratio, max_drawdown
    
    -- 改进结果
    improvements JSONB,
    -- 包含: weight_adjustments, new_factors, removed_factors
    
    -- 新发现的因子
    new_factors JSONB,
    
    -- 特征重要性
    feature_importance JSONB,
    
    -- 执行信息
    execution_time_seconds DOUBLE PRECISION,
    status TEXT DEFAULT 'completed',
    
    PRIMARY KEY (time, session_id)
);

SELECT create_hypertable('ml_learning_logs', 'time',
    chunk_time_interval => INTERVAL '90 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_ml_logs_model_type ON ml_learning_logs(model_type);
CREATE INDEX idx_ml_logs_status ON ml_learning_logs(status);
```

---

## 连续聚合视图 (Continuous Aggregates)

### 1. 日级推荐统计
```sql
CREATE MATERIALIZED VIEW daily_recommendation_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    trade_date,
    COUNT(*) as total_recommendations,
    COUNT(DISTINCT ts_code) as unique_stocks,
    
    -- 评分统计
    AVG(total_score) as avg_total_score,
    MAX(total_score) as max_total_score,
    MIN(total_score) as min_total_score,
    
    -- 风控统计
    AVG(market_risk_score) as avg_risk_score,
    COUNT(*) FILTER (WHERE market_risk_level = '高') as high_risk_count,
    COUNT(*) FILTER (WHERE market_risk_level = '低') as low_risk_count,
    
    -- 竞价统计
    AVG(auction_open_change_pct) as avg_auction_open_change,
    MAX(auction_open_change_pct) as max_auction_open_change,
    
    -- 成功标准统计
    COUNT(*) FILTER (WHERE success_threshold_met = TRUE) as success_count,
    COUNT(*) FILTER (WHERE success_threshold_met = FALSE) as failure_count
FROM stock_recommendations
GROUP BY bucket, trade_date
WITH NO DATA;

-- 刷新策略
SELECT add_continuous_aggregate_policy('daily_recommendation_stats',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

### 2. 周级因子效果统计
```sql
CREATE MATERIALIZED VIEW weekly_factor_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', time) AS bucket,
    factor_id,
    factor_name,
    factor_type,
    
    AVG(weight) as avg_weight,
    AVG(correlation_with_win) as avg_correlation,
    AVG(ic_value) as avg_ic,
    
    COUNT(*) FILTER (WHERE is_effective = TRUE) as effective_periods,
    COUNT(*) as total_periods,
    
    -- 有效性比例
    COUNT(*) FILTER (WHERE is_effective = TRUE)::FLOAT / NULLIF(COUNT(*), 0) as effectiveness_ratio
FROM factor_weights_history
GROUP BY bucket, factor_id, factor_name, factor_type
WITH NO DATA;

SELECT add_continuous_aggregate_policy('weekly_factor_performance',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);
```

### 3. 实时表现统计
```sql
CREATE MATERIALIZED VIEW daily_performance_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE win_loss = 1) as winning_trades,
    COUNT(*) FILTER (WHERE win_loss = 0) as losing_trades,
    
    -- 收益率统计
    AVG(return_pct) as avg_return,
    MAX(return_pct) as max_return,
    MIN(return_pct) as min_return,
    
    -- 胜率
    COUNT(*) FILTER (WHERE win_loss = 1)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE win_loss IN (0, 1)), 0) as win_rate,
    
    -- 成功标准达成率
    COUNT(*) FILTER (WHERE success_threshold_met = TRUE)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE success_threshold_met IS NOT NULL), 0) as success_rate,
    
    -- 风险指标
    AVG(max_drawdown) as avg_max_drawdown,
    AVG(holding_days) as avg_holding_days
FROM performance_stats
GROUP BY bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_performance_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

---

## 时间旅行查询示例

### 1. 查询特定时间点的股票推荐状态
```sql
-- 查询 2026-03-20 20:30:00 时的推荐状态
SELECT * FROM stock_recommendations
AS OF SYSTEM TIME '2026-03-20 20:30:00'
WHERE trade_date = '2026-03-20'
ORDER BY total_score DESC;
```

### 2. 查询因子权重的历史变化
```sql
-- 查询某个因子在过去 30 天的权重变化
SELECT 
    time,
    factor_name,
    weight,
    correlation_with_win,
    is_effective
FROM factor_weights_history
WHERE factor_id = 'first_limit_time'
  AND time >= NOW() - INTERVAL '30 days'
ORDER BY time;
```

### 3. 查询某个股票的历史推荐记录
```sql
-- 查询某股票的所有历史推荐及表现
SELECT 
    r.trade_date,
    r.total_score,
    r.market_risk_level,
    r.auction_open_change_pct,
    p.return_pct,
    p.win_loss,
    p.success_threshold_met
FROM stock_recommendations r
LEFT JOIN performance_stats p ON r.recommendation_id = p.recommendation_id
WHERE r.ts_code = '000001.SZ'
ORDER BY r.trade_date DESC;
```

### 4. 对比不同时间点的风控指标
```sql
-- 对比两个时间点的市场风控状态
WITH risk_comparison AS (
    SELECT 
        '2026-03-19 20:00:00' as snapshot_time,
        AVG(market_risk_score) as avg_risk_score,
        AVG(financing_change_ratio) as avg_financing_change
    FROM stock_recommendations
    AS OF SYSTEM TIME '2026-03-19 20:00:00'
    WHERE trade_date = '2026-03-19'
    
    UNION ALL
    
    SELECT 
        '2026-03-20 20:00:00' as snapshot_time,
        AVG(market_risk_score) as avg_risk_score,
        AVG(financing_change_ratio) as avg_financing_change
    FROM stock_recommendations
    AS OF SYSTEM TIME '2026-03-20 20:00:00'
    WHERE trade_date = '2026-03-20'
)
SELECT * FROM risk_comparison;
```

---

## 实施任务列表

### Phase 1: Docker 环境搭建
1. **创建 Docker Compose 配置**
   - 编写 `docker-compose.yml`
   - 配置 TimescaleDB 参数
   - 设置数据卷和持久化

2. **创建数据库初始化脚本**
   - 编写 `init/01_create_tables.sql`
   - 编写 `init/02_create_indexes.sql`
   - 编写 `init/03_create_continuous_aggregates.sql`
   - 编写 `init/04_create_functions.sql`

3. **启动并验证数据库**
   - 启动 Docker 容器
   - 验证 TimescaleDB 扩展已加载
   - 验证表结构正确

### Phase 2: Python 数据层重构
4. **创建 PostgreSQL 连接管理器**
   - 实现 `postgres_storage.py` 替代 `data_storage.py`
   - 支持连接池
   - 支持事务管理

5. **实现数据保存方法**
   - `save_t_day_recommendation()` - 保存T日推荐数据
   - `save_risk_control_data()` - 保存T日晚间风控数据
   - `save_auction_data()` - 保存T+1日竞价数据
   - `update_auction_risk_data()` - 更新竞价风控数据

6. **实现时间旅行查询方法**
   - `get_recommendation_as_of()` - 查询特定时间点的推荐
   - `get_factor_history()` - 查询因子历史变化
   - `get_stock_timeline()` - 查询股票完整时间线

7. **数据迁移脚本**
   - 从 SQLite 迁移历史数据到 PostgreSQL
   - 验证数据完整性

### Phase 3: 业务逻辑集成
8. **修改 T日评分流程**
   - 在 `scheduler.py` 中集成 PostgreSQL 保存
   - 保存完整的T日指标

9. **修改风控数据获取流程**
   - 在 `limit_up_strategy_new.py` 中保存风控数据
   - 确保T日晚间风控数据入库

10. **修改 T+1日竞价流程**
    - 保存竞价阶段完整指标
    - 保存竞价阶段风控数据
    - 更新推荐记录的竞价评分

11. **修改表现统计流程**
    - 在交易完成后保存表现数据
    - 计算并保存成功标准（T+2收盘价/T+1开盘价）

### Phase 4: 测试与验证
12. **单元测试**
    - 测试数据库连接
    - 测试数据保存和查询
    - 测试时间旅行查询

13. **集成测试**
    - 测试完整T日→T+1日流程
    - 验证数据完整性
    - 验证连续聚合视图

14. **性能测试**
    - 测试大数据量查询性能
    - 测试时间旅行查询性能
    - 优化慢查询

### Phase 5: 部署与监控
15. **生产部署**
    - 停止 T01 调度器
    - 执行数据迁移
    - 启动新系统
    - 验证运行正常

16. **监控配置**
    - 配置数据库监控
    - 设置磁盘空间告警
    - 配置备份策略

---

## 数据迁移策略

### 迁移步骤
1. **导出 SQLite 数据**
   ```bash
   sqlite3 t01_database.db ".dump" > t01_backup.sql
   ```

2. **转换数据格式**
   - 使用 Python 脚本读取 SQLite
   - 转换数据类型（SQLite 到 PostgreSQL）
   - 处理 JSON 字段

3. **导入 PostgreSQL**
   - 分批导入避免内存溢出
   - 每批 1000 条记录
   - 验证每批数据完整性

4. **验证迁移结果**
   - 对比记录数
   - 抽样验证数据准确性
   - 运行测试查询

---

## 备份策略

### 自动备份 (通过 Docker)
```yaml
# 在 docker-compose.yml 中添加备份服务
services:
  timescaledb-backup:
    image: timescale/timescaledb:latest-pg15
    volumes:
      - timescale_data:/var/lib/postgresql/data
      - ./backups:/backups
    command: |
      bash -c "
        while true; do
          pg_dump -h timescaledb -U t01_user t01_strategy > /backups/t01_backup_$$(date +%Y%m%d_%H%M%S).sql
          find /backups -name 't01_backup_*.sql' -mtime +30 -delete
          sleep 86400
        done
      "
```

### 连续归档 (WAL Archiving)
- 启用 PostgreSQL WAL 归档
- 支持时间点恢复 (PITR)
- 保留最近 7 天的 WAL 文件

---

## 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| 数据迁移失败 | 高 | 保留 SQLite 备份，可回滚 |
| Docker 容器故障 | 中 | 配置自动重启，数据卷持久化 |
| 磁盘空间不足 | 高 | 监控磁盘使用，配置告警 |
| 查询性能下降 | 中 | 使用 Hypertable 分区，创建合适索引 |
| 数据丢失 | 高 | 每日自动备份，WAL 归档 |

---

## 验收标准

1. **数据完整性**
   - [ ] T日10个股票的完整指标保存
   - [ ] T日晚间风控指标保存
   - [ ] T+1日竞价阶段完整指标保存
   - [ ] T+1日竞价阶段风控指标保存

2. **时间旅行查询**
   - [ ] 支持 `AS OF SYSTEM TIME` 查询
   - [ ] 可查询任意历史时间点的数据状态
   - [ ] 查询性能 < 1秒（单股票）

3. **连续聚合**
   - [ ] 日级统计视图自动刷新
   - [ ] 周级因子效果视图正常工作
   - [ ] 表现统计视图数据准确

4. **迁移验证**
   - [ ] 历史数据完整迁移
   - [ ] 新系统正常运行
   - [ ] 无数据丢失

---

## 下一步行动

等待用户确认设计后，进入 **Phase 3: Subagent-Driven Development**，开始实施具体任务。
