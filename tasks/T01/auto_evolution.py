#!/usr/bin/env python3
"""
T01自动化进化流程模块 (auto_evolution.py)
实现完全自动化的策略优化流程
包括：每周策略评估、因子权重优化、失效检测、MoA自动调用
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import yaml

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from machine_learning import T01MachineLearning

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """进化配置数据类"""
    review_interval_days: int = 7  # 每周反思
    optimization_frequency: str = "weekly"  # 优化频率
    success_threshold: float = 1.03  # 成功阈值
    min_win_rate: float = 0.40  # 最低胜率
    max_drawdown: float = 0.20  # 最大回撤
    ic_threshold: float = 0.03  # IC阈值
    population_size: int = 50  # 遗传算法种群大小
    generations: int = 30  # 遗传算法迭代次数
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyPerformance:
    """策略绩效数据类"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    success_rate: float = 0.0  # T+2收盘/T+1开盘 > 1.03%的比例
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvolutionReport:
    """进化报告数据类"""
    report_date: str
    phase: str
    performance: StrategyPerformance
    recommendations: List[str]
    factor_adjustments: Dict[str, float]
    warnings: List[str]
    next_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_date": self.report_date,
            "phase": self.phase,
            "performance": self.performance.to_dict(),
            "recommendations": self.recommendations,
            "factor_adjustments": self.factor_adjustments,
            "warnings": self.warnings,
            "next_actions": self.next_actions
        }


class AutoEvolution:
    """
    自动化进化流程管理器
    实现策略的自动评估、优化和进化
    """
    
    def __init__(self, config_path: Optional[str] = None, tushare_token: Optional[str] = None):
        """
        初始化自动化进化管理器
        
        Args:
            config_path: 配置文件路径
            tushare_token: Tushare API token
        """
        self.current_dir = Path(__file__).parent
        self.config_path = config_path or self.current_dir / "config.yaml"
        self.config = self._load_config()
        self.evolution_config = self._load_evolution_config()
        
        # Tushare token
        self.token = tushare_token or self.config.get("tushare_token", os.getenv("TUSHARE_TOKEN"))
        if self.token:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            self.pro = None
            
        # 遗传算法优化器
        self.genetic_optimizer = None
        if self.token and self.token != 'test_token':
            try:
                self.genetic_optimizer = T01MachineLearning(self.config_path)
            except Exception as e:
                logger.warning(f"遗传算法优化器初始化失败: {e}")
        
        # 日志目录
        self.log_dir = self.current_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 状态目录
        self.state_dir = self.current_dir / "state"
        self.state_dir.mkdir(exist_ok=True)
        
        logger.info("AutoEvolution初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _load_evolution_config(self) -> EvolutionConfig:
        """加载进化配置"""
        config = self.config.get("evolution", {})
        return EvolutionConfig(
            review_interval_days=config.get("review_interval_days", 7),
            optimization_frequency=config.get("optimization_frequency", "weekly"),
            success_threshold=config.get("success_threshold", 1.03),
            min_win_rate=config.get("min_win_rate", 0.40),
            max_drawdown=config.get("max_drawdown", 0.20),
            ic_threshold=config.get("ic_threshold", 0.03),
            population_size=config.get("population_size", 50),
            generations=config.get("generations", 30)
        )
    
    def evaluate_strategy_performance(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> StrategyPerformance:
        """
        评估策略绩效
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            StrategyPerformance: 策略绩效数据
        """
        logger.info("开始评估策略绩效...")
        
        # 默认评估最近一周
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_dt = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=7)
            start_date = start_dt.strftime("%Y%m%d")
        
        # 从回测数据加载交易记录
        backtest_data = self._load_backtest_data(start_date, end_date)
        
        if not backtest_data:
            logger.warning("未找到回测数据，返回默认绩效")
            return StrategyPerformance()
        
        # 计算绩效指标
        performance = self._calculate_performance_metrics(backtest_data)
        
        logger.info(f"策略绩效评估完成: 胜率={performance.win_rate:.2%}, 成功率={performance.success_rate:.2%}")
        return performance
    
    def _load_backtest_data(self, start_date: str, end_date: str) -> List[Dict]:
        """加载回测数据"""
        backtest_dir = self.current_dir / "backtest"
        data_file = backtest_dir / "backtest_results.json"
        
        if not data_file.exists():
            # 尝试从state目录加载候选股历史
            return self._load_candidate_history(start_date, end_date)
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            # 过滤日期范围
            filtered_data = [
                d for d in all_data 
                if start_date <= d.get("trade_date", "") <= end_date
            ]
            return filtered_data
        except Exception as e:
            logger.error(f"加载回测数据失败: {e}")
            return []
    
    def _load_candidate_history(self, start_date: str, end_date: str) -> List[Dict]:
        """从候选股文件加载历史数据"""
        state_dir = self.current_dir / "state"
        history = []
        
        try:
            for candidate_file in state_dir.glob("candidates_*.json"):
                with open(candidate_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    trade_date = data.get("t_date", "")
                    if start_date <= trade_date <= end_date:
                        history.append(data)
        except Exception as e:
            logger.error(f"加载候选股历史失败: {e}")
        
        return history
    
    def _calculate_performance_metrics(self, trades: List[Dict]) -> StrategyPerformance:
        """计算绩效指标"""
        if not trades:
            return StrategyPerformance()
        
        total_trades = len(trades)
        winning_trades = 0
        losing_trades = 0
        total_profit = 0.0
        total_loss = 0.0
        success_count = 0
        
        profits = []
        
        for trade in trades:
            # 计算收益率
            buy_price = trade.get("buy_price", 0)
            sell_price = trade.get("sell_price", 0)
            
            if buy_price > 0 and sell_price > 0:
                profit_pct = (sell_price - buy_price) / buy_price
                profits.append(profit_pct)
                
                if profit_pct > 0:
                    winning_trades += 1
                    total_profit += profit_pct
                else:
                    losing_trades += 1
                    total_loss += abs(profit_pct)
                
                # 检查是否达到成功阈值
                if profit_pct > (self.evolution_config.success_threshold - 1):
                    success_count += 1
        
        # 计算指标
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_profit = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        success_rate = success_count / total_trades if total_trades > 0 else 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(profits)
        
        # 计算夏普比率（简化版，假设无风险利率为0）
        sharpe_ratio = 0.0
        if profits:
            returns = np.array(profits)
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        return StrategyPerformance(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            success_rate=success_rate
        )
    
    def _calculate_max_drawdown(self, profits: List[float]) -> float:
        """计算最大回撤"""
        if not profits:
            return 0.0
        
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / (running_max + 1e-10)
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    def analyze_trade_characteristics(
        self, 
        trades: List[Dict]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        分析盈利和亏损交易的特征差异
        
        Returns:
            (winning_features, losing_features): 盈利和亏损交易的特征
        """
        winning_trades = [t for t in trades if t.get("profit", 0) > 0]
        losing_trades = [t for t in trades if t.get("profit", 0) <= 0]
        
        winning_features = self._extract_trade_features(winning_trades)
        losing_features = self._extract_trade_features(losing_trades)
        
        return winning_features, losing_features
    
    def _extract_trade_features(self, trades: List[Dict]) -> Dict[str, Any]:
        """提取交易特征"""
        if not trades:
            return {}
        
        features = {
            "avg_limit_up_score": np.mean([t.get("limit_up_score", 0) for t in trades]),
            "avg_auction_score": np.mean([t.get("auction_score", 0) for t in trades]),
            "avg_turnover": np.mean([t.get("turnover", 0) for t in trades]),
            "avg_volume_ratio": np.mean([t.get("volume_ratio", 0) for t in trades]),
            "hot_sector_ratio": sum(1 for t in trades if t.get("is_hot_sector", False)) / len(trades),
            "dragon_leader_ratio": sum(1 for t in trades if t.get("is_dragon_leader", False)) / len(trades),
        }
        
        return features
    
    def optimize_factor_weights(
        self, 
        performance: StrategyPerformance,
        winning_features: Dict[str, Any],
        losing_features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        使用遗传算法优化因子权重
        
        Returns:
            Dict[str, float]: 优化后的因子权重
        """
        logger.info("开始优化因子权重...")
        
        if not self.genetic_optimizer:
            logger.warning("遗传算法优化器未初始化，返回默认权重")
            return self._get_default_weights()
        
        try:
            # 运行遗传算法优化
            optimized_weights = self.genetic_optimizer.optimize_factor_weights(
                population_size=self.evolution_config.population_size,
                generations=self.evolution_config.generations
            )
            
            logger.info(f"因子权重优化完成: {optimized_weights}")
            return optimized_weights
            
        except Exception as e:
            logger.error(f"因子权重优化失败: {e}")
            return self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """获取默认权重"""
        return {
            "limit_up_time": 0.15,
            "seal_amount_ratio": 0.20,
            "turnover": 0.10,
            "volume_ratio": 0.10,
            "main_force_net": 0.15,
            "hot_sector": 0.15,
            "dragon_leader": 0.15
        }
    
    def detect_strategy_failure(self, performance: StrategyPerformance) -> List[str]:
        """
        检测策略失效信号
        
        Returns:
            List[str]: 失效警告列表
        """
        warnings = []
        
        # 胜率过低
        if performance.win_rate < self.evolution_config.min_win_rate:
            warnings.append(
                f"⚠️ 策略胜率过低: {performance.win_rate:.2%} < {self.evolution_config.min_win_rate:.2%}"
            )
        
        # 回撤过大
        if performance.max_drawdown > self.evolution_config.max_drawdown:
            warnings.append(
                f"⚠️ 策略回撤过大: {performance.max_drawdown:.2%} > {self.evolution_config.max_drawdown:.2%}"
            )
        
        # 夏普比率为负
        if performance.sharpe_ratio < 0:
            warnings.append(f"⚠️ 策略夏普比率为负: {performance.sharpe_ratio:.2f}")
        
        # 成功率过低
        if performance.success_rate < 0.3:
            warnings.append(f"⚠️ 策略成功率过低: {performance.success_rate:.2%}")
        
        return warnings
    
    def generate_recommendations(
        self,
        performance: StrategyPerformance,
        winning_features: Dict[str, Any],
        losing_features: Dict[str, Any]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于胜率建议
        if performance.win_rate < 0.5:
            recommendations.append("建议提高选股标准，减少交易频率")
        
        # 基于盈亏比建议
        if performance.profit_factor < 1.5:
            recommendations.append("建议优化止损策略，提高盈亏比")
        
        # 基于特征差异建议
        if winning_features and losing_features:
            if winning_features.get("hot_sector_ratio", 0) > losing_features.get("hot_sector_ratio", 0):
                recommendations.append("热点板块对盈利贡献显著，建议加强板块筛选")
            
            if winning_features.get("dragon_leader_ratio", 0) > losing_features.get("dragon_leader_ratio", 0):
                recommendations.append("龙头股识别有效，建议提高龙头因子权重")
        
        return recommendations
    
    def call_moa_reflection(self) -> bool:
        """
        调用MoA进行策略深度反思
        
        Returns:
            bool: 是否成功调用
        """
        logger.info("准备调用MoA进行策略反思...")
        
        try:
            # 准备MoA调用参数
            moa_prompt = self._prepare_moa_prompt()
            
            # 调用MoA技能
            result = subprocess.run(
                [
                    "python3", "-c",
                    f"""
import sys
sys.path.insert(0, '{self.current_dir}')
from moa import MoAAnalyzer
analyzer = MoAAnalyzer()
result = analyzer.analyze('{moa_prompt}')
print(result)
"""
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("MoA策略反思完成")
                return True
            else:
                logger.error(f"MoA调用失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"MoA调用异常: {e}")
            return False
    
    def _prepare_moa_prompt(self) -> str:
        """准备MoA调用提示词"""
        performance = self.evaluate_strategy_performance()
        
        prompt = f"""
T01龙头战法策略反思分析

当前策略绩效:
- 总交易次数: {performance.total_trades}
- 胜率: {performance.win_rate:.2%}
- 平均盈利: {performance.avg_profit:.2%}
- 平均亏损: {performance.avg_loss:.2%}
- 盈亏比: {performance.profit_factor:.2f}
- 最大回撤: {performance.max_drawdown:.2%}
- 夏普比率: {performance.sharpe_ratio:.2f}
- 成功率(T+2/T+1>1.03%): {performance.success_rate:.2%}

请分析:
1. 当前策略的优势和劣势
2. 可能的改进方向
3. 需要关注的风险信号
4. 建议的优化措施
"""
        return prompt
    
    def update_config_file(self, factor_weights: Dict[str, float]) -> bool:
        """
        更新配置文件中的因子权重
        
        Args:
            factor_weights: 新的因子权重
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 加载现有配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 更新因子权重
            if "scoring" not in config:
                config["scoring"] = {}
            config["scoring"]["weights"] = factor_weights
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置文件已更新: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def run_evolution_cycle(self) -> EvolutionReport:
        """
        执行完整的进化周期
        
        Returns:
            EvolutionReport: 进化报告
        """
        logger.info("=" * 50)
        logger.info("开始T01策略自动化进化周期")
        logger.info("=" * 50)
        
        # 1. 评估策略绩效
        performance = self.evaluate_strategy_performance()
        
        # 2. 分析交易特征
        trades = self._load_backtest_data(
            (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
            datetime.now().strftime("%Y%m%d")
        )
        winning_features, losing_features = self.analyze_trade_characteristics(trades)
        
        # 3. 检测策略失效
        warnings = self.detect_strategy_failure(performance)
        
        # 4. 优化因子权重
        factor_weights = self.optimize_factor_weights(
            performance, winning_features, losing_features
        )
        
        # 5. 生成建议
        recommendations = self.generate_recommendations(
            performance, winning_features, losing_features
        )
        
        # 6. 更新配置文件
        if factor_weights:
            self.update_config_file(factor_weights)
        
        # 7. 准备下一步行动
        next_actions = [
            "监控下一周期策略表现",
            "验证优化后的因子权重效果"
        ]
        if warnings:
            next_actions.append("关注策略失效警告，准备应对措施")
        
        # 8. 生成报告
        report = EvolutionReport(
            report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            phase="Phase2-中期增强",
            performance=performance,
            recommendations=recommendations,
            factor_adjustments=factor_weights,
            warnings=warnings,
            next_actions=next_actions
        )
        
        # 9. 保存报告
        self._save_evolution_report(report)
        
        logger.info("进化周期完成")
        return report
    
    def _save_evolution_report(self, report: EvolutionReport):
        """保存进化报告"""
        report_file = self.state_dir / f"evolution_report_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"进化报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存进化报告失败: {e}")
    
    def send_evolution_report(self, report: EvolutionReport) -> bool:
        """
        发送进化报告到飞书
        
        Args:
            report: 进化报告
            
        Returns:
            bool: 是否成功发送
        """
        try:
            # 格式化报告
            message = self._format_report_for_feishu(report)
            
            # 使用openclaw发送消息
            env = os.environ.copy()
            node_path = "/root/.nvm/versions/node/v22.22.0/bin"
            if node_path not in env.get('PATH', ''):
                env['PATH'] = node_path + ':' + env.get('PATH', '')
            
            cmd = [
                '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
                'message', 'send',
                '--channel', 'feishu',
                '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
                '--message', message
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("进化报告已发送到飞书")
                return True
            else:
                logger.error(f"发送飞书消息失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"发送报告异常: {e}")
            return False
    
    def _format_report_for_feishu(self, report: EvolutionReport) -> str:
        """格式化报告为飞书消息格式"""
        p = report.performance
        
        message = f"""🔄 **T01策略自动化进化报告**

**📅 报告时间**: {report.report_date}
**🎯 进化阶段**: {report.phase}

**📊 策略绩效**:
• 总交易: {p.total_trades}次 (盈{p.winning_trades}/亏{p.losing_trades})
• 胜率: {p.win_rate:.2%}
• 成功率: {p.success_rate:.2%}
• 盈亏比: {p.profit_factor:.2f}
• 最大回撤: {p.max_drawdown:.2%}
• 夏普比率: {p.sharpe_ratio:.2f}

**⚠️ 风险警告**:
{chr(10).join(f'• {w}' for w in report.warnings) if report.warnings else '• 无警告'}

**💡 优化建议**:
{chr(10).join(f'• {r}' for r in report.recommendations) if report.recommendations else '• 保持当前策略'}

**🔧 因子权重调整**:
{chr(10).join(f'• {k}: {v:.3f}' for k, v in list(report.factor_adjustments.items())[:5]) if report.factor_adjustments else '• 未调整'}

**📋 下一步行动**:
{chr(10).join(f'• {a}' for a in report.next_actions)}
"""
        return message
    
    def schedule_weekly_evolution(self):
        """
        调度每周进化任务
        建议通过cron每周五运行
        """
        logger.info("执行每周策略进化...")
        
        # 1. 执行进化周期
        report = self.run_evolution_cycle()
        
        # 2. 发送报告
        self.send_evolution_report(report)
        
        # 3. 调用MoA反思（每周一次）
        if datetime.now().weekday() == 4:  # 周五
            self.call_moa_reflection()
        
        logger.info("每周进化任务完成")


def main():
    """主函数 - 用于命令行执行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01自动化进化流程')
    parser.add_argument('--run', action='store_true', help='执行进化周期')
    parser.add_argument('--evaluate', action='store_true', help='仅评估策略绩效')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--token', type=str, help='Tushare token')
    
    args = parser.parse_args()
    
    # 初始化进化管理器
    evolution = AutoEvolution(
        config_path=args.config,
        tushare_token=args.token
    )
    
    if args.evaluate:
        # 仅评估绩效
        performance = evolution.evaluate_strategy_performance()
        print(json.dumps(performance.to_dict(), indent=2, ensure_ascii=False))
    elif args.run:
        # 执行完整进化周期
        report = evolution.run_evolution_cycle()
        evolution.send_evolution_report(report)
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        # 调度每周进化
        evolution.schedule_weekly_evolution()


if __name__ == "__main__":
    main()
