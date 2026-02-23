#!/bin/bash
# T99: Setup cron job for A-share intraday scan

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/run_scan.sh"
CRON_JOB="30 14 * * 1-5 cd $SCRIPT_DIR && $SCRIPT_PATH"

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: run_scan.sh not found at $SCRIPT_PATH"
    exit 1
fi

# Add to crontab
echo "Adding cron job for T99 (A-share intraday scan)..."
(crontab -l 2>/dev/null | grep -v "T99" ; echo "# T99: A-share intraday scan (conservative)") | crontab -
(crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" ; echo "$CRON_JOB # T99") | crontab -

echo "Cron job added:"
echo "  Schedule: 30 14 * * 1-5 (Mon-Fri 14:30)"
echo "  Command: $SCRIPT_PATH"
echo ""
echo "Current crontab:"
crontab -l