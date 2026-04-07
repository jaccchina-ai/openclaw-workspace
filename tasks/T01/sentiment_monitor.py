#!/usr/bin/env python3
"""
情绪指标预警系统 - Market Sentiment Monitor
监控炸板率、连板高度、涨跌家数比等情绪指标，极端行情自动预警
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
import tushare as ts
import json
import os
import sys
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def safe_api_call(func: Callable, *args, max_retries: int = 3, retry_delay: float = 1.0, **kwargs) -> Any:
    """
    安全的API调用包装函数，支持自动重试机制
    
    Args:
        func: 要调用的函数
        *args: 函数的位置参数
        max_retries: 最大重试次数 (默认3次)
        retry_delay: 重试间隔秒数 (默认1秒)
        **kwargs: 函数的关键字参数
        
    Returns:
        函数调用结果
        
    Raises:
        最后一次调用的异常
    """
    last_exception = None
    # 至少尝试一次，即使max_retries=0
    total_attempts = max(1, max_retries)
    
    for attempt in range(1, total_attempts + 1):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            last_exception = e
            if attempt < total_attempts:
                logger.warning(f"API调用失败 (尝试 {attempt}/{total_attempts}): {e}. {retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error(f"API调用失败，已重试{total_attempts}次，放弃: {e}")
    
    # 重试次数用尽，抛出最后一次异常
    raise last_exception


class MarketSentimentMonitor:
    """市场情绪监控器"""
    
    # 情绪指标阈值配置
    DEFAULT_THRESHOLDS = {
        # 炸板率 (开板数/涨停数)
        'explosion_rate': {
            'extreme_high': 0.7,      # 极端高炸板率 (>70%)
            'high': 0.5,              # 高炸板率 (>50%)
            'warning': 0.3,           # 警告阈值 (>30%)
        },
        # 连板高度 (最高连板数)
        'consecutive_limits': {
            'extreme_low': 2,         # 极端低迷 (最高2板)
            'low': 3,                 # 情绪低迷 (最高3板)
            'normal': 5,              # 正常 (最高5板)
        },
        # 涨跌家数比
        'advance_decline_ratio': {
            'extreme_bear': 0.3,      # 极端熊市 (<0.3)
            'bear': 0.5,              # 熊市 (<0.5)
            'bull': 2.0,              # 牛市 (>2.0)
            'extreme_bull': 3.0,      # 极端牛市 (>3.0)
        },
        # 涨停家数
        'limit_up_count': {
            'extreme_low': 20,        # 极端低迷 (<20家)
            'low': 40,                # 低迷 (<40家)
            'normal': 60,             # 正常 (60-100家)
            'high': 100,              # 活跃 (>100家)
        },
        # 跌停家数
        'limit_down_count': {
            'warning': 10,            # 警告 (>10家)
            'danger': 30,             # 危险 (>30家)
            'extreme': 50,            # 极端 (>50家)
        },
        # 昨日涨停今日表现 (溢价率)
        'yesterday_limit_up_premium': {
            'extreme_low': -2.0,      # 极端负溢价 (<-2%)
            'low': 0,                 # 无溢价 (<0%)
            'normal': 2.0,            # 正常溢价 (2%)
            'high': 5.0,              # 高溢价 (>5%)
        },
        # 封板率
        'seal_rate': {
            'extreme_low': 0.5,       # 极端低封板率 (<50%)
            'low': 0.6,               # 低封板率 (<60%)
            'normal': 0.75,           # 正常 (>75%)
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化情绪监控器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.thresholds = self.config.get('sentiment_thresholds', self.DEFAULT_THRESHOLDS)
        
        # 初始化 Tushare
        # 尝试从多个位置获取 token
        self.token = self.config.get('api_key', '')
        if not self.token:
            # 尝试从 api 配置获取
            api_config = self.config.get('api', {})
            self.token = api_config.get('api_key', '')
        if not self.token:
            # 尝试环境变量
            self.token = os.getenv('TUSHARE_TOKEN', '')
        
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            logger.error("Tushare token 未配置")
            self.pro = None
        
        # 预警状态
        self.alert_history = []
        self.last_alert_time = None
        self.alert_cooldown_minutes = self.config.get('alert_cooldown_minutes', 30)
        
        # 仓位建议
        self.position_suggestions = {
            'extreme_bear': {'position': 0.0, 'action': '清仓观望'},
            'bear': {'position': 0.2, 'action': '大幅减仓'},
            'caution': {'position': 0.5, 'action': '谨慎操作'},
            'neutral': {'position': 0.7, 'action': '正常操作'},
            'bull': {'position': 1.0, 'action': '积极操作'},
        }
        
        # 结果缓存机制
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_cache_ttl = 300  # 默认缓存TTL: 5分钟 (300秒)
        
        logger.info("情绪指标预警系统初始化完成")
    
    def _get_cache_key(self, method_name: str, args: tuple = None, kwargs: dict = None) -> str:
        """
        生成缓存键
        
        Args:
            method_name: 方法名称
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            缓存键字符串
        """
        # 将参数转换为字符串并生成哈希
        key_parts = [method_name]
        
        if args:
            key_parts.append(str(args))
        if kwargs:
            # 排序kwargs确保一致性
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(str(sorted_kwargs))
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, key: str) -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果过期或不存在则返回None
        """
        try:
            if key not in self._cache:
                return None
            
            cache_entry = self._cache[key]
            timestamp = cache_entry.get('timestamp', 0)
            ttl = cache_entry.get('ttl', self._default_cache_ttl)
            
            # 检查是否过期
            if time.time() - timestamp > ttl:
                # 删除过期缓存
                del self._cache[key]
                return None
            
            return cache_entry.get('data')
        except Exception as e:
            # 缓存失败时不影响正常功能
            logger.warning(f"获取缓存失败: {e}")
            return None
    
    def _set_cached_result(self, key: str, data: Any, ttl: int = None) -> None:
        """
        设置缓存结果
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 缓存存活时间（秒），默认使用类默认值
        """
        try:
            if ttl is None:
                ttl = self._default_cache_ttl
            
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl
            }
        except Exception as e:
            # 缓存失败时不影响正常功能
            logger.warning(f"设置缓存失败: {e}")
    
    def get_trade_date(self, date: Optional[str] = None) -> str:
        """获取交易日期"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        return date
    
    def _is_trading_day(self, date: str) -> bool:
        """检查是否为交易日"""
        try:
            cal_df = self.pro.trade_cal(exchange='SSE', start_date=date, end_date=date)
            if cal_df is not None and not cal_df.empty:
                return cal_df.iloc[0]['is_open'] == 1
            return False
        except Exception as e:
            logger.error(f"检查交易日失败: {e}")
            return False
    
    def calculate_explosion_rate(self, trade_date: str) -> Dict[str, Any]:
        """
        计算炸板率
        炸板率 = 开板股票数 / 曾涨停股票数
        """
        try:
            # 获取涨停股列表
            limit_up_df = self.pro.limit_list_d(trade_date=trade_date)
            
            if limit_up_df is None or limit_up_df.empty:
                return {'rate': 0, 'total': 0, 'exploded': 0, 'sealed': 0}
            
            # 统计开板和封板
            # 炸板定义: 曾涨停但未封住 (close < high_limit 或 pct_chg < 9.5)
            total_touched = len(limit_up_df)
            
            # 曾涨停但未封住的 (炸板)
            exploded = len(limit_up_df[limit_up_df['pct_chg'] < 9.5])
            
            # 成功封板的
            sealed = total_touched - exploded
            
            rate = exploded / total_touched if total_touched > 0 else 0
            
            return {
                'rate': round(rate, 4),
                'total': total_touched,
                'exploded': exploded,
                'sealed': sealed
            }
        except Exception as e:
            logger.error(f"计算炸板率失败: {e}")
            return {'rate': 0, 'total': 0, 'exploded': 0, 'sealed': 0}
    
    def calculate_consecutive_limits(self, trade_date: str) -> Dict[str, Any]:
        """
        计算连板高度
        返回最高连板数和连板分布
        """
        try:
            # 获取涨停股列表
            limit_up_df = self.pro.limit_list_d(trade_date=trade_date)
            
            if limit_up_df is None or limit_up_df.empty:
                return {'max_consecutive': 0, 'distribution': {}}
            
            # 获取连板天数
            if 'con_times' in limit_up_df.columns:
                max_consecutive = limit_up_df['con_times'].max()
                distribution = limit_up_df['con_times'].value_counts().to_dict()
            else:
                max_consecutive = 1
                distribution = {1: len(limit_up_df)}
            
            return {
                'max_consecutive': int(max_consecutive),
                'distribution': {int(k): int(v) for k, v in distribution.items()}
            }
        except Exception as e:
            logger.error(f"计算连板高度失败: {e}")
            return {'max_consecutive': 0, 'distribution': {}}
    
    def calculate_advance_decline_ratio(self, trade_date: str) -> Dict[str, Any]:
        """
        计算涨跌家数比
        """
        try:
            # 获取当日行情
            df = self.pro.daily(trade_date=trade_date)
            
            if df is None or df.empty:
                return {'ratio': 1.0, 'advance': 0, 'decline': 0, 'flat': 0}
            
            advance = len(df[df['pct_chg'] > 0])
            decline = len(df[df['pct_chg'] < 0])
            flat = len(df[df['pct_chg'] == 0])
            
            ratio = advance / decline if decline > 0 else float('inf')
            
            return {
                'ratio': round(ratio, 2),
                'advance': advance,
                'decline': decline,
                'flat': flat
            }
        except Exception as e:
            logger.error(f"计算涨跌家数比失败: {e}")
            return {'ratio': 1.0, 'advance': 0, 'decline': 0, 'flat': 0}
    
    def calculate_limit_up_down_stats(self, trade_date: str) -> Dict[str, Any]:
        """
        计算涨跌停家数统计
        """
        try:
            # 获取当日行情
            df = self.pro.daily(trade_date=trade_date)
            
            if df is None or df.empty:
                return {'limit_up': 0, 'limit_down': 0, 'strong_up': 0, 'strong_down': 0}
            
            # 涨停 (>9.5% for ST, >9.9% for normal)
            limit_up = len(df[df['pct_chg'] >= 9.5])
            
            # 跌停 (<-9.5% for ST, <-9.9% for normal)
            limit_down = len(df[df['pct_chg'] <= -9.5])
            
            # 大涨 (>5%)
            strong_up = len(df[df['pct_chg'] >= 5])
            
            # 大跌 (<-5%)
            strong_down = len(df[df['pct_chg'] <= -5])
            
            return {
                'limit_up': limit_up,
                'limit_down': limit_down,
                'strong_up': strong_up,
                'strong_down': strong_down
            }
        except Exception as e:
            logger.error(f"计算涨跌停统计失败: {e}")
            return {'limit_up': 0, 'limit_down': 0, 'strong_up': 0, 'strong_down': 0}
    
    def calculate_yesterday_limit_up_premium(self, trade_date: str) -> Dict[str, Any]:
        """
        计算昨日涨停股今日表现 (溢价率)
        """
        try:
            # 获取前一个交易日
            cal_df = self.pro.trade_cal(exchange='SSE', end_date=trade_date, limit=2)
            if cal_df is None or len(cal_df) < 2:
                return {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}
            
            prev_date = cal_df.iloc[1]['cal_date']
            
            # 获取昨日涨停股
            yesterday_limit = self.pro.limit_list_d(trade_date=prev_date)
            if yesterday_limit is None or yesterday_limit.empty:
                return {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}
            
            ts_codes = yesterday_limit['ts_code'].tolist()
            
            # 获取今日行情
            today_df = self.pro.daily(trade_date=trade_date)
            if today_df is None or today_df.empty:
                return {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}
            
            # 筛选昨日涨停股
            matched = today_df[today_df['ts_code'].isin(ts_codes)]
            
            if matched.empty:
                return {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}
            
            # 计算平均开盘和收盘溢价
            avg_open_premium = matched['open'].pct_change().mean() * 100 if len(matched) > 0 else 0
            avg_close_premium = matched['pct_chg'].mean()
            
            return {
                'premium': round(avg_close_premium, 2),
                'avg_open': round(avg_open_premium, 2),
                'avg_close': round(avg_close_premium, 2),
                'count': len(matched)
            }
        except Exception as e:
            logger.error(f"计算昨日涨停溢价失败: {e}")
            return {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}
    
    def calculate_seal_rate(self, trade_date: str) -> Dict[str, Any]:
        """
        计算封板率
        封板率 = 封板数 / 曾涨停数
        """
        explosion_data = self.calculate_explosion_rate(trade_date)
        
        total = explosion_data['total']
        sealed = explosion_data['sealed']
        
        rate = sealed / total if total > 0 else 0
        
        return {
            'rate': round(rate, 4),
            'sealed': sealed,
            'total': total
        }
    
    def _get_default_result(self, indicator_name: str) -> Dict[str, Any]:
        """
        获取指标的默认结果（当计算失败时使用）
        
        Args:
            indicator_name: 指标名称
            
        Returns:
            默认结果字典
        """
        defaults = {
            'explosion_rate': {'rate': 0, 'total': 0, 'exploded': 0, 'sealed': 0},
            'consecutive_limits': {'max_consecutive': 0, 'distribution': {}},
            'advance_decline_ratio': {'ratio': 1.0, 'advance': 0, 'decline': 0, 'flat': 0},
            'limit_up_down_stats': {'limit_up': 0, 'limit_down': 0, 'strong_up': 0, 'strong_down': 0},
            'yesterday_limit_up_premium': {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0},
        }
        return defaults.get(indicator_name, {})
    
    def analyze_sentiment_parallel(self, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """
        并行综合分析市场情绪
        
        使用ThreadPoolExecutor并行计算5个情绪指标，提高性能。
        单个指标计算失败不影响其他指标，失败的指标返回默认值。
        
        Args:
            trade_date: 交易日期 (YYYYMMDD格式)，默认为今天
            
        Returns:
            情绪分析结果字典
        """
        trade_date = self.get_trade_date(trade_date)
        
        if not self._is_trading_day(trade_date):
            logger.info(f"{trade_date} 非交易日，跳过情绪分析")
            return {'is_trading_day': False}
        
        logger.info(f"开始并行分析 {trade_date} 市场情绪...")
        
        # 定义要并行执行的指标计算任务
        indicator_tasks = [
            ('explosion_rate', self.calculate_explosion_rate),
            ('consecutive_limits', self.calculate_consecutive_limits),
            ('advance_decline_ratio', self.calculate_advance_decline_ratio),
            ('limit_up_down_stats', self.calculate_limit_up_down_stats),
            ('yesterday_limit_up_premium', self.calculate_yesterday_limit_up_premium),
        ]
        
        # 存储结果
        results = {}
        
        # 使用ThreadPoolExecutor并行执行
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_indicator = {
                executor.submit(task_func, trade_date): indicator_name
                for indicator_name, task_func in indicator_tasks
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_indicator):
                indicator_name = future_to_indicator[future]
                try:
                    result = future.result()
                    results[indicator_name] = result
                    logger.debug(f"{indicator_name} 计算完成")
                except Exception as e:
                    logger.error(f"{indicator_name} 计算失败: {e}")
                    # 返回默认值
                    results[indicator_name] = self._get_default_result(indicator_name)
        
        # 计算封板率（依赖于炸板率结果）
        explosion_data = results.get('explosion_rate', self._get_default_result('explosion_rate'))
        total = explosion_data.get('total', 0)
        sealed = explosion_data.get('sealed', 0)
        seal_rate = sealed / total if total > 0 else 0
        seal_data = {
            'rate': round(seal_rate, 4),
            'sealed': sealed,
            'total': total
        }
        
        # 提取各指标数据
        explosion_data = results.get('explosion_rate', self._get_default_result('explosion_rate'))
        consecutive_data = results.get('consecutive_limits', self._get_default_result('consecutive_limits'))
        ad_ratio_data = results.get('advance_decline_ratio', self._get_default_result('advance_decline_ratio'))
        limit_stats = results.get('limit_up_down_stats', self._get_default_result('limit_up_down_stats'))
        premium_data = results.get('yesterday_limit_up_premium', self._get_default_result('yesterday_limit_up_premium'))
        
        # 综合评分
        sentiment_score = self._calculate_sentiment_score(
            explosion_data, consecutive_data, ad_ratio_data,
            limit_stats, premium_data, seal_data
        )
        
        # 判断市场状态
        market_status = self._determine_market_status(
            explosion_data, consecutive_data, ad_ratio_data,
            limit_stats, premium_data, seal_data
        )
        
        result = {
            'trade_date': trade_date,
            'is_trading_day': True,
            'sentiment_score': sentiment_score,
            'market_status': market_status,
            'position_suggestion': self.position_suggestions.get(market_status, {'position': 0.5, 'action': '谨慎'}),
            'indicators': {
                'explosion_rate': explosion_data,
                'consecutive_limits': consecutive_data,
                'advance_decline_ratio': ad_ratio_data,
                'limit_stats': limit_stats,
                'yesterday_premium': premium_data,
                'seal_rate': seal_data
            }
        }
        
        logger.info(f"并行情绪分析完成: 评分={sentiment_score}, 状态={market_status}")
        
        return result
    
    def analyze_sentiment(self, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """
        综合分析市场情绪
        
        Returns:
            情绪分析结果字典
        """
        trade_date = self.get_trade_date(trade_date)
        
        # 检查缓存
        cache_key = self._get_cache_key('analyze_sentiment', (trade_date,), {})
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logger.info(f"使用缓存的情绪分析结果: {trade_date}")
            return cached_result
        
        if not self._is_trading_day(trade_date):
            logger.info(f"{trade_date} 非交易日，跳过情绪分析")
            return {'is_trading_day': False}
        
        logger.info(f"开始分析 {trade_date} 市场情绪...")
        
        # 计算各项指标
        explosion_data = self.calculate_explosion_rate(trade_date)
        consecutive_data = self.calculate_consecutive_limits(trade_date)
        ad_ratio_data = self.calculate_advance_decline_ratio(trade_date)
        limit_stats = self.calculate_limit_up_down_stats(trade_date)
        premium_data = self.calculate_yesterday_limit_up_premium(trade_date)
        seal_data = self.calculate_seal_rate(trade_date)
        
        # 综合评分
        sentiment_score = self._calculate_sentiment_score(
            explosion_data, consecutive_data, ad_ratio_data,
            limit_stats, premium_data, seal_data
        )
        
        # 判断市场状态
        market_status = self._determine_market_status(
            explosion_data, consecutive_data, ad_ratio_data,
            limit_stats, premium_data, seal_data
        )
        
        result = {
            'trade_date': trade_date,
            'is_trading_day': True,
            'sentiment_score': sentiment_score,
            'market_status': market_status,
            'position_suggestion': self.position_suggestions.get(market_status, {'position': 0.5, 'action': '谨慎'}),
            'indicators': {
                'explosion_rate': explosion_data,
                'consecutive_limits': consecutive_data,
                'advance_decline_ratio': ad_ratio_data,
                'limit_stats': limit_stats,
                'yesterday_premium': premium_data,
                'seal_rate': seal_data
            }
        }
        
        # 缓存结果
        self._set_cached_result(cache_key, result)
        
        logger.info(f"情绪分析完成: 评分={sentiment_score}, 状态={market_status}")
        
        return result
    
    def _calculate_sentiment_score(self, explosion_data, consecutive_data,
                                    ad_ratio_data, limit_stats, premium_data, seal_data) -> float:
        """计算综合情绪评分 (0-100)"""
        score = 50  # 基础分
        
        # 炸板率评分 (权重: 20%)
        explosion_rate = explosion_data.get('rate', 0)
        if explosion_rate > self.thresholds['explosion_rate']['extreme_high']:
            score -= 20
        elif explosion_rate > self.thresholds['explosion_rate']['high']:
            score -= 10
        elif explosion_rate < self.thresholds['explosion_rate']['warning']:
            score += 10
        
        # 连板高度评分 (权重: 15%)
        max_consecutive = consecutive_data.get('max_consecutive', 0)
        if max_consecutive >= 7:
            score += 15
        elif max_consecutive >= 5:
            score += 10
        elif max_consecutive <= 2:
            score -= 15
        elif max_consecutive <= 3:
            score -= 10
        
        # 涨跌比评分 (权重: 20%)
        ad_ratio = ad_ratio_data.get('ratio', 1)
        if ad_ratio > self.thresholds['advance_decline_ratio']['extreme_bull']:
            score += 20
        elif ad_ratio > self.thresholds['advance_decline_ratio']['bull']:
            score += 10
        elif ad_ratio < self.thresholds['advance_decline_ratio']['extreme_bear']:
            score -= 20
        elif ad_ratio < self.thresholds['advance_decline_ratio']['bear']:
            score -= 10
        
        # 涨停家数评分 (权重: 15%)
        limit_up = limit_stats.get('limit_up', 0)
        if limit_up > self.thresholds['limit_up_count']['high']:
            score += 15
        elif limit_up > self.thresholds['limit_up_count']['normal']:
            score += 10
        elif limit_up < self.thresholds['limit_up_count']['extreme_low']:
            score -= 15
        elif limit_up < self.thresholds['limit_up_count']['low']:
            score -= 10
        
        # 跌停家数评分 (权重: 15%)
        limit_down = limit_stats.get('limit_down', 0)
        if limit_down > self.thresholds['limit_down_count']['extreme']:
            score -= 15
        elif limit_down > self.thresholds['limit_down_count']['danger']:
            score -= 10
        elif limit_down > self.thresholds['limit_down_count']['warning']:
            score -= 5
        
        # 昨日涨停溢价评分 (权重: 10%)
        premium = premium_data.get('premium', 0)
        if premium > self.thresholds['yesterday_limit_up_premium']['high']:
            score += 10
        elif premium > self.thresholds['yesterday_limit_up_premium']['normal']:
            score += 5
        elif premium < self.thresholds['yesterday_limit_up_premium']['extreme_low']:
            score -= 10
        elif premium < self.thresholds['yesterday_limit_up_premium']['low']:
            score -= 5
        
        # 封板率评分 (权重: 5%)
        seal_rate = seal_data.get('rate', 0)
        if seal_rate > self.thresholds['seal_rate']['normal']:
            score += 5
        elif seal_rate < self.thresholds['seal_rate']['extreme_low']:
            score -= 5
        
        return max(0, min(100, score))
    
    def _determine_market_status(self, explosion_data, consecutive_data,
                                  ad_ratio_data, limit_stats, premium_data, seal_data) -> str:
        """判断市场状态"""
        
        # 极端熊市信号
        if (explosion_data['rate'] > self.thresholds['explosion_rate']['extreme_high'] or
            limit_stats['limit_down'] > self.thresholds['limit_down_count']['extreme'] or
            ad_ratio_data['ratio'] < self.thresholds['advance_decline_ratio']['extreme_bear']):
            return 'extreme_bear'
        
        # 熊市信号
        if (explosion_data['rate'] > self.thresholds['explosion_rate']['high'] or
            limit_stats['limit_down'] > self.thresholds['limit_down_count']['danger'] or
            ad_ratio_data['ratio'] < self.thresholds['advance_decline_ratio']['bear'] or
            consecutive_data['max_consecutive'] <= 2):
            return 'bear'
        
        # 牛市信号
        if (consecutive_data['max_consecutive'] >= 6 and
            ad_ratio_data['ratio'] > self.thresholds['advance_decline_ratio']['bull'] and
            limit_stats['limit_up'] > self.thresholds['limit_up_count']['high']):
            return 'bull'
        
        # 谨慎信号
        if (explosion_data['rate'] > self.thresholds['explosion_rate']['warning'] or
            limit_stats['limit_down'] > self.thresholds['limit_down_count']['warning'] or
            consecutive_data['max_consecutive'] <= 3):
            return 'caution'
        
        return 'neutral'
    
    def check_alert(self, sentiment_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查是否需要发送预警
        
        Returns:
            预警信息或None
        """
        if not sentiment_result.get('is_trading_day'):
            return None
        
        # 检查冷却时间
        if self.last_alert_time:
            elapsed = (datetime.now() - self.last_alert_time).total_seconds() / 60
            if elapsed < self.alert_cooldown_minutes:
                return None
        
        market_status = sentiment_result.get('market_status', 'neutral')
        sentiment_score = sentiment_result.get('sentiment_score', 50)
        
        # 判断是否需要预警
        alert_needed = False
        alert_level = 'info'
        alert_message = ''
        
        if market_status == 'extreme_bear':
            alert_needed = True
            alert_level = 'critical'
            alert_message = '⚠️ 极端熊市信号！建议清仓观望'
        elif market_status == 'bear':
            alert_needed = True
            alert_level = 'warning'
            alert_message = '🔴 熊市信号明显，建议大幅减仓'
        elif sentiment_score < 30:
            alert_needed = True
            alert_level = 'warning'
            alert_message = '📉 市场情绪极度低迷，谨慎操作'
        elif sentiment_score > 80:
            alert_needed = True
            alert_level = 'info'
            alert_message = '📈 市场情绪高涨，可积极操作'
        
        if not alert_needed:
            return None
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': alert_level,
            'message': alert_message,
            'sentiment_score': sentiment_score,
            'market_status': market_status,
            'position_suggestion': sentiment_result.get('position_suggestion', {}),
            'indicators': sentiment_result.get('indicators', {})
        }
        
        self.alert_history.append(alert)
        self.last_alert_time = datetime.now()
        
        return alert
    
    def format_report(self, sentiment_result: Dict[str, Any]) -> str:
        """格式化情绪分析报告"""
        if not sentiment_result.get('is_trading_day'):
            return f"📅 {sentiment_result.get('trade_date')} 非交易日"
        
        trade_date = sentiment_result['trade_date']
        score = sentiment_result['sentiment_score']
        status = sentiment_result['market_status']
        suggestion = sentiment_result['position_suggestion']
        indicators = sentiment_result['indicators']
        
        # 状态表情
        status_emoji = {
            'extreme_bear': '🔴🔴🔴',
            'bear': '🔴🔴',
            'caution': '🟡',
            'neutral': '⚪',
            'bull': '🟢🟢'
        }.get(status, '⚪')
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║          📊 市场情绪指标报告 - {trade_date}              ║
╚══════════════════════════════════════════════════════════╝

【综合评分】{score}/100  {status_emoji}
【市场状态】{status}
【操作建议】{suggestion.get('action', '观望')} | 建议仓位: {int(suggestion.get('position', 0) * 100)}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 关键指标:

1️⃣ 炸板率: {indicators['explosion_rate']['rate']*100:.1f}%
   └─ 涨停{indicators['explosion_rate']['total']}家, 炸板{indicators['explosion_rate']['exploded']}家

2️⃣ 连板高度: {indicators['consecutive_limits']['max_consecutive']}板
   └─ 分布: {indicators['consecutive_limits']['distribution']}

3️⃣ 涨跌比: {indicators['advance_decline_ratio']['ratio']:.2f}
   └─ 涨{indicators['advance_decline_ratio']['advance']} / 跌{indicators['advance_decline_ratio']['decline']} / 平{indicators['advance_decline_ratio']['flat']}

4️⃣ 涨跌停: 涨停{indicators['limit_stats']['limit_up']}家 / 跌停{indicators['limit_stats']['limit_down']}家
   └─ 大涨(>5%): {indicators['limit_stats']['strong_up']}家 | 大跌(<-5%): {indicators['limit_stats']['strong_down']}家

5️⃣ 昨日涨停溢价: {indicators['yesterday_premium']['premium']:.2f}%
   └─ 统计{indicators['yesterday_premium']['count']}只股票

6️⃣ 封板率: {indicators['seal_rate']['rate']*100:.1f}%
   └─ 封板{indicators['seal_rate']['sealed']}家 / 曾涨停{indicators['seal_rate']['total']}家

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 系统建议:
• {suggestion.get('action', '观望')}
• 建议仓位控制在 {int(suggestion.get('position', 0) * 100)}%

"""
        return report


def get_sentiment_factor(trade_date: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    获取情绪因子，供选股流程调用
    
    Args:
        trade_date: 交易日期 (YYYYMMDD格式)
        config: 可选配置字典
        
    Returns:
        Dict 包含以下字段:
        - score: 情绪评分 (0-100)
        - status: 市场状态 (extreme_bear/bear/caution/neutral/bull)
        - factor_value: 因子值 (标准化后的情绪值，范围0-1)
        - should_filter: 是否应过滤股票 (极端熊市时为True)
        - reason: 过滤原因说明
        - indicators: 详细指标数据
    """
    # 创建监控器实例
    monitor = MarketSentimentMonitor(config)
    
    # 分析市场情绪
    sentiment_result = monitor.analyze_sentiment(trade_date)
    
    # 非交易日返回默认值
    if not sentiment_result.get('is_trading_day', True):
        return {
            'score': 50,
            'status': 'neutral',
            'factor_value': 0.0,
            'should_filter': False,
            'reason': '非交易日，使用默认中性值',
            'indicators': sentiment_result.get('indicators', {})
        }
    
    # 获取评分和状态
    score = sentiment_result.get('sentiment_score', 50)
    status = sentiment_result.get('market_status', 'neutral')
    indicators = sentiment_result.get('indicators', {})
    
    # 计算因子值 (将0-100评分映射到0-1)
    factor_value = score / 100.0
    
    # 判断是否需要过滤
    # 极端熊市(score<20或status='extreme_bear')时 should_filter=True
    should_filter = score < 20 or status == 'extreme_bear'
    
    # 生成原因说明
    if should_filter:
        if score < 20:
            reason = f'情绪评分极低({score})，建议停止选股'
        else:
            reason = f'极端熊市状态，建议停止选股'
    elif status == 'bear':
        reason = f'熊市状态({score}分)，建议谨慎选股'
    elif status == 'caution':
        reason = f'谨慎状态({score}分)，建议控制仓位'
    elif status == 'bull':
        reason = f'牛市状态({score}分)，可积极选股'
    else:
        reason = f'中性状态({score}分)，正常选股'
    
    return {
        'score': score,
        'status': status,
        'factor_value': round(factor_value, 4),
        'should_filter': should_filter,
        'reason': reason,
        'indicators': indicators
    }


# 独立运行入口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='市场情绪指标监控')
    parser.add_argument('--date', type=str, help='指定日期 (YYYYMMDD)')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--alert', action='store_true', help='检查是否需要预警')
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            import yaml
            config = yaml.safe_load(f)
    
    # 创建监控器
    monitor = MarketSentimentMonitor(config)
    
    # 分析情绪
    result = monitor.analyze_sentiment(args.date)
    
    # 打印报告
    print(monitor.format_report(result))
    
    # 检查预警
    if args.alert:
        alert = monitor.check_alert(result)
        if alert:
            print(f"\n🚨 预警触发: {alert['message']}")
        else:
            print("\n✅ 无预警")
