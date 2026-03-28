#!/usr/bin/env python3
"""T01策略回测入口脚本"""

import argparse
import yaml
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest.backtest_engine import BacktestEngine
from backtest.report_generator import ReportGenerator
from feishu_direct_sender import send_feishu_message_direct

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"✅ 配置文件加载成功: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"❌ 配置文件解析错误: {e}")
        sys.exit(1)


def get_default_dates() -> tuple:
    """
    获取默认的回测日期范围（最近252个交易日，约1年）
    
    Returns:
        (start_date, end_date) 格式: YYYYMMDD
    """
    end_date = datetime.now()
    # 252个交易日约等于1年
    start_date = end_date - timedelta(days=365)
    
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')


def validate_date(date_str: str) -> bool:
    """
    验证日期格式
    
    Args:
        date_str: 日期字符串 (YYYYMMDD)
        
    Returns:
        是否有效
    """
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False


def send_report_to_feishu(report: Dict[str, Any], config: Dict[str, Any], 
                          start_date: str, end_date: str) -> bool:
    """
    发送回测报告到飞书
    
    Args:
        report: 回测报告字典
        config: 配置字典
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        是否发送成功
    """
    try:
        # 获取用户ID
        notification_config = config.get('notification', {})
        user_id = notification_config.get('feishu_user_id', 
                                          'ou_b8a256a9cb526db6c196cb438d6893a6')
        
        # 生成报告摘要
        report_gen = ReportGenerator(config)
        feishu_report = report_gen.generate_feishu_report(report)
        
        # 添加日期信息
        header = f"📊 T01策略回测报告\n"
        header += f"回测期间: {start_date} - {end_date}\n"
        header += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "=" * 40 + "\n\n"
        
        full_message = header + feishu_report
        
        # 发送消息
        logger.info(f"📤 发送回测报告到飞书...")
        success = send_feishu_message_direct(user_id, full_message)
        
        if success:
            logger.info("✅ 飞书消息发送成功")
        else:
            logger.error("❌ 飞书消息发送失败")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 发送飞书消息异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='T01策略回测 - 龙头战法策略回测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 回测最近252个交易日
  python3 run_backtest.py
  
  # 指定日期范围回测
  python3 run_backtest.py --start-date 20240101 --end-date 20241231
  
  # 指定配置文件和输出路径
  python3 run_backtest.py --config my_config.yaml --output ./reports/
  
  # 不回测，仅生成报告
  python3 run_backtest.py --start-date 20240101 --end-date 20241231 --no-send
        """
    )
    
    parser.add_argument('--start-date', 
                        help='回测开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', 
                        help='回测结束日期 (YYYYMMDD)')
    parser.add_argument('--config', 
                        default='config.yaml', 
                        help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--output', 
                        help='报告输出路径 (默认: 当前目录)')
    parser.add_argument('--no-send', 
                        action='store_true', 
                        help='不发送飞书消息')
    
    args = parser.parse_args()
    
    # 处理日期参数
    if args.start_date and args.end_date:
        # 验证日期格式
        if not validate_date(args.start_date):
            logger.error(f"❌ 开始日期格式错误: {args.start_date} (应为YYYYMMDD)")
            sys.exit(1)
        if not validate_date(args.end_date):
            logger.error(f"❌ 结束日期格式错误: {args.end_date} (应为YYYYMMDD)")
            sys.exit(1)
        start_date = args.start_date
        end_date = args.end_date
    else:
        # 使用默认日期（最近252个交易日）
        start_date, end_date = get_default_dates()
        logger.info(f"📅 使用默认日期范围: {start_date} - {end_date}")
    
    # 确定配置文件路径
    config_path = args.config
    if not os.path.isabs(config_path):
        # 相对路径，相对于脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)
    
    # 加载配置
    logger.info(f"📂 加载配置文件: {config_path}")
    config = load_config(config_path)
    
    # 确定输出路径
    output_dir = args.output
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    logger.info("=" * 60)
    logger.info("🚀 T01策略回测启动")
    logger.info(f"   回测期间: {start_date} - {end_date}")
    logger.info(f"   配置文件: {config_path}")
    logger.info(f"   输出目录: {output_dir}")
    logger.info("=" * 60)
    
    try:
        # 初始化回测引擎
        logger.info("🔧 初始化回测引擎...")
        engine = BacktestEngine(config, start_date, end_date)
        
        # 加载历史数据
        logger.info("📊 加载历史数据...")
        engine.load_historical_data()
        
        # 执行回测
        logger.info("⚙️ 执行回测...")
        engine.run_backtest()
        
        # 计算指标
        logger.info("📈 计算绩效指标...")
        engine.calculate_metrics()
        
        # 生成报告
        logger.info("📝 生成回测报告...")
        report = engine.generate_report()
        
        # 保存报告到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"backtest_report_{start_date}_{end_date}_{timestamp}"
        
        # 保存JSON格式报告
        json_path = os.path.join(output_dir, f"{report_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 JSON报告已保存: {json_path}")
        
        # 生成并保存文本格式报告
        report_gen = ReportGenerator(config)
        text_report = report_gen.generate_text_report(report)
        text_path = os.path.join(output_dir, f"{report_filename}.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        logger.info(f"💾 文本报告已保存: {text_path}")
        
        # 输出关键指标
        metrics = report.get('metrics', {})
        logger.info("\n" + "=" * 60)
        logger.info("📊 回测结果摘要")
        logger.info("=" * 60)
        logger.info(f"   总收益率: {metrics.get('total_return', 0) * 100:.2f}%")
        logger.info(f"   年化收益率: {metrics.get('annual_return', 0) * 100:.2f}%")
        logger.info(f"   胜率: {metrics.get('win_rate', 0) * 100:.2f}%")
        logger.info(f"   最大回撤: {metrics.get('max_drawdown', 0) * 100:.2f}%")
        logger.info(f"   夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        logger.info(f"   总交易次数: {metrics.get('total_trades', 0)}")
        logger.info("=" * 60)
        
        # 发送飞书消息（如果未指定--no-send）
        if not args.no_send:
            send_report_to_feishu(report, config, start_date, end_date)
        else:
            logger.info("📭 跳过飞书消息发送 (--no-send)")
        
        logger.info("\n✅ 回测完成!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 回测被用户中断")
        return 130
    except Exception as e:
        logger.error(f"\n❌ 回测执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
