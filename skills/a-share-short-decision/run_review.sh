#!/bin/bash
# T99: A-share strategy review script (weekly/monthly)
# Compares predictions vs actual market performance and generates optimization suggestions.

set -e

# OpenClaw CLI absolute path (for cron environment)
OPENCLAW_PATH="/root/.nvm/versions/node/v22.22.0/bin/openclaw"

export PATH="/usr/local/bin:/usr/bin:/bin:/root/.nvm/versions/node/v22.22.0/bin:$PATH"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SKILL_DIR"

LOG_FILE="$SKILL_DIR/review.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Strategy review started at $(date) ==="

# Decision log path
DECISION_LOG="$SKILL_DIR/data/decision_log.jsonl"

# Default review period: last 14 days (trading days)
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -d "$END_DATE -14 days" +%Y-%m-%d)

# If arguments provided, use them
if [ $# -ge 2 ]; then
    START_DATE="$1"
    END_DATE="$2"
elif [ $# -eq 1 ]; then
    START_DATE="$1"
    # END_DATE remains today
fi

# If no arguments and this is the first review (T99 initial review), use earliest date from log
if [ $# -eq 0 ] && [ -f "$DECISION_LOG" ]; then
    # Extract earliest prediction date from log
    EARLIEST=$(grep -o '"date":"[^"]*"' "$DECISION_LOG" | cut -d'"' -f4 | sort -u | head -1)
    if [ -n "$EARLIEST" ]; then
        START_DATE="$EARLIEST"
        echo "Using earliest prediction date from log: $START_DATE"
    fi
fi

echo "Review period: $START_DATE to $END_DATE"

# Check if decision log exists
if [ ! -f "$DECISION_LOG" ] || [ ! -s "$DECISION_LOG" ]; then
    echo "ERROR: No decision log found at $DECISION_LOG. Run the scan for at least a few days first."
    exit 1
fi

# Extract unique prediction dates within the period
echo "Extracting prediction dates from log..."
PREDICTION_DATES=$(grep -o '"date":"[^"]*"' "$DECISION_LOG" | cut -d'"' -f4 | sort -u | \
    awk -v start="$START_DATE" -v end="$END_DATE" '$1 >= start && $1 <= end' | head -20)

if [ -z "$PREDICTION_DATES" ]; then
    echo "No prediction dates found in the period. Exiting."
    exit 0
fi

echo "Found $(echo "$PREDICTION_DATES" | wc -l) prediction dates."

# For each prediction date, compare with next trading day
TOTAL_CANDIDATES=0
SUCCESS_CANDIDATES=0
TOTAL_RETURN=0

for PRED_DATE in $PREDICTION_DATES; do
    # Determine actual date (next trading day). For simplicity, use PRED_DATE +1 day.
    # In production, should skip weekends/holidays.
    ACTUAL_DATE=$(date -d "$PRED_DATE +1 day" +%Y-%m-%d)
    
    echo "Comparing prediction for $PRED_DATE vs actual $ACTUAL_DATE..."
    
    # Run comparison
    OUTPUT=$(python3 main.py compare_prediction_with_market \
        --prediction-date "$PRED_DATE" \
        --actual-date "$ACTUAL_DATE" 2>&1)
    
    # Extract summary stats (simplistic parsing; in real scenario, parse JSON)
    if echo "$OUTPUT" | grep -q '"total_candidates"'; then
        # JSON output - use jq if available
        if command -v jq >/dev/null 2>&1; then
            CANDIDATES=$(echo "$OUTPUT" | jq '.total_candidates // 0')
            SUCCESS=$(echo "$OUTPUT" | jq '.success_candidates // 0')
            AVG_RETURN=$(echo "$OUTPUT" | jq '.avg_return_pct // 0')
            TOTAL_CANDIDATES=$((TOTAL_CANDIDATES + CANDIDATES))
            SUCCESS_CANDIDATES=$((SUCCESS_CANDIDATES + SUCCESS))
            # Weighted return
            TOTAL_RETURN=$(echo "$TOTAL_RETURN + ($AVG_RETURN * $CANDIDATES)" | bc -l 2>/dev/null || echo "$TOTAL_RETURN")
        else
            # Fallback: count lines with positive return
            echo "$OUTPUT" | grep -E '"return_pct":\s*[0-9]+\.?[0-9]*' | while read line; do
                RETURN=$(echo "$line" | grep -o '"return_pct":[0-9]*\.\?[0-9]*' | cut -d':' -f2)
                TOTAL_CANDIDATES=$((TOTAL_CANDIDATES + 1))
                if [ $(echo "$RETURN > 0" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
                    SUCCESS_CANDIDATES=$((SUCCESS_CANDIDATES + 1))
                fi
                TOTAL_RETURN=$(echo "$TOTAL_RETURN + $RETURN" | bc -l 2>/dev/null || echo "$TOTAL_RETURN")
            done
        fi
    fi
    
    # Sleep to avoid overloading
    sleep 2
done

# Calculate metrics
if [ $TOTAL_CANDIDATES -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $SUCCESS_CANDIDATES * 100 / $TOTAL_CANDIDATES" | bc)
    AVG_RETURN_PCT=$(echo "scale=2; $TOTAL_RETURN / $TOTAL_CANDIDATES" | bc)
else
    SUCCESS_RATE=0
    AVG_RETURN_PCT=0
fi

# Generate report
REPORT="【A股短线策略复盘报告】
统计周期：${START_DATE} 至 ${END_DATE}
总候选股票数：${TOTAL_CANDIDATES}
成功上涨数：${SUCCESS_CANDIDATES}
胜率：${SUCCESS_RATE}%
平均收益率：${AVG_RETURN_PCT}%

初步建议："
if [ $TOTAL_CANDIDATES -eq 0 ]; then
    REPORT="${REPORT} 数据不足，请继续积累。"
elif [ $(echo "$SUCCESS_RATE < 45" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
    REPORT="${REPORT} 胜率偏低，建议调高筛选阈值（如 min_change_pct 增加 1‑2%）。"
elif [ $(echo "$SUCCESS_RATE > 60" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
    REPORT="${REPORT} 胜率良好，可考虑适度放宽条件以增加候选数量。"
else
    REPORT="${REPORT} 策略表现中等，建议维持当前参数，继续观察。"
fi

REPORT="${REPORT}

下一步行动：
1. 查看详细日志：$SKILL_DIR/data/decision_log.jsonl
2. 调整 config.json 参数（如需）
3. 重新部署扫描任务

—— 全自动化优化闭环（T99）"

echo "$REPORT"

# Auto-tuning based on review results
echo "---"
echo "Running auto-tuning..."
cd "$SKILL_DIR"
if python3 auto_tune.py >> "$LOG_FILE" 2>&1; then
    echo "Auto-tuning completed."
else
    echo "Auto-tuning failed (check log)."
fi

# Send report to Feishu group (auto-send for scheduled reviews)
echo "Sending report to Feishu group..."
"$OPENCLAW_PATH" message send --channel feishu \
    --target "chat:oc_ff08c55a23630937869cd222dad0bf14" \
    --message "$REPORT"

echo "=== Review completed at $(date) ==="