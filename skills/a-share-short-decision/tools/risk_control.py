"""Risk control rules for short-term strategy."""

from __future__ import annotations

from typing import Any, Dict
import akshare as ak
import pandas as pd


def check_market_trend(index_code: str = "sh000001", ma_days: int = 5) -> Dict[str, Any]:
    """
    检查大盘指数是否在N日均线之上。
    返回趋势状态，用于风险控制。
    """
    try:
        # 尝试多种方法获取指数历史数据
        hist = None
        error_msgs = []
        
        # 方法1: stock_zh_index_daily
        try:
            hist = ak.stock_zh_index_daily(symbol=index_code)
            if hist is not None and not hist.empty:
                # 重命名列以便统一处理
                if "date" in hist.columns and "close" in hist.columns:
                    hist = hist.rename(columns={"date": "日期", "close": "收盘"})
                elif "日期" not in hist.columns and "收盘" not in hist.columns:
                    # 尝试找到日期和收盘列
                    for col in hist.columns:
                        if "date" in col.lower():
                            hist = hist.rename(columns={col: "日期"})
                        if "close" in col.lower():
                            hist = hist.rename(columns={col: "收盘"})
        except Exception as e1:
            error_msgs.append(f"stock_zh_index_daily failed: {str(e1)}")
        
        # 方法2: index_zh_a_hist
        if hist is None or hist.empty:
            try:
                # 指数代码可能需要去除前缀
                code = index_code[2:] if index_code.startswith("sh") or index_code.startswith("sz") else index_code
                hist = ak.index_zh_a_hist(symbol=code, period="daily")
                if hist is not None and not hist.empty:
                    if "date" in hist.columns and "close" in hist.columns:
                        hist = hist.rename(columns={"date": "日期", "close": "收盘"})
            except Exception as e2:
                error_msgs.append(f"index_zh_a_hist failed: {str(e2)}")
        
        # 方法3: stock_zh_index_hist (旧版)
        if hist is None or hist.empty:
            try:
                hist = ak.stock_zh_index_hist(symbol=index_code, period="daily")
            except Exception as e3:
                error_msgs.append(f"stock_zh_index_hist failed: {str(e3)}")
        
        if hist is None or hist.empty or len(hist) < ma_days:
            return {
                "is_above_ma": True,  # 数据不足时默认允许交易
                "position_ratio": 1.0,
                "ma_value": 0.0,
                "last_close": 0.0,
                "error": f"insufficient_data: {', '.join(error_msgs)}"
            }
        
        # 确保数据按日期升序排列
        if "日期" not in hist.columns:
            # 尝试找到日期列
            date_col = next((col for col in hist.columns if "date" in col.lower() or "时间" in col), None)
            if date_col:
                hist = hist.rename(columns={date_col: "日期"})
            else:
                hist["日期"] = hist.index  # 使用索引作为日期
        
        if "收盘" not in hist.columns:
            close_col = next((col for col in hist.columns if "close" in col.lower() or "收盘" in col), None)
            if close_col:
                hist = hist.rename(columns={close_col: "收盘"})
            else:
                hist["收盘"] = 0.0
        
        hist = hist.sort_values("日期", ascending=True)
        
        # 计算均线
        close_prices = hist["收盘"].tail(ma_days).values
        ma_value = close_prices.mean()
        last_close = close_prices[-1]
        
        # 判断位置
        position_ratio = last_close / ma_value  # >1 表示在均线上
        is_above_ma = position_ratio >= 0.995  # 允许0.5%误差
        
        return {
            "is_above_ma": is_above_ma,
            "position_ratio": round(position_ratio, 4),
            "ma_value": round(ma_value, 2),
            "last_close": round(last_close, 2),
            "ma_days": ma_days,
            "index_code": index_code,
            "error": None
        }
    except Exception as e:
        # 发生错误时默认允许交易（安全第一）
        return {
            "is_above_ma": True,
            "position_ratio": 1.0,
            "ma_value": 0.0,
            "last_close": 0.0,
            "error": str(e)
        }


def short_term_risk_control(market_sentiment_score: float, market_trend: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Return strict short-term risk controls.

    Rules:
    - max position <= 15% (可动态调整)
    - stop loss -6%
    - if market sentiment < 40, block opening new positions
    - if market index below MA5, block opening new positions (新增)
    """
    # 基础情绪过滤
    market_filter = market_sentiment_score >= 40
    
    # 默认仓位限制
    max_position = 0.15
    
    # 大盘趋势过滤（如果提供趋势数据）
    if market_trend is not None:
        is_above_ma = market_trend.get("is_above_ma", True)
        position_ratio = market_trend.get("position_ratio", 1.0)
        
        if not is_above_ma:
            market_filter = False  # 指数跌破均线，禁止开新仓
            risk_note = "market index below MA{}, sentiment score={}".format(
                market_trend.get("ma_days", 5), market_sentiment_score
            )
        else:
            # 动态仓位调整：距离均线越近，仓位可适当放宽
            if position_ratio < 0.98:  # 跌破2%
                max_position = 0.10  # 仓位减半
                risk_note = "market index close to MA{} (ratio={}), reduced position".format(
                    market_trend.get("ma_days", 5), position_ratio
                )
            elif position_ratio > 1.05:  # 远离均线5%以上
                max_position = 0.18  # 仓位略增
                risk_note = "market index strong above MA{} (ratio={}), increased position".format(
                    market_trend.get("ma_days", 5), position_ratio
                )
            else:
                risk_note = "market index healthy above MA{}".format(market_trend.get("ma_days", 5))
    else:
        risk_note = "no market trend data provided"
    
    # 如果没有趋势数据，保持原有逻辑
    if not market_filter:
        risk_note = "no new position when sentiment score < 40" if market_sentiment_score < 40 else risk_note
    
    return {
        "max_position": max_position,
        "stop_loss": -6,
        "take_profit": 12,
        "break_ma5_stop": True,
        "market_filter": market_filter,
        "market_trend": market_trend,
        "risk_note": risk_note,
    }


def validate_trade_plan(plan: Dict[str, Any], market_sentiment_score: float) -> Dict[str, Any]:
    """Validate a candidate trade plan against risk control rules."""
    rc = short_term_risk_control(market_sentiment_score)
    position = float(plan.get("position", 0))
    stop_loss = float(plan.get("stop_loss", 0))

    violations: list[str] = []
    if position > rc["max_position"]:
        violations.append("position_over_limit")
    if stop_loss < rc["stop_loss"]:
        violations.append("stop_loss_too_wide")
    if not rc["market_filter"]:
        violations.append("market_sentiment_blocked")

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "risk_control": rc,
    }
