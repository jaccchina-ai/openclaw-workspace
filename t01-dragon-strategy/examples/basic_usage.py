#!/usr/bin/env python3
"""
T01 龙头战法选股策略 - 简单示例
展示如何使用核心功能
"""

import os
import sys

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from limit_up_strategy import LimitUpScoringStrategyV2
import yaml


def load_config(config_path='config.yaml'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 从环境变量替换占位符
    if '${TUSHARE_TOKEN}' in str(config):
        token = os.getenv('TUSHARE_TOKEN', '')
        config_str = yaml.dump(config)
        config_str = config_str.replace('${TUSHARE_TOKEN}', token)
        config = yaml.safe_load(config_str)
    
    if '${FEISHU_USER_ID}' in str(config):
        user_id = os.getenv('FEISHU_USER_ID', '')
        config_str = yaml.dump(config)
        config_str = config_str.replace('${FEISHU_USER_ID}', user_id)
        config = yaml.safe_load(config_str)
    
    return config


def example_t_day_scoring():
    """T日评分示例"""
    print("=" * 50)
    print("T日涨停股评分示例")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 初始化策略
    strategy = LimitUpScoringStrategyV2(config)
    
    # 运行T日评分
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"\n运行日期: {today}")
    print("正在获取涨停股数据...")
    
    # 这里调用实际的评分函数
    # result = strategy.run_t_day_scoring(today)
    
    print("\n评分完成！")
    print("查看 output/ 目录获取详细结果")


def example_t1_auction():
    """T+1竞价分析示例"""
    print("=" * 50)
    print("T+1竞价分析示例")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 初始化策略
    strategy = LimitUpScoringStrategyV2(config)
    
    # 运行T+1竞价分析
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"\n运行日期: {today}")
    print("正在获取竞价数据...")
    
    # 这里调用实际的竞价分析函数
    # result = strategy.run_t1_auction_analysis(today)
    
    print("\n竞价分析完成！")
    print("查看 output/ 目录获取详细结果")


def example_custom_config():
    """自定义配置示例"""
    print("=" * 50)
    print("自定义配置示例")
    print("=" * 50)
    
    # 创建自定义配置
    custom_config = {
        'api': {
            'api_key': os.getenv('TUSHARE_TOKEN', ''),
            'endpoint': 'http://api.tushare.pro',
            'timeout': 30
        },
        'strategy': {
            't_day_scoring': {
                'first_limit_time': 30,
                'seal_amount_ratio': 20,
                'order_amount_to_circ_mv': 15,
            },
            'risk_control': {
                'min_total_score': 60,
                'max_position_per_stock': 0.2
            }
        }
    }
    
    print("\n自定义配置:")
    print(f"最低入选分数: {custom_config['strategy']['risk_control']['min_total_score']}")
    print(f"单股最大仓位: {custom_config['strategy']['risk_control']['max_position_per_stock']}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='T01策略示例')
    parser.add_argument('--example', choices=['t_day', 't1_auction', 'config'], 
                        default='t_day', help='选择示例')
    
    args = parser.parse_args()
    
    if args.example == 't_day':
        example_t_day_scoring()
    elif args.example == 't1_auction':
        example_t1_auction()
    elif args.example == 'config':
        example_custom_config()
