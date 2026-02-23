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
            # 1. 剔除ST股票 (name字段包含"ST")
            non_st_mask = ~limit_up_df['name'].str.contains('ST')
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
                logger.info(f"剔除ST股票: {st_count} 只")
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
        """获取换手率/20日均换手率"""
        try:
            # 获取历史换手率数据
            end_date = trade_date
            start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=60)).strftime('%Y%m%d')
            
            hist_df = self.pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='trade_date,turnover_rate'
            )
            
            if len(hist_df) >= 20:
                # 计算20日平均换手率
                turnover_20ma = hist_df['turnover_rate'].tail(20).mean()
                current_turnover = hist_df['turnover_rate'].iloc[-1] if not hist_df.empty else 0
                
                if turnover_20ma > 0:
                    return current_turnover / turnover_20ma
                
            return 1.0
            
        except Exception as e:
            logger.error(f"计算换手率20日均值失败: {e}")
            return 1.0
    
    def _get_volume_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取量比"""
        # 尝试从竞价数据获取
        try:
            auction_df = self.pro.stk_auction(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='volume_ratio'
            )
            
            if not auction_df.empty and 'volume_ratio' in auction_df.columns:
                ratio = auction_df.iloc[0]['volume_ratio']
                if pd.notna(ratio):
                    return float(ratio)
        except Exception as e:
            logger.debug(f"无法从竞价数据获取量比: {e}")
        
        # 备选方案: 计算当日成交量/5日平均成交量
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
                    return current_vol / avg_vol
        except Exception as e:
            logger.error(f"计算量比失败: {e}")
        
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
    
    # T+1竞价评分相关方法 (待完善)
    def analyze_t1_auction(self, candidates: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        分析T+1日竞价数据并重新评分
        
        Args:
            candidates: T日选出的候选股票
            trade_date: T+1日日期
            
        Returns:
            包含竞价评分和最终推荐的DataFrame
        """
        logger.warning("T+1竞价评分功能待完善 (竞价数据接口可能无法获取历史数据)")
        
        if candidates.empty:
            return pd.DataFrame()
        
        # 简单实现: 使用模拟数据或基础评分
        results = []
        
        for idx, row in candidates.iterrows():
            ts_code = row['ts_code']
            
            try:
                # 尝试获取真实竞价数据
                auction_data = self._get_real_auction_data(ts_code, trade_date)
                
                if auction_data:
                    auction_score = self._calculate_auction_score(auction_data)
                else:
                    # 使用模拟数据
                    auction_score = 60.0  # 默认分数
                    auction_data = {'open_change_pct': 2.5, 'auction_volume_ratio': 1.8}
                
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
        
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('final_score', ascending=False)
        
        return df
    
    def _get_real_auction_data(self, ts_code: str, trade_date: str) -> Dict[str, Any]:
        """获取真实竞价数据"""
        try:
            auction_df = self.pro.stk_auction(
                trade_date=trade_date,
                ts_code=ts_code,
                fields='price,pre_close,amount,turnover_rate,volume_ratio'
            )
            
            if not auction_df.empty:
                price = auction_df.iloc[0]['price']
                pre_close = auction_df.iloc[0]['pre_close']
                open_change_pct = (price - pre_close) / pre_close * 100 if pre_close > 0 else 0
                
                return {
                    'open_change_pct': open_change_pct,
                    'auction_volume_ratio': auction_df.iloc[0].get('volume_ratio', 1),
                    'auction_turnover_rate': auction_df.iloc[0].get('turnover_rate', 0),
                    'auction_amount': auction_df.iloc[0].get('amount', 0)
                }
        except Exception as e:
            logger.debug(f"无法获取真实竞价数据: {e}")
        
        return None
    
    def _calculate_auction_score(self, auction_data: Dict[str, Any]) -> float:
        """计算竞价评分"""
        open_change = auction_data.get('open_change_pct', 0)
        volume_ratio = auction_data.get('auction_volume_ratio', 1)
        turnover_rate = auction_data.get('auction_turnover_rate', 0)
        amount = auction_data.get('auction_amount', 0)
        
        # 开盘涨幅评分
        open_score = min(max(open_change, -10), 10) / 10.0 * self.t1_weights.get('open_change_pct', 40)
        
        # 竞价量比评分
        volume_score = min(volume_ratio, 5.0) / 5.0 * self.t1_weights.get('auction_volume_ratio', 20)
        
        # 竞价换手率评分
        turnover_score = min(turnover_rate / 5.0, 1.0) * self.t1_weights.get('auction_turnover_rate', 20)
        
        # 竞价金额评分
        amount_score = min(amount / 50000000, 1.0) * self.t1_weights.get('auction_amount', 20)
        
        return open_score + volume_score + turnover_score + amount_score
    
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
        if open_change > 3:
            reasons.append("竞价大幅高开")
        elif open_change > 0:
            reasons.append("竞价小幅高开")
        
        volume_ratio = auction_data.get('auction_volume_ratio', 1)
        if volume_ratio > 2:
            reasons.append("竞价量比显著放大")
        
        return {
            'position': round(position, 2),
            'confidence': confidence,
            'reasons': reasons,
            'action': '买入' if final_score >= 60 else '观望'
        }
    
    def generate_final_report(self, t_day_results: pd.DataFrame, t1_results: pd.DataFrame) -> Dict[str, Any]:
        """生成最终报告"""
        top_n = self.strategy_config.get('output', {}).get('final_recommendation_count', 3)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            't_day_summary': {
                'total_candidates': len(t_day_results),
                'top_scores': t_day_results.head(5).to_dict('records') if not t_day_results.empty else []
            },
            't1_recommendations': t1_results.head(top_n).to_dict('records') if not t1_results.empty else [],
            'market_condition': self._get_market_condition(),
            'next_steps': [
                "监控推荐股票的盘中表现",
                "设置止损位（建议-6%）",
                "关注大盘走势变化"
            ]
        }
        
        return report
    
    def _get_market_condition(self) -> Dict[str, Any]:
        """获取市场状况"""
        # 简单实现
        return {
            'condition': '正常',
            'risk_level': '中等',
            'suggestion': '控制仓位，谨慎操作'
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