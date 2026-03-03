import json
import hashlib
from datetime import datetime

# 从 Playwriter 获取的数据
new_prompts = [
    {
        "prompt": "zidiusArt, black cat is looking in shock at deformed and elongated white bird looking at it. Cat is atop of birdhouse. Cat is clearly horrified and shocked, with eyes wide open and mouth slightly open as well. Bird has extremely long neck. Cat is looking at bird",
        "tool": "Z-Image Turbo",
        "imageUrl": "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/122270509.jpeg",
        "source": "civitai"
    }
]

# 加载现有数据
with open('data/prompts.json', 'r', encoding='utf-8') as f:
    existing = json.load(f)

# 去重
existing_hashes = {hashlib.md5(p.get('prompt', '').encode()).hexdigest()[:12] for p in existing if p.get('prompt')}
existing_urls = {img for p in existing for img in p.get('images', [])}

added = 0
for item in new_prompts:
    content_hash = hashlib.md5(item['prompt'].encode()).hexdigest()[:12]
    if content_hash not in existing_hashes and item['imageUrl'] not in existing_urls:
        existing.append({
            "id": f"civitai_{content_hash}",
            "prompt": item['prompt'],
            "tool": item['tool'],
            "tags": ["animal", "humor"],
            "style": "realistic",
            "images": [item['imageUrl']],
            "source_url": "https://civitai.com/images/122270509",
            "author": "Lostcut",
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "collected_at": datetime.utcnow().isoformat() + 'Z'
        })
        added += 1

print(f"新增: {added}, 总数: {len(existing)}")
