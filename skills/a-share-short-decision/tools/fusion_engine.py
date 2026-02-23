"""Signal fusion engine for short-term stock decisions."""

from __future__ import annotations

from typing import Any, Dict, List

from .debug_utils import resolve_debug, with_debug
from .indicators import clamp
from .market_data import get_market_sentiment, get_sector_rotation, scan_strong_stocks
from .money_flow import analyze_capital_flow
from .risk_control import short_term_risk_control, check_market_trend
from .settings import get_screener_config


def _calc_sector_score(top_sectors: List[dict[str, Any]]) -> float:
    if not top_sectors:
        return 0.0
    top3 = top_sectors[:3]
    return sum(float(x.get("strength", 0.0)) for x in top3) / len(top3)


def _calc_stock_volume_score(stocks: List[dict[str, Any]]) -> float:
    if not stocks:
        return 0.0
    top = stocks[0]
    ratio = float(top.get("volume_ratio", 0.0))
    change = float(top.get("change_pct", 0.0))
    return clamp(ratio / 3.0 * 60 + change / 10.0 * 40, 0, 100)


def _calc_capital_score(capital: dict[str, Any]) -> float:
    main_flow = float(capital.get("main_flow", 0.0))
    inflow_days = float(capital.get("northbound_inflow_days", 0.0))
    score = clamp(main_flow / 300_000_000 * 70, 0, 70) + clamp(inflow_days / 5 * 30, 0, 30)
    return clamp(score, 0, 100)


def _calc_technical_score(stocks: List[dict[str, Any]]) -> float:
    if not stocks:
        return 0.0
    top = stocks[0]
    ratio = float(top.get("volume_ratio", 0.0))
    return clamp(55 + ratio * 10, 0, 100)


def _calc_liquidity_score(stocks: List[dict[str, Any]]) -> float:
    """
    计算流动性因子分数（0-100）
    成交金额分位数×40% + 换手率分位数×30% + 振幅分位数×30%
    """
    if not stocks:
        return 0.0
    
    # 提取所有候选股的成交金额、换手率和振幅
    turnovers = []
    turnover_rates = []
    amplitudes = []
    
    for stock in stocks:
        turnover = float(stock.get("turnover", 0.0))  # 亿元
        turnover_rate = float(stock.get("turnover_rate", 0.0))  # %
        amplitude = float(stock.get("amplitude", 0.0))  # %
        
        # 设置合理范围过滤异常值
        if 0 <= turnover <= 100:  # 成交金额0-100亿元
            turnovers.append(turnover)
        if 0 <= turnover_rate <= 50:  # 换手率0-50%
            turnover_rates.append(turnover_rate)
        if 0 <= amplitude <= 30:  # 振幅0-30%
            amplitudes.append(amplitude)
    
    if not turnovers or not turnover_rates or not amplitudes:
        return 50.0  # 数据不足时返回中性分数
    
    # 计算分位数（相对于候选股池）
    # 简单归一化：当前值 / 最大值 * 100
    max_turnover = max(turnovers) if max(turnovers) > 0 else 1.0
    max_turnover_rate = max(turnover_rates) if max(turnover_rates) > 0 else 1.0
    max_amplitude = max(amplitudes) if max(amplitudes) > 0 else 1.0
    
    # 取排名第一的股票（即最强候选股）
    top_stock = stocks[0]
    top_turnover = float(top_stock.get("turnover", 0.0))
    top_turnover_rate = float(top_stock.get("turnover_rate", 0.0))
    top_amplitude = float(top_stock.get("amplitude", 0.0))
    
    # 计算分位数分数（0-100）
    turnover_score = min(100.0, (top_turnover / max_turnover) * 100)
    turnover_rate_score = min(100.0, (top_turnover_rate / max_turnover_rate) * 100)
    amplitude_score = min(100.0, (top_amplitude / max_amplitude) * 100)
    
    # 加权合并：成交金额×40% + 换手率×30% + 振幅×30%
    liquidity_score = (
        turnover_score * 0.4 +
        turnover_rate_score * 0.3 +
        amplitude_score * 0.3
    )
    
    return clamp(liquidity_score, 0, 100)


def _calc_price_volume_score(stocks: List[dict[str, Any]]) -> float:
    """
    计算量价配合度分数（0-100）
    检测价格上涨是否伴随放量（量价背离预警）
    增强版：更精细的量价关系检测
    """
    if not stocks:
        return 0.0
    
    # 取排名第一的股票（即最强候选股）
    top_stock = stocks[0]
    change_pct = float(top_stock.get("change_pct", 0.0))  # 涨幅百分比
    volume_ratio = float(top_stock.get("volume_ratio", 0.0))  # 量比
    amplitude = float(top_stock.get("amplitude", 0.0))  # 振幅（%）
    
    # 基础分数
    base_score = 50.0
    volume_score = 0.0
    price_score = 0.0
    divergence_penalty = 0.0
    pattern_bonus = 0.0
    
    # 1. 量能评分（0-30分）
    if volume_ratio > 0:
        if volume_ratio > 2.5:  # 巨量
            volume_score = 30.0
            pattern_bonus += 5.0  # 巨量关注
        elif volume_ratio > 1.8:  # 放量明显
            volume_score = 25.0
            pattern_bonus += 3.0
        elif volume_ratio > 1.2:  # 温和放量
            volume_score = 20.0
            pattern_bonus += 2.0
        elif volume_ratio > 0.8:  # 量能正常
            volume_score = 15.0
        elif volume_ratio > 0.5:  # 缩量
            volume_score = 10.0
            divergence_penalty += 5.0  # 缩量预警
        else:  # 严重缩量
            volume_score = 5.0
            divergence_penalty += 10.0
    
    # 2. 价格评分（0-20分）
    if change_pct > 0:
        if change_pct > 7.0:  # 大涨
            price_score = 20.0
            pattern_bonus += 5.0
        elif change_pct > 4.0:  # 中涨
            price_score = 15.0
            pattern_bonus += 2.0
        elif change_pct > 1.0:  # 小涨
            price_score = 10.0
        else:  # 微涨
            price_score = 5.0
    else:
        if change_pct < -5.0:  # 大跌
            price_score = 0.0
            divergence_penalty += 15.0
        elif change_pct < -2.0:  # 中跌
            price_score = 5.0
            divergence_penalty += 10.0
        else:  # 微跌
            price_score = 10.0
    
    # 3. 振幅分析（0-10分）
    amplitude_score = 0.0
    if amplitude > 0:
        if amplitude > 10.0:  # 高波动
            amplitude_score = 10.0
            if change_pct > 3.0:  # 高波动上涨，强势
                pattern_bonus += 3.0
            elif change_pct < -3.0:  # 高波动下跌，风险
                divergence_penalty += 5.0
        elif amplitude > 5.0:  # 中波动
            amplitude_score = 7.0
        elif amplitude > 2.0:  # 低波动
            amplitude_score = 5.0
        else:  # 极低波动
            amplitude_score = 3.0
    
    # 4. 量价背离精细检测
    # a) 价格上涨但量能不足（最危险背离）
    if change_pct > 5.0 and volume_ratio < 0.7:
        divergence_penalty += 25.0  # 严重背离
    elif change_pct > 3.0 and volume_ratio < 0.8:
        divergence_penalty += 15.0
    
    # b) 价格下跌但放量（恐慌抛售）
    if change_pct < -4.0 and volume_ratio > 2.0:
        divergence_penalty += 20.0
    
    # c) 价格窄幅震荡但巨量（可能异动或对倒）
    if abs(change_pct) < 1.5 and volume_ratio > 2.5:
        if change_pct > 0:
            pattern_bonus += 5.0  # 异动吸筹可能
        else:
            divergence_penalty += 8.0  # 对倒出货可能
    
    # d) 价格新高但量能未新高（顶背离预警）
    # 注意：需要历史数据，此处无法判断，标记为TODO
    
    # 5. 综合评分
    score = base_score + volume_score + price_score + amplitude_score + pattern_bonus - divergence_penalty
    
    # 6. 特殊模式识别
    # 涨停板量价关系
    if top_stock.get("is_limit_up", False):
        if volume_ratio > 1.5:  # 放量涨停，强势
            score = min(100.0, score + 8.0)
        elif volume_ratio < 0.7:  # 缩量涨停，惜售
            score = min(100.0, score + 5.0)
    
    return clamp(score, 0, 100)


def _calc_intra_sector_strength_score(stocks: List[dict[str, Any]]) -> float:
    """
    计算板块内相对强度因子分数（0-100）
    个股 vs 所属板块的平均表现（基于候选股池）
    """
    if not stocks or len(stocks) < 2:
        return 50.0  # 数据不足时返回中性分数
    
    # 取排名第一的股票（即最强候选股）
    top_stock = stocks[0]
    top_sector = top_stock.get("sector", "")
    top_change = float(top_stock.get("change_pct", 0.0))
    
    if not top_sector:
        return 50.0
    
    # 收集同一板块内所有候选股的涨幅
    sector_changes = []
    for stock in stocks:
        sector = stock.get("sector", "")
        if sector == top_sector:
            change_pct = float(stock.get("change_pct", 0.0))
            sector_changes.append(change_pct)
    
    if len(sector_changes) < 2:
        return 50.0  # 板块内股票不足
    
    # 计算板块平均涨幅和标准差
    n = len(sector_changes)
    mean_change = sum(sector_changes) / n
    
    # 计算方差
    variance = sum((x - mean_change) ** 2 for x in sector_changes) / max(n - 1, 1)
    import math
    std_change = math.sqrt(variance) if variance > 0 else 1.0
    
    # 计算相对强度（Z-score）
    if std_change > 0:
        z_score = (top_change - mean_change) / std_change
    else:
        z_score = 0.0
    
    # 将Z-score映射到0-100分
    # 比板块平均每高1个标准差，加15分（比整个候选股池的20分略低）
    normalized_score = 50.0 + (z_score * 15.0)
    
    # 额外加分：如果个股是板块内唯一涨幅超过阈值的
    if top_change > 5.0 and all(x < 3.0 for x in sector_changes if x != top_change):
        normalized_score = min(100.0, normalized_score + 10.0)
    
    return clamp(normalized_score, 0, 100)


def _calc_relative_strength_score(stocks: List[dict[str, Any]]) -> float:
    """
    计算相对强度因子分数（0-100）
    个股 vs 候选股池的相对表现
    """
    if not stocks or len(stocks) < 2:
        return 50.0  # 数据不足时返回中性分数
    
    # 提取所有候选股的涨幅
    changes = []
    for stock in stocks:
        change_pct = float(stock.get("change_pct", 0.0))
        changes.append(change_pct)
    
    if not changes:
        return 50.0
    
    # 计算候选股池的平均涨幅和标准差（手动计算，避免numpy依赖）
    n = len(changes)
    mean_change = sum(changes) / n
    
    # 计算方差
    variance = sum((x - mean_change) ** 2 for x in changes) / max(n - 1, 1)
    import math
    std_change = math.sqrt(variance) if variance > 0 else 1.0
    
    # 取排名第一的股票（即最强候选股）
    top_stock = stocks[0]
    top_change = float(top_stock.get("change_pct", 0.0))
    
    # 计算相对强度（Z-score标准化）
    if std_change > 0:
        z_score = (top_change - mean_change) / std_change
    else:
        z_score = 0.0
    
    # 将Z-score映射到0-100分
    # Z-score在-2到+2之间，映射到0-100分
    normalized_score = 50.0 + (z_score * 20.0)  # 每1个标准差对应20分
    
    return clamp(normalized_score, 0, 100)


def _calc_market_cap_score(stocks: List[dict[str, Any]], macro_weight: float = 0.5) -> float:
    """
    计算流通市值因子分数（0-100）
    评估股票市值风格的适宜性，根据宏观环境动态调整
    macro_weight: 宏观权重（0-1，越高表示宏观环境越好）
    """
    if not stocks:
        return 50.0  # 数据不足时返回中性分数
    
    # 取排名第一的股票（即最强候选股）
    top_stock = stocks[0]
    circ_mv = float(top_stock.get("circ_mv", 0.0))  # 流通市值（亿元）
    
    if circ_mv <= 0:
        return 50.0  # 数据缺失
    
    # 基础市值分档评分（亿元）
    if circ_mv < 30:
        base_score = 30.0   # 微小盘，高风险
        size_type = "micro"
    elif circ_mv < 100:
        base_score = 60.0   # 小盘，适中
        size_type = "small"
    elif circ_mv < 300:
        base_score = 85.0   # 中盘，黄金区间
        size_type = "mid"
    elif circ_mv < 1000:
        base_score = 70.0   # 大盘，稳定
        size_type = "large"
    else:
        base_score = 50.0   # 超大盘，弹性不足
        size_type = "mega"
    
    # 根据宏观环境动态调整
    # 宏观环境好（macro_weight高）时，偏好中小盘（弹性大）
    # 宏观环境差（macro_weight低）时，偏好大盘（稳定性好）
    adjustment = 0.0
    
    if macro_weight >= 0.7:  # 宏观环境很好
        if size_type in ["micro", "small"]:
            adjustment = 15.0  # 小盘股加分
        elif size_type in ["large", "mega"]:
            adjustment = -10.0  # 大盘股减分
    elif macro_weight <= 0.3:  # 宏观环境较差
        if size_type in ["micro", "small"]:
            adjustment = -15.0  # 小盘股减分
        elif size_type in ["large", "mega"]:
            adjustment = 10.0   # 大盘股加分
    # 宏观中性时，保持基础分数
    
    final_score = base_score + adjustment
    return clamp(final_score, 0, 100)


def _build_no_recommendation_message(
    signal: str,
    stocks: List[dict[str, Any]],
    top_sectors: List[dict[str, Any]],
    sentiment_score: float,
) -> str:
    if signal == "SHORT_BUY" and stocks:
        return "已筛选到可跟踪标的，请结合盘中量能确认后执行。"
    if signal == "WATCHLIST_LIMIT_UP" and stocks:
        return "最强候选股已涨停，买入机会有限，建议作为观察标的或关注其他候选股。"
    if sentiment_score < 40:
        return "当前市场情绪偏弱，建议禁止开新仓，等待情绪修复。"
    if not top_sectors:
        return "未获取到可靠板块轮动数据，建议今日观望，等待数据恢复。"
    if not stocks:
        return "当前未筛选到满足短线条件的真实标的，建议继续观望。"
    return "当前不满足短线开仓条件，建议观望。"


def short_term_signal_engine(analysis_date: str | None = None, debug: bool = False) -> Dict[str, Any]:
    """Build weighted short-term signal."""
    debug = resolve_debug(debug)
    sentiment = get_market_sentiment(analysis_date=analysis_date, debug=debug)
    sector_info = get_sector_rotation(top_n=5, analysis_date=analysis_date, debug=debug)
    # 检查大盘趋势（上证指数 vs 5日均线）
    market_trend = check_market_trend(index_code="sh000001", ma_days=5)
    if debug:
        print(f"[DEBUG] Market trend: {market_trend}")
    sector_names = [x["name"] for x in sector_info.get("top_sectors", [])]
    
    # 优先使用 config.json 中的宏观板块列表（如果存在且非空）
    config = get_screener_config()
    macro_sectors = config.get("strategy", {}).get("macro", {}).get("sectors", [])
    if macro_sectors and isinstance(macro_sectors, list) and len(macro_sectors) > 0:
        sector_names = macro_sectors
        if debug:
            print(f"[DEBUG] Using macro sectors from config: {sector_names}")
    
    stocks = scan_strong_stocks(sectors=sector_names, top_n=10, analysis_date=analysis_date, debug=debug)
    target_symbol = stocks[0]["code"] if stocks else None
    capital = analyze_capital_flow(symbol=target_symbol, analysis_date=analysis_date, debug=debug)
    risk = short_term_risk_control(float(sentiment.get("market_sentiment_score", 0.0)), market_trend)

    sentiment_score = float(sentiment.get("market_sentiment_score", 0.0))
    sector_score = _calc_sector_score(sector_info.get("top_sectors", []))
    stock_score = _calc_stock_volume_score(stocks)
    capital_score = _calc_capital_score(capital)
    technical_score = _calc_technical_score(stocks)
    liquidity_score = _calc_liquidity_score(stocks)
    price_volume_score = _calc_price_volume_score(stocks)
    relative_strength_score = _calc_relative_strength_score(stocks)
    # 获取宏观权重用于市值风格动态调整
    macro_weight = config.get("strategy", {}).get("macro", {}).get("weight", 0.5)
    market_cap_score = _calc_market_cap_score(stocks, macro_weight)
    intra_sector_strength_score = _calc_intra_sector_strength_score(stocks)

    score = (
        sentiment_score * 0.18          # 保持0.18
        + sector_score * 0.18           # 保持0.18
        + stock_score * 0.13            # 从0.15调至0.13（-2%给板块内相对强度）
        + capital_score * 0.15          # 保持0.15
        + technical_score * 0.10        # 保持0.10
        + liquidity_score * 0.10        # 保持0.10
        + price_volume_score * 0.05     # 保持0.05
        + relative_strength_score * 0.05 # 保持0.05
        + market_cap_score * 0.04       # 保持0.04
        + intra_sector_strength_score * 0.02 # 新增板块内相对强度因子（+2%）
    )
    score = round(clamp(score, 0, 100), 2)

    # 检查最强候选股是否涨停
    top_stock_limit_up = False
    if len(stocks) > 0:
        top_stock = stocks[0]
        top_stock_limit_up = top_stock.get("is_limit_up", False)
    
    if score >= 75 and risk["market_filter"] and len(stocks) > 0:
        if top_stock_limit_up:
            # 最强股已涨停，降级为观察名单（实际买入困难）
            signal = "WATCHLIST_LIMIT_UP"
            confidence = clamp(score / 100.0 * 0.8, 0.0, 0.85)  # 略低于正常SHORT_BUY
            holding_days = "1-2"
        else:
            signal = "SHORT_BUY"
            confidence = clamp(score / 100.0 * 0.9, 0.0, 0.95)
            holding_days = "1-3"
    elif score >= 60 and risk["market_filter"]:
        signal = "WATCHLIST"
        confidence = clamp(score / 100.0 * 0.75, 0.0, 0.85)
        holding_days = "1-2"
    else:
        signal = "NO_TRADE"
        confidence = clamp(score / 100.0 * 0.6, 0.0, 0.7)
        holding_days = "0"

    no_msg = _build_no_recommendation_message(signal, stocks, sector_info.get("top_sectors", []), sentiment_score)

    payload = {
        "analysis_date": sentiment.get("analysis_date", analysis_date),
        "score": score,
        "signal": signal,
        "holding_days": holding_days,
        "confidence": round(confidence, 2),
        "risk_control": risk,
        "market_sentiment": sentiment,
        "top_sectors": sector_info.get("top_sectors", []),
        "candidates": stocks,
        "capital_flow": capital,
        "has_recommendation": len(stocks) > 0 and signal == "SHORT_BUY",
        "no_recommendation_message": no_msg,
        "factor_breakdown": {
            "market_sentiment": round(sentiment_score, 2),
            "sector_strength": round(sector_score, 2),
            "stock_volume_strength": round(stock_score, 2),
            "capital_inflow": round(capital_score, 2),
            "technical_structure": round(technical_score, 2),
            "liquidity": round(liquidity_score, 2),
            "price_volume": round(price_volume_score, 2),
            "relative_strength": round(relative_strength_score, 2),
            "market_cap": round(market_cap_score, 2),
            "intra_sector_strength": round(intra_sector_strength_score, 2),
        },
    }
    if not debug:
        return payload
    debug_info = {
        "module": "short_term_signal_engine",
        "selected_symbol": target_symbol,
        "sources": {
            "market_sentiment": sentiment.get("data_source", "unknown"),
            "sector_rotation": sector_info.get("data_source", "unknown"),
            "capital_flow": capital.get("data_source", "unknown"),
        },
    }
    return with_debug(payload, debug, debug_info)
