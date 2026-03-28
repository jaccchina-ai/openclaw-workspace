#!/usr/bin/env python3
"""
BacktestEngine使用示例

演示如何使用BacktestEngine完成一次完整的回测流程
"""

import sys
import os
import yaml
import logging

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import BacktestEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_backtest_example():
    """运行回测示例"""
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        # 使用默认配置
        config = {
            'backtest': {
                'initial_capital': 1000000,
                'commission_rate': 0.0003,
                'slippage': 0.005,
                'position_size': 0.2,
                'max_positions': 5
            },
            'strategy': {
                'output': {
                    'top_n_candidates': 10
                },
                't_day_scoring': {
                    'first_limit_time': 30,
                    'buy_to_sell_ratio': 10,
                    'order_amount_to_circ_mv': 15,
                    'turnover_rate': 5,
                    'turnover_rate_to_20ma': 10,
                    'volume_ratio': 5,
                    'main_net_amount': 5,
                    'main_net_ratio': 5,
                    'medium_net_amount': 5,
                    'is_hot_sector': 10
                },
                't1_auction_scoring': {
                    'open_change_pct': 35,
                    'auction_volume_ratio': 20,
                    'auction_turnover_rate': 0,
                    'auction_amount': 20,
                    'auction_volume_to_t_volume': 25
                },
                'risk_control': {
                    'max_position_per_stock': 0.2,
                    'min_total_score': 60
                }
            },
            'api': {
                'api_key': '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
            }
        }
    else:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    
    # 设置回测参数
    start_date = '20250301'
    end_date = '20250315'
    
    logger.info(f"开始回测: {start_date} - {end_date}")
    
    # 创建回测引擎
    engine = BacktestEngine(
        config=config,
        start_date=start_date,
        end_date=end_date
    )
    
    logger.info("回测引擎初始化完成")
    
    # 加载历史数据
    logger.info("加载历史数据...")
    engine.load_historical_data()
    
    # 执行回测
    logger.info("执行回测...")
    engine.run_backtest()
    
    # 计算指标
    logger.info("计算绩效指标...")
    engine.calculate_metrics()
    
    # 生成报告
    logger.info("生成回测报告...")
    report = engine.generate_report()
    
    # 输出结果
    print("\n" + "="*60)
    print("回测结果报告")
    print("="*60)
    print(f"回测期间: {report['start_date']} - {report['end_date']}")
    print(f"初始资金: {report['initial_capital']:,.2f}")
    print(f"最终资金: {report['final_capital']:,.2f}")
    print(f"总收益率: {report['total_return']*100:.2f}%")
    print(f"交易次数: {len(report['trades'])}")
    
    if report['metrics']:
        print("\n绩效指标:")
        print(f"  胜率: {report['metrics'].get('win_rate', 0)*100:.2f}%")
        print(f"  盈亏比: {report['metrics'].get('profit_loss_ratio', 0):.2f}")
        print(f"  夏普比率: {report['metrics'].get('sharpe_ratio', 0):.2f}")
        print(f"  最大回撤: {report['metrics'].get('max_drawdown', 0)*100:.2f}%")
        print(f"  年化收益率: {report['metrics'].get('annual_return', 0)*100:.2f}%")
    
    print("\n交易记录:")
    for i, trade in enumerate(report['trades'][:10]):  # 只显示前10条
        action = "买入" if trade['action'] == 'buy' else "卖出"
        print(f"  {i+1}. {trade['trade_date']} {action} {trade['name']}({trade['ts_code']}) "
              f"@ {trade['actual_price']:.2f} x {trade['amount']}股")
        if trade['action'] == 'sell':
            print(f"      盈亏: {trade.get('profit', 0):.2f} ({trade.get('profit_pct', 0)*100:.2f}%)")
    
    if len(report['trades']) > 10:
        print(f"  ... 还有 {len(report['trades']) - 10} 条交易记录")
    
    print("\n权益曲线 (前5天):")
    for point in report['equity_curve'][:5]:
        print(f"  {point['date']}: {point['equity']:,.2f}")
    
    if len(report['equity_curve']) > 5:
        print(f"  ... 还有 {len(report['equity_curve']) - 5} 天")
    
    print("="*60)
    
    return report


if __name__ == '__main__':
    try:
        report = run_backtest_example()
        logger.info("回测示例完成")
    except Exception as e:
        logger.error(f"回测示例失败: {e}")
        import traceback
        traceback.print_exc()
