#!/bin/bash
# Quick test script for playwriter_scraper.py

echo "=== Testing Playwriter Scraper ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi
echo "✅ Python3 found"

# Check script exists
if [ ! -f "scrapers/playwriter_scraper.py" ]; then
    echo "❌ playwriter_scraper.py not found"
    exit 1
fi
echo "✅ Script exists"

# Check data file
if [ ! -f "data/prompts.json" ]; then
    echo "❌ data/prompts.json not found"
    exit 1
fi
echo "✅ Data file exists"

# Count current prompts
BEFORE=$(python3 -c "import json; print(len(json.load(open('data/prompts.json'))))")
echo "📊 Current prompts: $BEFORE"

echo ""
echo "Running scraper (dry-run mode)..."
echo ""

# Run scraper
python3 scrapers/playwriter_scraper.py

echo ""
echo "=== Test Complete ==="
