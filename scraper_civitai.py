import json
import urllib.request
import hashlib
from pathlib import Path

def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def fetch_civitai_prompts(limit=50):
    url = f"https://civitai.com/api/v1/images?limit={limit}&sort=Most+Reactions&period=Week"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
    prompts = []
    for item in data.get('items', []):
        if item.get('nsfwLevel') not in ['None', 'Soft']:
            continue
        
        meta = item.get('meta') or {}
        prompt_text = meta.get('prompt', '').strip()
        
        if not prompt_text or len(prompt_text) < 20:
            continue
        
        prompts.append({
            'prompt': prompt_text[:1000],
            'imageUrl': item.get('url', ''),
            'tool': 'Stable Diffusion',
            'tags': ['general'],
            'style': 'realistic',
            'hash': get_hash(prompt_text)
        })
    
    return prompts

# 加载现有数据
existing = json.load(open('data/prompts.json'))
existing_hashes = {get_hash(p.get('prompt', '')) for p in existing if p.get('prompt')}
existing_urls = {p.get('imageUrl', '') for p in existing if p.get('imageUrl')}

print(f"现有 prompts: {len(existing)}")

# 抓取新数据
new_prompts = fetch_civitai_prompts(50)
print(f"Civitai 抓取: {len(new_prompts)} 条")

# 去重
unique = []
for p in new_prompts:
    if p['hash'] not in existing_hashes and p['imageUrl'] not in existing_urls:
        unique.append(p)
        existing_hashes.add(p['hash'])
        existing_urls.add(p['imageUrl'])

print(f"去重后新增: {len(unique)} 条")

if unique:
    existing.extend(unique)
    json.dump(existing, open('data/prompts.json', 'w'), indent=2, ensure_ascii=False)
    print(f"✅ 保存成功，总数: {len(existing)}")
else:
    print("⚠️ 无新增数据")
