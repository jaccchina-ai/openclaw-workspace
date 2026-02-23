#!/usr/bin/env python3
"""
T99 auto-tuning script.
Adjusts config.json parameters based on review results.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

SKILL_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / "config.json"
REVIEW_LOG = SKILL_DIR / "review.log"

# Default conservative config (baseline)
DEFAULT_CONFIG = {
    "screener": {
        "prefilter_change_pct": 6.0,
        "min_change_pct": 6.0,
        "min_volume_ratio": 2.0,
        "trend_lookback": 3,
        "volume_baseline_days": 5,
        "high_volume_bearish_drop_pct": -2.0,
        "high_volume_bearish_vol_ratio": 2.2,
        "min_history_days": 6,
    }
}

def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def parse_review_log() -> tuple[float, float, int]:
    """Extract win_rate, avg_return, sample_size from latest review.log entry."""
    win_rate = 0.0
    avg_return = 0.0
    sample_size = 0
    if not REVIEW_LOG.exists():
        return win_rate, avg_return, sample_size
    
    lines = REVIEW_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Look for the last summary block
    for line in reversed(lines):
        if "胜率：" in line:
            # e.g., "胜率：55.0%"
            try:
                win_rate = float(line.split("胜率：")[1].replace("%", "").strip())
            except:
                pass
        if "平均收益率：" in line:
            try:
                avg_return = float(line.split("平均收益率：")[1].replace("%", "").strip())
            except:
                pass
        if "总候选股票数：" in line:
            try:
                sample_size = int(line.split("总候选股票数：")[1].strip())
            except:
                pass
    return win_rate, avg_return, sample_size

def tune_parameters(config: Dict[str, Any], win_rate: float, avg_return: float, sample_size: int) -> Dict[str, Any]:
    """
    Adjust config based on performance.
    Goal: maintain win_rate > 50%, avg_return > 1%, sample_size >= 3 per day.
    """
    screener = config.setdefault("screener", DEFAULT_CONFIG["screener"])
    
    # Current values
    min_change = screener.get("min_change_pct", 6.0)
    min_volume = screener.get("min_volume_ratio", 2.0)
    prefilter_change = screener.get("prefilter_change_pct", 6.0)
    
    # Adjustment rules
    if sample_size < 10 and win_rate > 55:
        # Too few candidates but high win rate → loosen thresholds
        screener["min_change_pct"] = max(4.5, min_change - 0.5)
        screener["prefilter_change_pct"] = max(4.0, prefilter_change - 0.5)
        screener["min_volume_ratio"] = max(1.5, min_volume - 0.2)
        print(f"Loosening thresholds: min_change_pct → {screener['min_change_pct']}, min_volume_ratio → {screener['min_volume_ratio']}")
    elif win_rate < 45:
        # Low win rate → tighten thresholds
        screener["min_change_pct"] = min(9.0, min_change + 0.5)
        screener["prefilter_change_pct"] = min(8.0, prefilter_change + 0.5)
        screener["min_volume_ratio"] = min(3.0, min_volume + 0.3)
        print(f"Tightening thresholds: min_change_pct → {screener['min_change_pct']}, min_volume_ratio → {screener['min_volume_ratio']}")
    elif avg_return < 0.5 and sample_size > 15:
        # Low average return but enough samples → tighten volume requirement
        screener["min_volume_ratio"] = min(3.0, min_volume + 0.2)
        print(f"Increasing volume requirement: min_volume_ratio → {screener['min_volume_ratio']}")
    else:
        print("No tuning needed; keeping current parameters.")
    
    return config

def main() -> None:
    print("=== T99 Auto‑Tuning Script ===")
    config = load_config()
    print(f"Loaded config from {CONFIG_PATH}")
    
    win_rate, avg_return, sample_size = parse_review_log()
    print(f"Review stats: win_rate={win_rate:.1f}%, avg_return={avg_return:.1f}%, sample_size={sample_size}")
    
    if sample_size < 5:
        print("Insufficient sample size (<5). Skipping tuning.")
        sys.exit(0)
    
    new_config = tune_parameters(config, win_rate, avg_return, sample_size)
    save_config(new_config)
    print(f"Updated config saved to {CONFIG_PATH}")
    
    # Show diff
    old_screener = config.get("screener", {})
    new_screener = new_config.get("screener", {})
    for key in sorted(set(old_screener.keys()) | set(new_screener.keys())):
        old_val = old_screener.get(key, "N/A")
        new_val = new_screener.get(key, "N/A")
        if old_val != new_val:
            print(f"  {key}: {old_val} → {new_val}")

if __name__ == "__main__":
    main()