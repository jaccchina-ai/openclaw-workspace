#!/usr/bin/env python3
"""
涨停股评分策略
根据老板要求的因子对当日涨停股进行打分
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging
import tushare as ts

logger = logging.getLogger(__name__)


class LimitUpScoringStrategy:
    """涨停股评分策略"""
    
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
        
        logger.info("涨停股评分策略初始化完成")
    
    def get_limit_up_stocks(self, trade_date: str) -> pd.DataFrame:
        """
        获取当日涨停股票列表 - 使用limit_list_d接口
        
        Args:
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            DataFrame包含涨停股票基本信息
        """
        if not self.pro:
            logger.error("tushare未初始化")
            return pd.DataFrame()
        
        try:
            # 使用tushare获取涨停股票 - 使用limit_list_d接口
            limit_up_df = self.pro.limit_list_d(
                trade_date=trade_date,
                limit_type='U',  # 涨停
                fields='ts_code,trade_date,industry,name,close,pct_chg,amount,turnover_ratio,fd_amount,float_mv,total_mv,first_time,last_time,open_times,up_stat,limit_times'
            )
            
            logger.info(f"获取到 {len(limit_up_df)} 只涨停股票")
            return limit_up_df
            
        except Exception as e:
            logger.error(f"获取涨停股票失败 (limit_list_d): {e}")
            # 尝试备选接口
            return self._get_limit_up_stocks_fallback(trade_date)
    
    def _get_limit_up_stocks_fallback(self, trade_date: str) -> pd.DataFrame:
        """备选方法获取涨停股票"""
        try:
            # 使用日线数据筛选涨停股票
            daily_df = self.pro.daily(
                trade_date=trade_date,
                fields='ts_code,trade_date,close,pct_chg,amount'
            )
            
            # 筛选涨停股票 (涨幅>=9.8%)
            limit_up_df = daily_df[daily_df['pct_chg'] >= 9.8].copy()
            
            # 获取换手率数据
            basic_df = self.pro.daily_basic(
                trade_date=trade_date,
                fields='ts_code,turnover_rate'
            )
            
            # 合并数据
            if not limit_up_df.empty and not basic_df.empty:
                limit_up_df = pd.merge(limit_up_df, basic_df, on='ts_code', how='left')
            
            logger.info(f"备选方法获取到 {len(limit_up_df)} 只涨停股票")
            return limit_up_df
            
        except Exception as e:
            logger.error(f"备选方法也失败: {e}")
            return pd.DataFrame()
    
    def calculate_t_day_score(self, stock_data: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        计算T日涨停股评分
        
        Args:
            stock_data: 涨停股票基础数据
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
            
            # 获取股票代码
            ts_code = row['ts_code']
            
            try:
                # 1. 获取首次涨停时间 (需要分时数据)
                first_limit_time = self._get_first_limit_time(ts_code, trade_date)
                time_score = self._score_first_limit_time(first_limit_time)
                score_details['first_limit_time'] = time_score
                total_score += time_score
                
                # 2. 获取封单相关数据 (需要level2数据或龙虎榜)
                buy_sell_ratio = self._get_buy_sell_ratio(ts_code, trade_date)
                order_amount_to_mv = self._get_order_amount_to_mv(ts_code, trade_date)
                
                order_score = self._score_order_quality(buy_sell_ratio, order_amount_to_mv)
                score_details['order_quality'] = order_score
                total_score += order_score
                
                # 3. 流动性评分 (使用已有数据)
                turnover_rate = row.get('turnover_rate', 0)
                turnover_20ma_ratio = self._get_turnover_20ma_ratio(ts_code, trade_date)
                volume_ratio = self._get_volume_ratio(ts_code, trade_date)
                
                liquidity_score = self._score_liquidity(turnover_rate, turnover_20ma_ratio, volume_ratio)
                score_details['liquidity'] = liquidity_score
                total_score += liquidity_score
                
                # 4. 资金流评分
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
                
                # 收集结果
                result = {
                    'ts_code': ts_code,
                    'name': row.get('name', ''),
                    'trade_date': trade_date,
                    'close': row.get('close', 0),
                    'pct_chg': row.get('pct_chg', 0),
                    'total_score': total_score,
                    'score_details': score_details,
                    'first_limit_time': first_limit_time,
                    'buy_sell_ratio': buy_sell_ratio,
                    'order_amount_to_mv': order_amount_to_mv,
                    'turnover_rate': turnover_rate,
                    'turnover_20ma_ratio': turnover_20ma_ratio,
                    'volume_ratio': volume_ratio,
                    'main_net_amount': main_net,
                    'main_net_ratio': main_ratio,
                    'medium_net_amount': medium_net,
                    'is_hot_sector': is_hot_sector
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"评分股票 {ts_code} 时出错: {e}")
                continue
        
        # 转换为DataFrame并排序
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('total_score', ascending=False)
        
        return df
    
    def _get_first_limit_time(self, ts_code: str, trade_date: str) -> Optional[str]:
        """获取首次涨停时间 (需要实现具体API调用)"""
        # TODO: 实现获取首次涨停时间的逻辑
        # 可能使用tushare的stk_limit接口或其他分时数据接口
        logger.warning(f"首次涨停时间获取未实现: {ts_code}")
        return None
    
    def _get_buy_sell_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取分成比 (买一/卖一)"""
        # TODO: 实现获取分成比的逻辑
        # 可能需要level2数据
        logger.warning(f"分成比获取未实现: {ts_code}")
        return 0.0
    
    def _get_order_amount_to_mv(self, ts_code: str, trade_date: str) -> float:
        """获取封单金额/流通市值"""
        # TODO: 实现获取封单金额的逻辑
        logger.warning(f"封单金额/流通市值获取未实现: {ts_code}")
        return 0.0
    
    def _get_turnover_20ma_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取换手率/20日均换手率"""
        try:
            # 获取历史换手率数据
            end_date = trade_date
            start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=60)).strftime('%Y%m%d')
            
            hist_df = self.pro.daily(
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
        # TODO: 实现获取量比的逻辑
        # tushare可能有专门的量比接口
        logger.warning(f"量比获取未实现: {ts_code}")
        return 1.0
    
    def _get_main_net_amount(self, ts_code: str, trade_date: str) -> float:
        """获取主力净额"""
        # TODO: 实现获取主力净额的逻辑
        # 可能使用tushare的moneyflow接口
        logger.warning(f"主力净额获取未实现: {ts_code}")
        return 0.0
    
    def _get_main_net_ratio(self, ts_code: str, trade_date: str) -> float:
        """获取主力净占比"""
        # TODO: 实现获取主力净占比的逻辑
        logger.warning(f"主力净占比获取未实现: {ts_code}")
        return 0.0
    
    def _get_medium_net_amount(self, ts_code: str, trade_date: str) -> float:
        """获取中单净额"""
        # TODO: 实现获取中单净额的逻辑
        logger.warning(f"中单净额获取未实现: {ts_code}")
        return 0.0
    
    def _check_hot_sector(self, ts_code: str, trade_date: str) -> bool:
        """检查是否属于热点行业板块"""
        # TODO: 实现热点板块检查逻辑
        # 需要获取行业板块数据和热点判断
        logger.warning(f"热点板块检查未实现: {ts_code}")
        return False
    
    # 评分函数
    def _score_first_limit_time(self, first_limit_time: Optional[str]) -> float:
        """评分首次涨停时间 (越早越好)"""
        if not first_limit_time:
            return self.t_day_weights.get('first_limit_time', 30) * 0.5  # 缺省50%分数
        
        # 解析时间，计算分数
        # 简单实现：根据时间字符串判断
        try:
            hour = int(first_limit_time[:2])
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
    
    def _score_order_quality(self, buy_sell_ratio: float, order_amount_to_mv: float) -> float:
        """评分封单质量"""
        buy_sell_weight = self.t_day_weights.get('buy_to_sell_ratio', 10)
        order_mv_weight = self.t_day_weights.get('order_amount_to_circ_mv', 15)
        
        # 分成比评分 (越高越好)
        buy_sell_score = min(buy_sell_ratio, 10) / 10.0 * buy_sell_weight if buy_sell_ratio > 0 else 0
        
        # 封单金额/流通市值评分 (越高越好)
        order_mv_score = min(order_amount_to_mv * 100, 1.0) * order_mv_weight
        
        return buy_sell_score + order_mv_score
    
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
    
    def analyze_t1_auction(self, candidates: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        分析T+1日竞价数据并重新评分
        
        Args:
            candidates: T日选出的候选股票
            trade_date: T+1日日期
            
        Returns:
            包含竞价评分和最终推荐的DataFrame
        """
        if candidates.empty:
            return pd.DataFrame()
        
        results = []
        
        for idx, row in candidates.iterrows():
            ts_code = row['ts_code']
            
            try:
                # 获取竞价数据
                auction_data = self._get_auction_data(ts_code, trade_date)
                
                if not auction_data:
                    continue
                
                # 计算竞价评分
                auction_score = self._calculate_auction_score(auction_data)
                
                # 获取大盘指数位置
                index_position = self._get_index_position(trade_date)
                
                # 计算风险调整系数
                risk_adjustment = self._calculate_risk_adjustment(index_position)
                
                # 最终总分 = T日分数 * 风险系数 + 竞价分数
                final_score = row['total_score'] * risk_adjustment + auction_score
                
                # 生成推荐结果
                recommendation = {
                    'ts_code': ts_code,
                    'name': row.get('name', ''),
                    't_date': row['trade_date'],
                    't1_date': trade_date,
                    't_day_score': row['total_score'],
                    'auction_score': auction_score,
                    'risk_adjustment': risk_adjustment,
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
    
    def _get_auction_data(self, ts_code: str, trade_date: str) -> Dict[str, Any]:
        """获取竞价数据"""
        # TODO: 实现获取竞价数据的逻辑
        # 需要tushare的竞价数据接口
        logger.warning(f"竞价数据获取未实现: {ts_code}")
        return {}
    
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
        amount_score = min(amount / 50000000, 1.0) * self.t1_weights.get('auction_amount', 20)  # 5000万为满分
        
        return open_score + volume_score + turnover_score + amount_score
    
    def _get_index_position(self, trade_date: str) -> str:
        """获取大盘指数相对于5日均线的位置"""
        # TODO: 实现大盘指数位置判断
        logger.warning("大盘指数位置判断未实现")
        return "above"  # 默认在5日线上方
    
    def _calculate_risk_adjustment(self, index_position: str) -> float:
        """计算风险调整系数"""
        if index_position == "above":
            return self.risk_config.get('index_above_5ma_weight', 1.0)
        else:
            return self.risk_config.get('index_below_5ma_weight', 0.7)
    
    def _generate_recommendation(self, final_score: float, auction_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成推荐建议"""
        # 根据分数确定仓位
        if final_score >= 80:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 1.0
            confidence = "高"
        elif final_score >= 60:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 0.7
            confidence = "中"
        else:
            position = self.risk_config.get('max_position_per_stock', 0.2) * 0.3
            confidence = "低"
        
        # 生成理由
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
        # TODO: 实现市场状况分析
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
    
    strategy = LimitUpScoringStrategy(config)
    
    # 测试获取涨停股票
    test_date = datetime.now().strftime('%Y%m%d')
    limit_up_stocks = strategy.get_limit_up_stocks(test_date)
    
    print(f"测试获取涨停股票: {len(limit_up_stocks)} 只")
    
    if not limit_up_stocks.empty:
        # 测试评分
        scored_stocks = strategy.calculate_t_day_score(limit_up_stocks.head(3), test_date)
        print(f"测试评分完成: {len(scored_stocks)} 只股票已评分")