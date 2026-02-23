#!/usr/bin/env python3
"""
T99 宏观数据提取器
集成到 run_scan.sh 中，用于：
1. 获取大盘趋势（上证指数） → 计算宏观分数
2. 获取当日强势板块列表
3. 计算宏观权重，动态调整选股阈值
"""

import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"ERROR: Missing required library: {e}")
    sys.exit(1)

def get_shanghai_index_trend(days: int = 20) -> Dict[str, Any]:
    """获取上证指数近期趋势，计算宏观分数（0-100）"""
    try:
        # 获取上证指数日线数据
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or df.empty:
            return {"score": 50, "trend": "unknown", "error": "No data"}
        
        # 取最近 days 个交易日
        recent = df.tail(days).copy()
        if len(recent) < 5:
            return {"score": 50, "trend": "insufficient_data"}
        
        # 计算涨跌幅
        start_close = recent.iloc[0]["close"]
        end_close = recent.iloc[-1]["close"]
        total_change_pct = (end_close - start_close) / start_close * 100
        
        # 计算短期趋势（最近5日）
        short = recent.tail(5)
        short_change = (short.iloc[-1]["close"] - short.iloc[0]["close"]) / short.iloc[0]["close"] * 100
        
        # 计算均线排列（5日、10日）
        recent["ma5"] = recent["close"].rolling(5).mean()
        recent["ma10"] = recent["close"].rolling(10).mean()
        ma5 = recent.iloc[-1]["ma5"]
        ma10 = recent.iloc[-1]["ma10"]
        ma5_above_ma10 = ma5 > ma10
        
        # 计算波动率
        volatility = recent["close"].std() / recent["close"].mean() * 100
        
        # 综合打分（经验公式）
        score = 50  # 基准分
        
        # 总涨幅贡献（-20 到 +20）
        if total_change_pct > 5:
            score += 15
        elif total_change_pct > 2:
            score += 8
        elif total_change_pct > 0:
            score += 3
        elif total_change_pct < -5:
            score -= 15
        elif total_change_pct < -2:
            score -= 8
        elif total_change_pct < 0:
            score -= 3
        
        # 短期趋势贡献（-10 到 +10）
        if short_change > 2:
            score += 8
        elif short_change > 0:
            score += 4
        elif short_change < -2:
            score -= 8
        elif short_change < 0:
            score -= 4
        
        # 均线排列贡献（0 或 +5）
        if ma5_above_ma10:
            score += 5
        
        # 波动率惩罚（高波动扣分，-5 到 0）
        if volatility > 3:
            score -= 5
        elif volatility > 2:
            score -= 3
        
        # 限制在 0-100
        score = max(0, min(100, int(score)))
        
        # 趋势定性
        if score >= 70:
            trend = "strong_up"
        elif score >= 55:
            trend = "moderate_up"
        elif score >= 45:
            trend = "neutral"
        elif score >= 30:
            trend = "moderate_down"
        else:
            trend = "weak_down"
        
        return {
            "score": score,
            "trend": trend,
            "total_change_pct": round(total_change_pct, 2),
            "short_change_pct": round(short_change, 2),
            "ma5_above_ma10": bool(ma5_above_ma10),
            "volatility": round(volatility, 2),
            "last_date": recent.index[-1].strftime("%Y-%m-%d") if hasattr(recent.index[-1], 'strftime') else str(recent.index[-1]),
        }
    except Exception as e:
        return {"score": 50, "trend": "error", "error": str(e)}

def get_sector_rotation(top_n: int = 5) -> Tuple[List[str], Dict[str, Any]]:
    """获取强势板块列表（使用 akshare 行业板块）"""
    try:
        # 获取行业板块行情
        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            # 尝试概念板块
            df = ak.stock_board_concept_name_em()
        
        if df is None or df.empty:
            return [], {"error": "No sector data"}
        
        # 按涨跌幅排序
        df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
        df = df.dropna(subset=["涨跌幅"])
        df = df.sort_values("涨跌幅", ascending=False)
        
        top_sectors = []
        sector_details = []
        for i, row in df.head(top_n).iterrows():
            name = row.get("板块名称", str(row.get("名称", "未知")))
            top_sectors.append(name)
            sector_details.append({
                "name": name,
                "change_pct": round(float(row["涨跌幅"]), 2),
                "turnover": row.get("成交额", "N/A"),
                "limit_up_count": row.get("涨停家数", "N/A"),
            })
        
        return top_sectors, {"top_sectors": sector_details}
    except Exception as e:
        return [], {"error": str(e)}

def load_t100_macro_data() -> Dict[str, Any]:
    """
    加载 T100 宏观数据（如果存在）
    返回简化版数据字典，如果文件不存在则返回空字典
    """
    import json
    import os
    
    shared_dir = "/root/.openclaw/workspace/data/shared"
    file_path = os.path.join(shared_dir, "t100_macro_simplified.json")
    
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"警告：加载 T100 数据失败: {e}")
        return {}

def calculate_t100_influence(t100_data: Dict[str, Any]) -> float:
    """
    基于 T100 数据计算影响因子（0.8 ~ 1.2）
    因子 >1 表示正面影响（放宽阈值），<1 表示负面影响（收紧阈值）
    """
    if not t100_data:
        return 1.0  # 无数据时中性
    
    # 1. 情绪指数影响（主要）
    composite = t100_data.get("composite_index")
    if composite is not None:
        # 将 0‑100 映射到 0.8‑1.2
        sentiment_factor = 0.8 + (composite / 100) * 0.4
    else:
        sentiment_factor = 1.0
    
    # 2. PMI 影响
    pmi = t100_data.get("pmi_manufacturing")
    if pmi is not None:
        pmi_factor = 0.9 if pmi < 50 else 1.1 if pmi > 52 else 1.0
    else:
        pmi_factor = 1.0
    
    # 3. VIX 影响（反向）
    vix = t100_data.get("vix")
    if vix is not None:
        vix_factor = 0.85 if vix > 25 else 1.15 if vix < 15 else 1.0
    else:
        vix_factor = 1.0
    
    # 综合因子（加权平均）
    influence = sentiment_factor * 0.5 + pmi_factor * 0.3 + vix_factor * 0.2
    return round(influence, 3)

def calculate_macro_weight(macro_score: int) -> float:
    """
    将宏观分数（0-100）转换为宏观权重（0-1）
    权重越高表示宏观环境越好，可适当放宽选股条件
    """
    # 线性映射：30分→0.0，70分→1.0，中间线性插值
    normalized = (macro_score - 30) / 40.0 if 30 <= macro_score <= 70 else (
        0.0 if macro_score < 30 else 1.0
    )
    return max(0.0, min(1.0, normalized))

def adjust_screener_thresholds(base_thresholds: Dict[str, Any], macro_weight: float) -> Dict[str, Any]:
    """
    根据宏观权重调整 screener 阈值
    macro_weight=1（宏观极好）→ 放宽阈值（乘以 0.8）
    macro_weight=0（宏观极差）→ 收紧阈值（乘以 1.2）
    """
    adjust_factor = 1.2 - (macro_weight * 0.4)  # 1.2 ~ 0.8 线性变化
    
    adjusted = base_thresholds.copy()
    # 调整百分比类阈值
    pct_keys = ["min_change_pct", "prefilter_change_pct", "high_volume_bearish_drop_pct"]
    for key in pct_keys:
        if key in adjusted:
            adjusted[key] = round(adjusted[key] * adjust_factor, 2)
    
    # 调整量比阈值
    if "min_volume_ratio" in adjusted:
        adjusted["min_volume_ratio"] = round(adjusted["min_volume_ratio"] * adjust_factor, 2)
    
    # 调整趋势回看天数（宏观好时多看几天）
    if "trend_lookback" in adjusted:
        original = adjusted["trend_lookback"]
        adjusted["trend_lookback"] = max(2, min(6, int(original + (macro_weight * 2) - 0.5)))
    
    return adjusted

def main():
    print("=== T99 宏观数据提取器 ===")
    
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    
    # 1. 获取大盘趋势
    print("获取上证指数趋势...")
    macro_result = get_shanghai_index_trend(days=20)
    macro_score = macro_result.get("score", 50)
    print(f"宏观分数: {macro_score}/100 ({macro_result.get('trend', 'unknown')})")
    print(f"近期涨跌幅: {macro_result.get('total_change_pct', 0)}%")
    
    # 2. 获取强势板块
    print("获取强势板块列表...")
    sectors, sector_info = get_sector_rotation(top_n=5)
    if sectors:
        print(f"强势板块 ({len(sectors)}): {', '.join(sectors)}")
    else:
        print("警告：未获取到板块数据")
        sectors = []
    
    # 3. 计算宏观权重（基于上证指数趋势）
    macro_weight = calculate_macro_weight(macro_score)
    print(f"基础宏观权重: {macro_weight:.2f} (0=差, 1=好)")
    
    # 4. 加载 T100 宏观数据并计算影响因子
    t100_data = load_t100_macro_data()
    if t100_data:
        t100_influence = calculate_t100_influence(t100_data)
        print(f"T100影响因子: {t100_influence:.3f} (0.8‑1.2)")
        # 调整宏观权重
        macro_weight = macro_weight * t100_influence
        macro_weight = max(0.0, min(1.0, macro_weight))  # 钳制到 0‑1
        print(f"调整后宏观权重: {macro_weight:.2f} (含T100影响)")
    else:
        t100_influence = 1.0
        print("T100数据未找到，使用纯技术面宏观权重")
    
    print(f"最终宏观权重: {macro_weight:.2f} (0=差, 1=好)")
    
    # 5. 输出结果（供 shell 脚本使用）
    output = {
        "macro": macro_result,
        "sectors": sectors,
        "sector_details": sector_info.get("top_sectors", []),
        "macro_weight": macro_weight,
        "t100_influence": t100_influence if 't100_influence' in locals() else None,
        "t100_data_available": bool(t100_data),
        "t100_composite_index": t100_data.get("composite_index") if t100_data else None,
        "t100_sentiment": t100_data.get("sentiment") if t100_data else None,
        "t100_predicted_sectors": t100_data.get("predicted_sectors", []) if t100_data else [],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # JSON 输出到 stdout（供 shell 捕获）
    json_output = json.dumps(output, ensure_ascii=False)
    print("\n=== 输出 JSON ===")
    print(json_output)
    
    # 同时写入临时文件，供后续脚本读取
    tmp_file = os.path.join(os.path.dirname(__file__), "data", "macro_sectors.json")
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(json_output)
    print(f"数据已保存至: {tmp_file}")
    
    # 更新 config.json 中的 macro 字段
    print("更新 config.json 中的 macro 字段...")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        
        # 确保嵌套结构存在
        if "strategy" not in config:
            config["strategy"] = {}
        if "macro" not in config["strategy"]:
            config["strategy"]["macro"] = {}
        
        config["strategy"]["macro"]["weight"] = macro_weight
        config["strategy"]["macro"]["sectors"] = sectors
        config["strategy"]["macro"]["score"] = macro_score
        config["strategy"]["macro"]["trend"] = macro_result.get("trend", "unknown")
        config["strategy"]["macro"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config["strategy"]["macro"]["t100_influence"] = t100_influence
        config["strategy"]["macro"]["t100_data_available"] = bool(t100_data)
        config["strategy"]["macro"]["t100_composite_index"] = t100_data.get("composite_index") if t100_data else None
        config["strategy"]["macro"]["t100_sentiment"] = t100_data.get("sentiment") if t100_data else None
        config["strategy"]["macro"]["t100_predicted_sectors"] = t100_data.get("predicted_sectors", []) if t100_data else []
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"配置已更新至: {config_path}")
    except Exception as e:
        print(f"警告：更新 config.json 失败: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())