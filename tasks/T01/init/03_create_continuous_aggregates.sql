-- 创建连续聚合视图 (Continuous Aggregates)
-- 用于自动计算日/周/月级别的统计指标

-- =====================================================
-- 1. 日级推荐统计
-- =====================================================
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
    STDDEV(total_score) as std_total_score,
    
    -- 风控统计
    AVG(market_risk_score) as avg_risk_score,
    MAX(market_risk_score) as max_risk_score,
    MIN(market_risk_score) as min_risk_score,
    COUNT(*) FILTER (WHERE market_risk_level = '高') as high_risk_count,
    COUNT(*) FILTER (WHERE market_risk_level = '中') as medium_risk_count,
    COUNT(*) FILTER (WHERE market_risk_level = '低') as low_risk_count,
    
    -- 融资余额统计
    AVG(market_financing_balance) as avg_financing_balance,
    AVG(financing_change_ratio) as avg_financing_change_ratio,
    
    -- 竞价统计
    AVG(auction_open_change_pct) as avg_auction_open_change,
    MAX(auction_open_change_pct) as max_auction_open_change,
    MIN(auction_open_change_pct) as min_auction_open_change,
    AVG(auction_volume_ratio) as avg_auction_volume_ratio,
    
    -- 成功标准统计
    COUNT(*) FILTER (WHERE success_threshold_met = TRUE) as success_count,
    COUNT(*) FILTER (WHERE success_threshold_met = FALSE) as failure_count,
    
    -- 行业分布（JSONB聚合）
    jsonb_object_agg(
        industry, 
        COUNT(*) 
        FILTER (WHERE industry IS NOT NULL)
    ) as industry_distribution
    
FROM stock_recommendations
GROUP BY bucket, trade_date
WITH NO DATA;

-- 创建刷新策略
SELECT add_continuous_aggregate_policy('daily_recommendation_stats',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- =====================================================
-- 2. 周级因子效果统计
-- =====================================================
CREATE MATERIALIZED VIEW weekly_factor_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', time) AS bucket,
    factor_id,
    factor_name,
    factor_type,
    
    -- 权重统计
    AVG(weight) as avg_weight,
    MAX(weight) as max_weight,
    MIN(weight) as min_weight,
    AVG(previous_weight) as avg_previous_weight,
    AVG(weight_change_pct) as avg_weight_change_pct,
    
    -- 效果评估
    AVG(correlation_with_win) as avg_correlation,
    AVG(importance_score) as avg_importance,
    AVG(ic_value) as avg_ic,
    MAX(ic_value) as max_ic,
    MIN(ic_value) as min_ic,
    
    -- 有效性统计
    COUNT(*) FILTER (WHERE is_effective = TRUE) as effective_periods,
    COUNT(*) as total_periods,
    COUNT(*) FILTER (WHERE is_effective = TRUE)::FLOAT / 
        NULLIF(COUNT(*), 0) as effectiveness_ratio,
    
    -- 活跃状态
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_periods
    
FROM factor_weights_history
GROUP BY bucket, factor_id, factor_name, factor_type
WITH NO DATA;

SELECT add_continuous_aggregate_policy('weekly_factor_performance',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- =====================================================
-- 3. 日级表现统计
-- =====================================================
CREATE MATERIALIZED VIEW daily_performance_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    
    -- 交易统计
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE win_loss = 1) as winning_trades,
    COUNT(*) FILTER (WHERE win_loss = 0) as losing_trades,
    COUNT(*) FILTER (WHERE win_loss = -1) as pending_trades,
    
    -- 胜率
    COUNT(*) FILTER (WHERE win_loss = 1)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE win_loss IN (0, 1)), 0) as win_rate,
    
    -- 收益率统计
    AVG(return_pct) as avg_return,
    MAX(return_pct) as max_return,
    MIN(return_pct) as min_return,
    STDDEV(return_pct) as std_return,
    SUM(profit_amount) as total_profit,
    
    -- 成功标准达成率
    COUNT(*) FILTER (WHERE success_threshold_met = TRUE)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE success_threshold_met IS NOT NULL), 0) as success_rate,
    
    -- 风险指标
    AVG(max_drawdown) as avg_max_drawdown,
    MAX(max_drawdown) as max_drawdown,
    AVG(holding_days) as avg_holding_days,
    
    -- 盈亏比
    CASE 
        WHEN COUNT(*) FILTER (WHERE win_loss = 0) > 0 THEN
            ABS(AVG(return_pct) FILTER (WHERE win_loss = 1)) / 
            ABS(AVG(return_pct) FILTER (WHERE win_loss = 0))
        ELSE NULL
    END as profit_loss_ratio
    
FROM performance_stats
GROUP BY bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_performance_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- =====================================================
-- 4. 周级股票表现统计
-- =====================================================
CREATE MATERIALIZED VIEW weekly_stock_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', time) AS bucket,
    ts_code,
    name,
    
    -- 交易次数
    COUNT(*) as trade_count,
    COUNT(*) FILTER (WHERE win_loss = 1) as win_count,
    COUNT(*) FILTER (WHERE win_loss = 0) as loss_count,
    
    -- 胜率
    COUNT(*) FILTER (WHERE win_loss = 1)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE win_loss IN (0, 1)), 0) as win_rate,
    
    -- 收益统计
    AVG(return_pct) as avg_return,
    SUM(return_pct) as total_return,
    MAX(return_pct) as best_return,
    MIN(return_pct) as worst_return,
    
    -- 成功标准
    COUNT(*) FILTER (WHERE success_threshold_met = TRUE)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE success_threshold_met IS NOT NULL), 0) as success_rate,
    
    -- 平均持有天数
    AVG(holding_days) as avg_holding_days
    
FROM performance_stats
GROUP BY bucket, ts_code, name
WITH NO DATA;

SELECT add_continuous_aggregate_policy('weekly_stock_performance',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- =====================================================
-- 5. 月级综合统计
-- =====================================================
CREATE MATERIALIZED VIEW monthly_comprehensive_stats
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', time) AS bucket,
    
    -- 推荐统计
    COUNT(DISTINCT s.ts_code) as unique_stocks_recommended,
    AVG(s.total_score) as avg_recommendation_score,
    
    -- 交易统计
    COUNT(t.trade_id) as total_trades,
    
    -- 表现统计
    AVG(p.return_pct) as avg_trade_return,
    COUNT(p.performance_id) FILTER (WHERE p.win_loss = 1)::FLOAT / 
        NULLIF(COUNT(p.performance_id) FILTER (WHERE p.win_loss IN (0, 1)), 0) as overall_win_rate,
    
    -- 复合统计
    jsonb_build_object(
        'avg_financing_balance', AVG(s.market_financing_balance),
        'avg_risk_score', AVG(s.market_risk_score),
        'avg_auction_open_change', AVG(s.auction_open_change_pct)
    ) as market_stats
    
FROM stock_recommendations s
LEFT JOIN trade_records t ON s.ts_code = t.ts_code 
    AND DATE(s.time) = t.trade_date
LEFT JOIN performance_stats p ON s.ts_code = p.ts_code 
    AND DATE(s.time) = p.buy_date
GROUP BY bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('monthly_comprehensive_stats',
    start_offset => INTERVAL '1 year',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

SELECT 'Continuous aggregates created successfully' as status;
