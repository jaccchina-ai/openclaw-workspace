#!/usr/bin/env python3
"""
交易日历工具函数
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, List

# 默认交易日历文件路径
DEFAULT_CALENDAR_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trading_calendar.json')


def load_trading_calendar(calendar_path: Optional[str] = None) -> dict:
    """
    加载交易日历
    
    Args:
        calendar_path: 日历文件路径，默认使用内置日历
        
    Returns:
        交易日历字典
    """
    path = calendar_path or DEFAULT_CALENDAR_PATH
    
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 返回空日历
    return {'trading_days': [], 'last_updated': None}


def is_trading_day(date_str: str, calendar_path: Optional[str] = None) -> bool:
    """
    判断是否为交易日
    
    Args:
        date_str: 日期字符串 (YYYYMMDD)
        calendar_path: 日历文件路径
        
    Returns:
        是否为交易日
    """
    # 首先检查周末
    dt = datetime.strptime(date_str, '%Y%m%d')
    if dt.weekday() >= 5:  # 周六或周日
        return False
    
    # 然后检查交易日历
    calendar = load_trading_calendar(calendar_path)
    return date_str in calendar.get('trading_days', [])


def get_prev_trading_day(date_str: str, calendar_path: Optional[str] = None) -> Optional[str]:
    """
    获取前一个交易日
    
    Args:
        date_str: 日期字符串 (YYYYMMDD)
        calendar_path: 日历文件路径
        
    Returns:
        前一个交易日字符串，如果没有则返回None
    """
    calendar = load_trading_calendar(calendar_path)
    trading_days = calendar.get('trading_days', [])
    
    if date_str in trading_days:
        idx = trading_days.index(date_str)
        if idx > 0:
            return trading_days[idx - 1]
    
    # 如果不在日历中，向前查找
    dt = datetime.strptime(date_str, '%Y%m%d')
    for i in range(1, 10):  # 最多向前查10天
        prev_dt = dt - timedelta(days=i)
        prev_str = prev_dt.strftime('%Y%m%d')
        if prev_str in trading_days:
            return prev_str
    
    return None


def get_next_trading_day(date_str: str, calendar_path: Optional[str] = None) -> Optional[str]:
    """
    获取后一个交易日
    
    Args:
        date_str: 日期字符串 (YYYYMMDD)
        calendar_path: 日历文件路径
        
    Returns:
        后一个交易日字符串，如果没有则返回None
    """
    calendar = load_trading_calendar(calendar_path)
    trading_days = calendar.get('trading_days', [])
    
    if date_str in trading_days:
        idx = trading_days.index(date_str)
        if idx < len(trading_days) - 1:
            return trading_days[idx + 1]
    
    # 如果不在日历中，向后查找
    dt = datetime.strptime(date_str, '%Y%m%d')
    for i in range(1, 10):  # 最多向后查10天
        next_dt = dt + timedelta(days=i)
        next_str = next_dt.strftime('%Y%m%d')
        if next_str in trading_days:
            return next_str
    
    return None


def get_trading_days_in_range(start_date: str, end_date: str, calendar_path: Optional[str] = None) -> List[str]:
    """
    获取日期范围内的所有交易日
    
    Args:
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        calendar_path: 日历文件路径
        
    Returns:
        交易日列表
    """
    calendar = load_trading_calendar(calendar_path)
    trading_days = calendar.get('trading_days', [])
    
    result = []
    for day in trading_days:
        if start_date <= day <= end_date:
            result.append(day)
    
    return result
