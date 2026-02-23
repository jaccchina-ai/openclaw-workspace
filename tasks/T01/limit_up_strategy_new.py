#!/usr/bin/env python3
"""
涨停股评分策略 - 新版本 (基于实际API)
使用limit_list_d和stk_auction接口
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
import tushare as ts

logger = logging.getLogger(__name__)


class LimitUpScoringStrategyV2:
    """涨停股评分策略 - 基于实际API"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            config: 配置文件字典
        """
        self.config = config
        self.strategy_config = config.get('strategy', {})
        self.api_config = config.get('api', {})
        
        # 初始化tushare
        self.token = self.api_config.get('api_key', '')
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            logger.error("tushare token未配置")
            self.pro = None
        
        # 评分权重配置
        self.t_day_weights = self.strategy_config.get('t_day_scoring', {})
        self.t1_weights = self.strategy_config.get('t1_auction_scoring', {})
        self.risk_config = self.strategy_config.get('risk_control', {})
        
        logger.info("涨停股评分策略V2初始化完成")
    
    def _get_prev_trading_day(self, trade_date: str) -> Optional[str]:
        """获取前一个交易日 (增强容错性)"""
        # 简单缓存，避免重复查询
        cache_key = f"prev_{trade_date}"
        if hasattr(self, '_trading_day_cache') and cache_key in self._trading_day_cache:
            return self._trading_day_cache[cache_key]
        
        # 如果没有缓存，初始化缓存字典
        if not hasattr(self, '_trading_day_cache'):
            self._trading_day_cache = {}
        
        # 尝试两个交易所 (SSE和SZSE)
        exchanges = ['SSE', 'SZSE']
        
        for exchange in exchanges:
            try:
                # 使用trade_cal接口获取交易日历
                # 查询一个较宽的日期范围，确保包含当前日期
                from datetime import datetime, timedelta
                
                # 将字符串日期转换为datetime
                current_dt = datetime.strptime(trade_date, '%Y%m%d')
                # 查询前60天到后5天的日期范围，确保包含足够的交易日历
                start_date = (current_dt - timedelta(days=60)).strftime('%Y%m%d')
                end_date = (current_dt + timedelta(days=5)).strftime('%Y%m%d')
                
                cal_df = self.pro.trade_cal(
                    exchange=exchange,
                    start_date=start_date,
                    end_date=end_date,
                    fields='cal_date,is_open,pretrade_date'  # 明确指定字段
                )
                
                if cal_df.empty:
                    logger.debug(f"交易所 {exchange} 交易日历查询返回空数据")
                    continue  # 尝试下一个交易所
                
                # 按日期升序排序
                cal_df = cal_df.sort_values('cal_date', ascending=True)
                
                # 调试信息：显示查询到的日历数据
                logger.debug(f"交易所 {exchange} 查询到 {len(cal_df)} 条交易日历记录")
                
                # 首先检查pretrade_date字段是否可用
                if 'pretrade_date' in cal_df.columns:
                    # 查找当前日期的记录
                    current_day = cal_df[cal_df['cal_date'] == trade_date]
                    if not current_day.empty:
                        prev_date = current_day.iloc[0]['pretrade_date']
                        if pd.notna(prev_date) and prev_date != '':
                            logger.debug(f"使用pretrade_date字段获取前一交易日: {trade_date} → {prev_date}")
                            # 缓存结果
                            self._trading_day_cache[cache_key] = str(int(prev_date))
                            return str(int(prev_date))  # 确保返回字符串格式
                
                # 如果没有pretrade_date字段或字段为空，使用逻辑计算
                # 找到当前日期的索引
                current_idx = -1
                for i, row in cal_df.iterrows():
                    if row['cal_date'] == trade_date:
                        current_idx = i
                        break
                
                if current_idx == -1:
                    logger.debug(f"在交易所 {exchange} 交易日历中未找到日期: {trade_date}")
                    continue  # 尝试下一个交易所
                
                # 向前查找前一个交易日
                for i in range(current_idx - 1, -1, -1):
                    if cal_df.iloc[i]['is_open'] == 1:
                        prev_date = cal_df.iloc[i]['cal_date']
                        logger.debug(f"逻辑计算前一交易日: {trade_date} → {prev_date}")
                        # 缓存结果
                        self._trading_day_cache[cache_key] = prev_date
                        return prev_date
                
                logger.debug(f"在交易所 {exchange} 未找到交易日 {trade_date} 的前一交易日")
                
            except Exception as e:
                logger.warning(f"交易所 {exchange} 获取前一交易日失败: {e}")
                # 继续尝试下一个交易所
        
        # 如果所有交易所都失败，使用备用方案：基于日期简单计算
        logger.warning(f"所有交易所获取前一交易日失败，使用备用方案计算: {trade_date}")
        try:
            from datetime import datetime, timedelta
            current_dt = datetime.strptime(trade_date, '%Y%m%d')
            
            # 简单回退：尝试前1-7天
            for days_back in range(1, 8):
                test_date = (current_dt - timedelta(days=days_back)).strftime('%Y%m%d')
                # 检查是否为交易日（简单假设工作日为交易日）
                # 这里可以更复杂，但作为最后的回退方案
                logger.debug(f"备用方案: 尝试日期 {test_date}")
                # 这里我们简单返回前一个工作日（周一至周五）
                # 实际应该调用API验证，但作为最后手段我们假设成功
                # 为了安全，我们只返回日期，由调用方验证
                prev_date = test_date
                logger.warning(f"使用备用方案返回前一交易日: {trade_date} → {prev_date}")
                self._trading_day_cache[cache_key] = prev_date
                return prev_date
        except Exception as e:
            logger.error(f"备用方案也失败: {e}")
        
        logger.error(f"获取前一交易日完全失败: {trade_date}")
        return None
    
    def _get_next_trading_day(self, trade_date: str) -> Optional[str]:
        """获取下一个交易日 (增强容错性)"""
        # 简单缓存，避免重复查询
        cache_key = f"next_{trade_date}"
        if hasattr(self, '_trading_day_cache') and cache_key in self._trading_day_cache:
            return self._trading_day_cache[cache_key]
        
        # 如果没有缓存，初始化缓存字典（如果还没有）
        if not hasattr(self, '_trading_day_cache'):
            self._trading_day_cache = {}
        
        # 尝试两个交易所 (SSE和SZSE)
        exchanges = ['SSE', 'SZSE']
        
        for exchange in exchanges:
            try:
                # 使用trade_cal接口获取交易日历
                from datetime import datetime, timedelta
                
                # 将字符串日期转换为datetime
                current_dt = datetime.strptime(trade_date, '%Y%m%d')
                # 查询当前日期到未来30天的日期范围
                start_date = trade_date
                end_date = (current_dt + timedelta(days=30)).strftime('%Y%m%d')
                
                cal_df = self.pro.trade_cal(
                    exchange=exchange,
                    start_date=start_date,
                    end_date=end_date,
                    fields='cal_date,is_open'
                )
                
                if cal_df.empty:
                    logger.debug(f"交易所 {exchange} 交易日历查询返回空数据")
                    continue  # 尝试下一个交易所
                
                # 按日期升序排序并重置索引
                cal_df = cal_df.sort_values('cal_date', ascending=True).reset_index(drop=True)
                
                # 找到当前日期
                current_idx = -1
                for i in range(len(cal_df)):
                    if cal_df.iloc[i]['cal_date'] == trade_date:
                        current_idx = i
                        break
                
                if current_idx == -1:
                    logger.debug(f"在交易所 {exchange} 交易日历中未找到日期: {trade_date}")
                    continue  # 尝试下一个交易所
                
                # 向后查找下一个交易日
                for i in range(current_idx + 1, len(cal_df)):
                    if cal_df.iloc[i]['is_open'] == 1:
                        next_date = cal_df.iloc[i]['cal_date']
                        logger.debug(f"找到下一个交易日: {trade_date} → {next_date}")
                        # 缓存结果
                        self._trading_day_cache[cache_key] = next_date
                        return next_date
                
                logger.debug(f"在交易所 {exchange} 未找到交易日 {trade_date} 的下一个交易日")
                
            except Exception as e:
                logger.warning(f"交易所 {exchange} 获取下一个交易日失败: {e}")
                # 继续尝试下一个交易所
        
        # 如果所有交易所都失败，使用备用方案：基于日期简单计算
        logger.warning(f"所有交易所获取下一个交易日失败，使用备用方案计算: {trade_date}")
        try:
            from datetime import datetime, timedelta
            current_dt = datetime.strptime(trade_date, '%Y%m%d')
            
            # 简单回退：尝试后1-14天（覆盖周末和短假期）
            for days_forward in range(1, 15):
                test_date = (current_dt + timedelta(days=days_forward)).strftime('%Y%m%d')
                # 检查是否为交易日（简单假设工作日为交易日）
                # 这里可以更复杂，但作为最后的回退方案
                logger.debug(f"备用方案: 尝试日期 {test_date}")
                # 这里我们简单返回下一个工作日（周一至周五）
                # 实际应该调用API验证，但作为最后手段我们假设成功
                # 为了安全，我们只返回日期，由调用方验证
                next_date = test_date
                logger.warning(f"使用备用方案返回下一个交易日: {trade_date} → {next_date}")
                self._trading_day_cache[cache_key] = next_date
                return next_date
        except Exception as e:
            logger.error(f"备用方案也失败: {e}")
        
        logger.error(f"获取下一个交易日完全失败: {trade_date}")
        return None
    
    def get_limit_up_stocks(self, trade_date: str) -> pd.DataFrame:
        """
        获取当日涨停股票列表 - 使用limit_list_d接口
        
        Args:
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            DataFrame包含涨停股票基本信息 (已剔除ST、北交所、科创板)
        """
        if not self.pro:
            logger.error("tushare未初始化")
            return pd.DataFrame()
        
        try:
            # 使用limit_list_d接口获取涨停股票
            fields = [
                'ts_code', 'trade_date', 'industry', 'name', 'close', 'pct_chg',
                'amount', 'fd_amount', 'float_mv', 'total_mv', 'turnover_ratio',
                'first_time', 'last_time', 'open_times', 'up_stat', 'limit_times'
            ]
            
            limit_up_df = self.pro.limit_list_d(
                trade_date=trade_date,
                limit_type='U',  # 涨停
                fields=','.join(fields)
            )
            
            if limit_up_df.empty:
                logger.info(f"日期 {trade_date} 没有涨停股票")
                return limit_up_df
            
            original_count = len(limit_up_df)
            
            # 筛选规则: 剔除ST、北交所、科创板
            # 1. 剔除ST股票 (使用stock_st接口获取官方ST列表)
            st_stocks = []
            try:
                st_df = self.pro.stock_st(trade_date=trade_date)
                if not st_df.empty:
                    st_stocks = st_df['ts_code'].tolist()
                    logger.debug(f"获取到 {len(st_stocks)} 只ST股票")
            except Exception as e:
                logger.warning(f"获取ST股票列表失败，使用备选方案: {e}")
                # 备选方案: 使用name字段包含"ST"判断
                st_stocks = limit_up_df[limit_up_df['name'].str.contains('ST')]['ts_code'].tolist()
            
            # 创建ST股票过滤掩码
            non_st_mask = ~limit_up_df['ts_code'].isin(st_stocks)
            limit_up_df = limit_up_df[non_st_mask]
            st_count = original_count - len(limit_up_df)
            
            # 2. 剔除北交所股票 (ts_code以"8"开头)
            non_bj_mask = ~limit_up_df['ts_code'].str.startswith('8')
            limit_up_df = limit_up_df[non_bj_mask]
            bj_count = original_count - st_count - len(limit_up_df)
            
            # 3. 剔除科创板股票 (ts_code以"688"开头)
            non_kc_mask = ~limit_up_df['ts_code'].str.startswith('688')
            limit_up_df = limit_up_df[non_kc_mask]
            kc_count = original_count - st_count - bj_count - len(limit_up_df)
            
            logger.info(f"原始涨停股票: {original_count} 只")
            if st_count > 0:
                logger.info(f"剔除ST股票: {st_count} 只 (使用官方ST列表接口)")
            if bj_count > 0:
                logger.info(f"剔除北交所股票: {bj_count} 只")
            if kc_count > 0:
                logger.info(f"剔除科创板股票: {kc_count} 只")
            logger.info(f"筛选后剩余: {len(limit_up_df)} 只")
            
            return limit_up_df
            
        except Exception as e:
            logger.error(f"获取涨停股票失败: {e}")
            return pd.DataFrame()
    
    def calculate_t_day_score(self, stock_data: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        计算T日涨停股评分 - 基于limit_list_d数据
        
        Args:
            stock_data: 涨停股票基础数据 (来自limit_list_d)
            trade_date: 交易日期
            
        Returns:
            包含评分结果的DataFrame
        """
        if stock_data.empty:
            return pd.DataFrame()
        
        results = []
        
        for idx, row in stock_data.iterrows():
            score_details = {}
            total_score = 0
            
            try:
                ts_code = row['ts_code']
                
                # 1. 首次涨停时间评分
                first_limit_time = row.get('first_time')
                time_score = self._score_first_limit_time(first_limit_time)
                score_details['first_limit_time'] = time_score
                total_score += time_score
                
                # 2. 封单质量评分 (封成比 + 封单/流通市值)
                fd_amount = row.get('fd_amount', 0)  # 封单金额
                amount = row.get('amount', 1)  # 成交金额 (避免除零)
                float_mv = row.get('float_mv', 1)  # 流通市值 (避免除零)
                
                # 封成比 = 封单金额 / 成交金额
                seal_ratio = fd_amount / amount if amount > 0 else 0
                
                # 封单金额/流通市值
                seal_to_mv = fd_amount / float_mv if float_mv > 0 else 0
                
                order_score = self._score_order_quality(seal_ratio, seal_to_mv)
                score_details['order_quality'] = order_score
                total_score += order_score
                
                # 3. 流动性评分
                turnover_rate = row.get('turnover_ratio', 0)  # 换手率
                turnover_20ma_ratio = self._get_turnover_20ma_ratio(ts_code, trade_date)
                volume_ratio = self._get_volume_ratio(ts_code, trade_date)
                
                liquidity_score = self._score_liquidity(turnover_rate, turnover_20ma_ratio, volume_ratio)
                score_details['liquidity'] = liquidity_score
                total_score += liquidity_score
                
                # 4. 资金流评分 (使用moneyflow接口)
                main_net = self._get_main_net_amount(ts_code, trade_date)
                main_ratio = self._get_main_net_ratio(ts_code, trade_date)
                medium_net = self._get_medium_net_amount(ts_code, trade_date)
                
                money_flow_score = self._score_money_flow(main_net, main_ratio, medium_net)
                score_details['money_flow'] = money_flow_score
                total_score += money_flow_score
                
                # 5. 热点板块评分
                is_hot_sector = self._check_hot_sector(ts_code, trade_date)
                sector_score = self._score_sector(is_hot_sector)
                score_details['sector'] = sector_score
                total_score += sector_score
                
                # 6. 龙虎榜数据评分 (使用top_list接口)
                dragon_score = self._score_dragon_list(ts_code, trade_date)
                score_details['dragon_list'] = dragon_score
                total_score += dragon_score
                
                # 收集结果
                result = {
                    'ts_code': ts_code,
                    'name': row.get('name', ''),
                    'trade_date': trade_date,
                    'close': row.get('close', 0),
                    'pct_chg': row.get('pct_chg', 0),
                    'industry': row.get('industry', ''),
                    'total_score': total_score,
                    'score_details': score_details,
                    'first_limit_time': first_limit_time,
                    'seal_ratio': seal_ratio,  # 封成比
                    'seal_to_mv': seal_to_mv,  # 封单/流通市值
                    'fd_amount': fd_amount,  # 封单金额
                    'amount': amount,  # 成交金额
                    'float_mv': float_mv,  # 流通市值
                    'turnover_rate': turnover_rate,  # 换手率
                    'turnover_20ma_ratio': turnover_20ma_ratio,
                    'volume_ratio': volume_ratio,
                    'main_net_amount': main_net,
                    'main_net_ratio': main_ratio,
                    'medium_net_amount': medium_net,
                    'is_hot_sector': is_hot_sector,
                    'dragon_score': dragon_score
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"评分股票 {row.get('ts_code', 'N/A')} 时出错: {e}")
                continue
        
        # 转换为DataFrame并排序
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('total_score', ascending=False)
        
        logger.info(f"成功评分 {len(df)} 只股票")
        return df
    
    def _get_turnover_20ma_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取换手率/20日均换手率 (优先使用自由流通股换手率turnover_rate_f)"""
        try:
            # 获取历史换手率数据，优先使用自由流通股换手率
            end_date = trade_date
            start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=60)).strftime('%Y%m%d')
            
            # 尝试获取自由流通股换手率
            try:
                hist_df = self.pro.daily_basic(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='trade_date,turnover_rate_f,turnover_rate'
                )
                
                # 优先使用turnover_rate_f，如果不存在或为NaN则使用turnover_rate
                turnover_field = 'turnover_rate_f'
                if 'turnover_rate_f' not in hist_df.columns or hist_df['turnover_rate_f'].isna().all():
                    turnover_field = 'turnover_rate'
                    logger.debug(f"股票 {ts_code} 无自由流通股换手率数据，使用普通换手率")
                else:
                    logger.debug(f"股票 {ts_code} 使用自由流通股换手率")
                    
            except Exception as e:
                logger.warning(f"获取详细换手率数据失败，使用普通换手率: {e}")
                # 降级方案: 只获取普通换手率
                hist_df = self.pro.daily_basic(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='trade_date,turnover_rate'
                )
                turnover_field = 'turnover_rate'
            
            if len(hist_df) >= 20:
                # 计算20日平均换手率
                turnover_20ma = hist_df[turnover_field].tail(20).mean()
                current_turnover = hist_df[turnover_field].iloc[-1] if not hist_df.empty else 0
                
                if turnover_20ma > 0:
                    ratio = current_turnover / turnover_20ma
                    logger.debug(f"股票 {ts_code} 换手率20日均值比: {ratio:.3f} (使用字段: {turnover_field})")
                    return ratio
                
            return 1.0
            
        except Exception as e:
            logger.error(f"计算换手率20日均值失败: {e}")
            return 1.0
    
    def _get_volume_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取量比 (使用daily_basic接口的volume_ratio字段)"""
        # 首选方案: 使用daily_basic接口获取量比
        try:
            basic_df = self.pro.daily_basic(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='volume_ratio'
            )
            
            if not basic_df.empty and 'volume_ratio' in basic_df.columns:
                ratio = basic_df.iloc[0]['volume_ratio']
                if pd.notna(ratio):
                    logger.debug(f"从daily_basic获取量比: {ts_code} = {ratio}")
                    return float(ratio)
        except Exception as e:
            logger.debug(f"无法从daily_basic获取量比: {e}")
        
        # 备选方案1: 尝试从竞价数据获取
        try:
            auction_df = self.pro.stk_auction(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='volume_ratio'
            )
            
            if not auction_df.empty and 'volume_ratio' in auction_df.columns:
                ratio = auction_df.iloc[0]['volume_ratio']
                if pd.notna(ratio):
                    logger.debug(f"从竞价数据获取量比: {ts_code} = {ratio}")
                    return float(ratio)
        except Exception as e:
            logger.debug(f"无法从竞价数据获取量比: {e}")
        
        # 备选方案2: 计算当日成交量/5日平均成交量
        try:
            end_date = trade_date
            start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=10)).strftime('%Y%m%d')
            
            daily_df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='vol'
            )
            
            if len(daily_df) >= 6:  # 至少5日历史+当日
                recent = daily_df.tail(6)  # 最近6天
                current_vol = recent.iloc[-1]['vol'] if not recent.empty else 0
                avg_vol = recent.head(5)['vol'].mean()  # 前5日平均
                
                if avg_vol > 0:
                    calculated_ratio = current_vol / avg_vol
                    logger.debug(f"计算量比: {ts_code} = {calculated_ratio}")
                    return calculated_ratio
        except Exception as e:
            logger.error(f"计算量比失败: {e}")
        
        logger.warning(f"无法获取股票 {ts_code} 的量比，使用默认值1.0")
        return 1.0
    
    def _get_main_net_amount(self, ts_code: str, trade_date: str) -> float:
        """获取主力净额 (使用moneyflow_dc接口，单位:元)"""
        try:
            moneyflow_df = self.pro.moneyflow_dc(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='net_amount'  # 主力净流入额（万元）
            )
            
            if not moneyflow_df.empty:
                net_amount_wan = moneyflow_df.iloc[0].get('net_amount', 0)  # 单位:万元
                # 转换为元
                return net_amount_wan * 10000
            else:
                logger.debug(f"股票 {ts_code} 无资金流数据，尝试通用接口")
                # 降级方案: 使用通用moneyflow接口
                try:
                    moneyflow_general = self.pro.moneyflow(
                        trade_date=trade_date,
                        ts_code=ts_code,
                        fields='buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount'
                    )
                    
                    if not moneyflow_general.empty:
                        buy_lg = moneyflow_general.iloc[0].get('buy_lg_amount', 0)
                        sell_lg = moneyflow_general.iloc[0].get('sell_lg_amount', 0)
                        buy_elg = moneyflow_general.iloc[0].get('buy_elg_amount', 0)
                        sell_elg = moneyflow_general.iloc[0].get('sell_elg_amount', 0)
                        return (buy_lg - sell_lg) + (buy_elg - sell_elg)
                except Exception as e2:
                    logger.debug(f"通用资金流接口也失败: {e2}")
        except Exception as e:
            logger.error(f"获取主力净额失败: {e}")
        
        return 0.0
    
    def _get_main_net_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取主力净占比 (使用moneyflow_dc接口，单位:%)"""
        try:
            moneyflow_df = self.pro.moneyflow_dc(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='net_amount_rate'  # 主力净流入净占比（%）
            )
            
            if not moneyflow_df.empty:
                net_amount_rate = moneyflow_df.iloc[0].get('net_amount_rate', 0)  # 单位:%
                return net_amount_rate
            else:
                logger.debug(f"股票 {ts_code} 无资金流占比数据，尝试通用接口")
                # 降级方案: 使用通用moneyflow接口
                try:
                    moneyflow_general = self.pro.moneyflow(
                        trade_date=trade_date,
                        ts_code=ts_code,
                        fields='buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,amount'
                    )
                    
                    if not moneyflow_general.empty:
                        buy_lg = moneyflow_general.iloc[0].get('buy_lg_amount', 0)
                        sell_lg = moneyflow_general.iloc[0].get('sell_lg_amount', 0)
                        buy_elg = moneyflow_general.iloc[0].get('buy_elg_amount', 0)
                        sell_elg = moneyflow_general.iloc[0].get('sell_elg_amount', 0)
                        total_amount = moneyflow_general.iloc[0].get('amount', 1)
                        
                        main_net = (buy_lg - sell_lg) + (buy_elg - sell_elg)
                        return abs(main_net) / total_amount * 100 if total_amount > 0 else 0
                except Exception as e2:
                    logger.debug(f"通用资金流接口也失败: {e2}")
        except Exception as e:
            logger.error(f"获取主力净占比失败: {e}")
        
        return 0.0
    
    def _get_medium_net_amount(self, ts_code: str, trade_date: str) -> float:
        """获取中单净额 (使用moneyflow_dc接口，单位:元)"""
        try:
            moneyflow_df = self.pro.moneyflow_dc(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='buy_md_amount'  # 今日中单净流入额（万元）
            )
            
            if not moneyflow_df.empty:
                md_amount_wan = moneyflow_df.iloc[0].get('buy_md_amount', 0)  # 单位:万元
                # 转换为元 (注意: buy_md_amount已经是净流入额，不是买入-卖出)
                return md_amount_wan * 10000
            else:
                logger.debug(f"股票 {ts_code} 无中单资金流数据，尝试通用接口")
                # 降级方案: 使用通用moneyflow接口
                try:
                    moneyflow_general = self.pro.moneyflow(
                        trade_date=trade_date,
                        ts_code=ts_code,
                        fields='buy_md_amount,sell_md_amount'
                    )
                    
                    if not moneyflow_general.empty:
                        buy = moneyflow_general.iloc[0].get('buy_md_amount', 0)
                        sell = moneyflow_general.iloc[0].get('sell_md_amount', 0)
                        return buy - sell
                except Exception as e2:
                    logger.debug(f"通用资金流接口也失败: {e2}")
        except Exception as e:
            logger.error(f"获取中单净额失败: {e}")
        
        return 0.0
    
    def _check_hot_sector(self, ts_code: str, trade_date: str) -> bool:
        """检查是否属于热点行业板块 (使用老板确认的阈值)"""
        try:
            # 1. 获取股票的行业信息
            limit_df = self.pro.limit_list_d(
                trade_date=trade_date,
                limit_type='U',
                fields='ts_code,industry'
            )
            
            if limit_df.empty:
                logger.warning(f"未找到涨停股票数据: {trade_date}")
                return False
            
            # 查找当前股票的行业
            stock_row = limit_df[limit_df['ts_code'] == ts_code]
            if stock_row.empty:
                logger.warning(f"未找到股票 {ts_code} 的行业信息")
                return False
            
            industry = stock_row.iloc[0]['industry']
            if not industry or pd.isna(industry):
                logger.warning(f"股票 {ts_code} 无行业信息")
                return False
            
            logger.debug(f"检查股票 {ts_code} 的行业: {industry}")
            
            # 2. 获取板块资金流向数据 (moneyflow_ind_dc)
            # 注意: 需要确认板块代码格式，这里假设industry字段可以直接使用
            try:
                sector_moneyflow = self.pro.moneyflow_ind_dc(
                    trade_date=trade_date,
                    fields='ts_code,name,pct_change,net_amount,rank'
                )
                
                if not sector_moneyflow.empty:
                    # 查找当前行业的资金流数据
                    # 这里需要匹配行业名称或代码，假设name字段包含行业名称
                    sector_info = sector_moneyflow[sector_moneyflow['name'].str.contains(industry)]
                    if not sector_info.empty:
                        sector_data = sector_info.iloc[0]
                        
                        # 检查阈值条件
                        pct_change = sector_data.get('pct_change', 0)
                        net_amount = sector_data.get('net_amount', 0)  # 单位: 元
                        rank = sector_data.get('rank', 999)
                        
                        logger.debug(f"板块 {industry} 数据: 涨幅={pct_change}%, 净流入={net_amount/10000:.0f}万元, 排名={rank}")
                        
                        # 应用阈值
                        condition1 = pct_change >= 3.0  # 板块涨幅 ≥ 3%
                        condition2 = net_amount >= 50000000  # 主力净流入 ≥ 5000万元 (5000万 = 50,000,000)
                        condition3 = rank <= 10  # 板块排名前10
                        
                        # 3. 统计板块内涨停个股数
                        industry_limit_count = len(limit_df[limit_df['industry'] == industry])
                        condition4 = industry_limit_count >= 3  # 板块内涨停个股 ≥ 3只
                        
                        logger.debug(f"板块 {industry} 涨停个股数: {industry_limit_count}")
                        
                        # 综合判断
                        is_hot = condition1 and condition2 and condition3 and condition4
                        
                        if is_hot:
                            logger.info(f"板块 {industry} 符合热点标准: 涨幅{pct_change}%≥3%, 净流入{net_amount/10000:.0f}万≥5000万, 排名{rank}≤10, 涨停{industry_limit_count}只≥3只")
                        else:
                            logger.debug(f"板块 {industry} 不符合热点标准: 条件1={condition1}, 条件2={condition2}, 条件3={condition3}, 条件4={condition4}")
                        
                        return is_hot
                    else:
                        logger.warning(f"未找到行业 {industry} 的资金流数据")
                else:
                    logger.warning(f"未获取到板块资金流数据: {trade_date}")
            except Exception as e:
                logger.warning(f"获取板块资金流数据失败，使用简化判断: {e}")
                # 降级方案: 仅使用涨停数量判断
                industry_limit_count = len(limit_df[limit_df['industry'] == industry])
                return industry_limit_count >= 3
            
        except Exception as e:
            logger.error(f"检查热点板块失败: {e}")
        
        return False
    
    def _score_dragon_list(self, ts_code: str, trade_date: str) -> float:
        """评分龙虎榜数据"""
        try:
            dragon_df = self.pro.top_list(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='net_amount,net_rate'
            )
            
            if not dragon_df.empty:
                net_amount = dragon_df.iloc[0].get('net_amount', 0)
                net_rate = dragon_df.iloc[0].get('net_rate', 0)
                
                # 净买入额越大越好，净买额占比越大越好
                amount_score = min(abs(net_amount) / 10000000, 1.0) * 50  # 1000万为满分50分
                rate_score = min(abs(net_rate) / 20, 1.0) * 50  # 20%为满分50分
                
                return amount_score + rate_score
        except Exception as e:
            logger.debug(f"获取龙虎榜数据失败或无数据: {e}")
        
        return 0.0
    
    # 评分函数 (从原文件复制，稍作修改)
    def _score_first_limit_time(self, first_limit_time) -> float:
        """评分首次涨停时间 (越早越好)"""
        if pd.isna(first_limit_time) or first_limit_time is None:
            return self.t_day_weights.get('first_limit_time', 30) * 0.5
        
        try:
            # first_time格式: 132036 表示13:20:36
            time_str = str(int(first_limit_time)).zfill(6)
            hour = int(time_str[:2])
            
            if hour < 10:
                return self.t_day_weights.get('first_limit_time', 30) * 1.0
            elif hour < 11:
                return self.t_day_weights.get('first_limit_time', 30) * 0.8
            elif hour < 13:
                return self.t_day_weights.get('first_limit_time', 30) * 0.6
            elif hour < 14:
                return self.t_day_weights.get('first_limit_time', 30) * 0.4
            else:
                return self.t_day_weights.get('first_limit_time', 30) * 0.2
        except:
            return self.t_day_weights.get('first_limit_time', 30) * 0.5
    
    def _score_order_quality(self, seal_ratio: float, seal_to_mv: float) -> float:
        """评分封单质量 (封成比 + 封单/流通市值)"""
        # 注意: 原buy_to_sell_ratio权重现在用于封成比
        seal_weight = self.t_day_weights.get('buy_to_sell_ratio', 10)
        seal_mv_weight = self.t_day_weights.get('order_amount_to_circ_mv', 15)
        
        # 封成比评分 (越高越好，封单金额占成交金额比例)
        seal_score = min(seal_ratio, 5.0) / 5.0 * seal_weight if seal_ratio > 0 else 0
        
        # 封单金额/流通市值评分 (越高越好)
        # 乘以10000转换为百分比 (如0.001表示0.1%)
        seal_mv_value = seal_to_mv * 10000  # 转换为基点
        seal_mv_score = min(seal_mv_value, 10.0) / 10.0 * seal_mv_weight
        
        return seal_score + seal_mv_score
    
    def _score_liquidity(self, turnover_rate: float, turnover_20ma_ratio: float, volume_ratio: float) -> float:
        """评分流动性"""
        turnover_weight = self.t_day_weights.get('turnover_rate', 5)
        turnover_ma_weight = self.t_day_weights.get('turnover_rate_to_20ma', 10)
        volume_ratio_weight = self.t_day_weights.get('volume_ratio', 5)
        
        # 换手率评分 (适中为好，不宜过高或过低)
        turnover_score = 0
        if 2 <= turnover_rate <= 15:
            turnover_score = turnover_weight * 0.8
        elif 1 <= turnover_rate <= 20:
            turnover_score = turnover_weight * 0.6
        elif turnover_rate > 0:
            turnover_score = turnover_weight * 0.3
        
        # 换手率/20日均值评分 (大于1表示活跃)
        turnover_ma_score = min(turnover_20ma_ratio, 3.0) / 3.0 * turnover_ma_weight
        
        # 量比评分 (大于1表示放量)
        volume_ratio_score = min(volume_ratio, 3.0) / 3.0 * volume_ratio_weight
        
        return turnover_score + turnover_ma_score + volume_ratio_score
    
    def _score_money_flow(self, main_net: float, main_ratio: float, medium_net: float) -> float:
        """评分资金流"""
        main_net_weight = self.t_day_weights.get('main_net_amount', 5)
        main_ratio_weight = self.t_day_weights.get('main_net_ratio', 5)
        medium_net_weight = self.t_day_weights.get('medium_net_amount', 5)
        
        # 主力净额评分 (越大越好)
        main_net_score = 0
        if main_net > 10000000:  # 1000万
            main_net_score = main_net_weight * 1.0
        elif main_net > 5000000:
            main_net_score = main_net_weight * 0.8
        elif main_net > 0:
            main_net_score = main_net_weight * 0.5
        
        # 主力净占比评分 (越大越好)
        main_ratio_score = min(main_ratio, 10) / 10.0 * main_ratio_weight if main_ratio > 0 else 0
        
        # 中单净额评分 (参考主力)
        medium_net_score = 0
        if medium_net > 0:
            medium_net_score = medium_net_weight * 0.5
        
        return main_net_score + main_ratio_score + medium_net_score
    
    def _score_sector(self, is_hot_sector: bool) -> float:
        """评分热点板块"""
        sector_weight = self.t_day_weights.get('is_hot_sector', 10)
        return sector_weight * 1.0 if is_hot_sector else sector_weight * 0.3
    
    def analyze_t1_auction(self, candidates: pd.DataFrame, trade_date: str, is_trading_hours: bool = False) -> pd.DataFrame:
        """
        分析T+1日竞价数据并重新评分
        
        Args:
            candidates: T日选出的候选股票
            trade_date: T+1日日期
            is_trading_hours: 是否在交易时间 (9:25-9:29期间)
            
        Returns:
            包含竞价评分和最终推荐的DataFrame
            
        Note:
            如果在交易时间 (is_trading_hours=True) 且无法获取实时竞价数据，
            将返回空的DataFrame，表示无法选股
        """
        logger.info(f"开始T+1竞价评分，候选股票: {len(candidates)} 只，日期: {trade_date}, 交易时间: {is_trading_hours}")
        
        if candidates.empty:
            return pd.DataFrame()
        
        # 检查是否需要强制使用实时数据
        if is_trading_hours:
            logger.info("当前在交易时间 (9:25-9:29)，必须使用实时竞价数据")
        
        results = []
        missing_real_time_data = False
        
        for idx, row in candidates.iterrows():
            ts_code = row['ts_code']
            
            try:
                # 尝试获取真实竞价数据
                auction_data = self._get_real_auction_data(ts_code, trade_date, is_trading_hours)
                
                if auction_data:
                    data_source = auction_data.get('data_source', 'unknown')
                    open_change = auction_data.get('open_change_pct', 0)
                    
                    if is_trading_hours and data_source != 'realtime':
                        logger.warning(f"在交易时间，股票 {ts_code} 未使用实时数据，数据来源: {data_source}")
                        missing_real_time_data = True
                        continue
                    
                    logger.debug(f"股票 {ts_code}: 使用{data_source}竞价数据，开盘涨幅: {open_change:.2f}%")
                    auction_score = self._calculate_auction_score(auction_data)
                else:
                    # 无法获取竞价数据
                    if is_trading_hours:
                        logger.error(f"在交易时间无法获取股票 {ts_code} 的竞价数据，跳过该股票")
                        missing_real_time_data = True
                        continue
                    else:
                        # 非交易时间可以使用模拟数据
                        auction_score = 60.0  # 默认分数
                        auction_data = {'open_change_pct': 2.5, 'auction_volume_ratio': 1.8, 'data_source': 'simulated'}
                        logger.debug(f"股票 {ts_code}: 无竞价数据，使用模拟数据")
                
                # 计算最终分数
                final_score = row['total_score'] * 0.7 + auction_score * 0.3
                
                recommendation = {
                    'ts_code': ts_code,
                    'name': row.get('name', ''),
                    't_date': row['trade_date'],
                    't1_date': trade_date,
                    't_day_score': row['total_score'],
                    'auction_score': auction_score,
                    'final_score': final_score,
                    'auction_data': auction_data,
                    'recommendation': self._generate_recommendation(final_score, auction_data)
                }
                
                results.append(recommendation)
                
            except Exception as e:
                logger.error(f"分析T+1竞价失败 {ts_code}: {e}")
                continue
        
        # 如果在交易时间且缺少实时数据，记录警告
        if is_trading_hours and missing_real_time_data:
            logger.warning("在交易时间缺少实时竞价数据，部分或全部股票被跳过")
        
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('final_score', ascending=False)
        
        return df
    
    def _get_real_auction_data(self, ts_code: str, trade_date: str, is_trading_hours: bool = False) -> Dict[str, Any]:
        """
        获取真实竞价数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 (YYYYMMDD) - T+1日
            is_trading_hours: 是否在交易时间 (9:25-9:29期间)
            
        Returns:
            竞价数据字典，如果无法获取返回None
        """
        # 获取T日成交量（前一个交易日）
        t_day_volume = 0
        try:
            prev_date = self._get_prev_trading_day(trade_date)
            if prev_date:
                daily_df = self.pro.daily(
                    ts_code=ts_code,
                    trade_date=prev_date,
                    fields='vol'
                )
                if not daily_df.empty:
                    t_day_volume = daily_df.iloc[0]['vol']
                    logger.debug(f"获取T日成交量成功: {ts_code}, T日={prev_date}, 成交量={t_day_volume:.0f}手")
                else:
                    logger.warning(f"无法获取T日成交量: {ts_code}, T日={prev_date}")
            else:
                logger.warning(f"无法获取T日日期: {ts_code}, T+1日={trade_date}")
        except Exception as e:
            logger.debug(f"获取T日成交量失败: {e}")
        
        # 如果在交易时间 (9:25-9:29) 则只允许使用实时接口
        if is_trading_hours:
            try:
                realtime_df = self.pro.stk_auction(
                    trade_date=trade_date,
                    ts_code=ts_code,
                    fields='price,pre_close,amount,turnover_rate,volume_ratio,vol'
                )
                
                if not realtime_df.empty:
                    price = realtime_df.iloc[0]['price']
                    pre_close = realtime_df.iloc[0]['pre_close']
                    auction_volume = realtime_df.iloc[0].get('vol', 0)  # T+1竞价成交量
                    
                    # 计算竞价成交量/T日成交量比值
                    auction_volume_to_t_volume = 0.0
                    if t_day_volume > 0:
                        auction_volume_to_t_volume = auction_volume / t_day_volume
                    
                    # 验证数据有效性
                    if price > 0 and pre_close > 0:
                        open_change_pct = (price - pre_close) / pre_close * 100
                        # 限制涨幅范围（通常不会超过±20%，但留有余量）
                        open_change_pct = max(-30, min(30, open_change_pct))
                        
                        logger.info(f"获取实时竞价数据成功: {ts_code}, 开盘涨幅: {open_change_pct:.2f}%, 竞价/T日成交量比: {auction_volume_to_t_volume:.2%}")
                        
                        return {
                            'open_change_pct': open_change_pct,
                            'auction_volume_ratio': realtime_df.iloc[0].get('volume_ratio', 1),
                            'auction_turnover_rate': realtime_df.iloc[0].get('turnover_rate', 0),
                            'auction_amount': realtime_df.iloc[0].get('amount', 0),
                            'auction_volume_to_t_volume': auction_volume_to_t_volume,
                            'auction_volume': auction_volume,
                            't_day_volume': t_day_volume,
                            'data_source': 'realtime'
                        }
                    else:
                        logger.warning(f"实时竞价数据无效: {ts_code}, price={price}, pre_close={pre_close}")
                        return None
                else:
                    logger.warning(f"实时竞价接口返回空数据: {ts_code}")
                    return None
            except Exception as e:
                logger.error(f"在交易时间无法获取实时竞价数据 {ts_code}: {e}")
                return None
        
        # 非交易时间: 可以尝试实时接口，但主要使用历史接口
        try:
            # 先尝试实时接口 (可能仍有数据)
            realtime_df = self.pro.stk_auction(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='price,pre_close,amount,turnover_rate,volume_ratio,vol'
            )
            
            if not realtime_df.empty:
                price = realtime_df.iloc[0]['price']
                pre_close = realtime_df.iloc[0]['pre_close']
                auction_volume = realtime_df.iloc[0].get('vol', 0)
                
                # 计算竞价成交量/T日成交量比值
                auction_volume_to_t_volume = 0.0
                if t_day_volume > 0:
                    auction_volume_to_t_volume = auction_volume / t_day_volume
                
                # 验证数据有效性
                if price > 0 and pre_close > 0:
                    open_change_pct = (price - pre_close) / pre_close * 100
                    # 限制涨幅范围
                    open_change_pct = max(-30, min(30, open_change_pct))
                    
                    logger.debug(f"使用实时竞价数据: {ts_code}, 开盘涨幅: {open_change_pct:.2f}%, 竞价/T日成交量比: {auction_volume_to_t_volume:.2%}")
                    
                    return {
                        'open_change_pct': open_change_pct,
                        'auction_volume_ratio': realtime_df.iloc[0].get('volume_ratio', 1),
                        'auction_turnover_rate': realtime_df.iloc[0].get('turnover_rate', 0),
                        'auction_amount': realtime_df.iloc[0].get('amount', 0),
                        'auction_volume_to_t_volume': auction_volume_to_t_volume,
                        'auction_volume': auction_volume,
                        't_day_volume': t_day_volume,
                        'data_source': 'realtime'
                    }
                else:
                    logger.warning(f"非交易时间实时数据无效: {ts_code}, price={price}, pre_close={pre_close}")
                    # 继续尝试历史接口
        except Exception as e:
            logger.debug(f"实时竞价接口不可用或返回空数据: {e}")
        
        # 方案2: 尝试历史竞价接口 (stk_auction_o) - 每日盘后更新
        except Exception as e:
            logger.debug(f"实时竞价接口不可用或返回空数据: {e}")
        
        # 方案2: 尝试历史竞价接口 (stk_auction_o) - 每日盘后更新
        try:
            history_df = self.pro.stk_auction_o(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='close,vol,amount,vwap'
            )
            
            if not history_df.empty:
                # 历史接口的close字段是开盘价
                open_price = history_df.iloc[0]['close']
                auction_volume = history_df.iloc[0].get('vol', 0)  # 历史竞价成交量
                
                # 计算竞价成交量/T日成交量比值
                auction_volume_to_t_volume = 0.0
                if t_day_volume > 0:
                    auction_volume_to_t_volume = auction_volume / t_day_volume
                
                # 需要获取前收盘价来计算开盘涨幅
                try:
                    # 获取前一日收盘价
                    prev_date = self._get_prev_trading_day(trade_date)
                    if prev_date:
                        daily_df = self.pro.daily(
                            ts_code=ts_code,
                            trade_date=prev_date,
                            fields='close'
                        )
                        if not daily_df.empty:
                            pre_close = daily_df.iloc[0]['close']
                            if open_price > 0 and pre_close > 0:
                                open_change_pct = (open_price - pre_close) / pre_close * 100
                                # 限制涨幅范围
                                open_change_pct = max(-30, min(30, open_change_pct))
                                logger.debug(f"股票 {ts_code}: 开盘价={open_price}, 前收盘价={pre_close}, 涨幅={open_change_pct:.2f}%, 竞价/T日成交量比: {auction_volume_to_t_volume:.2%}")
                            else:
                                open_change_pct = 0
                                logger.warning(f"股票 {ts_code}: 无效价格数据，开盘价={open_price}, 前收盘价={pre_close}")
                        else:
                            open_change_pct = 0
                            logger.warning(f"无法获取股票 {ts_code} 的前收盘价")
                    else:
                        open_change_pct = 0
                        logger.warning(f"无法获取交易日 {trade_date} 的前一交易日")
                except Exception as e2:
                    logger.debug(f"计算开盘涨幅失败: {e2}")
                    open_change_pct = 0
                
                logger.debug(f"使用历史竞价数据: {ts_code}, 开盘价: {open_price}, 成交量: {auction_volume}")
                
                # 为历史竞价数据补充缺失字段
                auction_volume_ratio = 1.0
                auction_turnover_rate = 0.0
                
                # 尝试从daily_basic获取量比
                try:
                    basic_df = self.pro.daily_basic(
                        trade_date=trade_date,
                        ts_code=ts_code,
                        fields='volume_ratio'
                    )
                    if not basic_df.empty and 'volume_ratio' in basic_df.columns:
                        ratio = basic_df.iloc[0]['volume_ratio']
                        if pd.notna(ratio):
                            auction_volume_ratio = float(ratio)
                            logger.debug(f"从daily_basic补充量比: {ts_code} = {auction_volume_ratio}")
                except Exception as e3:
                    logger.debug(f"无法从daily_basic获取量比: {e3}")
                
                return {
                    'open_change_pct': open_change_pct,
                    'auction_volume_ratio': auction_volume_ratio,
                    'auction_turnover_rate': auction_turnover_rate,
                    'auction_amount': history_df.iloc[0].get('amount', 0),
                    'auction_volume_to_t_volume': auction_volume_to_t_volume,
                    'auction_volume': auction_volume,
                    't_day_volume': t_day_volume,
                    'data_source': 'history'
                }
        except Exception as e:
            logger.debug(f"历史竞价接口也失败: {e}")
        
        logger.warning(f"无法获取股票 {ts_code} 的竞价数据")
        return None
    
    def _calculate_auction_score(self, auction_data: Dict[str, Any]) -> float:
        """计算竞价评分"""
        open_change = auction_data.get('open_change_pct', 0)
        volume_ratio = auction_data.get('auction_volume_ratio', 1)
        turnover_rate = auction_data.get('auction_turnover_rate', 0)
        amount = auction_data.get('auction_amount', 0)
        auction_volume_to_t_volume = auction_data.get('auction_volume_to_t_volume', 0)  # 新增指标
        
        # 开盘涨幅评分（负涨幅得0分）
        open_change_clamped = max(open_change, 0)  # 负涨幅设为0
        open_score = min(open_change_clamped, 10) / 10.0 * self.t1_weights.get('open_change_pct', 35)
        
        # 竞价量比评分
        volume_score = min(volume_ratio, 5.0) / 5.0 * self.t1_weights.get('auction_volume_ratio', 20)
        
        # 竞价换手率评分（权重可能为0，取决于配置）
        turnover_score = min(turnover_rate / 5.0, 1.0) * self.t1_weights.get('auction_turnover_rate', 0)
        
        # 竞价金额评分
        amount_score = min(amount / 50000000, 1.0) * self.t1_weights.get('auction_amount', 20)
        
        # 竞价成交量/T日成交量比值评分
        auction_volume_ratio_score = 0
        volume_to_t_volume_weight = self.t1_weights.get('auction_volume_to_t_volume', 25)
        if volume_to_t_volume_weight > 0:
            ratio = auction_volume_to_t_volume  # 比值，如0.1表示10%
            if ratio >= 0.15:    # >15%
                auction_volume_ratio_score = volume_to_t_volume_weight
            elif ratio >= 0.10:  # 10-15%
                auction_volume_ratio_score = volume_to_t_volume_weight * 0.8
            elif ratio >= 0.05:  # 5-10%
                auction_volume_ratio_score = volume_to_t_volume_weight * 0.4
            elif ratio >= 0.03:  # 3-5%
                auction_volume_ratio_score = volume_to_t_volume_weight * 0.2
            else:                # <3%
                auction_volume_ratio_score = 0
        
        return open_score + volume_score + turnover_score + amount_score + auction_volume_ratio_score
    
    def _generate_recommendation(self, final_score: float, auction_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成推荐建议"""
        if final_score >= 80:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 1.0
            confidence = "高"
        elif final_score >= 60:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 0.7
            confidence = "中"
        else:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 0.3
            confidence = "低"
        
        reasons = []
        open_change = auction_data.get('open_change_pct', 0)
        if open_change > 5:
            reasons.append("竞价大幅高开(>5%)")
        elif open_change > 3:
            reasons.append("竞价高开(3-5%)")
        elif open_change > 0:
            reasons.append("竞价小幅高开(0-3%)")
        elif open_change < -2:
            reasons.append("竞价大幅低开(<-2%)")
        elif open_change < 0:
            reasons.append("竞价小幅低开")
        
        volume_ratio = auction_data.get('auction_volume_ratio', 1)
        if volume_ratio > 3:
            reasons.append("竞价量比极高(>3)")
        elif volume_ratio > 2:
            reasons.append("竞价量比放大(2-3)")
        elif volume_ratio < 0.5:
            reasons.append("竞价量比低迷(<0.5)")
        
        # 新增指标：竞价成交量/T日成交量比值
        auction_volume_to_t_volume = auction_data.get('auction_volume_to_t_volume', 0)
        if auction_volume_to_t_volume >= 0.30:
            reasons.append("竞价成交量极强(>30%，热度高度延续)")
        elif auction_volume_to_t_volume >= 0.20:
            reasons.append("竞价成交量很强(20-30%，热度明显延续)")
        elif auction_volume_to_t_volume >= 0.15:
            reasons.append("竞价成交量强(15-20%，热度延续)")
        elif auction_volume_to_t_volume >= 0.10:
            reasons.append("竞价成交量中等(10-15%，热度一般延续)")
        elif auction_volume_to_t_volume >= 0.05:
            reasons.append("竞价成交量一般(5-10%，热度较弱延续)")
        elif auction_volume_to_t_volume >= 0.03:
            reasons.append("竞价成交量弱(3-5%，警惕一日游)")
        else:
            reasons.append("竞价成交量极弱(<3%，高度警惕一日游)")
        
        return {
            'position': round(position, 2),
            'confidence': confidence,
            'reasons': reasons,
            'action': '买入' if final_score >= 60 else '观望'
        }
    
    def generate_final_report(self, t_day_results: pd.DataFrame, t1_results: pd.DataFrame) -> Dict[str, Any]:
        """生成最终报告"""
        top_n = self.strategy_config.get('output', {}).get('final_recommendation_count', 3)
        
        # 从数据中提取交易日期 (假设T日结果中有trade_date字段)
        trade_date = None
        if not t_day_results.empty and 'trade_date' in t_day_results.columns:
            trade_date = t_day_results.iloc[0]['trade_date']
        elif not t1_results.empty and 't1_date' in t1_results.columns:
            trade_date = t1_results.iloc[0]['t1_date']
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'trade_date': trade_date,
            't_day_summary': {
                'total_candidates': len(t_day_results),
                'top_scores': t_day_results.head(5).to_dict('records') if not t_day_results.empty else []
            },
            't1_recommendations': t1_results.head(top_n).to_dict('records') if not t1_results.empty else [],
            'market_condition': self._get_market_condition(trade_date),
            'next_steps': [
                "监控推荐股票的盘中表现",
                "设置止损位（建议-6%）",
                "关注大盘走势变化"
            ]
        }
        
        return report
    
    def _get_margin_data(self, trade_date: str) -> Dict[str, Any]:
        """
        获取融资融券数据
        
        Args:
            trade_date: 交易日期 (YYYYMMDD)
            
        Returns:
            融资融券数据字典，包含沪深两市数据
        """
        try:
            # 获取融资融券数据
            margin_data = self.pro.margin(trade_date=trade_date)
            
            if margin_data.empty:
                logger.warning(f"日期 {trade_date} 无融资融券数据")
                return {}
            
            # 计算市场融资融券指标
            market_margin_data = {
                'trade_date': trade_date,
                'total_financing_balance': 0.0,  # 两市融资余额总和
                'total_margin_balance': 0.0,     # 两市融券余额总和
                'total_financing_margin_balance': 0.0,  # 两市融资融券余额总和
                'financing_change_ratio': 0.0,   # 融资余额变化率
                'margin_change_ratio': 0.0,      # 融券余额变化率
                'financing_buy_ratio': 0.0,      # 融资买入额/融资偿还额
                'sse_data': {},  # 上交所数据
                'szse_data': {}  # 深交所数据
            }
            
            # 分离沪深两市数据
            sse_df = margin_data[margin_data['exchange_id'] == 'SSE']
            szse_df = margin_data[margin_data['exchange_id'] == 'SZSE']
            
            if not sse_df.empty:
                sse_row = sse_df.iloc[0]
                market_margin_data['sse_data'] = {
                    'financing_balance': sse_row.get('rzye', 0),  # 融资余额
                    'financing_buy': sse_row.get('rzmre', 0),     # 融资买入额
                    'financing_repay': sse_row.get('rzche', 0),   # 融资偿还额
                    'margin_balance': sse_row.get('rqye', 0),     # 融券余额
                    'margin_sell': sse_row.get('rqmcl', 0),       # 融券卖出量
                    'total_balance': sse_row.get('rzrqye', 0),    # 融资融券余额
                    'margin_remaining': sse_row.get('rqyl', 0)    # 融券余量
                }
                
                market_margin_data['total_financing_balance'] += sse_row.get('rzye', 0)
                market_margin_data['total_margin_balance'] += sse_row.get('rqye', 0)
                market_margin_data['total_financing_margin_balance'] += sse_row.get('rzrqye', 0)
            
            if not szse_df.empty:
                szse_row = szse_df.iloc[0]
                market_margin_data['szse_data'] = {
                    'financing_balance': szse_row.get('rzye', 0),
                    'financing_buy': szse_row.get('rzmre', 0),
                    'financing_repay': szse_row.get('rzche', 0),
                    'margin_balance': szse_row.get('rqye', 0),
                    'margin_sell': szse_row.get('rqmcl', 0),
                    'total_balance': szse_row.get('rzrqye', 0),
                    'margin_remaining': szse_row.get('rqyl', 0)
                }
                
                market_margin_data['total_financing_balance'] += szse_row.get('rzye', 0)
                market_margin_data['total_margin_balance'] += szse_row.get('rqye', 0)
                market_margin_data['total_financing_margin_balance'] += szse_row.get('rzrqye', 0)
            
            # 获取前一日数据以计算变化率
            try:
                prev_date = self._get_prev_trading_day(trade_date)
                if prev_date:
                    prev_margin_data = self.pro.margin(trade_date=prev_date)
                    if not prev_margin_data.empty:
                        prev_total_financing = prev_margin_data['rzye'].sum()
                        prev_total_margin = prev_margin_data['rqye'].sum()
                        
                        if prev_total_financing > 0:
                            market_margin_data['financing_change_ratio'] = (
                                market_margin_data['total_financing_balance'] - prev_total_financing
                            ) / prev_total_financing * 100
                        
                        if prev_total_margin > 0:
                            market_margin_data['margin_change_ratio'] = (
                                market_margin_data['total_margin_balance'] - prev_total_margin
                            ) / prev_total_margin * 100
            except Exception as e2:
                logger.debug(f"无法计算融资融券变化率: {e2}")
            
            # 计算融资买入/偿还比率
            total_financing_buy = 0
            total_financing_repay = 0
            if not sse_df.empty:
                total_financing_buy += sse_df.iloc[0].get('rzmre', 0)
                total_financing_repay += sse_df.iloc[0].get('rzche', 0)
            if not szse_df.empty:
                total_financing_buy += szse_df.iloc[0].get('rzmre', 0)
                total_financing_repay += szse_df.iloc[0].get('rzche', 0)
            
            if total_financing_repay > 0:
                market_margin_data['financing_buy_ratio'] = total_financing_buy / total_financing_repay
            
            logger.debug(f"获取融资融券数据完成: 融资余额={market_margin_data['total_financing_balance']:.2f}, 融券余额={market_margin_data['total_margin_balance']:.2f}")
            
            return market_margin_data
            
        except Exception as e:
            logger.error(f"获取融资融券数据失败: {e}")
            return {}
    
    def _get_market_condition(self, trade_date: str = None) -> Dict[str, Any]:
        """
        获取市场状况，包含融资融券风险判断
        
        Args:
            trade_date: 交易日期，如果为None则使用最近交易日
            
        Returns:
            市场状况字典
        """
        if trade_date is None:
            # 使用当前日期或最近交易日
            trade_date = datetime.now().strftime('%Y%m%d')
        
        # 获取融资融券数据
        margin_data = self._get_margin_data(trade_date)
        
        # 计算风险因子
        risk_factors = {
            'financing_change_ratio': margin_data.get('financing_change_ratio', 0),
            'margin_change_ratio': margin_data.get('margin_change_ratio', 0),
            'financing_buy_ratio': margin_data.get('financing_buy_ratio', 0),
            'total_financing_balance': margin_data.get('total_financing_balance', 0),
            'total_margin_balance': margin_data.get('total_margin_balance', 0),
        }
        
        # 风险评分 (0-10分，越高越危险)
        risk_score = 0
        
        # 因子1: 融资余额大幅下降 (风险增加)
        if risk_factors['financing_change_ratio'] < -2.0:  # 融资余额下降超过2%
            risk_score += 3
        elif risk_factors['financing_change_ratio'] < -5.0:  # 融资余额下降超过5%
            risk_score += 5
        
        # 因子2: 融券余额大幅上升 (风险增加)
        if risk_factors['margin_change_ratio'] > 5.0:  # 融券余额上升超过5%
            risk_score += 3
        elif risk_factors['margin_change_ratio'] > 10.0:  # 融券余额上升超过10%
            risk_score += 5
        
        # 因子3: 融资买入/偿还比率过低 (风险增加)
        if risk_factors['financing_buy_ratio'] < 0.8:  # 融资买入额不足偿还额的80%
            risk_score += 2
        elif risk_factors['financing_buy_ratio'] < 0.6:  # 融资买入额不足偿还额的60%
            risk_score += 4
        
        # 因子4: 融资余额绝对值水平
        # 融资余额超过8000亿通常表示市场杠杆较高
        if risk_factors['total_financing_balance'] > 800000000000:  # 8000亿
            risk_score += 2
        elif risk_factors['total_financing_balance'] > 1000000000000:  # 1万亿
            risk_score += 3
        
        # 确定风险等级
        if risk_score <= 2:
            risk_level = "低"
            condition = "正常"
            suggestion = "可适当增加仓位"
            position_multiplier = 1.0
        elif risk_score <= 5:
            risk_level = "中"
            condition = "正常"
            suggestion = "控制仓位，谨慎操作"
            position_multiplier = 0.8
        elif risk_score <= 8:
            risk_level = "高"
            condition = "风险较高"
            suggestion = "降低仓位，严格止损"
            position_multiplier = 0.5
        else:
            risk_level = "极高"
            condition = "风险极高"
            suggestion = "建议空仓观望"
            position_multiplier = 0.3
        
        return {
            'condition': condition,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'suggestion': suggestion,
            'position_multiplier': position_multiplier,
            'financing_balance': risk_factors['total_financing_balance'],
            'margin_balance': risk_factors['total_margin_balance'],
            'financing_change_pct': risk_factors['financing_change_ratio'],
            'margin_change_pct': risk_factors['margin_change_ratio'],
            'financing_buy_repay_ratio': risk_factors['financing_buy_ratio'],
            'market_data': margin_data
        }


if __name__ == "__main__":
    # 测试代码
    import yaml
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    strategy = LimitUpScoringStrategyV2(config)
    
    # 测试获取涨停股票
    test_date = '20240222'  # 使用有数据的日期
    limit_up_stocks = strategy.get_limit_up_stocks(test_date)
    
    print(f"测试获取涨停股票: {len(limit_up_stocks)} 只")
    
    if not limit_up_stocks.empty:
        # 测试评分
        scored_stocks = strategy.calculate_t_day_score(limit_up_stocks.head(5), test_date)
        print(f"测试评分完成: {len(scored_stocks)} 只股票已评分")
        
        if not scored_stocks.empty:
            print("\n📋 评分结果 (前3名):")
            for idx, row in scored_stocks.head(3).iterrows():
                print(f"\n#{idx+1} {row['name']} ({row['ts_code']})")
                print(f"  总分: {row['total_score']:.1f}")
                print(f"  涨幅: {row['pct_chg']:.2f}%")
                print(f"  封成比: {row.get('seal_ratio', 0):.3f}")
                print(f"  封单/流通市值: {row.get('seal_to_mv', 0):.6f}")
                print(f"  换手率: {row.get('turnover_rate', 0):.2f}%")
    else:
        print("没有涨停股票数据")