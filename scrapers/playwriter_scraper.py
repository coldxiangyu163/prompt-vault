#!/usr/bin/env python3
"""
Playwriter-based scraper for Civitai and PromptHero.
Uses Arc browser via Playwriter extension to scrape new prompts.
"""

import json
import hashlib
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).parent.parent
DATA_FILE = REPO_ROOT / "data" / "prompts.json"
LOG_FILE = REPO_ROOT / "scrapers" / "output" / "scrape_log.json"

# Ensure output dir exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def content_hash(prompt_text):
    """Generate dedup hash from prompt text"""
    normalized = " ".join(prompt_text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def load_existing():
    """Load existing prompts.json"""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def is_nsfw(prompt):
    """Basic NSFW filter"""
    nsfw_terms = ["nsfw", "nude", "naked", "topless", "erotic", "sexy lingerie",
                  "bondage", "explicit", "hentai", "xxx", "porn", "sex"]
    prompt_lower = prompt.lower()
    return any(term in prompt_lower for term in nsfw_terms)


def playwriter_execute(script, timeout=10):
    """Execute Playwriter script via MCP"""
    try:
        result = subprocess.run(
            ["npx", "-y", "@playwright/test", "--headed"],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT)
        )
        return result.stdout
    except Exception as e:
        print(f"  Playwriter error: {e}")
        return ""


def scrape_civitai_browser(limit=30):
    """Scrape Civitai via browser automation"""
    print("\n[Civitai Browser] Starting scrape...")
    
    script = f"""
    const {{ chromium }} = require('playwright');
    (async () => {{
      const browser = await chromium.connectOverCDP('http://localhost:9222');
      const contexts = browser.contexts();
      const page = contexts[0].pages()[0] || await contexts[0].newPage();
      
      await page.goto('https://civitai.com/images?sort=Most+Reactions&period=Week', {{waitUntil: 'networkidle'}});
      await page.waitForTimeout(2000);
      
      // Scroll to load more
      for (let i = 0; i < 3; i++) {{
        await page.evaluate(() => window.scrollBy(0, 1000));
        await page.waitForTimeout(1000);
      }}
      
      // Extract prompts
      const items = await page.$$eval('article', articles => {{
        return articles.slice(0, {limit}).map(article => {{
          const img = article.querySelector('img');
          const promptBtn = article.querySelector('[aria-label*="prompt"]');
          return {{
            image: img?.src || '',
            prompt: promptBtn?.textContent || '',
            url: article.querySelector('a')?.href || ''
          }};
        }});
      }});
      
      console.log(JSON.stringify(items));
      await browser.close();
    }})();
    """
    
    output = playwriter_execute(script, timeout=30)
    
    try:
        # Parse JSON from output
        lines = output.strip().split('\n')
        for line in lines:
            if line.startswith('['):
                return json.loads(line)
    except:
        pass
    
    return []


def scrape_civitai_api(limit=50):
    """Scrape Civitai via API (fallback)"""
    print("\n[Civitai API] Starting scrape...")
    
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    
    params = {
        "limit": min(limit, 100),
        "sort": "Most Reactions",
        "period": "Week",
        "nsfw": "None",
    }
    url = f"https://civitai.com/api/v1/images?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "PromptVault/1.0"})
    
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        items = data.get("items", [])
        print(f"  Raw API response: {len(items)} items")
        
        # Convert API format to our format
        processed = []
        for img in items:
            meta = img.get("meta") or {}
            prompt_text = (meta.get("prompt") or "").strip()
            
            if not prompt_text or len(prompt_text) < 20:
                continue
            
            # Add negative prompt if exists
            negative = (meta.get("negativePrompt") or "").strip()
            if negative:
                prompt_text += f"\n\nNegative prompt: {negative}"
            
            processed.append({
                "prompt": prompt_text,
                "image": img.get("url", ""),
                "url": f"https://civitai.com/images/{img.get('id', '')}",
                "author": img.get("username", ""),
                "meta": meta
            })
        
        return processed
        
    except Exception as e:
        print(f"  API error: {e}")
        return []


def scrape_prompthero_browser(limit=20):
    """Scrape PromptHero via browser (SPA requires JS execution)"""
    print("\n[PromptHero Browser] Starting scrape...")
    
    script = f"""
    const {{ chromium }} = require('playwright');
    (async () => {{
      const browser = await chromium.connectOverCDP('http://localhost:9222');
      const contexts = browser.contexts();
      const page = contexts[0].pages()[0] || await contexts[0].newPage();
      
      await page.goto('https://prompthero.com/prompts?sort=popular&time=week', {{waitUntil: 'networkidle'}});
      await page.waitForTimeout(3000);
      
      // Scroll to load more
      for (let i = 0; i < 2; i++) {{
        await page.evaluate(() => window.scrollBy(0, 1000));
        await page.waitForTimeout(1500);
      }}
      
      // Extract prompts
      const items = await page.$$eval('[data-testid="prompt-card"]', cards => {{
        return cards.slice(0, {limit}).map(card => {{
          const img = card.querySelector('img');
          const prompt = card.querySelector('[data-testid="prompt-text"]');
          const link = card.querySelector('a');
          return {{
            image: img?.src || '',
            prompt: prompt?.textContent || '',
            url: link?.href || ''
          }};
        }});
      }});
      
      console.log(JSON.stringify(items));
      await browser.close();
    }})();
    """
    
    output = playwriter_execute(script, timeout=30)
    
    try:
        lines = output.strip().split('\n')
        for line in lines:
            if line.startswith('['):
                return json.loads(line)
    except:
        pass
    
    return []


def infer_tags(prompt):
    """Infer tags from prompt text"""
    prompt_lower = prompt.lower()
    tag_keywords = {
        "portrait": ["portrait", "face", "headshot", "woman", "man", "girl", "boy"],
        "landscape": ["landscape", "scenery", "mountain", "ocean", "forest", "nature"],
        "anime": ["anime", "manga", "waifu", "chibi"],
        "photorealistic": ["photorealistic", "photo", "realistic", "raw photo", "dslr"],
        "fantasy": ["fantasy", "dragon", "magic", "wizard", "elf", "sword"],
        "sci-fi": ["sci-fi", "cyberpunk", "futuristic", "robot", "mech", "space"],
        "architecture": ["architecture", "building", "interior", "room", "house"],
        "character": ["character", "oc", "costume", "armor"],
        "cinematic": ["cinematic", "film", "movie", "dramatic lighting"],
    }
    tags = []
    for tag, keywords in tag_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            tags.append(tag)
    return tags or ["general"]


def infer_style(prompt):
    """Infer style from prompt text"""
    prompt_lower = prompt.lower()
    styles = [
        ("anime", ["anime", "manga", "waifu"]),
        ("photorealistic", ["photorealistic", "raw photo", "dslr", "realistic"]),
        ("digital-art", ["digital art", "digital painting", "illustration"]),
        ("3d-render", ["3d render", "blender", "octane", "unreal engine"]),
        ("cinematic", ["cinematic", "film still", "movie"]),
        ("concept-art", ["concept art", "environment design"]),
    ]
    for style, keywords in styles:
        if any(kw in prompt_lower for kw in keywords):
            return style
    return "mixed"


def infer_tool(prompt, meta=None):
    """Infer tool from prompt text and metadata"""
    # Check metadata first (more reliable)
    if meta:
        model = (meta.get("Model") or "").lower()
        if "flux" in model:
            return "Flux"
        if "sdxl" in model:
            return "SDXL"
        if "midjourney" in model:
            return "Midjourney"
    
    # Fallback to prompt text
    prompt_lower = prompt.lower()
    if "midjourney" in prompt_lower or "--ar" in prompt_lower:
        return "Midjourney"
    if "flux" in prompt_lower:
        return "Flux"
    if "sdxl" in prompt_lower:
        return "SDXL"
    return "Stable Diffusion"


def process_items(raw_items, source_name):
    """Process raw scraped items into standardized format"""
    processed = []
    
    for item in raw_items:
        prompt_text = item.get("prompt", "").strip()
        
        # Skip invalid
        if not prompt_text or len(prompt_text) < 20:
            continue
        
        # NSFW filter
        if is_nsfw(prompt_text):
            continue
        
        processed.append({
            "prompt": prompt_text,
            "images": [item.get("image", "")] if item.get("image") else [],
            "tags": infer_tags(prompt_text),
            "style": infer_style(prompt_text),
            "source_url": item.get("url", ""),
            "author": item.get("author", ""),
            "tool": infer_tool(prompt_text, item.get("meta")),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "collected_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source_name": source_name,
        })
    
    return processed


def deduplicate(existing, new_items):
    """Deduplicate new items against existing"""
    existing_hashes = {content_hash(p["prompt"]) for p in existing}
    existing_images = {img for p in existing for img in p.get("images", [])}
    
    unique = []
    for item in new_items:
        h = content_hash(item["prompt"])
        if h in existing_hashes:
            continue
        
        # Check image duplication
        if item["images"] and item["images"][0] in existing_images:
            continue
        
        existing_hashes.add(h)
        unique.append(item)
    
    return unique


def assign_ids(items, existing):
    """Assign unique IDs to new items"""
    max_id = max((int(p["id"].split("_")[-1]) for p in existing if p.get("id")), default=0)
    date_str = datetime.now().strftime("%Y%m%d")
    
    for i, item in enumerate(items, 1):
        source_prefix = item["source_name"][:3]
        item["id"] = f"{date_str}_{source_prefix}_{max_id + i:03d}"
    
    return items


def save_log(stats):
    """Save scrape log"""
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats
    }
    
    logs = []
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    
    # Keep last 100 entries
    logs = logs[-100:]
    
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def git_commit_push():
    """Commit and push to GitHub"""
    try:
        subprocess.run(["git", "add", "data/prompts.json"], cwd=REPO_ROOT, check=True)
        commit_msg = f"chore: auto-update prompts ({datetime.now().strftime('%Y-%m-%d')})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, check=True)
        print("\n✅ Git push successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Git push failed: {e}")
        return False


def main():
    print("=" * 60)
    print("PromptVault Auto Scraper")
    print("=" * 60)
    
    # Load existing data
    existing = load_existing()
    print(f"\nExisting prompts: {len(existing)}")
    
    # Scrape sources
    all_new = []
    stats = {}
    
    # Try Civitai API first (more reliable)
    civitai_items = scrape_civitai_api(limit=50)
    if civitai_items:
        processed = process_items(civitai_items, "civitai")
        all_new.extend(processed)
        stats["civitai_api"] = len(processed)
        print(f"  Civitai API: {len(processed)} items")
    
    # Try PromptHero browser scrape
    prompthero_items = scrape_prompthero_browser(limit=20)
    if prompthero_items:
        processed = process_items(prompthero_items, "prompthero")
        all_new.extend(processed)
        stats["prompthero_browser"] = len(processed)
        print(f"  PromptHero Browser: {len(processed)} items")
    
    # Deduplicate
    unique_new = deduplicate(existing, all_new)
    print(f"\nAfter deduplication: {len(unique_new)} unique new prompts")
    
    if not unique_new:
        print("\n⚠️  No new prompts found")
        return
    
    # Assign IDs
    unique_new = assign_ids(unique_new, existing)
    
    # Merge and save
    merged = existing + unique_new
    with open(DATA_FILE, "w") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved {len(unique_new)} new prompts")
    print(f"Total prompts: {len(merged)}")
    
    # Save log
    stats["new_unique"] = len(unique_new)
    stats["total"] = len(merged)
    stats["sources"] = list(set(item["source_name"] for item in unique_new))
    save_log(stats)
    
    # Git commit and push
    git_commit_push()
    
    print("\n" + "=" * 60)
    print("Scrape complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
