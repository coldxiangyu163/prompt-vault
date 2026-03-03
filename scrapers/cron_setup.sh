#!/bin/bash
# Setup cron job for automatic prompt scraping

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$SCRIPT_DIR/output"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Cron job command
CRON_CMD="0 10 * * * cd $REPO_ROOT/scrapers && /usr/bin/python3 playwriter_scraper.py >> $LOG_DIR/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "playwriter_scraper.py"; then
    echo "✅ Cron job already exists"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "playwriter_scraper.py"
else
    echo "Adding cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added successfully"
    echo ""
    echo "Schedule: Daily at 10:00 AM"
    echo "Log file: $LOG_DIR/cron.log"
fi

echo ""
echo "To view/edit crontab:"
echo "  crontab -e"
echo ""
echo "To remove cron job:"
echo "  crontab -l | grep -v 'playwriter_scraper.py' | crontab -"
