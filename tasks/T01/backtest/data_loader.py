"""
数据加载模块

负责从各种数据源加载历史行情数据、财务数据和基本面数据
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataLoader:
    """
    数据加载器

    负责加载回测所需的历史数据，包括：
    - 股票历史行情数据（开盘价、收盘价、最高价、最低价、成交量）
    - 涨停股历史数据
    - 竞价数据

    Attributes:
        pro_api: Tushare pro_api实例
        config: 配置字典
        cache: 数据缓存字典
    """

    def __init__(self, pro_api, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据加载器
        
        Args:
            pro_api: Tushare pro_api实例
            config: 配置字典，可选
        """
        self.pro_api = pro_api
        self.config = config or {}
        self.cache = {}
        
        # 获取超时设置
        self.timeout = self.config.get('api', {}).get('timeout', 30)
        
        logger.info("DataLoader初始化完成")

    def load_limit_up_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载指定日期范围内的涨停股数据
        
        使用Tushare的limit_list_d接口加载涨停股数据
        
        Args:
            start_date: 开始日期 (格式: YYYYMMDD)
            end_date: 结束日期 (格式: YYYYMMDD)
            
        Returns:
            DataFrame包含涨停股数据，如果失败返回空DataFrame
        """
        cache_key = f'limit_up_{start_date}_{end_date}'
        
        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"从缓存获取涨停数据: {start_date} - {end_date}")
            return self.cache[cache_key]
        
        try:
            logger.info(f"加载涨停数据: {start_date} - {end_date}")
            
            # 使用limit_list_d接口获取涨停股票
            fields = [
                'ts_code', 'trade_date', 'industry', 'name', 'close', 'pct_chg',
                'amount', 'fd_amount', 'float_mv', 'total_mv', 'turnover_ratio',
                'first_time', 'last_time', 'open_times', 'up_stat', 'limit_times'
            ]
            
            all_data = []
            
            # 如果是单日查询
            if start_date == end_date:
                df = self.pro_api.limit_list_d(
                    trade_date=start_date,
                    limit_type='U',  # 涨停
                    fields=','.join(fields)
                )
                if not df.empty:
                    all_data.append(df)
            else:
                # 多日查询：获取交易日历，然后逐个日期查询
                try:
                    # 获取日期范围内的交易日
                    cal_df = self.pro_api.trade_cal(
                        exchange='SSE',
                        start_date=start_date,
                        end_date=end_date,
                        is_open='1'
                    )
                    
                    if not cal_df.empty:
                        trade_dates = cal_df['cal_date'].tolist()
                        
                        for trade_date in trade_dates:
                            try:
                                df = self.pro_api.limit_list_d(
                                    trade_date=trade_date,
                                    limit_type='U',
                                    fields=','.join(fields)
                                )
                                if not df.empty:
                                    all_data.append(df)
                            except Exception as e:
                                logger.warning(f"获取日期 {trade_date} 涨停数据失败: {e}")
                                continue
                except Exception as e:
                    logger.error(f"获取交易日历失败: {e}")
                    # 降级为单日查询
                    df = self.pro_api.limit_list_d(
                        trade_date=end_date,
                        limit_type='U',
                        fields=','.join(fields)
                    )
                    if not df.empty:
                        all_data.append(df)
            
            # 合并数据
            if all_data:
                result = pd.concat(all_data, ignore_index=True)
            else:
                result = pd.DataFrame()
            
            # 存入缓存
            self.cache[cache_key] = result
            
            logger.info(f"涨停数据加载完成: {len(result)} 条记录")
            return result
            
        except Exception as e:
            logger.error(f"加载涨停数据失败: {e}")
            return pd.DataFrame()

    def load_daily_price(self, ts_code: str, trade_date: str) -> Dict[str, Any]:
        """
        加载指定股票的日线数据
        
        使用Tushare的daily接口加载日线数据
        
        Args:
            ts_code: 股票代码 (格式: 000001.SZ)
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            包含开盘价、收盘价、最高价、最低价、成交量的字典
            如果失败返回空字典
        """
        cache_key = f'daily_{ts_code}_{trade_date}'
        
        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"从缓存获取日线数据: {ts_code} {trade_date}")
            return self.cache[cache_key]
        
        try:
            logger.debug(f"加载日线数据: {ts_code} {trade_date}")
            
            # 使用daily接口获取日线数据
            df = self.pro_api.daily(
                ts_code=ts_code,
                trade_date=trade_date,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
            
            if df.empty:
                logger.warning(f"未找到日线数据: {ts_code} {trade_date}")
                return {}
            
            # 转换为字典
            row = df.iloc[0]
            result = {
                'ts_code': row.get('ts_code', ts_code),
                'trade_date': row.get('trade_date', trade_date),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'volume': int(row.get('vol', 0)),
                'amount': float(row.get('amount', 0))
            }
            
            # 存入缓存
            self.cache[cache_key] = result
            
            logger.debug(f"日线数据加载完成: {ts_code} {trade_date}")
            return result
            
        except Exception as e:
            logger.error(f"加载日线数据失败: {ts_code} {trade_date} - {e}")
            return {}

    def load_auction_data(self, ts_code: str, trade_date: str) -> Dict[str, Any]:
        """
        加载历史竞价数据
        
        使用Tushare的stk_auction_o接口加载历史竞价数据
        
        Args:
            ts_code: 股票代码 (格式: 000001.SZ)
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            包含竞价数据的字典，如果失败返回空字典
        """
        cache_key = f'auction_{ts_code}_{trade_date}'
        
        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"从缓存获取竞价数据: {ts_code} {trade_date}")
            return self.cache[cache_key]
        
        try:
            logger.debug(f"加载竞价数据: {ts_code} {trade_date}")
            
            # 使用stk_auction_o接口获取历史竞价数据
            df = self.pro_api.stk_auction_o(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='ts_code,trade_date,close,vol,amount,vwap'
            )
            
            if df.empty:
                logger.warning(f"未找到竞价数据: {ts_code} {trade_date}")
                return {}
            
            # 转换为字典
            row = df.iloc[0]
            result = {
                'ts_code': row.get('ts_code', ts_code),
                'trade_date': row.get('trade_date', trade_date),
                'open_price': float(row.get('close', 0)),  # close字段是开盘价
                'volume': int(row.get('vol', 0)),
                'amount': float(row.get('amount', 0)),
                'vwap': float(row.get('vwap', 0))
            }
            
            # 存入缓存
            self.cache[cache_key] = result
            
            logger.debug(f"竞价数据加载完成: {ts_code} {trade_date}")
            return result
            
        except Exception as e:
            logger.error(f"加载竞价数据失败: {ts_code} {trade_date} - {e}")
            return {}

    def clear_cache(self):
        """
        清除数据缓存
        
        清除所有已缓存的数据，释放内存
        """
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"缓存已清除: {cache_size} 条记录")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计信息的字典
        """
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }

    def load_multiple_daily_prices(self, ts_codes: list, trade_date: str) -> Dict[str, Dict[str, Any]]:
        """
        批量加载多只股票日线数据
        
        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期
            
        Returns:
            以股票代码为键的数据字典
        """
        results = {}
        
        for ts_code in ts_codes:
            data = self.load_daily_price(ts_code, trade_date)
            if data:
                results[ts_code] = data
        
        return results

    def load_multiple_auction_data(self, ts_codes: list, trade_date: str) -> Dict[str, Dict[str, Any]]:
        """
        批量加载多只股票竞价数据
        
        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期
            
        Returns:
            以股票代码为键的数据字典
        """
        results = {}
        
        for ts_code in ts_codes:
            data = self.load_auction_data(ts_code, trade_date)
            if data:
                results[ts_code] = data
        
        return results
