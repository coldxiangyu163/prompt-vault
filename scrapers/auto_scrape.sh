#!/bin/bash
# PromptVault Auto Scraper - Daily execution script
# Runs via nanobot cron at 2:00 AM

set -e

REPO_DIR="/tmp/pv-check"
LOG_DIR="$REPO_DIR/scrapers/logs"
LOG_FILE="$LOG_DIR/scrape_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "=== PromptVault Auto Scraper ===" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"

cd "$REPO_DIR"

# Trigger nanobot to run the scraper
/usr/local/bin/nanobot "执行 PromptVault 自动爬取：使用 Playwriter + Arc 浏览器爬取 Civitai/PromptHero，去重后 push 到 GitHub。完成后推送飞书通知。" >> "$LOG_FILE" 2>&1

echo "Completed at: $(date)" | tee -a "$LOG_FILE"
