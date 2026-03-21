#!/usr/bin/env python3
"""
T01 龙头战法调度器 - PostgreSQL + TimescaleDB 版本
支持完整数据保存和时间旅行查询
"""

import os
import sys
import yaml
import json
import logging
import argparse
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from limit_up_strategy_new import LimitUpScoringStrategyV2 as LimitUpScoringStrategy
from output_formatter import OutputFormatter
from postgres_storage import T01PostgresStorage


class T01SchedulerPostgres:
    """T01 PostgreSQL 调度器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """初始化调度器"""
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # 初始化策略
        self.strategy = LimitUpScoringStrategy(self.config)
        
        # 初始化 PostgreSQL 存储
        self.pg_storage = T01PostgresStorage(config_path)
        
        # 状态目录
        self.state_dir = Path(self.config.get('storage', {}).get('state_dir', './state'))
        self.state_dir.mkdir(exist_ok=True)
        
        self.logger.info("T01 PostgreSQL 调度器初始化完成")
    
    def _load_config(self) -> dict:
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """配置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 't01_scheduler.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding='utf-8')
            ]
        )
        return logging.getLogger(__name__)
    
    def get_trade_date(self, offset: int = 0) -> str:
        """获取交易日期"""
        import tushare as ts
        
        today = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        pro = ts.pro_api()
        cal = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=today)
        trade_dates = cal[cal['is_open'] == 1]['cal_date'].tolist()
        
        if offset < 0 and abs(offset) <= len(trade_dates):
            return trade_dates[offset]
        
        return trade_dates[0] if trade_dates else today
    
    def run_t_day_scoring(self, trade_date: str = None) -> dict:
        """运行T日涨停股评分"""
        if trade_date is None:
            trade_date = self.get_trade_date(offset=0)
        
        self.logger.info(f"开始T日涨停股评分 (日期: {trade_date})")
        
        try:
            # 获取涨停股票
            limit_up_stocks = self.strategy.get_limit_up_stocks(trade_date)
            
            if limit_up_stocks.empty:
                self.logger.warning(f"日期 {trade_date} 没有涨停股票")
                return {'success': False, 'error': f"日期 {trade_date} 没有涨停股票", 'trade_date': trade_date}
            
            self.logger.info(f"获取到 {len(limit_up_stocks)} 只涨停股票")
            
            # 计算评分
            scored_stocks = self.strategy.calculate_t_day_score(limit_up_stocks, trade_date)
            
            if scored_stocks.empty:
                self.logger.warning("评分失败，没有有效结果")
                return {'success': False, 'error': "评分失败", 'trade_date': trade_date}
            
            self.logger.info(f"成功评分 {len(scored_stocks)} 只股票")
            
            # 选择前N名候选
            top_n = self.config['strategy']['output'].get('top_n_candidates', 10)
            candidates = scored_stocks.head(top_n).copy()
            
            # 准备结果
            result = {
                'success': True,
                'trade_date': trade_date,
                'candidates': candidates.to_dict('records'),
                'summary': {
                    'total_limit_up': len(limit_up_stocks),
                    'total_scored': len(scored_stocks),
                    'top_n_selected': len(candidates),
                    'top_score': candidates.iloc[0]['total_score'] if not candidates.empty else 0,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
            # 保存到 PostgreSQL
            self._save_to_postgresql(result)
            
            # 保存候选股票用于T+1日分析
            self._save_candidates_for_t1(result)
            
            # 获取并保存风控数据
            self._save_risk_control_data(trade_date)
            
            self.logger.info("✅ T日评分完成")
            return result
            
        except Exception as e:
            self.logger.error(f"T日评分失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'trade_date': trade_date}
    
    def _save_to_postgresql(self, result: dict):
        """保存推荐数据到 PostgreSQL"""
        try:
            if not result.get('success'):
                return
            
            trade_date = result['trade_date']
            candidates = result.get('candidates', [])
            
            saved_count = 0
            for candidate in candidates:
                try:
                    # 添加T+1日期
                    try:
                        t1_date = self.strategy._get_next_trading_day(trade_date)
                    except:
                        t1_date = trade_date
                    
                    candidate['t1_date'] = t1_date
                    self.pg_storage.save_t_day_recommendation(candidate)
                    saved_count += 1
                except Exception as e:
                    self.logger.warning(f"保存单个推荐失败: {e}")
                    continue
            
            self.logger.info(f"已保存 {saved_count} 个推荐到 PostgreSQL")
            
        except Exception as e:
            self.logger.error(f"保存到 PostgreSQL 失败: {e}")
    
    def _save_candidates_for_t1(self, result: dict):
        """保存候选股票用于T+1日分析"""
        try:
            if not result.get('success'):
                return
            
            trade_date = result['trade_date']
            
            # 获取T+1日期
            try:
                t1_date = self.strategy._get_next_trading_day(trade_date)
            except Exception as e:
                self.logger.warning(f"无法获取T+1日期: {e}")
                t1_date = trade_date
            
            # 保存为JSON文件（供T+1日使用）
            output_data = {
                't_date': trade_date,
                't1_date': t1_date,
                'candidates': result['candidates'],
                'generated_at': datetime.now().isoformat()
            }
            
            filename = self.state_dir / f"candidates_{trade_date}_to_{t1_date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"候选股票已保存: {filename}")
            
        except Exception as e:
            self.logger.error(f"保存候选股票失败: {e}")
    
    def _save_risk_control_data(self, trade_date: str):
        """保存风控数据"""
        try:
            # 获取融资融券数据
            risk_data = self.strategy._get_margin_data(trade_date)
            
            if risk_data:
                # 计算风险等级
                risk_score = 0
                if risk_data.get('financing_change_ratio', 0) < -2:
                    risk_score += 3
                if risk_data.get('margin_change_ratio', 0) > 5:
                    risk_score += 3
                if risk_data.get('financing_buy_ratio', 0) < 0.8:
                    risk_score += 2
                if risk_data.get('total_financing_balance', 0) > 800000000000:
                    risk_score += 2
                
                # 确定风险等级
                if risk_score >= 7:
                    risk_level = '高'
                    position_multiplier = 0.3
                elif risk_score >= 4:
                    risk_level = '中'
                    position_multiplier = 0.7
                else:
                    risk_level = '低'
                    position_multiplier = 1.0
                
                risk_data['risk_level'] = risk_level
                risk_data['risk_score'] = risk_score
                risk_data['position_multiplier'] = position_multiplier
                
                # 保存到 PostgreSQL
                self.pg_storage.save_risk_control_data(trade_date, risk_data)
                self.logger.info(f"风控数据已保存: {trade_date}, 风险等级: {risk_level}")
            
        except Exception as e:
            self.logger.error(f"保存风控数据失败: {e}")
    
    def run_t1_auction_analysis(self, trade_date: str = None) -> dict:
        """运行T+1日竞价分析"""
        if trade_date is None:
            trade_date = self.get_trade_date(offset=0)
        
        self.logger.info(f"开始T+1日竞价分析 (日期: {trade_date})")
        
        try:
            # 查找候选股票文件
            candidate_files = list(self.state_dir.glob(f"candidates_*_to_{trade_date}.json"))
            
            if not candidate_files:
                self.logger.warning(f"未找到 {trade_date} 的候选股票文件")
                return {'success': False, 'error': f"未找到候选股票文件", 'trade_date': trade_date}
            
            # 加载候选股票
            with open(candidate_files[0], 'r', encoding='utf-8') as f:
                candidates_data = json.load(f)
            
            candidates = candidates_data.get('candidates', [])
            t_date = candidates_data.get('t_date', trade_date)
            
            self.logger.info(f"分析 {len(candidates)} 只候选股票的竞价数据")
            
            # 分析竞价数据
            import pandas as pd
            candidates_df = pd.DataFrame(candidates)
            t1_results = self.strategy.analyze_t1_auction(candidates_df, trade_date)
            
            if t1_results.empty:
                self.logger.warning("竞价分析失败")
                return {'success': False, 'error': "竞价分析失败", 'trade_date': trade_date}
            
            # 保存竞价数据到 PostgreSQL
            self._save_auction_data(trade_date, t1_results)
            
            # 生成最终报告
            final_report = self.strategy.generate_final_report(candidates_df, t1_results)
            
            self.logger.info("✅ T+1日竞价分析完成")
            return {
                'success': True,
                'trade_date': trade_date,
                't_date': t_date,
                'results': final_report
            }
            
        except Exception as e:
            self.logger.error(f"T+1日竞价分析失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'trade_date': trade_date}
    
    def _save_auction_data(self, trade_date: str, t1_results):
        """保存竞价数据"""
        try:
            for _, row in t1_results.iterrows():
                try:
                    ts_code = row.get('ts_code', '')
                    
                    auction_data = {
                        'open_price': row.get('open_price', 0),
                        'open_change_pct': row.get('open_change_pct', 0),
                        'volume_ratio': row.get('volume_ratio', 0),
                        'turnover_rate': row.get('turnover_rate', 0),
                        'amount': row.get('amount', 0),
                        'vol': row.get('vol', 0),
                        'pre_close': row.get('pre_close', 0),
                        'auction_score': row.get('auction_score', 0),
                    }
                    
                    # 保存竞价数据
                    self.pg_storage.save_auction_data(trade_date, ts_code, auction_data)
                    
                    # 计算竞价风控
                    auction_risk_score = 0
                    if auction_data['open_change_pct'] > 8:
                        auction_risk_score += 3
                    elif auction_data['open_change_pct'] < 2:
                        auction_risk_score += 2
                    
                    if auction_data['volume_ratio'] < 0.5:
                        auction_risk_score += 2
                    
                    if auction_risk_score >= 5:
                        auction_risk_level = '高'
                        position_adj = 0.5
                    elif auction_risk_score >= 3:
                        auction_risk_level = '中'
                        position_adj = 0.8
                    else:
                        auction_risk_level = '低'
                        position_adj = 1.0
                    
                    # 获取T日风控数据
                    try:
                        t_day_data = self.pg_storage.get_recommendation_as_of(
                            trade_date, ts_code, datetime.now()
                        )
                        base_position = t_day_data.get('position_multiplier', 1.0) if t_day_data else 1.0
                    except:
                        base_position = 1.0
                    
                    final_position = base_position * position_adj
                    
                    risk_data = {
                        'risk_level': auction_risk_level,
                        'risk_score': auction_risk_score,
                        'position_adjustment': position_adj,
                        'final_recommendation': '买入' if final_position > 0.5 else '观望',
                        'suggested_position': final_position
                    }
                    
                    self.pg_storage.update_auction_risk_data(trade_date, ts_code, risk_data)
                    
                except Exception as e:
                    self.logger.warning(f"保存竞价数据失败 {row.get('ts_code', '')}: {e}")
                    continue
            
            self.logger.info(f"竞价数据已保存: {len(t1_results)} 只股票")
            
        except Exception as e:
            self.logger.error(f"保存竞价数据失败: {e}")
    
    def run_full_pipeline(self, t_date: str = None, t1_date: str = None):
        """运行完整流程"""
        if t_date is None:
            t_date = self.get_trade_date(offset=-1)  # T日
        if t1_date is None:
            t1_date = self.get_trade_date(offset=0)   # T+1日
        
        self.logger.info(f"运行完整流程: T日={t_date}, T+1日={t1_date}")
        
        # T日评分
        t_day_result = self.run_t_day_scoring(t_date)
        
        if not t_day_result.get('success'):
            self.logger.error(f"T日评分失败: {t_day_result.get('error')}")
            return t_day_result
        
        # T+1日竞价分析
        t1_result = self.run_t1_auction_analysis(t1_date)
        
        return {
            't_day': t_day_result,
            't1_auction': t1_result,
            'success': True
        }
    
    def close(self):
        """关闭资源"""
        if self.pg_storage:
            self.pg_storage.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='T01 PostgreSQL 调度器')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--mode', choices=['t-day', 't1-auction', 'full'], default='t-day', help='运行模式')
    parser.add_argument('--date', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--t-date', help='T日日期')
    parser.add_argument('--t1-date', help='T+1日日期')
    
    args = parser.parse_args()
    
    scheduler = T01SchedulerPostgres(args.config)
    
    try:
        if args.mode == 't-day':
            result = scheduler.run_t_day_scoring(args.date)
        elif args.mode == 't1-auction':
            result = scheduler.run_t1_auction_analysis(args.date)
        else:
            result = scheduler.run_full_pipeline(args.t_date, args.t1_date)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    finally:
        scheduler.close()


if __name__ == "__main__":
    main()
