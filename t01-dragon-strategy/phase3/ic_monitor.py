#!/usr/bin/env python3
"""
IC监控模块 - Information Coefficient Monitor
用于监控因子有效性，计算因子IC值并预警失效因子

IC值(信息系数)定义: 因子值与次日收益率的相关系数
IC值范围: -1 到 1
- |IC| > 0.1: 强预测能力
- 0.03 < |IC| < 0.1: 中等预测能力
- |IC| < 0.03: 弱预测能力(失效因子)
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ICResult:
    """IC计算结果数据类"""
    factor_name: str
    trade_date: str
    ic_value: float
    ic_window_20: Optional[float] = None
    ic_window_60: Optional[float] = None
    is_valid: bool = True  # |IC| >= 0.03
    trend: str = "stable"  # increasing, decreasing, stable
    trend_days: int = 0  # 趋势持续天数
    sample_size: int = 0  # 样本数量
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ICMonitorReport:
    """IC监控报告数据类"""
    report_date: str
    generated_at: str
    factors: List[ICResult]
    invalid_factors: List[str]  # 失效因子列表
    warning_factors: List[str]  # 预警因子列表(IC下降趋势)
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_date': self.report_date,
            'generated_at': self.generated_at,
            'factors': [f.to_dict() for f in self.factors],
            'invalid_factors': self.invalid_factors,
            'warning_factors': self.warning_factors,
            'summary': self.summary
        }


class ICMonitor:
    """IC监控器 - 计算和监控因子IC值"""
    
    # T01策略中的因子列表
    FACTORS = [
        'seal_ratio',           # 封成比
        'seal_to_mv',           # 封单/流通市值
        'turnover_rate',        # 换手率
        'turnover_20ma_ratio',  # 换手率/20日均量
        'volume_ratio',         # 量比
        'first_limit_time',     # 首次涨停时间
        'main_net_ratio',       # 主力净流入比例
        'medium_net_ratio',     # 中单净流入比例
        'dragon_score',         # 龙头得分
        'is_hot_sector',        # 是否热点板块
    ]
    
    # IC失效阈值
    IC_INVALID_THRESHOLD = 0.03
    
    # IC趋势下降阈值(连续下降天数)
    TREND_DAYS_THRESHOLD = 5
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化IC监控器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化Tushare API
        api_key = self.config.get('api', {}).get('api_key', '')
        if api_key:
            ts.set_token(api_key)
            self.pro = ts.pro_api()
        else:
            logger.error("Tushare API key未配置")
            self.pro = None
        
        # 数据存储路径
        self.data_dir = Path('data/ic_monitor')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # IC历史数据文件
        self.ic_history_file = self.data_dir / 'ic_history.json'
        
        # 加载IC历史数据
        self.ic_history = self._load_ic_history()
        
        logger.info(f"IC监控器初始化完成，监控{len(self.FACTORS)}个因子")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {'api': {'api_key': ''}}
    
    def _load_ic_history(self) -> Dict[str, List[Dict]]:
        """加载IC历史数据"""
        if self.ic_history_file.exists():
            try:
                with open(self.ic_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载IC历史数据失败: {e}")
        return {factor: [] for factor in self.FACTORS}
    
    def _save_ic_history(self):
        """保存IC历史数据"""
        try:
            with open(self.ic_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.ic_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存IC历史数据失败: {e}")
    
    def _get_prev_trading_day(self, trade_date: str) -> Optional[str]:
        """获取前一个交易日"""
        try:
            # 查询前30天的交易日历
            start_date = (datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
            cal = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=trade_date)
            
            if cal.empty:
                return None
            
            # 按日期降序排列
            cal = cal.sort_values('cal_date', ascending=False)
            
            # 找到当前日期的前一个交易日
            for i, row in cal.iterrows():
                if row['cal_date'] == trade_date and i > 0:
                    prev_row = cal.iloc[i+1] if i+1 < len(cal) else None
                    if prev_row is not None and prev_row['is_open'] == 1:
                        return prev_row['cal_date']
            
            # 如果没找到，返回最近的交易日
            trade_days = cal[cal['is_open'] == 1]['cal_date'].tolist()
            if len(trade_days) >= 2:
                return trade_days[1]  # 第二个是前一个交易日
                
        except Exception as e:
            logger.error(f"获取前一交易日失败: {e}")
        
        return None
    
    def _get_stock_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame with columns: trade_date, open, high, low, close, pct_chg
        """
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if not df.empty:
                df = df.sort_values('trade_date')
            return df
        except Exception as e:
            logger.warning(f"获取股票{ts_code}日线数据失败: {e}")
            return pd.DataFrame()
    
    def _get_next_day_return(self, ts_code: str, trade_date: str) -> Optional[float]:
        """
        获取次日收益率
        
        Args:
            ts_code: 股票代码
            trade_date: 当前交易日
            
        Returns:
            次日收益率(%)，如果无法获取则返回None
        """
        try:
            # 获取当前日期和之后的数据
            start_date = trade_date
            end_date = (datetime.strptime(trade_date, '%Y%m%d') + timedelta(days=10)).strftime('%Y%m%d')
            
            df = self._get_stock_daily_data(ts_code, start_date, end_date)
            
            if df.empty or len(df) < 2:
                return None
            
            # 找到当前日期的索引
            current_idx = df[df['trade_date'] == trade_date].index
            if len(current_idx) == 0:
                return None
            
            current_idx = current_idx[0]
            next_idx = current_idx + 1
            
            if next_idx >= len(df):
                return None
            
            # 计算次日收益率
            next_close = df.iloc[next_idx]['close']
            current_close = df.iloc[current_idx]['close']
            
            if pd.isna(next_close) or pd.isna(current_close) or current_close == 0:
                return None
            
            return (next_close - current_close) / current_close * 100
            
        except Exception as e:
            logger.warning(f"获取{ts_code}次日收益率失败: {e}")
            return None
    
    def _get_limit_up_stocks_with_factors(self, trade_date: str) -> pd.DataFrame:
        """
        获取涨停股及其因子数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            DataFrame with factor values
        """
        try:
            # 使用limit_list_d接口获取涨停股数据
            df = self.pro.limit_list_d(trade_date=trade_date)
            
            if df.empty:
                logger.warning(f"日期{trade_date}没有涨停股票")
                return pd.DataFrame()
            
            # 过滤有效涨停股(涨幅>=9.5%)
            df = df[df['pct_chg'] >= 9.5].copy()
            
            if df.empty:
                return pd.DataFrame()
            
            # 计算封成比
            df['seal_ratio'] = df['fd_amount'] / df['amount']
            
            # 获取流通市值计算封单/流通市值
            try:
                # 获取当日行情数据
                daily_df = self.pro.daily_basic(trade_date=trade_date)
                if not daily_df.empty:
                    df = df.merge(daily_df[['ts_code', 'float_mv']], on='ts_code', how='left')
                    df['seal_to_mv'] = df['fd_amount'] / (df['float_mv'] * 10000)  # float_mv是万元
            except Exception as e:
                logger.warning(f"获取流通市值数据失败: {e}")
                df['float_mv'] = np.nan
                df['seal_to_mv'] = np.nan
            
            # 获取资金流向数据
            try:
                moneyflow_df = self.pro.moneyflow(trade_date=trade_date)
                if not moneyflow_df.empty:
                    df = df.merge(
                        moneyflow_df[['ts_code', 'main_net_amount', 'main_net_ratio', 
                                     'medium_net_amount', 'medium_net_ratio']], 
                        on='ts_code', how='left'
                    )
            except Exception as e:
                logger.warning(f"获取资金流向数据失败: {e}")
                df['main_net_amount'] = np.nan
                df['main_net_ratio'] = np.nan
                df['medium_net_amount'] = np.nan
                df['medium_net_ratio'] = np.nan
            
            # 获取历史换手率数据计算换手率/20日均量
            try:
                # 获取前20个交易日的数据
                prev_date = self._get_prev_trading_day(trade_date)
                if prev_date:
                    start_date = (datetime.strptime(prev_date, '%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
                    
                    for idx, row in df.iterrows():
                        try:
                            ts_code = row['ts_code']
                            hist_df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=prev_date)
                            
                            if not hist_df.empty and len(hist_df) >= 10:
                                hist_df = hist_df.sort_values('trade_date')
                                df.at[idx, 'turnover_20ma'] = hist_df['turnover_rate'].mean()
                                if pd.notna(row['turnover_rate']) and df.at[idx, 'turnover_20ma'] > 0:
                                    df.at[idx, 'turnover_20ma_ratio'] = row['turnover_rate'] / df.at[idx, 'turnover_20ma']
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"计算换手率均值失败: {e}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取涨停股数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_ic_for_factor(self, factor_name: str, trade_date: str, 
                                lookback_days: int = 60) -> Optional[ICResult]:
        """
        计算单个因子的IC值
        
        Args:
            factor_name: 因子名称
            trade_date: 计算日期
            lookback_days: 回溯天数
            
        Returns:
            ICResult对象
        """
        try:
            # 获取回溯期间的数据
            end_date = trade_date
            start_date = (datetime.strptime(trade_date, '%Y%m%d') - 
                         timedelta(days=lookback_days*2)).strftime('%Y%m%d')
            
            # 获取交易日历
            cal = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            if cal.empty:
                return None
            
            trade_days = cal[cal['is_open'] == 1]['cal_date'].tolist()
            trade_days = trade_days[-lookback_days:]  # 取最近lookback_days个交易日
            
            if len(trade_days) < 20:  # 至少需要20个交易日
                logger.warning(f"交易日数据不足: {len(trade_days)}天")
                return None
            
            # 收集因子值和次日收益率
            factor_values = []
            next_returns = []
            
            for day in trade_days[:-1]:  # 排除最后一天，因为无法获取次日收益率
                try:
                    # 获取当日涨停股数据
                    df = self._get_limit_up_stocks_with_factors(day)
                    
                    if df.empty or factor_name not in df.columns:
                        continue
                    
                    # 过滤有效因子值
                    valid_df = df[df[factor_name].notna()].copy()
                    
                    if valid_df.empty:
                        continue
                    
                    # 获取次日收益率
                    for _, row in valid_df.iterrows():
                        ts_code = row['ts_code']
                        factor_val = row[factor_name]
                        next_ret = self._get_next_day_return(ts_code, day)
                        
                        if next_ret is not None and pd.notna(factor_val):
                            factor_values.append(factor_val)
                            next_returns.append(next_ret)
                            
                except Exception as e:
                    logger.debug(f"处理日期{day}数据失败: {e}")
                    continue
            
            if len(factor_values) < 30:  # 至少需要30个样本
                logger.warning(f"样本数量不足: {len(factor_values)}")
                return ICResult(
                    factor_name=factor_name,
                    trade_date=trade_date,
                    ic_value=0.0,
                    sample_size=len(factor_values),
                    is_valid=False
                )
            
            # 计算IC值 (Spearman秩相关系数)
            from scipy import stats
            ic_value, p_value = stats.spearmanr(factor_values, next_returns)
            
            if pd.isna(ic_value):
                ic_value = 0.0
            
            # 创建结果
            result = ICResult(
                factor_name=factor_name,
                trade_date=trade_date,
                ic_value=float(ic_value),
                sample_size=len(factor_values),
                is_valid=abs(ic_value) >= self.IC_INVALID_THRESHOLD
            )
            
            return result
            
        except Exception as e:
            logger.error(f"计算因子{factor_name}的IC值失败: {e}")
            return None
    
    def calculate_rolling_ic(self, factor_name: str, ic_history: List[Dict]) -> Tuple[Optional[float], Optional[float]]:
        """
        计算滚动窗口IC值
        
        Args:
            factor_name: 因子名称
            ic_history: IC历史数据列表
            
        Returns:
            (20日IC均值, 60日IC均值)
        """
        if not ic_history:
            return None, None
        
        ic_values = [h['ic_value'] for h in ic_history if 'ic_value' in h]
        
        if len(ic_values) < 20:
            return None, None
        
        ic_20 = np.mean(ic_values[-20:])
        ic_60 = np.mean(ic_values[-60:]) if len(ic_values) >= 60 else None
        
        return ic_20, ic_60
    
    def detect_trend(self, factor_name: str, ic_history: List[Dict]) -> Tuple[str, int]:
        """
        检测IC值趋势
        
        Args:
            factor_name: 因子名称
            ic_history: IC历史数据列表
            
        Returns:
            (趋势方向, 持续天数)
        """
        if len(ic_history) < 5:
            return "stable", 0
        
        ic_values = [h['ic_value'] for h in ic_history if 'ic_value' in h]
        
        if len(ic_values) < 5:
            return "stable", 0
        
        # 检查最近5天的趋势
        recent_values = ic_values[-5:]
        
        # 计算连续下降天数
        decreasing_days = 0
        for i in range(len(recent_values)-1, 0, -1):
            if abs(recent_values[i]) < abs(recent_values[i-1]):
                decreasing_days += 1
            else:
                break
        
        if decreasing_days >= 3:
            return "decreasing", decreasing_days
        
        # 计算连续上升天数
        increasing_days = 0
        for i in range(len(recent_values)-1, 0, -1):
            if abs(recent_values[i]) > abs(recent_values[i-1]):
                increasing_days += 1
            else:
                break
        
        if increasing_days >= 3:
            return "increasing", increasing_days
        
        return "stable", 0
    
    def run_daily_ic_calculation(self, trade_date: str = None) -> ICMonitorReport:
        """
        运行每日IC计算
        
        Args:
            trade_date: 交易日期，默认为最近交易日
            
        Returns:
            IC监控报告
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        logger.info(f"开始计算{trade_date}的IC值")
        
        factors_results = []
        invalid_factors = []
        warning_factors = []
        
        for factor_name in self.FACTORS:
            try:
                logger.info(f"计算因子: {factor_name}")
                
                # 计算当日IC值
                result = self.calculate_ic_for_factor(factor_name, trade_date)
                
                if result is None:
                    continue
                
                # 更新历史数据
                if factor_name not in self.ic_history:
                    self.ic_history[factor_name] = []
                
                self.ic_history[factor_name].append({
                    'trade_date': trade_date,
                    'ic_value': result.ic_value,
                    'sample_size': result.sample_size
                })
                
                # 计算滚动IC值
                ic_20, ic_60 = self.calculate_rolling_ic(factor_name, self.ic_history[factor_name])
                result.ic_window_20 = ic_20
                result.ic_window_60 = ic_60
                
                # 检测趋势
                trend, trend_days = self.detect_trend(factor_name, self.ic_history[factor_name])
                result.trend = trend
                result.trend_days = trend_days
                
                factors_results.append(result)
                
                # 检查是否失效
                if not result.is_valid:
                    invalid_factors.append(factor_name)
                    logger.warning(f"因子{factor_name}失效: IC={result.ic_value:.4f}")
                
                # 检查是否预警(下降趋势)
                if trend == "decreasing" and trend_days >= self.TREND_DAYS_THRESHOLD:
                    warning_factors.append(factor_name)
                    logger.warning(f"因子{factor_name}IC值连续下降{trend_days}天")
                
            except Exception as e:
                logger.error(f"计算因子{factor_name}失败: {e}")
                continue
        
        # 保存历史数据
        self._save_ic_history()
        
        # 生成报告
        report = ICMonitorReport(
            report_date=trade_date,
            generated_at=datetime.now().isoformat(),
            factors=factors_results,
            invalid_factors=invalid_factors,
            warning_factors=warning_factors,
            summary={
                'total_factors': len(self.FACTORS),
                'calculated_factors': len(factors_results),
                'invalid_count': len(invalid_factors),
                'warning_count': len(warning_factors),
                'valid_rate': (len(factors_results) - len(invalid_factors)) / len(factors_results) * 100 if factors_results else 0
            }
        )
        
        # 保存报告
        self._save_report(report)
        
        logger.info(f"IC计算完成: {len(factors_results)}个因子, {len(invalid_factors)}个失效, {len(warning_factors)}个预警")
        
        return report
    
    def _save_report(self, report: ICMonitorReport):
        """保存IC监控报告"""
        try:
            report_file = self.data_dir / f"ic_report_{report.report_date}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"IC报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存IC报告失败: {e}")
    
    def get_latest_report(self) -> Optional[ICMonitorReport]:
        """获取最新的IC监控报告"""
        try:
            report_files = sorted(self.data_dir.glob("ic_report_*.json"), reverse=True)
            if not report_files:
                return None
            
            with open(report_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ICMonitorReport(
                report_date=data['report_date'],
                generated_at=data['generated_at'],
                factors=[ICResult(**f) for f in data['factors']],
                invalid_factors=data['invalid_factors'],
                warning_factors=data['warning_factors'],
                summary=data['summary']
            )
        except Exception as e:
            logger.error(f"获取最新报告失败: {e}")
            return None
    
    def format_report_for_feishu(self, report: ICMonitorReport) -> str:
        """
        格式化报告为飞书消息
        
        Args:
            report: IC监控报告
            
        Returns:
            飞书消息字符串
        """
        lines = []
        lines.append(f"📊 **T01因子IC监控报告 ({report.report_date})**")
        lines.append("=" * 40)
        
        # 汇总信息
        summary = report.summary
        lines.append(f"**监控因子数**: {summary['total_factors']}")
        lines.append(f"**有效因子数**: {summary['calculated_factors']}")
        lines.append(f"**失效因子数**: {summary['invalid_count']} ⚠️")
        lines.append(f"**预警因子数**: {summary['warning_count']}")
        lines.append(f"**因子有效率**: {summary['valid_rate']:.1f}%")
        lines.append("")
        
        # 失效因子警告
        if report.invalid_factors:
            lines.append("🚨 **失效因子警告** (|IC| < 0.03)")
            for factor in report.invalid_factors:
                # 找到对应的IC值
                ic_value = 0
                for f in report.factors:
                    if f.factor_name == factor:
                        ic_value = f.ic_value
                        break
                lines.append(f"  • {factor}: IC={ic_value:.4f}")
            lines.append("")
        
        # 预警因子
        if report.warning_factors:
            lines.append("⚠️ **IC下降趋势预警**")
            for factor in report.warning_factors:
                for f in report.factors:
                    if f.factor_name == factor:
                        lines.append(f"  • {factor}: 连续下降{f.trend_days}天")
                        break
            lines.append("")
        
        # 各因子IC值详情
        lines.append("**因子IC值详情**")
        lines.append("```")
        lines.append(f"{'因子名称':<20} {'当日IC':<10} {'20日IC':<10} {'60日IC':<10} {'状态':<8}")
        lines.append("-" * 70)
        
        for factor in report.factors:
            status = "✅" if factor.is_valid else "❌"
            ic_20 = f"{factor.ic_window_20:.4f}" if factor.ic_window_20 is not None else "N/A"
            ic_60 = f"{factor.ic_window_60:.4f}" if factor.ic_window_60 is not None else "N/A"
            lines.append(f"{factor.factor_name:<20} {factor.ic_value:<10.4f} {ic_20:<10} {ic_60:<10} {status:<8}")
        
        lines.append("```")
        lines.append("")
        
        # 说明
        lines.append("**说明**:")
        lines.append("• IC值: 因子与次日收益率的Spearman秩相关系数")
        lines.append("• |IC| ≥ 0.03: 因子有效 ✅")
        lines.append("• |IC| < 0.03: 因子失效 ❌")
        lines.append("• 20日/60日IC: 滚动窗口平均IC值")
        lines.append("")
        lines.append(f"⏰ 生成时间: {report.generated_at}")
        
        return "\n".join(lines)


def send_ic_report_to_feishu(report: ICMonitorReport, config: Dict[str, Any] = None):
    """
    发送IC监控报告到飞书
    
    Args:
        report: IC监控报告
        config: 配置字典
    """
    try:
        # 格式化消息
        monitor = ICMonitor()
        message = monitor.format_report_for_feishu(report)
        
        # 获取用户ID
        if config is None:
            config = monitor.config
        
        user_id = config.get('notification', {}).get('feishu_user_id', os.getenv('FEISHU_USER_ID', ''))
        
        # 使用subprocess调用openclaw发送消息
        import subprocess
        
        env = os.environ.copy()
        node_path = '/root/.nvm/versions/node/v22.22.0/bin'
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        cmd = [
            '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
            'message', 'send',
            '--channel', 'feishu',
            '--target', f'user:{user_id}',
            '--message', message
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("IC监控报告已发送到飞书")
            return True
        else:
            logger.error(f"发送飞书消息失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"发送IC报告到飞书失败: {e}")
        return False


def main():
    """主函数 - 用于命令行运行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01 IC监控模块')
    parser.add_argument('--date', type=str, help='交易日期(YYYYMMDD)')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    parser.add_argument('--send-feishu', action='store_true', help='发送到飞书')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建监控器
    monitor = ICMonitor(config_path=args.config)
    
    # 确定日期
    if args.date:
        trade_date = args.date
    else:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    logger.info(f"运行IC监控: 日期={trade_date}")
    
    # 运行计算
    if args.test:
        # 测试模式 - 生成模拟数据
        logger.info("测试模式: 生成模拟IC报告")
        report = ICMonitorReport(
            report_date=trade_date,
            generated_at=datetime.now().isoformat(),
            factors=[
                ICResult(factor_name='seal_ratio', trade_date=trade_date, ic_value=0.15, ic_window_20=0.12, ic_window_60=0.10, is_valid=True, trend='stable'),
                ICResult(factor_name='turnover_rate', trade_date=trade_date, ic_value=0.02, ic_window_20=0.05, ic_window_60=0.08, is_valid=False, trend='decreasing', trend_days=5),
            ],
            invalid_factors=['turnover_rate'],
            warning_factors=['turnover_rate'],
            summary={
                'total_factors': 10,
                'calculated_factors': 2,
                'invalid_count': 1,
                'warning_count': 1,
                'valid_rate': 50.0
            }
        )
    else:
        # 正常模式
        report = monitor.run_daily_ic_calculation(trade_date)
    
    # 打印报告
    print(monitor.format_report_for_feishu(report))
    
    # 发送到飞书
    if args.send_feishu:
        send_ic_report_to_feishu(report, monitor.config)
    
    logger.info("IC监控完成")


if __name__ == '__main__':
    main()
