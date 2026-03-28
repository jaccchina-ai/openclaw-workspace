#!/usr/bin/env python3
"""
T01深度因子挖掘模块 (factor_mining.py)
实现50+个技术指标、基本面、资金流和情绪因子
支持因子相关性分析、IC值有效性筛选和PCA正交化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
import tushare as ts
from dataclasses import dataclass, field
from enum import Enum
import warnings
import os
import yaml
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class FactorCategory(Enum):
    """因子类别枚举"""
    TECHNICAL = "technical"          # 技术指标
    FUNDAMENTAL = "fundamental"      # 基本面
    MONEY_FLOW = "money_flow"        # 资金流
    SENTIMENT = "sentiment"          # 情绪
    CUSTOM = "custom"                # 自定义


@dataclass
class Factor:
    """因子数据类"""
    name: str                        # 因子名称
    code: str                        # 因子代码
    category: FactorCategory         # 因子类别
    description: str                 # 因子描述
    formula: str                     # 计算公式
    ic_value: Optional[float] = None # IC值
    correlation: Dict[str, float] = field(default_factory=dict)  # 与其他因子的相关性
    is_valid: bool = True            # 是否有效
    weight: float = 1.0              # 权重


class FactorMiner:
    """
    深度因子挖掘器
    负责挖掘、计算、分析和管理50+个因子
    """
    
    def __init__(self, tushare_token: str, config: Optional[Dict] = None):
        """
        初始化因子挖掘器
        
        Args:
            tushare_token: Tushare Pro API Token
            config: 配置字典
        """
        self.config = config or {}
        self.token = tushare_token
        
        # 初始化Tushare
        ts.set_token(tushare_token)
        self.pro = ts.pro_api()
        
        # 因子库
        self.factors: Dict[str, Factor] = {}
        self.factor_data: pd.DataFrame = pd.DataFrame()
        
        # 配置参数
        self.correlation_threshold = self.config.get('correlation_threshold', 0.8)
        self.ic_threshold = self.config.get('ic_threshold', 0.03)
        self.min_periods = self.config.get('min_periods', 20)
        
        # 初始化因子定义
        self._init_factor_definitions()
        
        logger.info(f"因子挖掘器初始化完成，已定义 {len(self.factors)} 个因子")
    
    def _init_factor_definitions(self):
        """初始化因子定义库（50+因子）"""
        
        # ==================== 技术指标因子 (20个) ====================
        technical_factors = [
            # MACD相关
            Factor("MACD_DIF", "macd_dif", FactorCategory.TECHNICAL, 
                   "MACD快线", "EMA12 - EMA26"),
            Factor("MACD_DEA", "macd_dea", FactorCategory.TECHNICAL,
                   "MACD慢线", "EMA(DIF, 9)"),
            Factor("MACD_HIST", "macd_hist", FactorCategory.TECHNICAL,
                   "MACD柱状图", "DIF - DEA"),
            Factor("MACD_GOLDEN_CROSS", "macd_golden", FactorCategory.TECHNICAL,
                   "MACD金叉", "DIF上穿DEA"),
            
            # KDJ相关
            Factor("KDJ_K", "kdj_k", FactorCategory.TECHNICAL,
                   "KDJ指标K值", "RSV的3日EMA"),
            Factor("KDJ_D", "kdj_d", FactorCategory.TECHNICAL,
                   "KDJ指标D值", "K的3日EMA"),
            Factor("KDJ_J", "kdj_j", FactorCategory.TECHNICAL,
                   "KDJ指标J值", "3K - 2D"),
            Factor("KDJ_OVERBOUGHT", "kdj_overbought", FactorCategory.TECHNICAL,
                   "KDJ超买", "J > 80"),
            Factor("KDJ_OVERSOLD", "kdj_oversold", FactorCategory.TECHNICAL,
                   "KDJ超卖", "J < 20"),
            
            # RSI相关
            Factor("RSI_6", "rsi_6", FactorCategory.TECHNICAL,
                   "6日RSI", "6日相对强弱指标"),
            Factor("RSI_12", "rsi_12", FactorCategory.TECHNICAL,
                   "12日RSI", "12日相对强弱指标"),
            Factor("RSI_24", "rsi_24", FactorCategory.TECHNICAL,
                   "24日RSI", "24日相对强弱指标"),
            Factor("RSI_DIVERGENCE", "rsi_divergence", FactorCategory.TECHNICAL,
                   "RSI背离", "价格与RSI背离"),
            
            # 布林带
            Factor("BB_UPPER", "bb_upper", FactorCategory.TECHNICAL,
                   "布林带上轨", "MA20 + 2*STD20"),
            Factor("BB_MIDDLE", "bb_middle", FactorCategory.TECHNICAL,
                   "布林带中轨", "MA20"),
            Factor("BB_LOWER", "bb_lower", FactorCategory.TECHNICAL,
                   "布林带下轨", "MA20 - 2*STD20"),
            Factor("BB_WIDTH", "bb_width", FactorCategory.TECHNICAL,
                   "布林带宽度", "(上轨-下轨)/中轨"),
            Factor("BB_POSITION", "bb_position", FactorCategory.TECHNICAL,
                   "布林带位置", "(收盘价-下轨)/(上轨-下轨)"),
            
            # 均线排列
            Factor("MA_ALIGNMENT", "ma_alignment", FactorCategory.TECHNICAL,
                   "均线多头排列", "MA5 > MA10 > MA20 > MA60"),
            Factor("MA_GOLDEN_CROSS", "ma_golden", FactorCategory.TECHNICAL,
                   "均线金叉", "短期均线上穿长期均线"),
            Factor("MA_DISTANCE", "ma_distance", FactorCategory.TECHNICAL,
                   "均线乖离率", "(收盘价-MA20)/MA20"),
        ]
        
        # ==================== 基本面因子 (15个) ====================
        fundamental_factors = [
            Factor("PE_TTM", "pe_ttm", FactorCategory.FUNDAMENTAL,
                   "市盈率TTM", "总市值/过去12个月净利润"),
            Factor("PB", "pb", FactorCategory.FUNDAMENTAL,
                   "市净率", "总市值/净资产"),
            Factor("PS_TTM", "ps_ttm", FactorCategory.FUNDAMENTAL,
                   "市销率TTM", "总市值/过去12个月营业收入"),
            Factor("PCF", "pcf", FactorCategory.FUNDAMENTAL,
                   "市现率", "总市值/经营现金流"),
            
            Factor("ROE", "roe", FactorCategory.FUNDAMENTAL,
                   "净资产收益率", "净利润/净资产"),
            Factor("ROA", "roa", FactorCategory.FUNDAMENTAL,
                   "总资产收益率", "净利润/总资产"),
            Factor("GROSS_MARGIN", "gross_margin", FactorCategory.FUNDAMENTAL,
                   "毛利率", "(营业收入-营业成本)/营业收入"),
            Factor("NET_MARGIN", "net_margin", FactorCategory.FUNDAMENTAL,
                   "净利率", "净利润/营业收入"),
            
            Factor("REVENUE_GROWTH", "revenue_growth", FactorCategory.FUNDAMENTAL,
                   "营收增长率", "(本期营收-上期营收)/上期营收"),
            Factor("PROFIT_GROWTH", "profit_growth", FactorCategory.FUNDAMENTAL,
                   "利润增长率", "(本期利润-上期利润)/上期利润"),
            Factor("EBITDA_GROWTH", "ebitda_growth", FactorCategory.FUNDAMENTAL,
                   "EBITDA增长率", "EBITDA同比增长"),
            
            Factor("DEBT_RATIO", "debt_ratio", FactorCategory.FUNDAMENTAL,
                   "资产负债率", "总负债/总资产"),
            Factor("CURRENT_RATIO", "current_ratio", FactorCategory.FUNDAMENTAL,
                   "流动比率", "流动资产/流动负债"),
            Factor("QUICK_RATIO", "quick_ratio", FactorCategory.FUNDAMENTAL,
                   "速动比率", "(流动资产-存货)/流动负债"),
            Factor("INTEREST_COVERAGE", "interest_coverage", FactorCategory.FUNDAMENTAL,
                   "利息保障倍数", "息税前利润/利息费用"),
        ]
        
        # ==================== 资金流因子 (10个) ====================
        money_flow_factors = [
            Factor("MAIN_NET_INFLOW", "main_net_inflow", FactorCategory.MONEY_FLOW,
                   "主力净流入", "大单买入-大单卖出"),
            Factor("RETAIL_NET_INFLOW", "retail_net_inflow", FactorCategory.MONEY_FLOW,
                   "散户净流入", "小单买入-小单卖出"),
            Factor("LARGE_ORDER_RATIO", "large_order_ratio", FactorCategory.MONEY_FLOW,
                   "大单占比", "大单成交额/总成交额"),
            Factor("MAIN_NET_RATIO", "main_net_ratio", FactorCategory.MONEY_FLOW,
                   "主力净流入占比", "主力净流入/成交额"),
            
            Factor("INFLOW_5D", "inflow_5d", FactorCategory.MONEY_FLOW,
                   "5日净流入", "近5日主力净流入"),
            Factor("INFLOW_10D", "inflow_10d", FactorCategory.MONEY_FLOW,
                   "10日净流入", "近10日主力净流入"),
            Factor("INFLOW_20D", "inflow_20d", FactorCategory.MONEY_FLOW,
                   "20日净流入", "近20日主力净流入"),
            
            Factor("NET_INFLOW_MA5", "net_inflow_ma5", FactorCategory.MONEY_FLOW,
                   "净流入5日均线", "MA(净流入, 5)"),
            Factor("NET_INFLOW_TREND", "net_inflow_trend", FactorCategory.MONEY_FLOW,
                   "净流入趋势", "净流入斜率"),
            Factor("BUY_SELL_RATIO", "buy_sell_ratio", FactorCategory.MONEY_FLOW,
                   "买卖比", "买入金额/卖出金额"),
        ]
        
        # ==================== 情绪因子 (10个) ====================
        sentiment_factors = [
            Factor("LIMIT_UP_SEAL_RATIO", "limit_up_seal_ratio", FactorCategory.SENTIMENT,
                   "涨停封单比", "封单金额/流通市值"),
            Factor("TURNOVER_CHANGE", "turnover_change", FactorCategory.SENTIMENT,
                   "换手率变化", "当日换手率/20日均换手率"),
            Factor("VOLUME_RATIO", "volume_ratio", FactorCategory.SENTIMENT,
                   "量比", "当日成交量/5日均成交量"),
            Factor("AMPLITUDE", "amplitude", FactorCategory.SENTIMENT,
                   "振幅", "(最高价-最低价)/昨收"),
            
            Factor("LIMIT_UP_TIME", "limit_up_time", FactorCategory.SENTIMENT,
                   "涨停时间", "首次涨停时间（分钟）"),
            Factor("BREAK_COUNT", "break_count", FactorCategory.SENTIMENT,
                   "涨停打开次数", "当日涨停被打开次数"),
            Factor("CONTINUOUS_LIMIT", "continuous_limit", FactorCategory.SENTIMENT,
                   "连续涨停天数", "连续涨停天数"),
            
            Factor("NEWS_SENTIMENT", "news_sentiment", FactorCategory.SENTIMENT,
                   "新闻情绪", "新闻情感分析得分"),
            Factor("HOT_RANK", "hot_rank", FactorCategory.SENTIMENT,
                   "热度排名", "市场热度排名"),
            Factor("ATTENTION_INDEX", "attention_index", FactorCategory.SENTIMENT,
                   "关注度指数", "综合关注度指标"),
        ]
        
        # 注册所有因子
        all_factors = technical_factors + fundamental_factors + money_flow_factors + sentiment_factors
        for factor in all_factors:
            self.factors[factor.code] = factor
        
        logger.info(f"已定义 {len(technical_factors)} 个技术指标因子")
        logger.info(f"已定义 {len(fundamental_factors)} 个基本面因子")
        logger.info(f"已定义 {len(money_flow_factors)} 个资金流因子")
        logger.info(f"已定义 {len(sentiment_factors)} 个情绪因子")
    
    # ==================== 技术指标计算 ====================
    
    def _calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均"""
        return data.ewm(span=period, adjust=False).mean()
    
    def _calculate_macd(self, close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = self._calculate_ema(close, fast)
        ema_slow = self._calculate_ema(close, slow)
        dif = ema_fast - ema_slow
        dea = self._calculate_ema(dif, signal)
        hist = dif - dea
        return dif, dea, hist
    
    def _calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ指标"""
        lowest_low = low.rolling(window=n, min_periods=1).min()
        highest_high = high.rolling(window=n, min_periods=1).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)
        
        k = pd.Series(index=close.index, dtype=float)
        d = pd.Series(index=close.index, dtype=float)
        
        k.iloc[0] = 50
        d.iloc[0] = 50
        
        for i in range(1, len(close)):
            k.iloc[i] = 2/3 * k.iloc[i-1] + 1/3 * rsv.iloc[i]
            d.iloc[i] = 2/3 * d.iloc[i-1] + 1/3 * k.iloc[i]
        
        j = 3 * k - 2 * d
        return k, d, j
    
    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger(self, close: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = close.rolling(window=period, min_periods=1).mean()
        std = close.rolling(window=period, min_periods=1).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower
    
    def _calculate_ma(self, close: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均"""
        return close.rolling(window=period, min_periods=1).mean()
    
    # ==================== 数据获取 ====================
    
    def get_stock_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame包含日线数据
        """
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
                df.reset_index(drop=True, inplace=True)
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    def get_stock_money_flow(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票资金流数据"""
        try:
            df = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
            return df
        except Exception as e:
            logger.error(f"获取资金流数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    def get_stock_fundamental(self, ts_code: str, trade_date: str) -> Dict[str, float]:
        """获取股票基本面数据"""
        try:
            # 获取最新财务指标
            df = self.pro.fina_indicator(ts_code=ts_code, limit=4)
            if df is None or df.empty:
                return {}
            
            df = df.sort_values('end_date', ascending=False)
            latest = df.iloc[0]
            
            # 获取每日指标
            daily_df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            daily_basic = daily_df.iloc[0] if daily_df is not None and not daily_df.empty else {}
            
            result = {
                'pe_ttm': daily_basic.get('pe_ttm', np.nan) if isinstance(daily_basic, pd.Series) else np.nan,
                'pb': daily_basic.get('pb', np.nan) if isinstance(daily_basic, pd.Series) else np.nan,
                'ps_ttm': daily_basic.get('ps_ttm', np.nan) if isinstance(daily_basic, pd.Series) else np.nan,
                'roe': latest.get('roe', np.nan),
                'roa': latest.get('roa', np.nan),
                'grossprofit_margin': latest.get('grossprofit_margin', np.nan),
                'netprofit_margin': latest.get('netprofit_margin', np.nan),
                'debt_to_assets': latest.get('debt_to_assets', np.nan),
                'current_ratio': latest.get('current_ratio', np.nan),
                'quick_ratio': latest.get('quick_ratio', np.nan),
                'tr_yoy': latest.get('tr_yoy', np.nan),  # 营收增长率
                'op_yoy': latest.get('op_yoy', np.nan),  # 营业利润增长率
            }
            return result
        except Exception as e:
            logger.error(f"获取基本面数据失败 {ts_code}: {e}")
            return {}
    
    def get_limit_up_data(self, trade_date: str) -> pd.DataFrame:
        """获取涨停股票数据"""
        try:
            df = self.pro.limit_list_d(trade_date=trade_date)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"获取涨停数据失败 {trade_date}: {e}")
            return pd.DataFrame()
    
    # ==================== 因子计算 ====================
    
    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标因子
        
        Args:
            df: 包含open, high, low, close, vol的DataFrame
            
        Returns:
            添加了技术指标因子的DataFrame
        """
        if df.empty or len(df) < self.min_periods:
            return df
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        # MACD
        df['macd_dif'], df['macd_dea'], df['macd_hist'] = self._calculate_macd(close)
        df['macd_golden'] = ((df['macd_dif'] > df['macd_dea']) & 
                             (df['macd_dif'].shift(1) <= df['macd_dea'].shift(1))).astype(int)
        
        # KDJ
        df['kdj_k'], df['kdj_d'], df['kdj_j'] = self._calculate_kdj(high, low, close)
        df['kdj_overbought'] = (df['kdj_j'] > 80).astype(int)
        df['kdj_oversold'] = (df['kdj_j'] < 20).astype(int)
        
        # RSI
        df['rsi_6'] = self._calculate_rsi(close, 6)
        df['rsi_12'] = self._calculate_rsi(close, 12)
        df['rsi_24'] = self._calculate_rsi(close, 24)
        
        # 布林带
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger(close)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 均线
        df['ma_5'] = self._calculate_ma(close, 5)
        df['ma_10'] = self._calculate_ma(close, 10)
        df['ma_20'] = self._calculate_ma(close, 20)
        df['ma_60'] = self._calculate_ma(close, 60)
        
        df['ma_alignment'] = ((df['ma_5'] > df['ma_10']) & 
                              (df['ma_10'] > df['ma_20']) & 
                              (df['ma_20'] > df['ma_60'])).astype(int)
        
        df['ma_golden'] = ((df['ma_5'] > df['ma_10']) & 
                           (df['ma_5'].shift(1) <= df['ma_10'].shift(1))).astype(int)
        
        df['ma_distance'] = (close - df['ma_20']) / df['ma_20']
        
        return df
    
    def calculate_fundamental_factors(self, ts_code: str, trade_date: str) -> Dict[str, float]:
        """计算基本面因子"""
        return self.get_stock_fundamental(ts_code, trade_date)
    
    def calculate_money_flow_factors(self, df: pd.DataFrame, money_flow_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算资金流因子
        
        Args:
            df: 价格数据
            money_flow_df: 资金流数据
            
        Returns:
            添加了资金流因子的DataFrame
        """
        if money_flow_df.empty:
            return df
        
        # 合并数据
        merged = df.merge(money_flow_df, on='trade_date', how='left', suffixes=('', '_mf'))
        
        # 当日资金流指标
        if 'buy_elg_amount' in merged.columns:
            merged['main_net_inflow'] = merged.get('buy_elg_amount', 0) - merged.get('sell_elg_amount', 0)
            merged['retail_net_inflow'] = merged.get('buy_sm_amount', 0) - merged.get('sell_sm_amount', 0)
            merged['large_order_ratio'] = (merged.get('buy_elg_amount', 0) + merged.get('buy_lg_amount', 0)) / merged.get('amount', 1)
            merged['main_net_ratio'] = merged['main_net_inflow'] / merged.get('amount', 1)
        
        # 多日累计
        merged['inflow_5d'] = merged['main_net_inflow'].rolling(5, min_periods=1).sum()
        merged['inflow_10d'] = merged['main_net_inflow'].rolling(10, min_periods=1).sum()
        merged['inflow_20d'] = merged['main_net_inflow'].rolling(20, min_periods=1).sum()
        
        # 均线和趋势
        merged['net_inflow_ma5'] = merged['main_net_inflow'].rolling(5, min_periods=1).mean()
        
        # 净流入趋势（简单线性回归斜率）
        def linear_slope(x):
            if len(x) < 2:
                return 0
            x_vals = np.arange(len(x))
            return np.polyfit(x_vals, x, 1)[0]
        
        merged['net_inflow_trend'] = merged['main_net_inflow'].rolling(10, min_periods=2).apply(linear_slope, raw=True)
        
        # 买卖比
        if 'buy_sm_amount' in merged.columns and 'sell_sm_amount' in merged.columns:
            total_buy = merged.get('buy_sm_amount', 0) + merged.get('buy_md_amount', 0) + merged.get('buy_lg_amount', 0) + merged.get('buy_elg_amount', 0)
            total_sell = merged.get('sell_sm_amount', 0) + merged.get('sell_md_amount', 0) + merged.get('sell_lg_amount', 0) + merged.get('sell_elg_amount', 0)
            merged['buy_sell_ratio'] = total_buy / total_sell.replace(0, np.nan)
        
        return merged
    
    def calculate_sentiment_factors(self, df: pd.DataFrame, limit_up_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        计算情绪因子
        
        Args:
            df: 价格数据
            limit_up_df: 涨停数据
            
        Returns:
            添加了情绪因子的DataFrame
        """
        if df.empty:
            return df
        
        # 换手率变化
        df['turnover_20ma'] = df['turnover_rate'].rolling(20, min_periods=1).mean() if 'turnover_rate' in df.columns else 0
        df['turnover_change'] = df['turnover_rate'] / df['turnover_20ma'] if 'turnover_rate' in df.columns else 1
        
        # 量比
        df['vol_5ma'] = df['vol'].rolling(5, min_periods=1).mean()
        df['volume_ratio'] = df['vol'] / df['vol_5ma']
        
        # 振幅
        df['amplitude'] = (df['high'] - df['low']) / df['pre_close']
        
        # 涨停相关
        if limit_up_df is not None and not limit_up_df.empty:
            df = df.merge(limit_up_df[['ts_code', 'trade_date', 'fd_amount', 'first_time', 'last_time']], 
                         on=['ts_code', 'trade_date'], how='left')
            
            if 'fd_amount' in df.columns and 'circ_mv' in df.columns:
                df['limit_up_seal_ratio'] = df['fd_amount'] / df['circ_mv']
            
            if 'first_time' in df.columns:
                df['limit_up_time'] = df['first_time'].apply(lambda x: int(x[:2]) * 60 + int(x[2:]) if pd.notna(x) and len(str(x)) >= 4 else 999)
        
        return df
    
    def mine_factors_for_stock(self, ts_code: str, trade_date: str, lookback_days: int = 60) -> Dict[str, float]:
        """
        为单只股票挖掘所有因子
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            lookback_days: 回溯天数
            
        Returns:
            因子值字典
        """
        end_date = trade_date
        start_date = (datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=lookback_days)).strftime('%Y%m%d')
        
        # 获取数据
        daily_df = self.get_stock_daily_data(ts_code, start_date, end_date)
        if daily_df.empty:
            return {}
        
        money_flow_df = self.get_stock_money_flow(ts_code, start_date, end_date)
        fundamental_dict = self.calculate_fundamental_factors(ts_code, trade_date)
        
        # 计算因子
        daily_df = self.calculate_technical_factors(daily_df)
        daily_df = self.calculate_money_flow_factors(daily_df, money_flow_df)
        
        # 获取最新值
        latest = daily_df.iloc[-1] if not daily_df.empty else {}
        
        # 构建因子结果
        factors = {}
        
        # 技术指标
        tech_cols = ['macd_dif', 'macd_dea', 'macd_hist', 'macd_golden',
                     'kdj_k', 'kdj_d', 'kdj_j', 'kdj_overbought', 'kdj_oversold',
                     'rsi_6', 'rsi_12', 'rsi_24',
                     'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
                     'ma_alignment', 'ma_golden', 'ma_distance']
        for col in tech_cols:
            if col in latest:
                factors[col] = latest[col]
        
        # 资金流
        flow_cols = ['main_net_inflow', 'retail_net_inflow', 'large_order_ratio', 'main_net_ratio',
                     'inflow_5d', 'inflow_10d', 'inflow_20d', 'net_inflow_ma5', 'net_inflow_trend', 'buy_sell_ratio']
        for col in flow_cols:
            if col in latest:
                factors[col] = latest[col]
        
        # 情绪
        sentiment_cols = ['turnover_change', 'volume_ratio', 'amplitude', 'limit_up_seal_ratio', 'limit_up_time']
        for col in sentiment_cols:
            if col in latest:
                factors[col] = latest[col]
        
        # 基本面
        factors.update(fundamental_dict)
        
        return factors
    
    def mine_factors_for_date(self, trade_date: str, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        为指定日期的所有股票挖掘因子
        
        Args:
            trade_date: 交易日期
            sample_size: 抽样数量（None表示全部）
            
        Returns:
            因子DataFrame
        """
        # 获取涨停股票作为样本
        limit_up_df = self.get_limit_up_data(trade_date)
        
        if limit_up_df.empty:
            logger.warning(f"{trade_date} 无涨停数据")
            return pd.DataFrame()
        
        stock_list = limit_up_df['ts_code'].tolist()
        if sample_size and len(stock_list) > sample_size:
            stock_list = stock_list[:sample_size]
        
        logger.info(f"开始为 {len(stock_list)} 只股票挖掘因子")
        
        all_factors = []
        for i, ts_code in enumerate(stock_list):
            try:
                factors = self.mine_factors_for_stock(ts_code, trade_date)
                if factors:
                    factors['ts_code'] = ts_code
                    factors['trade_date'] = trade_date
                    all_factors.append(factors)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"已处理 {i+1}/{len(stock_list)} 只股票")
                    
            except Exception as e:
                logger.error(f"处理 {ts_code} 失败: {e}")
                continue
        
        if all_factors:
            result_df = pd.DataFrame(all_factors)
            self.factor_data = result_df
            logger.info(f"成功挖掘 {len(result_df)} 只股票的因子数据")
            return result_df
        
        return pd.DataFrame()
    
    # ==================== 因子分析 ====================
    
    def calculate_ic(self, factor_values: pd.Series, forward_returns: pd.Series, method: str = 'spearman') -> float:
        """
        计算因子IC值（信息系数）
        
        Args:
            factor_values: 因子值序列
            forward_returns: 未来收益序列
            method: 相关系数方法 ('spearman' 或 'pearson')
            
        Returns:
            IC值
        """
        try:
            # 去除NaN
            mask = factor_values.notna() & forward_returns.notna()
            f = factor_values[mask]
            r = forward_returns[mask]
            
            if len(f) < 10:
                return np.nan
            
            if method == 'spearman':
                return f.corr(r, method='spearman')
            else:
                return f.corr(r, method='pearson')
        except Exception as e:
            logger.error(f"计算IC失败: {e}")
            return np.nan
    
    def analyze_factor_ic(self, factor_df: pd.DataFrame, forward_period: int = 5) -> Dict[str, float]:
        """
        分析所有因子的IC值
        
        Args:
            factor_df: 因子DataFrame（需要包含close和trade_date）
            forward_period: 前瞻期（天）
            
        Returns:
            IC值字典
        """
        if factor_df.empty:
            return {}
        
        # 需要计算未来收益
        if 'close' not in factor_df.columns or 'ts_code' not in factor_df.columns:
            logger.warning("缺少计算收益所需的列")
            return {}
        
        # 计算未来收益
        factor_df = factor_df.sort_values(['ts_code', 'trade_date'])
        factor_df['forward_return'] = factor_df.groupby('ts_code')['close'].pct_change(forward_period).shift(-forward_period)
        
        # 获取因子列（排除元数据列）
        exclude_cols = ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'amount', 'forward_return']
        factor_cols = [col for col in factor_df.columns if col not in exclude_cols]
        
        ic_results = {}
        for col in factor_cols:
            try:
                ic = self.calculate_ic(factor_df[col], factor_df['forward_return'])
                ic_results[col] = ic
                
                # 更新因子对象的IC值
                if col in self.factors:
                    self.factors[col].ic_value = ic
                    self.factors[col].is_valid = abs(ic) >= self.ic_threshold if not np.isnan(ic) else False
            except Exception as e:
                logger.error(f"计算因子 {col} IC失败: {e}")
                ic_results[col] = np.nan
        
        # 按IC绝对值排序
        sorted_ic = {k: v for k, v in sorted(ic_results.items(), 
                                              key=lambda x: abs(x[1]) if not np.isnan(x[1]) else 0, 
                                              reverse=True)}
        
        logger.info(f"IC分析完成，有效因子(>|{self.ic_threshold}|): {sum(1 for v in sorted_ic.values() if abs(v) >= self.ic_threshold and not np.isnan(v))}/{len(sorted_ic)}")
        
        return sorted_ic
    
    def calculate_correlation_matrix(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算因子相关性矩阵
        
        Args:
            factor_df: 因子DataFrame
            
        Returns:
            相关性矩阵
        """
        if factor_df.empty:
            return pd.DataFrame()
        
        # 获取因子列
        exclude_cols = ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'amount', 'forward_return']
        factor_cols = [col for col in factor_df.columns if col not in exclude_cols]
        
        # 只选择数值列
        numeric_df = factor_df[factor_cols].select_dtypes(include=[np.number])
        
        # 计算相关性
        corr_matrix = numeric_df.corr()
        
        return corr_matrix
    
    def analyze_factor_correlation(self, factor_df: pd.DataFrame, threshold: Optional[float] = None) -> Dict[str, List[Tuple[str, float]]]:
        """
        分析因子相关性，找出高相关因子对
        
        Args:
            factor_df: 因子DataFrame
            threshold: 相关性阈值（默认使用self.correlation_threshold）
            
        Returns:
            高相关因子字典 {因子: [(相关因子, 相关系数), ...]}
        """
        threshold = threshold or self.correlation_threshold
        corr_matrix = self.calculate_correlation_matrix(factor_df)
        
        if corr_matrix.empty:
            return {}
        
        high_corr = {}
        for i, factor1 in enumerate(corr_matrix.columns):
            high_corr[factor1] = []
            for j, factor2 in enumerate(corr_matrix.columns):
                if i != j:
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) >= threshold and not np.isnan(corr_val):
                        high_corr[factor1].append((factor2, corr_val))
                        
                        # 更新因子对象的相关性
                        if factor1 in self.factors:
                            self.factors[factor1].correlation[factor2] = corr_val
        
        # 统计高相关对数
        pair_count = sum(len(v) for v in high_corr.values()) // 2
        logger.info(f"相关性分析完成，发现 {pair_count} 对高相关因子(>|{threshold}|)")
        
        return high_corr
    
    def get_valid_factors(self) -> List[str]:
        """
        获取有效因子列表（基于IC值筛选）
        
        Returns:
            有效因子代码列表
        """
        return [code for code, factor in self.factors.items() 
                if factor.is_valid and factor.ic_value is not None and abs(factor.ic_value) >= self.ic_threshold]
    
    def get_factor_by_category(self, category: FactorCategory) -> List[Factor]:
        """
        按类别获取因子
        
        Args:
            category: 因子类别
            
        Returns:
            因子列表
        """
        return [f for f in self.factors.values() if f.category == category]
    
    # ==================== PCA正交化 ====================
    
    def apply_pca_orthogonalization(self, factor_df: pd.DataFrame, n_components: Optional[int] = None, 
                                     variance_threshold: float = 0.95) -> Tuple[pd.DataFrame, Any]:
        """
        应用PCA正交化处理因子
        
        Args:
            factor_df: 因子DataFrame
            n_components: 主成分数量（None则根据variance_threshold自动确定）
            variance_threshold: 方差解释率阈值
            
        Returns:
            (正交化后的DataFrame, PCA模型)
        """
        try:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.error("scikit-learn未安装，无法进行PCA正交化")
            return factor_df, None
        
        # 获取因子列
        exclude_cols = ['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'amount', 'forward_return']
        factor_cols = [col for col in factor_df.columns if col not in exclude_cols]
        
        # 提取因子数据
        X = factor_df[factor_cols].select_dtypes(include=[np.number])
        
        # 处理缺失值
        X = X.fillna(X.mean())
        
        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PCA
        if n_components is None:
            # 先拟合全部，然后根据方差阈值确定组件数
            pca_full = PCA()
            pca_full.fit(X_scaled)
            cumsum = np.cumsum(pca_full.explained_variance_ratio_)
            n_components = np.argmax(cumsum >= variance_threshold) + 1
            logger.info(f"根据方差阈值 {variance_threshold}，自动选择 {n_components} 个主成分")
        
        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X_scaled)
        
        # 构建结果DataFrame
        pca_cols = [f'pca_{i+1}' for i in range(n_components)]
        pca_df = pd.DataFrame(X_pca, columns=pca_cols, index=factor_df.index)
        
        # 保留原始元数据
        for col in ['ts_code', 'trade_date']:
            if col in factor_df.columns:
                pca_df[col] = factor_df[col].values
        
        logger.info(f"PCA正交化完成: {len(factor_cols)} 个因子 -> {n_components} 个主成分")
        logger.info(f"解释方差比例: {pca.explained_variance_ratio_.sum():.2%}")
        
        return pca_df, pca
    
    # ==================== 因子筛选与优化 ====================
    
    def select_best_factors(self, factor_df: pd.DataFrame, max_factors: int = 20, 
                           consider_correlation: bool = True) -> List[str]:
        """
        选择最优因子组合
        
        策略:
        1. 首先按IC值排序
        2. 然后剔除高相关因子（保留IC值更高的）
        
        Args:
            factor_df: 因子DataFrame
            max_factors: 最大因子数量
            consider_correlation: 是否考虑相关性
            
        Returns:
            选中的因子列表
        """
        # 计算IC值
        ic_results = self.analyze_factor_ic(factor_df)
        
        if not ic_results:
            return []
        
        # 按IC绝对值排序
        sorted_factors = sorted(ic_results.items(), 
                               key=lambda x: abs(x[1]) if not np.isnan(x[1]) else 0, 
                               reverse=True)
        
        if not consider_correlation:
            return [f[0] for f in sorted_factors[:max_factors]]
        
        # 考虑相关性，逐步选择
        corr_matrix = self.calculate_correlation_matrix(factor_df)
        selected = []
        
        for factor, ic in sorted_factors:
            if len(selected) >= max_factors:
                break
            
            if np.isnan(ic):
                continue
            
            # 检查与已选因子的相关性
            should_include = True
            for sel_factor in selected:
                if factor in corr_matrix.columns and sel_factor in corr_matrix.columns:
                    corr = abs(corr_matrix.loc[factor, sel_factor])
                    if corr >= self.correlation_threshold:
                        should_include = False
                        break
            
            if should_include:
                selected.append(factor)
        
        logger.info(f"因子筛选完成: 从 {len(sorted_factors)} 个因子中选出 {len(selected)} 个")
        return selected
    
    def generate_factor_report(self, factor_df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成因子分析报告
        
        Args:
            factor_df: 因子DataFrame
            
        Returns:
            报告字典
        """
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_factors': len(self.factors),
            'data_points': len(factor_df),
            'ic_analysis': {},
            'correlation_analysis': {},
            'category_distribution': {},
            'top_factors': [],
            'valid_factors': []
        }
        
        # IC分析
        ic_results = self.analyze_factor_ic(factor_df)
        report['ic_analysis'] = {
            'mean_ic': np.nanmean(list(ic_results.values())),
            'std_ic': np.nanstd(list(ic_results.values())),
            'valid_count': sum(1 for v in ic_results.values() if abs(v) >= self.ic_threshold and not np.isnan(v)),
            'total_count': len(ic_results)
        }
        
        # 相关性分析
        high_corr = self.analyze_factor_correlation(factor_df)
        report['correlation_analysis'] = {
            'high_correlation_pairs': sum(len(v) for v in high_corr.values()) // 2,
            'threshold': self.correlation_threshold
        }
        
        # 类别分布
        for category in FactorCategory:
            count = len(self.get_factor_by_category(category))
            report['category_distribution'][category.value] = count
        
        # 顶级因子
        sorted_ic = sorted(ic_results.items(), 
                          key=lambda x: abs(x[1]) if not np.isnan(x[1]) else 0, 
                          reverse=True)
        report['top_factors'] = [{'factor': f, 'ic': ic} for f, ic in sorted_ic[:10]]
        
        # 有效因子
        report['valid_factors'] = self.get_valid_factors()
        
        return report
    
    def export_factors_to_json(self, output_path: str):
        """
        导出因子定义到JSON
        
        Args:
            output_path: 输出文件路径
        """
        import json
        
        factors_export = {}
        for code, factor in self.factors.items():
            factors_export[code] = {
                'name': factor.name,
                'code': factor.code,
                'category': factor.category.value,
                'description': factor.description,
                'formula': factor.formula,
                'ic_value': factor.ic_value,
                'is_valid': factor.is_valid,
                'weight': factor.weight
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(factors_export, f, ensure_ascii=False, indent=2)
        
        logger.info(f"因子定义已导出到 {output_path}")
    
    def get_factor_library(self) -> Dict[str, Any]:
        """
        获取完整因子库信息
        
        Returns:
            因子库字典
        """
        return {
            'total_count': len(self.factors),
            'technical_count': len(self.get_factor_by_category(FactorCategory.TECHNICAL)),
            'fundamental_count': len(self.get_factor_by_category(FactorCategory.FUNDAMENTAL)),
            'money_flow_count': len(self.get_factor_by_category(FactorCategory.MONEY_FLOW)),
            'sentiment_count': len(self.get_factor_by_category(FactorCategory.SENTIMENT)),
            'factors': {code: {
                'name': f.name,
                'category': f.category.value,
                'description': f.description,
                'ic_value': f.ic_value,
                'is_valid': f.is_valid
            } for code, f in self.factors.items()}
        }


# ==================== 便捷函数 ====================

def create_factor_miner(config_path: Optional[str] = None) -> FactorMiner:
    """
    创建因子挖掘器实例（使用配置文件）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        FactorMiner实例
    """
    # 默认配置
    config = {
        'correlation_threshold': 0.8,
        'ic_threshold': 0.03,
        'min_periods': 20
    }
    
    # 加载配置文件
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)
            if file_config and 'machine_learning' in file_config:
                ml_config = file_config['machine_learning']
                if 'factor_discovery' in ml_config:
                    fd_config = ml_config['factor_discovery']
                    config['correlation_threshold'] = fd_config.get('correlation_threshold', 0.8)
                    config['max_factors'] = fd_config.get('max_factors', 50)
    
    # 获取Tushare Token
    token = os.getenv('TUSHARE_TOKEN', '')
    if not token and config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config and 'api' in file_config:
                    token = file_config['api'].get('api_key', '')
        except:
            pass
    
    if not token:
        raise ValueError("未找到Tushare Token，请设置环境变量TUSHARE_TOKEN或在配置文件中指定")
    
    return FactorMiner(token, config)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 创建因子挖掘器
    try:
        miner = create_factor_miner('config.yaml')
        
        # 打印因子库信息
        library = miner.get_factor_library()
        print(f"\n因子库统计:")
        print(f"  总因子数: {library['total_count']}")
        print(f"  技术指标: {library['technical_count']}")
        print(f"  基本面: {library['fundamental_count']}")
        print(f"  资金流: {library['money_flow_count']}")
        print(f"  情绪: {library['sentiment_count']}")
        
    except Exception as e:
        print(f"测试失败: {e}")
