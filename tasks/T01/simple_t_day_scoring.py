#!/usr/bin/env python3
"""
简化T日评分脚本 - 只使用Tushare API
确保生成候选股文件供明日竞价分析使用
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tushare as ts
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_tushare():
    """初始化Tushare API"""
    token = "870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab"
    if not token:
        logger.error("Tushare token未配置")
        sys.exit(1)
    
    ts.set_token(token)
    pro = ts.pro_api()
    logger.info("Tushare API初始化成功")
    return pro

def get_limit_up_stocks(pro, trade_date):
    """获取当日涨停股票 - 只使用Tushare limit_list_d接口"""
    try:
        logger.info(f"获取 {trade_date} 涨停股票...")
        
        # 使用limit_list_d接口
        df = pro.limit_list_d(trade_date=trade_date)
        
        if df is None or df.empty:
            logger.warning(f"日期 {trade_date} 没有涨停股票")
            return pd.DataFrame()
        
        logger.info(f"获取到 {len(df)} 只涨停股票")
        return df
        
    except Exception as e:
        logger.error(f"获取涨停股票失败: {e}")
        return pd.DataFrame()

def filter_stocks(df):
    """过滤股票 - 剔除ST、北交所、科创板"""
    if df.empty:
        return df
    
    # 移除ST股票
    df = df[~df['ts_code'].str.contains('ST')]
    
    # 移除北交所股票（代码以'8'开头）
    df = df[~df['ts_code'].str.startswith('8')]
    
    # 移除科创板股票（代码以'688'开头）
    df = df[~df['ts_code'].str.startswith('688')]
    
    logger.info(f"过滤后剩余 {len(df)} 只股票")
    return df

def calculate_basic_score(row):
    """计算基础评分 - 只基于Tushare数据"""
    score = 0
    
    # 1. 首次涨停时间 (权重: 30分)
    try:
        first_time = str(row.get('first_time', '0')).zfill(6)
        if first_time <= '093000':  # 9:30前涨停
            score += 30
        elif first_time <= '100000':  # 10:00前涨停
            score += 25
        elif first_time <= '110000':  # 11:00前涨停
            score += 20
        elif first_time <= '133000':  # 13:30前涨停
            score += 15
        elif first_time <= '140000':  # 14:00前涨停
            score += 10
        else:  # 14:00后涨停
            score += 5
    except:
        pass
    
    # 2. 封成比 (权重: 25分)
    try:
        fd_amount = float(row.get('fd_amount', 0))
        amount = float(row.get('amount', 1))
        if amount > 0:
            seal_ratio = fd_amount / amount
            if seal_ratio >= 0.3:  # 30%以上
                score += 25
            elif seal_ratio >= 0.2:
                score += 20
            elif seal_ratio >= 0.15:
                score += 15
            elif seal_ratio >= 0.1:
                score += 10
            elif seal_ratio >= 0.05:
                score += 5
    except:
        pass
    
    # 3. 封单金额/流通市值 (权重: 15分)
    try:
        fd_amount = float(row.get('fd_amount', 0))
        float_mv = float(row.get('float_mv', 1))
        if float_mv > 0:
            seal_to_mv = fd_amount / float_mv
            if seal_to_mv >= 0.01:  # 1%以上
                score += 15
            elif seal_to_mv >= 0.005:
                score += 10
            elif seal_to_mv >= 0.003:
                score += 5
    except:
        pass
    
    # 4. 换手率 (权重: 10分)
    try:
        turnover = float(row.get('turnover_rate', 0))
        if 3 <= turnover <= 15:  # 3-15%理想区间
            score += 10
        elif 15 < turnover <= 25:
            score += 7
        elif turnover > 25:
            score += 3
        elif turnover < 3:
            score += 2
    except:
        pass
    
    # 5. 成交金额 (权重: 10分)
    try:
        amount = float(row.get('amount', 0))
        if amount >= 1000000000:  # 10亿以上
            score += 10
        elif amount >= 500000000:
            score += 8
        elif amount >= 200000000:
            score += 6
        elif amount >= 100000000:
            score += 4
        else:
            score += 2
    except:
        pass
    
    # 基础分加龙虎榜分数
    try:
        dragon_score = float(row.get('dragon_score', 0))
        score += dragon_score
    except:
        pass
    
    return score

def score_stocks(df):
    """对股票进行评分"""
    if df.empty:
        return pd.DataFrame()
    
    # 计算基础评分
    df['basic_score'] = df.apply(calculate_basic_score, axis=1)
    
    # 按评分排序
    df = df.sort_values('basic_score', ascending=False)
    
    # 取前10名
    top_n = min(10, len(df))
    result_df = df.head(top_n).copy()
    
    logger.info(f"评分完成，前{top_n}名股票已选出")
    return result_df

def format_candidate(stock):
    """格式化候选股数据"""
    candidate = {
        'ts_code': stock['ts_code'],
        'name': stock.get('name', ''),
        'trade_date': stock.get('trade_date', ''),
        'close': float(stock.get('close', 0)),
        'pct_chg': float(stock.get('pct_chg', 0)),
        'industry': stock.get('industry', ''),
        'basic_score': float(stock.get('basic_score', 0)),
        'total_score': float(stock.get('basic_score', 0)),  # 简化版只用基础分
        'score_details': {
            'first_limit_time': 0,
            'order_quality': 0,
            'liquidity': 0,
            'money_flow': 0,
            'sector': 0,
            'dragon_list': float(stock.get('dragon_score', 0)),
            'sentiment': 0
        },
        'first_limit_time': str(stock.get('first_time', '0')).zfill(6),
        'seal_ratio': float(stock.get('fd_amount', 0)) / float(stock.get('amount', 1)) if stock.get('amount', 0) > 0 else 0,
        'seal_to_mv': float(stock.get('fd_amount', 0)) / float(stock.get('float_mv', 1)) if stock.get('float_mv', 0) > 0 else 0,
        'fd_amount': float(stock.get('fd_amount', 0)),
        'amount': float(stock.get('amount', 0)),
        'float_mv': float(stock.get('float_mv', 0)),
        'turnover_rate': float(stock.get('turnover_rate', 0)),
        'main_net_amount': float(stock.get('main_net_amount', 0)),
        'main_net_ratio': float(stock.get('main_net_ratio', 0)),
        'is_hot_sector': False,  # 简化版不分析热点板块
        'dragon_score': float(stock.get('dragon_score', 0)),
        'sentiment_score': 0  # 简化版无舆情分析
    }
    return candidate

def save_candidates(candidates, trade_date):
    """保存候选股到文件"""
    try:
        # 计算T+1日期
        t_date = trade_date
        t1_date = str(int(trade_date) + 1)  # 简化处理
        
        state_dir = os.path.join(os.path.dirname(__file__), "state")
        os.makedirs(state_dir, exist_ok=True)
        
        filename = f"candidates_{t_date}_to_{t1_date}.json"
        filepath = os.path.join(state_dir, filename)
        
        data = {
            't_date': t_date,
            't1_date': t1_date,
            'candidates': candidates
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"候选股文件已保存: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"保存候选股文件失败: {e}")
        return False

def main():
    """主函数"""
    # 获取当前日期
    trade_date = datetime.now().strftime('%Y%m%d')
    logger.info(f"开始T日评分 (日期: {trade_date}) - 只使用Tushare API")
    
    # 初始化Tushare
    pro = setup_tushare()
    
    # 获取涨停股票
    df = get_limit_up_stocks(pro, trade_date)
    if df.empty:
        logger.error("没有涨停股票，任务结束")
        sys.exit(1)
    
    # 过滤股票
    df = filter_stocks(df)
    if df.empty:
        logger.error("过滤后没有符合条件的股票")
        sys.exit(1)
    
    # 评分
    scored_df = score_stocks(df)
    if scored_df.empty:
        logger.error("评分后没有符合条件的股票")
        sys.exit(1)
    
    # 格式化候选股
    candidates = []
    for _, stock in scored_df.iterrows():
        candidate = format_candidate(stock)
        candidates.append(candidate)
    
    # 保存候选股文件
    success = save_candidates(candidates, trade_date)
    
    if success:
        logger.info(f"✅ T日评分完成！共选出 {len(candidates)} 只候选股")
        logger.info("候选股列表:")
        for i, cand in enumerate(candidates[:5], 1):
            logger.info(f"  {i}. {cand['name']} ({cand['ts_code']}) - 总分: {cand['total_score']:.2f}")
    else:
        logger.error("❌ T日评分失败")
        sys.exit(1)

if __name__ == "__main__":
    main()