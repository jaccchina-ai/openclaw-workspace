-- 创建辅助函数和存储过程

-- =====================================================
-- 1. 时间旅行查询函数
-- =====================================================

-- 查询特定时间点的股票推荐状态
CREATE OR REPLACE FUNCTION get_recommendation_as_of(
    p_trade_date DATE,
    p_ts_code TEXT,
    p_as_of_time TIMESTAMPTZ
)
RETURNS TABLE (
    time TIMESTAMPTZ,
    trade_date DATE,
    ts_code TEXT,
    name TEXT,
    total_score DOUBLE PRECISION,
    market_risk_level TEXT,
    auction_open_change_pct DOUBLE PRECISION,
    t_day_raw_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.time,
        r.trade_date,
        r.ts_code,
        r.name,
        r.total_score,
        r.market_risk_level,
        r.auction_open_change_pct,
        r.t_day_raw_data
    FROM stock_recommendations r
    WHERE r.trade_date = p_trade_date
      AND r.ts_code = p_ts_code
      AND r.time <= p_as_of_time
    ORDER BY r.time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 查询股票历史时间线
CREATE OR REPLACE FUNCTION get_stock_timeline(
    p_ts_code TEXT,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    trade_date DATE,
    name TEXT,
    total_score DOUBLE PRECISION,
    market_risk_level TEXT,
    auction_open_change_pct DOUBLE PRECISION,
    return_pct DOUBLE PRECISION,
    win_loss INTEGER,
    success_threshold_met BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.trade_date,
        r.name,
        r.total_score,
        r.market_risk_level,
        r.auction_open_change_pct,
        p.return_pct,
        p.win_loss,
        p.success_threshold_met
    FROM stock_recommendations r
    LEFT JOIN performance_stats p ON r.recommendation_id = p.recommendation_id
    WHERE r.ts_code = p_ts_code
      AND r.trade_date BETWEEN p_start_date AND p_end_date
    ORDER BY r.trade_date DESC;
END;
$$ LANGUAGE plpgsql;

-- 查询因子历史变化
CREATE OR REPLACE FUNCTION get_factor_history(
    p_factor_id TEXT,
    p_start_time TIMESTAMPTZ,
    p_end_time TIMESTAMPTZ
)
RETURNS TABLE (
    time TIMESTAMPTZ,
    factor_name TEXT,
    weight DOUBLE PRECISION,
    correlation_with_win DOUBLE PRECISION,
    ic_value DOUBLE PRECISION,
    is_effective BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.time,
        f.factor_name,
        f.weight,
        f.correlation_with_win,
        f.ic_value,
        f.is_effective
    FROM factor_weights_history f
    WHERE f.factor_id = p_factor_id
      AND f.time BETWEEN p_start_time AND p_end_time
    ORDER BY f.time;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. 统计计算函数
-- =====================================================

-- 计算日级胜率
CREATE OR REPLACE FUNCTION calculate_daily_win_rate(
    p_trade_date DATE
)
RETURNS TABLE (
    total_trades BIGINT,
    winning_trades BIGINT,
    losing_trades BIGINT,
    win_rate DOUBLE PRECISION,
    avg_return DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_trades,
        COUNT(*) FILTER (WHERE win_loss = 1)::BIGINT as winning_trades,
        COUNT(*) FILTER (WHERE win_loss = 0)::BIGINT as losing_trades,
        COUNT(*) FILTER (WHERE win_loss = 1)::DOUBLE PRECISION / 
            NULLIF(COUNT(*) FILTER (WHERE win_loss IN (0, 1)), 0) as win_rate,
        AVG(return_pct) as avg_return
    FROM performance_stats
    WHERE buy_date = p_trade_date;
END;
$$ LANGUAGE plpgsql;

-- 计算因子IC值（信息系数）
CREATE OR REPLACE FUNCTION calculate_factor_ic(
    p_factor_name TEXT,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    v_ic DOUBLE PRECISION;
BEGIN
    -- 简化的IC计算：因子值与收益率的相关系数
    SELECT 
        CORR(
            (r.t_day_raw_data->>'factor_value')::DOUBLE PRECISION,
            p.return_pct
        )
    INTO v_ic
    FROM stock_recommendations r
    JOIN performance_stats p ON r.recommendation_id = p.recommendation_id
    WHERE r.trade_date BETWEEN p_start_date AND p_end_date
      AND r.t_day_raw_data ? p_factor_name;
    
    RETURN v_ic;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. 数据更新触发器
-- =====================================================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 stock_recommendations 表创建触发器
DROP TRIGGER IF EXISTS update_stock_rec_updated_at ON stock_recommendations;
CREATE TRIGGER update_stock_rec_updated_at
    BEFORE UPDATE ON stock_recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 4. 数据验证函数
-- =====================================================

-- 验证推荐数据完整性
CREATE OR REPLACE FUNCTION validate_recommendation_data(
    p_trade_date DATE
)
RETURNS TABLE (
    ts_code TEXT,
    has_t_day_data BOOLEAN,
    has_risk_data BOOLEAN,
    has_auction_data BOOLEAN,
    completeness_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.ts_code,
        (r.t_day_score IS NOT NULL) as has_t_day_data,
        (r.market_risk_level IS NOT NULL) as has_risk_data,
        (r.auction_open_change_pct IS NOT NULL) as has_auction_data,
        CASE 
            WHEN r.t_day_score IS NOT NULL AND r.market_risk_level IS NOT NULL AND r.auction_open_change_pct IS NOT NULL THEN 100
            WHEN r.t_day_score IS NOT NULL AND r.market_risk_level IS NOT NULL THEN 66
            WHEN r.t_day_score IS NOT NULL THEN 33
            ELSE 0
        END as completeness_score
    FROM stock_recommendations r
    WHERE r.trade_date = p_trade_date;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. 机器学习辅助函数
-- =====================================================

-- 获取训练数据集
CREATE OR REPLACE FUNCTION get_ml_training_data(
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    trade_date DATE,
    ts_code TEXT,
    total_score DOUBLE PRECISION,
    market_risk_score INTEGER,
    auction_open_change_pct DOUBLE PRECISION,
    return_pct DOUBLE PRECISION,
    win_loss INTEGER,
    success_threshold_met BOOLEAN,
    features JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.trade_date,
        r.ts_code,
        r.total_score,
        r.market_risk_score,
        r.auction_open_change_pct,
        p.return_pct,
        p.win_loss,
        p.success_threshold_met,
        jsonb_build_object(
            't_day_score', r.t_day_score,
            'basic_score', r.basic_score,
            'seal_ratio', r.seal_ratio,
            'turnover_rate', r.turnover_rate,
            'main_net_ratio', r.main_net_ratio,
            'financing_change_ratio', r.financing_change_ratio,
            'is_hot_sector', r.is_hot_sector
        ) as features
    FROM stock_recommendations r
    LEFT JOIN performance_stats p ON r.recommendation_id = p.recommendation_id
    WHERE r.trade_date BETWEEN p_start_date AND p_end_date
      AND r.total_score IS NOT NULL
    ORDER BY r.trade_date, r.total_score DESC;
END;
$$ LANGUAGE plpgsql;

-- 批量更新因子权重
CREATE OR REPLACE FUNCTION update_factor_weights(
    p_weights JSONB,
    p_calculation_period TEXT
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_factor RECORD;
BEGIN
    FOR v_factor IN 
        SELECT * FROM jsonb_each(p_weights)
    LOOP
        INSERT INTO factor_weights_history (
            time,
            factor_id,
            factor_name,
            weight,
            calculation_period,
            valid_from
        )
        SELECT 
            NOW(),
            v_factor.key,
            v_factor.key,
            (v_factor.value->>'weight')::DOUBLE PRECISION,
            p_calculation_period,
            NOW()
        ON CONFLICT (time, factor_id) DO UPDATE
        SET weight = EXCLUDED.weight,
            calculation_period = EXCLUDED.calculation_period;
        
        v_count := v_count + 1;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

SELECT 'Functions created successfully' as status;
