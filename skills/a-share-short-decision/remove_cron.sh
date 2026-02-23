#!/bin/bash
# Remove T99 cron job

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/run_scan.sh"

echo "Removing T99 cron jobs..."
crontab -l 2>/dev/null | grep -v "T99" | grep -v "$SCRIPT_PATH" | crontab -

echo "Cron jobs removed."
echo "Current crontab:"
crontab -l 2>/dev/null || echo "(empty)"