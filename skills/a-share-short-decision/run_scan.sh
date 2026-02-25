#!/bin/bash
# T99: A-share intraday scan script (conservative)
# Sends results to Feishu group chat: oc_ff08c55a23630937869cd222dad0bf14

set -e

# OpenClaw CLI absolute path (for cron environment)
OPENCLAW_PATH="/root/.nvm/versions/node/v22.22.0/bin/openclaw"

# Ensure PATH includes OpenClaw
export PATH="/usr/local/bin:/usr/bin:/bin:/root/.nvm/versions/node/v22.22.0/bin:$PATH"

SKILL_DIR="/root/.openclaw/workspace/skills/a-share-short-decision"
cd "$SKILL_DIR"

LOG_FILE="$SKILL_DIR/scan.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Scan started at $(date) ==="

# Check if today is a trading day using akshare calendar + weekday fallback
echo "Checking if today is a trading day..."
PYCHECK=$(cat << 'EOF'
import sys
import akshare as ak
import pandas as pd
from datetime import datetime
today = datetime.now()
today_str1 = today.strftime("%Y%m%d")
today_str2 = today.strftime("%Y-%m-%d")
weekday = today.weekday()  # 0 Monday .. 5 Saturday, 6 Sunday
try:
    df = ak.tool_trade_date_hist_sina()
    if df is not None and not df.empty:
        trade_dates = df['trade_date'].astype(str).tolist()
        if today_str1 in trade_dates or today_str2 in trade_dates:
            print("TRADING_DAY")
            sys.exit(0)
        else:
            # Explicitly not in calendar -> treat as non‑trading day
            print("NON_TRADING_DAY")
            sys.exit(1)
    else:
        # Calendar empty/unavailable -> fallback to weekday
        print("CALENDAR_UNAVAILABLE")
        sys.exit(2)
except Exception as e:
    # Any error -> fallback to weekday
    print(f"CALENDAR_EXCEPTION: {e}")
    sys.exit(2)
EOF
)

TRADING_CHECK=$(python3 -c "$PYCHECK" 2>&1)
TRADING_CHECK_CODE=$?

case $TRADING_CHECK_CODE in
    0)
        echo "Today is a trading day (confirmed by calendar). Proceeding with scan."
        ;;
    1)
        echo "Today is NOT a trading day according to calendar (weekend/holiday). Skipping scan."
        exit 0
        ;;
    2)
        # Calendar unavailable or error -> decide by weekday
        if [ $(date +%u) -le 5 ]; then
            echo "Calendar check failed, but today is a weekday (Mon‑Fri). Assuming trading day."
        else
            echo "Calendar check failed, and today is weekend (Sat/Sun). Skipping scan."
            exit 0
        fi
        ;;
    *)
        echo "Warning: Unexpected return code $TRADING_CHECK_CODE ($TRADING_CHECK). Continuing scan anyway."
        ;;
esac

# 提取宏观数据与强势板块，更新 config.json
echo "Extracting macro data and strong sectors..."
MACRO_OUTPUT=$(python3 macro_sector_extractor.py 2>&1)
if [ $? -ne 0 ]; then
    echo "Warning: Macro extraction failed, but continuing scan."
    echo "$MACRO_OUTPUT"
else
    echo "Macro data extracted and config updated."
fi

# Get today's date in YYYY-MM-DD format
DATE=$(date +%Y-%m-%d)

# Run intraday scan with timeout (300 seconds)
echo "Running A-share short-term signal engine for $DATE (timeout 300s)..."
OUTPUT=$(timeout 300 python3 main.py short_term_signal_engine --date "$DATE" 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -eq 124 ]; then
    OUTPUT="ERROR: Skill execution timed out after 300 seconds. The scan may be too slow or stuck."
    EXIT_CODE=1
fi

echo "Skill exit code: $EXIT_CODE"

# Check if there's any error (e.g., missing data)
if [ $EXIT_CODE -ne 0 ] || echo "$OUTPUT" | grep -q "data_source: unavailable\|Error\|Traceback"; then
    MESSAGE="[测试] 【A股短线扫描 - $DATE】\n⚠️ 数据获取失败或技能运行出错。\n\n输出详情：\n$OUTPUT"
elif echo "$OUTPUT" | grep -q "当前暂无可执行短线买入标的"; then
    MESSAGE="[测试] 【A股短线扫描 - $DATE】（保守策略）\n$OUTPUT"
else
    # Format the output for Feishu
    MESSAGE="[测试] 【A股短线扫描 - $DATE】（保守策略）\n$OUTPUT"
fi

# Send to Feishu group (chat:oc_ff08c55a23630937869cd222dad0bf14)
echo "Sending results to Feishu group..."
"$OPENCLAW_PATH" message send --channel feishu \
    --target "chat:oc_ff08c55a23630937869cd222dad0bf14" \
    --message "$MESSAGE"

echo "Done. Results sent at $(date)."