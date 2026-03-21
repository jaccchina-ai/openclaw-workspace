#!/usr/bin/env python3
"""
T01 PostgreSQL + TimescaleDB 数据存储管理器
支持完整数据保存和时间旅行查询
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Union, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2 import sql
from psycopg2.pool import ThreadedConnectionPool
import pandas as pd

logger = logging.getLogger(__name__)


class T01PostgresStorage:
    """T01 PostgreSQL + TimescaleDB 数据存储管理器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """初始化数据存储管理器"""
        # 加载配置
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 数据库配置
        db_config = self.config.get('postgres', {})
        self.db_host = db_config.get('host', 'localhost')
        self.db_port = db_config.get('port', 5432)
        self.db_name = db_config.get('database', 't01_strategy')
        self.db_user = db_config.get('user', 't01_user')
        self.db_password = db_config.get('password', 't01_password')
        
        # 连接池配置
        pool_config = db_config.get('pool', {})
        self.pool_minconn = pool_config.get('min_size', 5)
        self.pool_maxconn = pool_config.get('max_size', 20)
        
        # 创建连接池
        self.pool = None
        self._initialize_pool()
        
        logger.info(f"T01 PostgreSQL存储管理器初始化完成: {self.db_host}:{self.db_port}/{self.db_name}")
    
    def _initialize_pool(self):
        """初始化连接池"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=self.pool_minconn,
                maxconn=self.pool_maxconn,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            logger.info(f"数据库连接池创建成功: {self.pool_minconn}-{self.pool_maxconn}连接")
        except Exception as e:
            logger.error(f"数据库连接池创建失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """获取数据库游标的上下文管理器"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def _generate_recommendation_id(self, trade_date: str, ts_code: str) -> str:
        """生成推荐记录ID"""
        data = f"{trade_date}_{ts_code}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    # =====================================================
    # 数据保存方法
    # =====================================================
    
    def save_t_day_recommendation(self, data: Dict[str, Any]) -> str:
        """
        保存T日推荐数据
        
        Args:
            data: 推荐数据字典，包含股票指标、评分等
            
        Returns:
            推荐记录ID
        """
        try:
            trade_date = data.get('trade_date', '')
            ts_code = data.get('ts_code', '')
            
            if not trade_date or not ts_code:
                raise ValueError("缺少必要字段: trade_date 或 ts_code")
            
            recommendation_id = self._generate_recommendation_id(trade_date, ts_code)
            
            # 准备数据
            record = {
                'time': datetime.now(),
                'trade_date': trade_date,
                't1_date': data.get('t1_date', ''),
                'ts_code': ts_code,
                'name': data.get('name', ''),
                'industry': data.get('industry', ''),
                
                # T日基础数据
                'close_price': data.get('close', 0),
                'pct_chg': data.get('pct_chg', 0),
                
                # T日评分
                't_day_score': data.get('t_day_score', 0) or data.get('total_score', 0),
                'total_score': data.get('total_score', 0),
                'basic_score': data.get('basic_score', 0),
                
                # 评分细节
                'score_details': data.get('score_details', {}),
                'first_limit_time_score': data.get('score_details', {}).get('first_limit_time', 0),
                'order_quality_score': data.get('score_details', {}).get('order_quality', 0),
                'liquidity_score': data.get('score_details', {}).get('liquidity', 0),
                'money_flow_score': data.get('score_details', {}).get('money_flow', 0),
                'sector_score': data.get('score_details', {}).get('sector', 0),
                'dragon_list_score': data.get('score_details', {}).get('dragon_list', 0),
                'sentiment_score': data.get('score_details', {}).get('sentiment', 0),
                
                # T日原始指标
                'first_limit_time': data.get('first_limit_time', ''),
                'seal_ratio': data.get('seal_ratio', 0),
                'seal_to_mv': data.get('seal_to_mv', 0),
                'fd_amount': data.get('fd_amount', 0),
                'amount': data.get('amount', 0),
                'float_mv': data.get('float_mv', 0),
                'turnover_rate': data.get('turnover_rate', 0),
                'turnover_20ma_ratio': data.get('turnover_20ma_ratio', 0),
                'volume_ratio': data.get('volume_ratio', 0),
                'main_net_amount': data.get('main_net_amount', 0),
                'main_net_ratio': data.get('main_net_ratio', 0),
                'medium_net_amount': data.get('medium_net_amount', 0),
                'is_hot_sector': data.get('is_hot_sector', False),
                
                # 风控数据（初始为空，后续更新）
                'market_financing_balance': None,
                'market_margin_balance': None,
                'market_total_balance': None,
                'financing_change_ratio': None,
                'margin_change_ratio': None,
                'financing_buy_ratio': None,
                'market_risk_level': None,
                'market_risk_score': None,
                'position_multiplier': None,
                
                # 竞价数据（初始为空，T+1日更新）
                'auction_open_price': None,
                'auction_open_change_pct': None,
                'auction_volume_ratio': None,
                'auction_turnover_rate': None,
                'auction_amount': None,
                'auction_vol': None,
                'pre_close': None,
                
                # 竞价风控（初始为空）
                'auction_risk_level': None,
                'auction_risk_score': None,
                'auction_position_adjustment': None,
                'final_recommendation': None,
                'suggested_position': None,
                
                # 原始数据JSON
                't_day_raw_data': json.dumps(data, ensure_ascii=False, default=str),
                'risk_control_raw_data': None,
                'auction_raw_data': None,
            }
            
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stock_recommendations (
                        time, trade_date, t1_date, ts_code, name, industry,
                        close_price, pct_chg, t_day_score, total_score, basic_score,
                        first_limit_time_score, order_quality_score, liquidity_score,
                        money_flow_score, sector_score, dragon_list_score, sentiment_score,
                        first_limit_time, seal_ratio, seal_to_mv, fd_amount, amount, float_mv,
                        turnover_rate, turnover_20ma_ratio, volume_ratio,
                        main_net_amount, main_net_ratio, medium_net_amount, is_hot_sector,
                        t_day_raw_data
                    ) VALUES (
                        %(time)s, %(trade_date)s, %(t1_date)s, %(ts_code)s, %(name)s, %(industry)s,
                        %(close_price)s, %(pct_chg)s, %(t_day_score)s, %(total_score)s, %(basic_score)s,
                        %(first_limit_time_score)s, %(order_quality_score)s, %(liquidity_score)s,
                        %(money_flow_score)s, %(sector_score)s, %(dragon_list_score)s, %(sentiment_score)s,
                        %(first_limit_time)s, %(seal_ratio)s, %(seal_to_mv)s, %(fd_amount)s, %(amount)s, %(float_mv)s,
                        %(turnover_rate)s, %(turnover_20ma_ratio)s, %(volume_ratio)s,
                        %(main_net_amount)s, %(main_net_ratio)s, %(medium_net_amount)s, %(is_hot_sector)s,
                        %(t_day_raw_data)s
                    )
                    ON CONFLICT (time, ts_code) DO UPDATE SET
                        t_day_score = EXCLUDED.t_day_score,
                        total_score = EXCLUDED.total_score,
                        basic_score = EXCLUDED.basic_score,
                        t_day_raw_data = EXCLUDED.t_day_raw_data,
                        updated_at = NOW()
                    RETURNING time
                """, record)
                
                result = cursor.fetchone()
                logger.debug(f"保存T日推荐记录: {recommendation_id} - {data.get('name', '')}({ts_code})")
                return recommendation_id
                
        except Exception as e:
            logger.error(f"保存T日推荐记录失败: {e}")
            raise
    
    def save_risk_control_data(self, trade_date: str, risk_data: Dict[str, Any]):
        """
        保存T日晚间风控数据
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            risk_data: 风控数据字典
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE stock_recommendations
                    SET 
                        market_financing_balance = %(financing_balance)s,
                        market_margin_balance = %(margin_balance)s,
                        market_total_balance = %(total_balance)s,
                        financing_change_ratio = %(financing_change_ratio)s,
                        margin_change_ratio = %(margin_change_ratio)s,
                        financing_buy_ratio = %(financing_buy_ratio)s,
                        market_risk_level = %(risk_level)s,
                        market_risk_score = %(risk_score)s,
                        position_multiplier = %(position_multiplier)s,
                        risk_control_raw_data = %(raw_data)s,
                        updated_at = NOW()
                    WHERE trade_date = %(trade_date)s
                """, {
                    'trade_date': trade_date,
                    'financing_balance': risk_data.get('total_financing_balance'),
                    'margin_balance': risk_data.get('total_margin_balance'),
                    'total_balance': risk_data.get('total_financing_margin_balance'),
                    'financing_change_ratio': risk_data.get('financing_change_ratio'),
                    'margin_change_ratio': risk_data.get('margin_change_ratio'),
                    'financing_buy_ratio': risk_data.get('financing_buy_ratio'),
                    'risk_level': risk_data.get('risk_level'),
                    'risk_score': risk_data.get('risk_score'),
                    'position_multiplier': risk_data.get('position_multiplier'),
                    'raw_data': json.dumps(risk_data, ensure_ascii=False, default=str)
                })
                
                updated_rows = cursor.rowcount
                logger.info(f"更新风控数据: {trade_date}, 影响 {updated_rows} 条记录")
                return updated_rows
                
        except Exception as e:
            logger.error(f"保存风控数据失败: {e}")
            raise
    
    def save_auction_data(self, trade_date: str, ts_code: str, auction_data: Dict[str, Any]):
        """
        保存T+1日竞价数据
        
        Args:
            trade_date: T+1日日期 (YYYYMMDD)
            ts_code: 股票代码
            auction_data: 竞价数据字典
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE stock_recommendations
                    SET 
                        auction_open_price = %(open_price)s,
                        auction_open_change_pct = %(open_change_pct)s,
                        auction_volume_ratio = %(volume_ratio)s,
                        auction_turnover_rate = %(turnover_rate)s,
                        auction_amount = %(amount)s,
                        auction_vol = %(vol)s,
                        pre_close = %(pre_close)s,
                        auction_score = %(auction_score)s,
                        auction_raw_data = %(raw_data)s,
                        total_score = COALESCE(t_day_score, 0) + COALESCE(%(auction_score)s, 0),
                        updated_at = NOW()
                    WHERE t1_date = %(trade_date)s AND ts_code = %(ts_code)s
                """, {
                    'trade_date': trade_date,
                    'ts_code': ts_code,
                    'open_price': auction_data.get('open_price'),
                    'open_change_pct': auction_data.get('open_change_pct'),
                    'volume_ratio': auction_data.get('volume_ratio'),
                    'turnover_rate': auction_data.get('turnover_rate'),
                    'amount': auction_data.get('amount'),
                    'vol': auction_data.get('vol'),
                    'pre_close': auction_data.get('pre_close'),
                    'auction_score': auction_data.get('auction_score', 0),
                    'raw_data': json.dumps(auction_data, ensure_ascii=False, default=str)
                })
                
                updated_rows = cursor.rowcount
                logger.debug(f"保存竞价数据: {ts_code} @ {trade_date}, 影响 {updated_rows} 条记录")
                return updated_rows
                
        except Exception as e:
            logger.error(f"保存竞价数据失败: {e}")
            raise
    
    def update_auction_risk_data(self, trade_date: str, ts_code: str, risk_data: Dict[str, Any]):
        """
        更新T+1日竞价风控数据
        
        Args:
            trade_date: T+1日日期 (YYYYMMDD)
            ts_code: 股票代码
            risk_data: 风控数据字典
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE stock_recommendations
                    SET 
                        auction_risk_level = %(risk_level)s,
                        auction_risk_score = %(risk_score)s,
                        auction_position_adjustment = %(position_adjustment)s,
                        final_recommendation = %(final_recommendation)s,
                        suggested_position = %(suggested_position)s,
                        updated_at = NOW()
                    WHERE t1_date = %(trade_date)s AND ts_code = %(ts_code)s
                """, {
                    'trade_date': trade_date,
                    'ts_code': ts_code,
                    'risk_level': risk_data.get('risk_level'),
                    'risk_score': risk_data.get('risk_score'),
                    'position_adjustment': risk_data.get('position_adjustment'),
                    'final_recommendation': risk_data.get('final_recommendation'),
                    'suggested_position': risk_data.get('suggested_position')
                })
                
                updated_rows = cursor.rowcount
                logger.debug(f"更新竞价风控数据: {ts_code} @ {trade_date}, 影响 {updated_rows} 条记录")
                return updated_rows
                
        except Exception as e:
            logger.error(f"更新竞价风控数据失败: {e}")
            raise
    
    # =====================================================
    # 时间旅行查询方法
    # =====================================================
    
    def get_recommendation_as_of(self, trade_date: str, ts_code: str, 
                                  as_of_time: datetime = None) -> Optional[Dict[str, Any]]:
        """
        查询特定时间点的股票推荐状态（时间旅行查询）
        
        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            as_of_time: 查询时间点，默认为当前时间
            
        Returns:
            推荐记录字典，如果未找到返回None
        """
        try:
            if as_of_time is None:
                as_of_time = datetime.now()
            
            with self.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM stock_recommendations
                    WHERE trade_date = %s AND ts_code = %s
                      AND time <= %s
                    ORDER BY time DESC
                    LIMIT 1
                """, (trade_date, ts_code, as_of_time))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    for key in ['t_day_raw_data', 'risk_control_raw_data', 'auction_raw_data']:
                        if result.get(key):
                            try:
                                result[key] = json.loads(result[key])
                            except:
                                pass
                    
                    return result
                return None
                
        except Exception as e:
            logger.error(f"时间旅行查询失败: {e}")
            return None
    
    def get_factor_history(self, factor_id: str, start_time: datetime = None, 
                           end_time: datetime = None) -> pd.DataFrame:
        """
        查询因子历史变化
        
        Args:
            factor_id: 因子ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            因子历史数据DataFrame
        """
        try:
            if end_time is None:
                end_time = datetime.now()
            if start_time is None:
                start_time = end_time - timedelta(days=30)
            
            query = """
                SELECT 
                    time,
                    factor_name,
                    weight,
                    correlation_with_win,
                    ic_value,
                    is_effective
                FROM factor_weights_history
                WHERE factor_id = %s
                  AND time BETWEEN %s AND %s
                ORDER BY time
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=(factor_id, start_time, end_time))
                return df
                
        except Exception as e:
            logger.error(f"查询因子历史失败: {e}")
            return pd.DataFrame()
    
    def get_stock_timeline(self, ts_code: str, start_date: str = None, 
                           end_date: str = None) -> pd.DataFrame:
        """
        查询股票完整时间线
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            股票时间线DataFrame
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            query = """
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
                WHERE r.ts_code = %s
                  AND r.trade_date BETWEEN %s AND %s
                ORDER BY r.trade_date DESC
            """
            
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=(ts_code, start_date, end_date))
                return df
                
        except Exception as e:
            logger.error(f"查询股票时间线失败: {e}")
            return pd.DataFrame()
    
    def get_daily_stats(self, trade_date: str) -> Dict[str, Any]:
        """
        获取日级统计
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            日级统计字典
        """
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM daily_recommendation_stats
                    WHERE trade_date = %s
                    LIMIT 1
                """, (trade_date,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return {}
                
        except Exception as e:
            logger.error(f"获取日级统计失败: {e}")
            return {}
    
    # =====================================================
    # 交易和表现记录
    # =====================================================
    
    def record_trade(self, trade_data: Dict[str, Any]) -> str:
        """
        记录交易
        
        Args:
            trade_data: 交易数据字典
            
        Returns:
            交易记录ID
        """
        try:
            recommendation_id = trade_data.get('recommendation_id', '')
            trade_type = trade_data.get('trade_type', '')
            trade_date = trade_data.get('trade_date', '')
            
            trade_id = f"{recommendation_id}_{trade_type}_{trade_date}"
            
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trade_records (
                        time, trade_id, recommendation_id, ts_code, name,
                        trade_date, trade_type, trade_time, price, quantity,
                        amount, commission, status, notes, entry_score
                    ) VALUES (
                        NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (time, trade_id) DO UPDATE SET
                        price = EXCLUDED.price,
                        quantity = EXCLUDED.quantity,
                        amount = EXCLUDED.amount,
                        status = EXCLUDED.status
                    RETURNING trade_id
                """, (
                    trade_id, recommendation_id, 
                    trade_data.get('ts_code', ''), trade_data.get('name', ''),
                    trade_date, trade_type, trade_data.get('trade_time', ''),
                    trade_data.get('price', 0), trade_data.get('quantity', 0),
                    trade_data.get('amount', 0), trade_data.get('commission', 0),
                    trade_data.get('status', 'pending'), trade_data.get('notes', ''),
                    trade_data.get('entry_score', 0)
                ))
                
                result = cursor.fetchone()
                logger.debug(f"记录交易: {trade_id}")
                return trade_id
                
        except Exception as e:
            logger.error(f"记录交易失败: {e}")
            raise
    
    def record_performance(self, performance_data: Dict[str, Any]) -> str:
        """
        记录表现统计
        
        Args:
            performance_data: 表现数据字典
            
        Returns:
            表现记录ID
        """
        try:
            recommendation_id = performance_data.get('recommendation_id', '')
            performance_id = f"{recommendation_id}_perf"
            
            # 计算成功标准 (T+2收盘价/T+1开盘价 > 1.03%)
            t1_open = performance_data.get('t1_open_price', 0)
            t2_close = performance_data.get('t2_close_price', 0)
            success_threshold_met = None
            t2_return = None
            
            if t1_open > 0 and t2_close > 0:
                t2_return = (t2_close - t1_open) / t1_open * 100
                success_threshold_met = t2_return > 1.03
            
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO performance_stats (
                        time, performance_id, recommendation_id, ts_code, name,
                        buy_date, buy_price, buy_time, sell_date, sell_price,
                        sell_time, holding_days, return_pct, win_loss,
                        max_drawdown, success_threshold_met, t1_open_price,
                        t2_close_price, t2_return_pct
                    ) VALUES (
                        NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (time, performance_id) DO UPDATE SET
                        sell_date = EXCLUDED.sell_date,
                        sell_price = EXCLUDED.sell_price,
                        return_pct = EXCLUDED.return_pct,
                        win_loss = EXCLUDED.win_loss,
                        success_threshold_met = EXCLUDED.success_threshold_met,
                        t2_return_pct = EXCLUDED.t2_return_pct
                    RETURNING performance_id
                """, (
                    performance_id, recommendation_id,
                    performance_data.get('ts_code', ''), performance_data.get('name', ''),
                    performance_data.get('buy_date', ''), performance_data.get('buy_price', 0),
                    performance_data.get('buy_time', ''), performance_data.get('sell_date'),
                    performance_data.get('sell_price', 0), performance_data.get('sell_time', ''),
                    performance_data.get('holding_days', 0), performance_data.get('return_pct', 0),
                    performance_data.get('win_loss', -1), performance_data.get('max_drawdown', 0),
                    success_threshold_met, t1_open, t2_close, t2_return
                ))
                
                result = cursor.fetchone()
                logger.debug(f"记录表现统计: {performance_id}, 成功标准: {success_threshold_met}")
                return performance_id
                
        except Exception as e:
            logger.error(f"记录表现统计失败: {e}")
            raise
    
    def log_ml_session(self, session_data: Dict[str, Any]) -> int:
        """
        记录机器学习会话
        
        Args:
            session_data: 会话数据字典
            
        Returns:
            日志记录ID
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ml_learning_logs (
                        time, session_id, model_type, model_version,
                        training_start_date, training_end_date,
                        training_data_size, test_data_size,
                        metrics, improvements, new_factors, feature_importance,
                        execution_time_seconds, status
                    ) VALUES (
                        NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    session_data.get('session_id', datetime.now().strftime('%Y%m%d_%H%M%S')),
                    session_data.get('model_type', 'unknown'),
                    session_data.get('model_version', ''),
                    session_data.get('training_start_date'),
                    session_data.get('training_end_date'),
                    session_data.get('training_data_size', 0),
                    session_data.get('test_data_size', 0),
                    json.dumps(session_data.get('metrics', {}), ensure_ascii=False),
                    json.dumps(session_data.get('improvements', {}), ensure_ascii=False),
                    json.dumps(session_data.get('new_factors', []), ensure_ascii=False),
                    json.dumps(session_data.get('feature_importance', {}), ensure_ascii=False),
                    session_data.get('execution_time_seconds', 0),
                    session_data.get('status', 'completed')
                ))
                
                result = cursor.fetchone()
                log_id = result[0]
                logger.info(f"记录ML会话: {session_data.get('session_id')} - {session_data.get('model_type')}")
                return log_id
                
        except Exception as e:
            logger.error(f"记录ML会话失败: {e}")
            return -1
    
    # =====================================================
    # 数据迁移方法
    # =====================================================
    
    def migrate_from_sqlite(self, sqlite_db_path: str):
        """
        从 SQLite 迁移历史数据
        
        Args:
            sqlite_db_path: SQLite 数据库路径
        """
        try:
            import sqlite3
            
            logger.info(f"开始从 SQLite 迁移数据: {sqlite_db_path}")
            
            # 连接 SQLite
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # 迁移推荐记录
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT * FROM t01_recommendations")
            rows = cursor.fetchall()
            
            migrated_count = 0
            for row in rows:
                try:
                    data = {
                        'trade_date': row['trade_date'],
                        'ts_code': row['ts_code'],
                        'name': row['name'],
                        'total_score': row['total_score'],
                        't_day_score': row['t_day_score'],
                        'auction_score': row['auction_score'],
                    }
                    
                    # 解析JSON数据
                    if row['recommendation_json']:
                        json_data = json.loads(row['recommendation_json'])
                        data.update(json_data)
                    
                    self.save_t_day_recommendation(data)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"迁移单条记录失败: {e}")
                    continue
            
            sqlite_conn.close()
            logger.info(f"数据迁移完成: {migrated_count} 条记录")
            return migrated_count
            
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            raise
    
    # =====================================================
    # 工具方法
    # =====================================================
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        执行自定义查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果 DataFrame
        """
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return pd.DataFrame()
    
    def close(self):
        """关闭数据库连接池"""
        if self.pool:
            self.pool.closeall()
            logger.info("数据库连接池已关闭")


# 便捷函数
def get_postgres_storage(config_path: str = 'config.yaml') -> T01PostgresStorage:
    """获取 PostgreSQL 存储实例（单例模式）"""
    if not hasattr(get_postgres_storage, '_instance'):
        get_postgres_storage._instance = T01PostgresStorage(config_path)
    return get_postgres_storage._instance


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建配置
    config = {
        'postgres': {
            'host': 'localhost',
            'port': 5432,
            'database': 't01_strategy',
            'user': 't01_user',
            'password': 't01_password',
            'pool': {
                'min_size': 5,
                'max_size': 20
            }
        }
    }
    
    # 保存配置到临时文件
    import yaml
    with open('/tmp/test_config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    try:
        storage = T01PostgresStorage('/tmp/test_config.yaml')
        
        # 测试保存推荐记录
        test_data = {
            'trade_date': '20260321',
            't1_date': '20260324',
            'ts_code': '000001.SZ',
            'name': '平安银行',
            'close': 10.5,
            'pct_chg': 10.02,
            'total_score': 150.5,
            'score_details': {
                'first_limit_time': 30,
                'order_quality': 25,
                'liquidity': 10,
                'money_flow': 10,
                'sector': 5,
                'dragon_list': 70.5,
                'sentiment': 0
            }
        }
        
        rec_id = storage.save_t_day_recommendation(test_data)
        print(f"✅ 保存推荐记录成功: {rec_id}")
        
        # 测试时间旅行查询
        result = storage.get_recommendation_as_of('20260321', '000001.SZ')
        if result:
            print(f"✅ 时间旅行查询成功: {result['name']} - 评分: {result['total_score']}")
        
        storage.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
