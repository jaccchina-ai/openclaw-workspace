#!/usr/bin/env python3
"""
飞书消息发送工具
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_feishu_message(message: str, user_id: Optional[str] = None) -> bool:
    """
    发送飞书消息
    
    Args:
        message: 消息内容
        user_id: 飞书用户ID，如果不提供则从环境变量读取
        
    Returns:
        是否发送成功
    """
    # 获取用户ID
    target_user = user_id or os.getenv('FEISHU_USER_ID')
    
    if not target_user:
        logger.error("未配置飞书用户ID，请设置 FEISHU_USER_ID 环境变量")
        return False
    
    try:
        # 尝试使用openclaw CLI发送
        import subprocess
        
        openclaw_path = os.getenv('OPENCLAW_PATH', 'openclaw')
        
        cmd = [
            openclaw_path,
            'message', 'send',
            '--channel', 'feishu',
            '--target', f'user:{target_user}',
            '--message', message
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("飞书消息发送成功")
            return True
        else:
            logger.error(f"飞书消息发送失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"飞书消息发送异常: {e}")
        return False


def send_feishu_message_simple(message: str, user_id: Optional[str] = None) -> bool:
    """
    简化版飞书消息发送（仅记录到日志，不依赖外部CLI）
    
    Args:
        message: 消息内容
        user_id: 飞书用户ID
        
    Returns:
        是否记录成功
    """
    target_user = user_id or os.getenv('FEISHU_USER_ID', 'unknown')
    
    logger.info(f"[飞书消息] 目标用户: {target_user}")
    logger.info(f"[飞书消息] 内容:\n{message}")
    
    # 同时写入消息日志文件
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'feishu_messages.log')
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"时间: {timestamp}\n")
        f.write(f"目标用户: {target_user}\n")
        f.write(f"内容:\n{message}\n")
    
    return True
