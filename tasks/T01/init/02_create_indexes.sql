-- 创建索引优化查询性能

-- =====================================================
-- stock_recommendations 表索引
-- =====================================================

-- 交易日期索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_trade_date 
ON stock_recommendations(trade_date);

-- 股票代码索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_ts_code 
ON stock_recommendations(ts_code);

-- 综合查询索引：交易日期 + 股票代码
CREATE INDEX IF NOT EXISTS idx_stock_rec_trade_date_ts_code 
ON stock_recommendations(trade_date, ts_code);

-- 评分排序索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_total_score 
ON stock_recommendations(total_score DESC);

-- 风险等级索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_risk_level 
ON stock_recommendations(market_risk_level);

-- 行业索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_industry 
ON stock_recommendations(industry);

-- 竞价开盘涨幅索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_auction_open_change 
ON stock_recommendations(auction_open_change_pct);

-- 成功标准索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_success_threshold 
ON stock_recommendations(success_threshold_met) 
WHERE success_threshold_met IS NOT NULL;

-- JSONB 数据 GIN 索引
CREATE INDEX IF NOT EXISTS idx_stock_rec_t_day_raw 
ON stock_recommendations USING GIN(t_day_raw_data);

CREATE INDEX IF NOT EXISTS idx_stock_rec_risk_raw 
ON stock_recommendations USING GIN(risk_control_raw_data);

CREATE INDEX IF NOT EXISTS idx_stock_rec_auction_raw 
ON stock_recommendations USING GIN(auction_raw_data);

-- =====================================================
-- factor_weights_history 表索引
-- =====================================================

-- 因子ID索引
CREATE INDEX IF NOT EXISTS idx_factor_weights_factor_id 
ON factor_weights_history(factor_id);

-- 活跃因子索引
CREATE INDEX IF NOT EXISTS idx_factor_weights_active 
ON factor_weights_history(factor_id, valid_from, valid_to) 
WHERE is_active = TRUE;

-- 有效性索引
CREATE INDEX IF NOT EXISTS idx_factor_weights_effective 
ON factor_weights_history(is_effective);

-- 因子类型索引
CREATE INDEX IF NOT EXISTS idx_factor_weights_type 
ON factor_weights_history(factor_type);

-- =====================================================
-- trade_records 表索引
-- =====================================================

-- 推荐记录关联索引
CREATE INDEX IF NOT EXISTS idx_trade_rec_recommendation 
ON trade_records(recommendation_id);

-- 股票代码索引
CREATE INDEX IF NOT EXISTS idx_trade_rec_ts_code 
ON trade_records(ts_code);

-- 交易日期索引
CREATE INDEX IF NOT EXISTS idx_trade_rec_trade_date 
ON trade_records(trade_date);

-- 交易状态索引
CREATE INDEX IF NOT EXISTS idx_trade_rec_status 
ON trade_records(status);

-- 交易类型索引
CREATE INDEX IF NOT EXISTS idx_trade_rec_type 
ON trade_records(trade_type);

-- =====================================================
-- performance_stats 表索引
-- =====================================================

-- 推荐记录关联索引
CREATE INDEX IF NOT EXISTS idx_perf_recommendation 
ON performance_stats(recommendation_id);

-- 股票代码索引
CREATE INDEX IF NOT EXISTS idx_perf_ts_code 
ON performance_stats(ts_code);

-- 买入日期索引
CREATE INDEX IF NOT EXISTS idx_perf_buy_date 
ON performance_stats(buy_date);

-- 盈亏状态索引
CREATE INDEX IF NOT EXISTS idx_perf_win_loss 
ON performance_stats(win_loss);

-- 成功标准索引
CREATE INDEX IF NOT EXISTS idx_perf_success 
ON performance_stats(success_threshold_met);

-- 收益率索引
CREATE INDEX IF NOT EXISTS idx_perf_return 
ON performance_stats(return_pct);

-- 综合表现查询索引
CREATE INDEX IF NOT EXISTS idx_perf_buy_date_win_loss 
ON performance_stats(buy_date, win_loss);

-- =====================================================
-- ml_learning_logs 表索引
-- =====================================================

-- 模型类型索引
CREATE INDEX IF NOT EXISTS idx_ml_logs_model_type 
ON ml_learning_logs(model_type);

-- 状态索引
CREATE INDEX IF NOT EXISTS idx_ml_logs_status 
ON ml_learning_logs(status);

-- 会话ID索引
CREATE INDEX IF NOT EXISTS idx_ml_logs_session 
ON ml_learning_logs(session_id);

-- JSONB 指标索引
CREATE INDEX IF NOT EXISTS idx_ml_logs_metrics 
ON ml_learning_logs USING GIN(metrics);

SELECT 'Indexes created successfully' as status;
