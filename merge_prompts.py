import json
import hashlib
from datetime import datetime

# 加载新数据
with open('new_prompts.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# 加载现有数据
with open('data/prompts.json', 'r', encoding='utf-8') as f:
    existing = json.load(f)

# 去重
existing_hashes = {hashlib.md5(p.get('prompt', '').encode()).hexdigest()[:12] for p in existing if p.get('prompt')}
existing_urls = {img for p in existing for img in p.get('images', [])}

added = 0
skipped = 0

for item in new_data:
    content_hash = hashlib.md5(item['prompt'].encode()).hexdigest()[:12]
    
    if content_hash in existing_hashes or item['imageUrl'] in existing_urls:
        skipped += 1
        continue
    
    # 推断标签
    tags = []
    prompt_lower = item['prompt'].lower()
    if any(w in prompt_lower for w in ['landscape', 'mountain', 'field', 'sky', 'nature']):
        tags.append('landscape')
    if any(w in prompt_lower for w in ['portrait', 'face', 'girl', 'woman', 'man']):
        tags.append('portrait')
    if any(w in prompt_lower for w in ['anime', 'manga']):
        tags.append('anime')
    if any(w in prompt_lower for w in ['fantasy', 'wizard', 'magic']):
        tags.append('fantasy')
    if any(w in prompt_lower for w in ['sci-fi', 'space', 'futuristic']):
        tags.append('sci-fi')
    if any(w in prompt_lower for w in ['cat', 'dog', 'animal', 'bird']):
        tags.append('animal')
    
    if not tags:
        tags = ['general']
    
    # 推断风格
    style = 'realistic'
    if 'anime' in prompt_lower or 'manga' in prompt_lower:
        style = 'anime'
    elif 'painting' in prompt_lower or 'oil painting' in prompt_lower:
        style = 'painting'
    elif 'cartoon' in prompt_lower or 'illustration' in prompt_lower:
        style = 'illustration'
    
    existing.append({
        "id": f"civitai_{content_hash}",
        "prompt": item['prompt'],
        "tool": item['model'],
        "tags": tags,
        "style": style,
        "images": [item['imageUrl']],
        "source_url": item['url'],
        "author": "Unknown",
        "created_at": datetime.utcnow().isoformat() + 'Z',
        "collected_at": datetime.utcnow().isoformat() + 'Z'
    })
    added += 1

print(f"新增: {added}, 跳过: {skipped}, 总数: {len(existing)}")

# 保存
with open('data/prompts.json', 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
