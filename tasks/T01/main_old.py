#!/usr/bin/env python3
"""
T01 龙头战法选股主程序 - 涨停股评分系统
"""

import argparse
import logging
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from limit_up_strategy import LimitUpScoringStrategy
from output_formatter import OutputFormatter


def setup_logging(level=logging.INFO):
    """配置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('t01_screening.log', encoding='utf-8')
        ]
    )


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='龙头战法选股系统 T01')
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['screen', 'test', 'config'],
        default='screen',
        help='运行模式: screen=执行选股, test=测试连接, config=查看配置'
    )
    
    parser.add_argument(
        '--output',
        choices=['table', 'json', 'csv', 'all'],
        default='table',
        help='输出格式 (默认: table)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='保存结果到文件'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    # 检查配置文件是否存在
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        print(f"请创建配置文件: {config_path}")
        print("可复制 config.example.yaml 并修改")
        sys.exit(1)
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if args.mode == 'config':
        # 显示配置
        print("当前配置:")
        print(yaml.dump(config, allow_unicode=True, default_flow_style=False))
        return
    
    # 初始化筛选器
    logger.info(f"初始化龙头战法选股系统 (T01)...")
    screener = StockScreener(args.config)
    
    if args.mode == 'test':
        # 测试模式
        logger.info("运行测试模式...")
        # 这里可以添加API连接测试等
        print("测试模式待实现 (需要API文档)")
        return
    
    # 执行选股
    logger.info("开始执行选股筛选...")
    try:
        results = screener.run_screening()
        
        # 初始化输出格式化器
        formatter = OutputFormatter(config)
        
        # 输出结果
        if args.output in ['table', 'all']:
            print("\n" + "="*60)
            print("龙头战法选股结果")
            print("="*60)
            table_output = formatter.to_table(results)
            print(table_output)
        
        if args.save or args.output in ['json', 'csv', 'all']:
            if args.output in ['json', 'all']:
                json_file = formatter.to_json(results)
                print(f"\nJSON结果已保存: {json_file}")
            
            if args.output in ['csv', 'all']:
                csv_file = formatter.to_csv(results)
                print(f"CSV结果已保存: {csv_file}")
        
        # 显示告警
        alerts = formatter.generate_alerts(results)
        if alerts:
            print("\n" + "!"*60)
            print("告警信息")
            print("!"*60)
            for alert in alerts:
                print(f"⚠️  {alert}")
        
        # 显示摘要
        summary = results.get('summary', {})
        if summary:
            print("\n" + "-"*60)
            print("筛选摘要")
            print("-"*60)
            print(f"候选股票数量: {summary.get('total_candidates', 0)}")
            print(f"排名股票数量: {summary.get('total_ranked', 0)}")
            print(f"告警数量: {summary.get('alert_count', 0)}")
            print(f"生成时间: {summary.get('generated_at', 'N/A')}")
        
        logger.info("选股完成")
        
    except Exception as e:
        logger.error(f"选股过程中发生错误: {e}", exc_info=True)
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()