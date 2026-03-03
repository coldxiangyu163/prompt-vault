#!/usr/bin/env python3
"""
PromptVault Auto Scraper - Playwriter + Arc Browser
Scrapes Civitai API + PromptHero, deduplicates, and pushes to GitHub.
"""

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
DATA_FILE = REPO_ROOT / "data" / "prompts.json"
LOG_FILE = REPO_ROOT / "scrapers" / "output" / "scrape_stats.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def content_hash(text):
    normalized = text.lower().replace('\n', ' ').strip()
    normalized = ' '.join(normalized.split())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]

def infer_tags(prompt):
    p = prompt.lower()
    tag_map = {
        'portrait': ['portrait', 'face', 'headshot', 'woman', 'man', 'girl', 'boy'],
        'landscape': ['landscape', 'scenery', 'mountain', 'ocean', 'forest', 'nature'],
        'anime': ['anime', 'manga', 'waifu', 'chibi'],
        'photorealistic': ['photorealistic', 'photo', 'realistic', 'raw photo', 'dslr'],
        'fantasy': ['fantasy', 'dragon', 'magic', 'wizard', 'elf', 'sword'],
        'sci-fi': ['sci-fi', 'cyberpunk', 'futuristic', 'robot', 'mech', 'space'],
        'architecture': ['architecture', 'building', 'interior', 'room', 'house'],
        'character': ['character', 'oc', 'costume', 'armor'],
        'cinematic': ['cinematic', 'film', 'movie', 'dramatic lighting'],
    }
    tags = []
    for tag, keywords in tag_map.items():
        if any(kw in p for kw in keywords):
            tags.append(tag)
    return tags if tags else ['general']

def infer_style(prompt):
    p = prompt.lower()
    styles = [
        ('anime', ['anime', 'manga', 'waifu']),
        ('photorealistic', ['photorealistic', 'raw photo', 'dslr', 'realistic']),
        ('digital-art', ['digital art', 'digital painting', 'illustration']),
        ('3d-render', ['3d render', 'blender', 'octane', 'unreal engine']),
        ('cinematic', ['cinematic', 'film still', 'movie']),
        ('concept-art', ['concept art', 'environment design']),
    ]
    for style, keywords in styles:
        if any(kw in p for kw in keywords):
            return style
    return 'mixed'

def scrape_civitai():
    """Scrape Civitai API"""
    import urllib.request
    log("Fetching Civitai API...")
    
    url = "https://civitai.com/api/v1/images?limit=200&sort=Most+Reactions&period=Month&nsfw=None"
    req = urllib.request.Request(url, headers={'User-Agent': 'PromptVault/2.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
            items = data.get('items', [])
            log(f"Civitai: {len(items)} items fetched")
            
            prompts = []
            nsfw_terms = ['nsfw', 'nude', 'naked', 'topless', 'erotic', 'sexy lingerie', 
                         'bondage', 'explicit', 'hentai', 'xxx', 'porn']
            
            for img in items:
                if not img:
                    continue
                meta = img.get('meta') or {}
                prompt = (meta.get('prompt') or '').strip()
                negative = (meta.get('negativePrompt') or '').strip()
                
                if negative:
                    full_prompt = f"{prompt}\n\nNegative prompt: {negative}"
                else:
                    full_prompt = prompt
                
                if len(full_prompt) < 20:
                    continue
                
                # NSFW filter
                if any(term in full_prompt.lower() for term in nsfw_terms):
                    continue
                
                model = (meta.get('Model') or meta.get('model') or '').lower()
                base_model = (img.get('baseModel') or '').lower()
                tool = 'Stable Diffusion'
                if 'flux' in model or 'flux' in base_model:
                    tool = 'Flux'
                elif 'sdxl' in model or 'sdxl' in base_model:
                    tool = 'SDXL'
                elif 'midjourney' in model:
                    tool = 'Midjourney'
                
                prompts.append({
                    'prompt': full_prompt,
                    'image': img.get('url', ''),
                    'url': f"https://civitai.com/images/{img.get('id')}",
                    'author': img.get('username', ''),
                    'tool': tool,
                    'createdAt': (img.get('createdAt') or '')[:10],
                })
            
            log(f"Civitai: {len(prompts)} valid prompts after filtering")
            return prompts
    except Exception as e:
        log(f"Civitai error: {e}")
        return []

def scrape_prompthero_playwriter():
    """
    Scrape PromptHero using Playwriter + Arc Browser
    This is a placeholder - actual implementation requires MCP Playwriter execution
    For now, return empty list (Civitai API is the primary source)
    """
    log("PromptHero scraping via Playwriter (skipped in standalone mode)")
    # TODO: Implement Playwriter MCP call when running in nanobot context
    return []

def main():
    log("=== PromptVault Auto Scraper ===")
    
    # Load existing data
    with open(DATA_FILE) as f:
        existing_data = json.load(f)
    log(f"Existing prompts: {len(existing_data)}")
    
    # Build dedup sets (handle both 'prompt' and 'content' fields)
    existing_hashes = set()
    for p in existing_data:
        text = p.get('prompt') or p.get('content', '')
        if text:
            existing_hashes.add(content_hash(text))
    
    existing_images = set()
    for p in existing_data:
        existing_images.update(p.get('images', []))
        if p.get('imageUrl'):
            existing_images.add(p['imageUrl'])
    
    log(f"Dedup sets: {len(existing_hashes)} hashes, {len(existing_images)} images")
    
    # Scrape sources
    civitai_prompts = scrape_civitai()
    prompthero_prompts = scrape_prompthero_playwriter()
    
    log(f"Raw scraped: Civitai {len(civitai_prompts)}, PromptHero {len(prompthero_prompts)}")
    
    # Deduplicate and merge
    new_prompts = []
    new_hashes = set(existing_hashes)
    now = datetime.now().isoformat()[:19]
    today = now[:10]
    
    nsfw_terms = ['nsfw', 'nude', 'naked', 'topless', 'erotic', 'sexy lingerie', 
                 'bondage', 'explicit', 'hentai', 'xxx', 'porn']
    
    for item in civitai_prompts + prompthero_prompts:
        h = content_hash(item['prompt'])
        if h in new_hashes:
            continue
        if item.get('image') and item['image'] in existing_images:
            continue
        if any(term in item['prompt'].lower() for term in nsfw_terms):
            continue
        
        new_hashes.add(h)
        new_prompts.append({
            'prompt': item['prompt'],
            'images': [item['image']] if item.get('image') else [],
            'tags': infer_tags(item['prompt']),
            'style': infer_style(item['prompt']),
            'source_url': item.get('url', ''),
            'author': item.get('author', ''),
            'tool': item.get('tool', 'Unknown'),
            'created_at': item.get('createdAt', today),
            'collected_at': now,
        })
    
    log(f"New unique prompts: {len(new_prompts)}")
    
    if len(new_prompts) == 0:
        log("No new prompts to add. Exiting.")
        return 0
    
    # Assign IDs
    max_id = 0
    for p in existing_data:
        if p.get('id'):
            parts = p['id'].split('_')
            try:
                num = int(parts[-1])
                if num > max_id:
                    max_id = num
            except:
                pass
    
    date_str = datetime.now().strftime('%Y%m%d')
    for i, p in enumerate(new_prompts):
        src = 'civ' if 'civitai' in p['source_url'] else 'phr'
        p['id'] = f"{date_str}_{src}_{str(max_id + i + 1).zfill(3)}"
    
    # Merge
    merged = existing_data + new_prompts
    log(f"Total after merge: {len(merged)} (was {len(existing_data)}, +{len(new_prompts)})")
    
    # Save
    with open(DATA_FILE, 'w') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    log("✅ Saved to prompts.json")
    
    # Git commit + push
    try:
        subprocess.run(['git', 'add', 'data/prompts.json'], cwd=REPO_ROOT, check=True)
        commit_msg = f"chore: auto-scrape +{len(new_prompts)} prompts → {len(merged)} total"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=REPO_ROOT, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=REPO_ROOT, check=True)
        log("✅ Pushed to GitHub")
    except subprocess.CalledProcessError as e:
        log(f"❌ Git error: {e}")
        return 1
    
    # Save stats
    stats = {
        'timestamp': now,
        'new_prompts': len(new_prompts),
        'total_prompts': len(merged),
        'sources': {
            'civitai': len([p for p in new_prompts if 'civitai' in p['source_url']]),
            'prompthero': len([p for p in new_prompts if 'prompthero' in p['source_url']]),
        }
    }
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    log(f"✅ Stats: {stats}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
