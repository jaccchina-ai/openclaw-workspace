-- T01 龙头战法策略数据库初始化脚本
-- 创建时间: 2026-03-21
-- 数据库: PostgreSQL 15 + TimescaleDB 2.11+

-- 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建 schema
CREATE SCHEMA IF NOT EXISTS t01;

-- =====================================================
-- 1. 股票推荐主表 (Hypertable)
-- 保存T日指标 + T日晚间风控 + T+1日竞价指标 + T+1日竞价风控
-- =====================================================
CREATE TABLE IF NOT EXISTS stock_recommendations (
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

-- =====================================================
-- 2. 因子权重历史表 (Hypertable)
-- =====================================================
CREATE TABLE IF NOT EXISTS factor_weights_history (
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

-- =====================================================
-- 3. 交易记录表 (Hypertable)
-- =====================================================
CREATE TABLE IF NOT EXISTS trade_records (
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

-- =====================================================
-- 4. 表现统计表 (Hypertable)
-- =====================================================
CREATE TABLE IF NOT EXISTS performance_stats (
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

-- =====================================================
-- 5. 机器学习日志表 (Hypertable)
-- =====================================================
CREATE TABLE IF NOT EXISTS ml_learning_logs (
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
    
    -- 改进结果
    improvements JSONB,
    
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

-- 初始化完成
SELECT 'Tables created successfully' as status;
