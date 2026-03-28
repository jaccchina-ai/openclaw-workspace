#!/usr/bin/env python3
"""
T01系统数据存储模块
负责本地化存储选股数据、交易记录、表现统计，为机器学习提供数据基础
"""

import sys
import sqlite3
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
import hashlib

logger = logging.getLogger(__name__)


class T01DataStorage:
    """T01系统数据存储管理器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化数据存储管理器"""
        # 加载配置
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 数据库配置
        db_config = self.config.get('data_storage', {}).get('database', {})
        self.db_type = db_config.get('type', 'sqlite')
        self.db_path = Path(db_config.get('path', './data/t01_database.db'))
        self.auto_backup = db_config.get('auto_backup', True)
        self.backup_path = Path(db_config.get('backup_path', './data/backups/'))
        
        # 表名配置
        tables_config = self.config.get('data_storage', {}).get('tables', {})
        self.table_recommendations = tables_config.get('recommendations', 't01_recommendations')
        self.table_trades = tables_config.get('trades', 't01_trades')
        self.table_performance = tables_config.get('performance', 't01_performance')
        self.table_factors = tables_config.get('factors', 't01_factors')
        self.table_learning_logs = tables_config.get('learning_logs', 't01_learning_logs')
        self.table_auction_data = tables_config.get('auction_data', 't01_auction_data')  # 竞价数据表
        
        # 创建数据库连接
        self.conn = None
        self.cursor = None
        
        # 初始化数据库
        self._initialize_database()
        
        logger.info(f"T01数据存储管理器初始化完成，数据库: {self.db_path}")
    
    def _initialize_database(self):
        """初始化数据库和表结构"""
        try:
            # 确保目录存在
            self.db_path.parent.mkdir(exist_ok=True)
            self.backup_path.mkdir(exist_ok=True)
            
            # 连接数据库
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 支持字典式访问
            self.cursor = self.conn.cursor()
            
            # 创建推荐记录表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_recommendations} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id TEXT UNIQUE NOT NULL,  -- 推荐ID (日期+股票代码的哈希)
                trade_date TEXT NOT NULL,                -- 交易日期 (YYYYMMDD)
                t1_date TEXT NOT NULL,                   -- T+1日期
                ts_code TEXT NOT NULL,                   -- 股票代码
                name TEXT NOT NULL,                      -- 股票名称
                total_score REAL,                        -- 总评分
                t_day_score REAL,                        -- T日评分
                auction_score REAL,                      -- 竞价评分
                open_change_pct REAL,                    -- 开盘涨幅
                recommendation_json TEXT,                -- 完整推荐信息 (JSON)
                risk_level TEXT,                         -- 风险等级 (低/中/高/极高)
                risk_score REAL,                         -- 风险评分 (0-10)
                financing_change_pct REAL,               -- 融资余额变化率 (%)
                margin_change_pct REAL,                  -- 融券余额变化率 (%)
                financing_buy_ratio REAL,                -- 融资买入/偿还比率
                position_multiplier REAL,                -- 仓位乘数
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建索引
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_rec_trade_date ON {self.table_recommendations}(trade_date)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_rec_ts_code ON {self.table_recommendations}(ts_code)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_rec_score ON {self.table_recommendations}(total_score DESC)')
            
            # 创建交易记录表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_trades} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,           -- 交易ID (推荐ID + 交易类型)
                recommendation_id TEXT NOT NULL,         -- 对应的推荐ID
                trade_type TEXT NOT NULL,                -- 交易类型 (buy/sell)
                trade_date TEXT NOT NULL,                -- 交易日期
                trade_time TEXT,                         -- 交易时间
                price REAL NOT NULL,                     -- 交易价格
                quantity INTEGER,                        -- 交易数量
                amount REAL,                             -- 交易金额
                commission REAL DEFAULT 0.0,             -- 手续费
                status TEXT DEFAULT 'pending',           -- 状态 (pending/completed/cancelled)
                notes TEXT,                              -- 备注
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES {self.table_recommendations}(recommendation_id)
            )
            ''')
            
            # 创建索引
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_trades_recommendation ON {self.table_trades}(recommendation_id)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_trades_date ON {self.table_trades}(trade_date)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_trades_type ON {self.table_trades}(trade_type)')
            
            # 创建表现统计表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_performance} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                performance_id TEXT UNIQUE NOT NULL,     -- 表现ID
                recommendation_id TEXT NOT NULL,         -- 对应的推荐ID
                buy_date TEXT NOT NULL,                  -- 买入日期
                buy_price REAL NOT NULL,                 -- 买入价格
                sell_date TEXT,                          -- 卖出日期
                sell_price REAL,                         -- 卖出价格
                holding_days INTEGER,                    -- 持有天数
                return_pct REAL,                         -- 收益率 (%)
                win_loss INTEGER,                        -- 盈亏 (1:盈利, 0:亏损, -1:未完成)
                max_drawdown REAL,                       -- 最大回撤
                sharpe_ratio REAL,                       -- 夏普比率
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES {self.table_recommendations}(recommendation_id)
            )
            ''')
            
            # 创建因子数据表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_factors} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_id TEXT UNIQUE NOT NULL,          -- 因子ID
                factor_name TEXT NOT NULL,               -- 因子名称
                factor_type TEXT NOT NULL,               -- 因子类型 (technical/fundamental/market/sentiment)
                calculation_formula TEXT,                -- 计算公式
                description TEXT,                        -- 因子描述
                weight REAL DEFAULT 1.0,                 -- 因子权重
                correlation_with_win REAL,               -- 与胜率的相关性
                importance_score REAL,                   -- 重要性评分
                is_active BOOLEAN DEFAULT 1,            -- 是否启用
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建学习日志表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_learning_logs} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,                -- 学习会话ID
                model_type TEXT NOT NULL,                -- 模型类型
                training_data_size INTEGER,              -- 训练数据大小
                test_data_size INTEGER,                  -- 测试数据大小
                metrics_json TEXT,                       -- 评估指标 (JSON)
                improvements_json TEXT,                  -- 改进结果 (JSON)
                new_factors_json TEXT,                   -- 新发现的因子 (JSON)
                execution_time REAL,                     -- 执行时间 (秒)
                status TEXT DEFAULT 'completed',         -- 状态
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建竞价数据表
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_auction_data} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id TEXT UNIQUE NOT NULL,         -- 竞价记录ID (日期+股票代码的哈希)
                trade_date TEXT NOT NULL,                -- T+1交易日期 (YYYYMMDD)
                t_date TEXT NOT NULL,                    -- T日日期 (YYYYMMDD)
                ts_code TEXT NOT NULL,                   -- 股票代码
                name TEXT NOT NULL,                      -- 股票名称
                open_price REAL,                         -- 开盘价
                pre_close REAL,                          -- 前收盘价
                open_change_pct REAL,                    -- 开盘涨幅 (%)
                auction_volume INTEGER,                  -- 竞价成交量 (手)
                auction_amount REAL,                     -- 竞价成交额 (元)
                auction_volume_ratio REAL,               -- 竞价量比
                auction_turnover_rate REAL,              -- 竞价换手率 (%)
                auction_volume_to_t_volume REAL,         -- 竞价成交量/T日成交量比值
                t_day_volume INTEGER,                    -- T日成交量 (手)
                auction_score REAL,                      -- 竞价评分
                data_source TEXT,                        -- 数据来源 (realtime/history/simulated)
                final_score REAL,                        -- 最终评分 (T日评分*0.7 + 竞价评分*0.3)
                recommendation TEXT,                     -- 推荐建议 (买入/观望)
                confidence TEXT,                         -- 置信度 (高/中/低)
                position_pct REAL,                       -- 建议仓位 (%)
                reasons_json TEXT,                       -- 推荐理由 (JSON数组)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建竞价数据表索引
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_auction_trade_date ON {self.table_auction_data}(trade_date)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_auction_ts_code ON {self.table_auction_data}(ts_code)')
            self.cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_auction_t_date ON {self.table_auction_data}(t_date)')

            self.conn.commit()
            logger.info("数据库表结构初始化完成")
            
            # 初始化默认因子数据
            self._initialize_default_factors()
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _initialize_default_factors(self):
        """初始化默认因子数据"""
        default_factors = [
            {
                'factor_id': 'first_limit_time',
                'factor_name': '首次涨停时间',
                'factor_type': 'technical',
                'description': '股票首次涨停时间，越早越好',
                'weight': 30.0
            },
            {
                'factor_id': 'seal_ratio',
                'factor_name': '封成比',
                'factor_type': 'technical', 
                'description': '封单金额/成交金额',
                'weight': 10.0
            },
            {
                'factor_id': 'seal_to_mv',
                'factor_name': '封单/流通市值',
                'factor_type': 'technical',
                'description': '封单金额/流通市值',
                'weight': 15.0
            },
            {
                'factor_id': 'turnover_rate',
                'factor_name': '换手率',
                'factor_type': 'technical',
                'description': '当日换手率',
                'weight': 5.0
            },
            {
                'factor_id': 'turnover_20ma_ratio',
                'factor_name': '换手率/20日均值',
                'factor_type': 'technical',
                'description': '换手率与20日均值的比值',
                'weight': 10.0
            },
            {
                'factor_id': 'volume_ratio',
                'factor_name': '量比',
                'factor_type': 'technical',
                'description': '成交量与过去5日均量的比值',
                'weight': 5.0
            },
            {
                'factor_id': 'main_net_amount',
                'factor_name': '主力净额',
                'factor_type': 'moneyflow',
                'description': '主力资金净流入金额',
                'weight': 5.0
            },
            {
                'factor_id': 'main_net_ratio',
                'factor_name': '主力净占比',
                'factor_type': 'moneyflow',
                'description': '主力资金净流入占比',
                'weight': 5.0
            },
            {
                'factor_id': 'medium_net_amount',
                'factor_name': '中单净额',
                'factor_type': 'moneyflow',
                'description': '中单资金净流入金额',
                'weight': 5.0
            },
            {
                'factor_id': 'is_hot_sector',
                'factor_name': '热点板块',
                'factor_type': 'market',
                'description': '是否属于热点行业板块',
                'weight': 10.0
            },
            {
                'factor_id': 'open_change_pct',
                'factor_name': '开盘涨幅',
                'factor_type': 'auction',
                'description': '竞价阶段开盘涨幅',
                'weight': 40.0
            },
            {
                'factor_id': 'auction_volume_ratio',
                'factor_name': '竞价量比',
                'factor_type': 'auction',
                'description': '竞价阶段量比',
                'weight': 20.0
            },
            {
                'factor_id': 'auction_turnover_rate',
                'factor_name': '竞价换手率',
                'factor_type': 'auction',
                'description': '竞价阶段换手率',
                'weight': 20.0
            },
            {
                'factor_id': 'auction_amount',
                'factor_name': '竞价金额',
                'factor_type': 'auction',
                'description': '竞价阶段成交金额',
                'weight': 20.0
            }
        ]
        
        try:
            for factor in default_factors:
                # 检查因子是否已存在
                self.cursor.execute(
                    f"SELECT COUNT(*) FROM {self.table_factors} WHERE factor_id = ?",
                    (factor['factor_id'],)
                )
                if self.cursor.fetchone()[0] == 0:
                    self.cursor.execute(f'''
                    INSERT INTO {self.table_factors} 
                    (factor_id, factor_name, factor_type, description, weight)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        factor['factor_id'],
                        factor['factor_name'],
                        factor['factor_type'],
                        factor['description'],
                        factor['weight']
                    ))
            
            self.conn.commit()
            logger.info(f"初始化 {len(default_factors)} 个默认因子")
            
        except Exception as e:
            logger.warning(f"初始化默认因子失败: {e}")
    
    def _generate_recommendation_id(self, trade_date: str, ts_code: str) -> str:
        """生成推荐记录ID"""
        # 使用日期和股票代码生成唯一ID
        data = f"{trade_date}_{ts_code}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def save_recommendation(self, recommendation_data: Dict[str, Any]) -> str:
        """
        保存推荐记录
        
        Args:
            recommendation_data: 推荐数据字典
            
        Returns:
            推荐记录ID
        """
        try:
            # 提取关键数据
            trade_date = recommendation_data.get('trade_date', '')
            t1_date = recommendation_data.get('t1_date', '')
            ts_code = recommendation_data.get('ts_code', '')
            name = recommendation_data.get('name', '')
            
            if not trade_date or not ts_code:
                raise ValueError("缺少必要字段: trade_date 或 ts_code")
            
            # 生成推荐ID
            recommendation_id = self._generate_recommendation_id(trade_date, ts_code)
            
            # 准备数据
            total_score = recommendation_data.get('total_score', 0.0)
            t_day_score = recommendation_data.get('t_day_score', total_score)
            auction_score = recommendation_data.get('auction_score', 0.0)
            open_change_pct = recommendation_data.get('auction_data', {}).get('open_change_pct', 0.0)

            # 风控数据
            risk_data = recommendation_data.get('risk_control', {})
            risk_level = risk_data.get('risk_level', '')
            risk_score = risk_data.get('risk_score', 0.0)
            financing_change_pct = risk_data.get('financing_change_pct', 0.0)
            margin_change_pct = risk_data.get('margin_change_pct', 0.0)
            financing_buy_ratio = risk_data.get('financing_buy_repay_ratio', 0.0)
            position_multiplier = risk_data.get('position_multiplier', 1.0)

            # 转换为JSON字符串
            recommendation_json = json.dumps(recommendation_data, ensure_ascii=False)

            # 插入或更新记录
            self.cursor.execute(f'''
            INSERT OR REPLACE INTO {self.table_recommendations}
            (recommendation_id, trade_date, t1_date, ts_code, name,
             total_score, t_day_score, auction_score, open_change_pct, recommendation_json,
             risk_level, risk_score, financing_change_pct, margin_change_pct, financing_buy_ratio, position_multiplier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation_id, trade_date, t1_date, ts_code, name,
                total_score, t_day_score, auction_score, open_change_pct, recommendation_json,
                risk_level, risk_score, financing_change_pct, margin_change_pct, financing_buy_ratio, position_multiplier
            ))
            
            self.conn.commit()
            logger.debug(f"保存推荐记录: {recommendation_id} - {name}({ts_code})")
            
            return recommendation_id
            
        except Exception as e:
            logger.error(f"保存推荐记录失败: {e}")
            raise
    
    def record_trade(self, recommendation_id: str, trade_data: Dict[str, Any]) -> str:
        """
        记录交易
        
        Args:
            recommendation_id: 推荐记录ID
            trade_data: 交易数据
            
        Returns:
            交易记录ID
        """
        try:
            # 提取交易数据
            trade_type = trade_data.get('trade_type', '')  # buy/sell
            trade_date = trade_data.get('trade_date', '')
            trade_time = trade_data.get('trade_time', '')
            price = trade_data.get('price', 0.0)
            quantity = trade_data.get('quantity', 0)
            amount = trade_data.get('amount', price * quantity if quantity else 0)
            commission = trade_data.get('commission', 0.0)
            status = trade_data.get('status', 'pending')
            notes = trade_data.get('notes', '')
            
            if not trade_type or not trade_date or price <= 0:
                raise ValueError("交易数据不完整")
            
            # 生成交易ID
            trade_id = f"{recommendation_id}_{trade_type}_{trade_date}"
            
            self.cursor.execute(f'''
            INSERT INTO {self.table_trades}
            (trade_id, recommendation_id, trade_type, trade_date, trade_time,
             price, quantity, amount, commission, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_id, recommendation_id, trade_type, trade_date, trade_time,
                price, quantity, amount, commission, status, notes
            ))
            
            self.conn.commit()
            logger.debug(f"记录交易: {trade_id} - {trade_type} @ {price}")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"记录交易失败: {e}")
            raise
    
    def record_performance(self, recommendation_id: str, performance_data: Dict[str, Any]) -> str:
        """
        记录表现统计
        
        Args:
            recommendation_id: 推荐记录ID
            performance_data: 表现数据
            
        Returns:
            表现记录ID
        """
        try:
            # 提取表现数据
            buy_date = performance_data.get('buy_date', '')
            buy_price = performance_data.get('buy_price', 0.0)
            sell_date = performance_data.get('sell_date', '')
            sell_price = performance_data.get('sell_price', 0.0)
            holding_days = performance_data.get('holding_days', 0)
            
            # 计算收益率
            return_pct = 0.0
            win_loss = -1  # 默认未完成
            
            if sell_price > 0 and buy_price > 0:
                return_pct = (sell_price - buy_price) / buy_price * 100
                win_loss = 1 if return_pct > 0 else 0
            
            # 其他指标
            max_drawdown = performance_data.get('max_drawdown', 0.0)
            sharpe_ratio = performance_data.get('sharpe_ratio', 0.0)
            
            # 生成表现ID
            performance_id = f"{recommendation_id}_perf"
            
            self.cursor.execute(f'''
            INSERT OR REPLACE INTO {self.table_performance}
            (performance_id, recommendation_id, buy_date, buy_price, sell_date,
             sell_price, holding_days, return_pct, win_loss, max_drawdown, sharpe_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                performance_id, recommendation_id, buy_date, buy_price, sell_date,
                sell_price, holding_days, return_pct, win_loss, max_drawdown, sharpe_ratio
            ))
            
            self.conn.commit()
            logger.debug(f"记录表现统计: {performance_id} - 收益率: {return_pct:.2f}%")
            
            return performance_id
            
        except Exception as e:
            logger.error(f"记录表现统计失败: {e}")
            raise
    
    def get_recommendation(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        """获取推荐记录"""
        try:
            self.cursor.execute(
                f"SELECT * FROM {self.table_recommendations} WHERE recommendation_id = ?",
                (recommendation_id,)
            )
            row = self.cursor.fetchone()
            
            if row:
                # 将Row对象转换为字典
                result = dict(row)
                # 解析JSON字段
                if result.get('recommendation_json'):
                    result['recommendation_data'] = json.loads(result['recommendation_json'])
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"获取推荐记录失败: {e}")
            return None
    
    def get_trades_by_recommendation(self, recommendation_id: str) -> List[Dict[str, Any]]:
        """获取某个推荐的所有交易记录"""
        try:
            self.cursor.execute(
                f"SELECT * FROM {self.table_trades} WHERE recommendation_id = ? ORDER BY trade_date, trade_type",
                (recommendation_id,)
            )
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取交易记录失败: {e}")
            return []
    
    def get_performance_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        获取表现统计
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            表现统计字典
        """
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if start_date:
                conditions.append("p.buy_date >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("p.buy_date <= ?")
                params.append(end_date)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 查询已完成交易的表现数据
            query = f'''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN p.win_loss = 1 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN p.win_loss = 0 THEN 1 ELSE 0 END) as losing_trades,
                AVG(p.return_pct) as avg_return,
                MIN(p.return_pct) as min_return,
                MAX(p.return_pct) as max_return,
                AVG(p.max_drawdown) as avg_drawdown,
                AVG(p.sharpe_ratio) as avg_sharpe,
                COUNT(DISTINCT r.ts_code) as unique_stocks
            FROM {self.table_performance} p
            JOIN {self.table_recommendations} r ON p.recommendation_id = r.recommendation_id
            {where_clause}
            AND p.win_loss IN (0, 1)  -- 只统计已完成交易
            '''
            
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            
            if row:
                stats = dict(row)
                total_trades = stats['total_trades']
                winning_trades = stats['winning_trades']
                
                # 计算胜率
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                stats['win_rate_pct'] = win_rate
                
                # 盈亏因子
                if stats.get('losing_trades', 0) > 0:
                    stats['profit_factor'] = winning_trades / stats['losing_trades']
                else:
                    stats['profit_factor'] = float('inf') if winning_trades > 0 else 0
                
                return stats
            
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0,
                'avg_return': 0,
                'profit_factor': 0
            }
            
        except Exception as e:
            logger.error(f"获取表现统计失败: {e}")
            return {}
    
    def get_factor_data(self) -> pd.DataFrame:
        """获取因子数据"""
        try:
            query = f"SELECT * FROM {self.table_factors} WHERE is_active = 1 ORDER BY weight DESC"
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            logger.error(f"获取因子数据失败: {e}")
            return pd.DataFrame()
    
    def update_factor_weight(self, factor_id: str, new_weight: float):
        """更新因子权重"""
        try:
            self.cursor.execute(
                f"UPDATE {self.table_factors} SET weight = ?, updated_at = CURRENT_TIMESTAMP WHERE factor_id = ?",
                (new_weight, factor_id)
            )
            self.conn.commit()
            logger.info(f"更新因子权重: {factor_id} -> {new_weight}")
        except Exception as e:
            logger.error(f"更新因子权重失败: {e}")
    
    def log_learning_session(self, session_data: Dict[str, Any]) -> int:
        """记录机器学习会话"""
        try:
            session_id = session_data.get('session_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
            model_type = session_data.get('model_type', 'unknown')
            training_data_size = session_data.get('training_data_size', 0)
            test_data_size = session_data.get('test_data_size', 0)
            metrics_json = json.dumps(session_data.get('metrics', {}), ensure_ascii=False)
            improvements_json = json.dumps(session_data.get('improvements', {}), ensure_ascii=False)
            new_factors_json = json.dumps(session_data.get('new_factors', []), ensure_ascii=False)
            execution_time = session_data.get('execution_time', 0.0)
            status = session_data.get('status', 'completed')
            
            self.cursor.execute(f'''
            INSERT INTO {self.table_learning_logs}
            (session_id, model_type, training_data_size, test_data_size,
             metrics_json, improvements_json, new_factors_json, execution_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, model_type, training_data_size, test_data_size,
                metrics_json, improvements_json, new_factors_json, execution_time, status
            ))
            
            self.conn.commit()
            log_id = self.cursor.lastrowid
            
            logger.info(f"记录机器学习会话: {session_id} - {model_type}")
            return log_id
            
        except Exception as e:
            logger.error(f"记录机器学习会话失败: {e}")
            return -1
    
    def backup_database(self):
        """备份数据库"""
        if not self.auto_backup:
            return
        
        try:
            backup_file = self.backup_path / f"t01_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # 创建备份连接
            backup_conn = sqlite3.connect(backup_file)
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"数据库备份完成: {backup_file}")
            
            # 清理旧备份文件（保留最近7天）
            cutoff_time = datetime.now() - timedelta(days=7)
            for backup in self.backup_path.glob("t01_db_backup_*.db"):
                backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
                if backup_time < cutoff_time:
                    backup.unlink()
                    logger.debug(f"删除旧备份: {backup}")
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
    
    def save_auction_data(self, auction_data: Dict[str, Any]) -> str:
        """
        保存竞价数据到数据库

        Args:
            auction_data: 竞价数据字典，包含以下字段:
                - trade_date: T+1日期
                - t_date: T日日期
                - ts_code: 股票代码
                - name: 股票名称
                - open_price: 开盘价
                - pre_close: 前收盘价
                - open_change_pct: 开盘涨幅
                - auction_volume: 竞价成交量
                - auction_amount: 竞价成交额
                - auction_volume_ratio: 竞价量比
                - auction_turnover_rate: 竞价换手率
                - auction_volume_to_t_volume: 竞价成交量/T日成交量比值
                - t_day_volume: T日成交量
                - auction_score: 竞价评分
                - data_source: 数据来源
                - final_score: 最终评分
                - recommendation: 推荐建议
                - confidence: 置信度
                - position_pct: 建议仓位
                - reasons: 推荐理由列表

        Returns:
            auction_id: 竞价记录ID
        """
        try:
            # 生成唯一ID
            trade_date = auction_data.get('trade_date', '')
            ts_code = auction_data.get('ts_code', '')
            auction_id = hashlib.md5(f"{trade_date}_{ts_code}".encode()).hexdigest()

            # 提取字段
            t_date = auction_data.get('t_date', '')
            name = auction_data.get('name', '')
            open_price = auction_data.get('open_price', 0)
            pre_close = auction_data.get('pre_close', 0)
            open_change_pct = auction_data.get('open_change_pct', 0)
            auction_volume = auction_data.get('auction_volume', 0)
            auction_amount = auction_data.get('auction_amount', 0)
            auction_volume_ratio = auction_data.get('auction_volume_ratio', 0)
            auction_turnover_rate = auction_data.get('auction_turnover_rate', 0)
            auction_volume_to_t_volume = auction_data.get('auction_volume_to_t_volume', 0)
            t_day_volume = auction_data.get('t_day_volume', 0)
            auction_score = auction_data.get('auction_score', 0)
            data_source = auction_data.get('data_source', 'unknown')
            final_score = auction_data.get('final_score', 0)
            recommendation = auction_data.get('recommendation', '观望')
            confidence = auction_data.get('confidence', '低')
            position_pct = auction_data.get('position_pct', 0)
            reasons = auction_data.get('reasons', [])
            reasons_json = json.dumps(reasons, ensure_ascii=False)

            # 插入或更新数据
            self.cursor.execute(f'''
            INSERT OR REPLACE INTO {self.table_auction_data}
            (auction_id, trade_date, t_date, ts_code, name, open_price, pre_close,
             open_change_pct, auction_volume, auction_amount, auction_volume_ratio,
             auction_turnover_rate, auction_volume_to_t_volume, t_day_volume,
             auction_score, data_source, final_score, recommendation, confidence,
             position_pct, reasons_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                auction_id, trade_date, t_date, ts_code, name, open_price, pre_close,
                open_change_pct, auction_volume, auction_amount, auction_volume_ratio,
                auction_turnover_rate, auction_volume_to_t_volume, t_day_volume,
                auction_score, data_source, final_score, recommendation, confidence,
                position_pct, reasons_json
            ))

            self.conn.commit()
            logger.info(f"保存竞价数据: {ts_code} ({name}) - 开盘涨幅: {open_change_pct:.2f}%, 竞价评分: {auction_score:.2f}")
            return auction_id

        except Exception as e:
            logger.error(f"保存竞价数据失败: {e}")
            return ""

    def get_auction_data(self, trade_date: str = None, ts_code: str = None) -> pd.DataFrame:
        """
        获取竞价数据

        Args:
            trade_date: 交易日期 (可选)
            ts_code: 股票代码 (可选)

        Returns:
            DataFrame: 竞价数据
        """
        try:
            query = f"SELECT * FROM {self.table_auction_data} WHERE 1=1"
            params = []

            if trade_date:
                query += " AND trade_date = ?"
                params.append(trade_date)
            if ts_code:
                query += " AND ts_code = ?"
                params.append(ts_code)

            query += " ORDER BY final_score DESC"

            df = pd.read_sql_query(query, self.conn, params=params)
            return df
        except Exception as e:
            logger.error(f"获取竞价数据失败: {e}")
            return pd.DataFrame()

    def cleanup_old_data(self):
        """清理旧数据"""
        try:
            retention_config = self.config.get('data_storage', {}).get('retention', {})

            # 清理推荐记录
            rec_retention = retention_config.get('recommendations', 365)
            cutoff_date = (datetime.now() - timedelta(days=rec_retention)).strftime('%Y%m%d')

            self.cursor.execute(
                f"DELETE FROM {self.table_recommendations} WHERE trade_date < ?",
                (cutoff_date,)
            )
            rec_deleted = self.cursor.rowcount

            # 清理交易记录
            trade_retention = retention_config.get('trades', 730)
            cutoff_date = (datetime.now() - timedelta(days=trade_retention)).strftime('%Y%m%d')

            self.cursor.execute(
                f"DELETE FROM {self.table_trades} WHERE trade_date < ?",
                (cutoff_date,)
            )
            trade_deleted = self.cursor.rowcount

            # 清理竞价数据
            auction_retention = retention_config.get('auction_data', 365)
            cutoff_date = (datetime.now() - timedelta(days=auction_retention)).strftime('%Y%m%d')

            self.cursor.execute(
                f"DELETE FROM {self.table_auction_data} WHERE trade_date < ?",
                (cutoff_date,)
            )
            auction_deleted = self.cursor.rowcount

            self.conn.commit()

            logger.info(f"数据清理完成: 删除 {rec_deleted} 条推荐记录, {trade_deleted} 条交易记录, {auction_deleted} 条竞价记录")

        except Exception as e:
            logger.error(f"数据清理失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


# 便捷函数
def get_data_storage(config_path='config.yaml') -> T01DataStorage:
    """获取数据存储实例（单例模式）"""
    if not hasattr(get_data_storage, '_instance'):
        get_data_storage._instance = T01DataStorage(config_path)
    return get_data_storage._instance


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    storage = T01DataStorage()
    
    try:
        # 测试保存推荐记录
        test_recommendation = {
            'trade_date': '20260224',
            't1_date': '20260225',
            'ts_code': '000859.SZ',
            'name': '国风新材',
            'total_score': 151.0,
            't_day_score': 151.0,
            'auction_score': 85.5,
            'auction_data': {
                'open_change_pct': 2.5,
                'data_source': 'realtime'
            }
        }
        
        rec_id = storage.save_recommendation(test_recommendation)
        print(f"✅ 保存推荐记录成功: {rec_id}")
        
        # 测试记录交易
        trade_data = {
            'trade_type': 'buy',
            'trade_date': '20260225',
            'trade_time': '09:30',
            'price': 10.25,
            'quantity': 1000,
            'notes': 'T+1开盘买入'
        }
        
        trade_id = storage.record_trade(rec_id, trade_data)
        print(f"✅ 记录交易成功: {trade_id}")
        
        # 测试获取因子数据
        factors_df = storage.get_factor_data()
        print(f"✅ 获取因子数据成功: {len(factors_df)} 个因子")
        if not factors_df.empty:
            print(factors_df[['factor_name', 'factor_type', 'weight']].head())
        
        # 测试备份
        storage.backup_database()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        storage.close()