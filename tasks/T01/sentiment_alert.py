#!/usr/bin/env python3
"""
情绪指标预警系统 - 飞书推送脚本
"""

import sys
import os
import json
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sentiment_monitor import MarketSentimentMonitor


def send_feishu_message(message: str, user_id: str = None):
    """发送飞书消息"""
    try:
        # 使用 openclaw CLI 发送消息
        import subprocess
        
        cmd = [
            '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
            'message', 'send',
            '--channel', 'feishu',
            '--message', message
        ]
        
        if user_id:
            cmd.extend(['--target', f'user:{user_id}'])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ 飞书消息发送成功")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送飞书消息异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='情绪指标监控并推送飞书')
    parser.add_argument('--date', type=str, help='指定日期 (YYYYMMDD)')
    parser.add_argument('--config', type=str, default='./config.yaml', help='配置文件路径')
    parser.add_argument('--user-id', type=str, default='ou_b8a256a9cb526db6c196cb438d6893a6', help='飞书用户ID')
    parser.add_argument('--force', action='store_true', help='强制发送报告（无论是否有预警）')
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if os.path.exists(args.config):
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    
    # 创建监控器
    monitor = MarketSentimentMonitor(config)
    
    # 分析情绪
    print(f"正在分析市场情绪...")
    result = monitor.analyze_sentiment(args.date)
    
    # 格式化报告
    report = monitor.format_report(result)
    print(report)
    
    # 检查是否需要发送
    should_send = args.force
    alert_info = ""
    
    if not should_send:
        alert = monitor.check_alert(result)
        if alert:
            should_send = True
            alert_info = f"\n🚨 {alert['message']}\n"
    
    # 发送飞书消息
    if should_send:
        message = report + alert_info
        message += f"\n⏰ 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        send_feishu_message(message, args.user_id)
    else:
        print("\n✅ 市场情绪正常，无需发送预警")


if __name__ == '__main__':
    main()
