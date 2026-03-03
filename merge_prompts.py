#!/usr/bin/env python3
import json
import hashlib
import re
from pathlib import Path

def clean_prompt(text):
    """清理 prompt 文本，移除统计数字和工具标签"""
    # 移除末尾的数字和 "Stable Diffusion" 标签
    text = re.sub(r'\d+\s*Stable Diffusion$', '', text)
    text = re.sub(r'\d+$', '', text)
    return text.strip()

def get_content_hash(prompt):
    """生成 prompt 内容的 hash（前12位）"""
    return hashlib.md5(prompt.encode()).hexdigest()[:12]

def infer_tags(prompt):
    """根据关键词推断标签"""
    prompt_lower = prompt.lower()
    tags = []
    
    if any(kw in prompt_lower for kw in ['portrait', 'face', 'headshot', 'person', 'woman', 'man']):
        tags.append('portrait')
    if any(kw in prompt_lower for kw in ['landscape', 'scenery', 'mountain', 'forest', 'garden']):
        tags.append('landscape')
    if any(kw in prompt_lower for kw in ['anime', 'manga', 'studio ghibli', 'makoto shinkai']):
        tags.append('anime')
    if any(kw in prompt_lower for kw in ['fantasy', 'magic', 'warrior', 'princess', 'dragon']):
        tags.append('fantasy')
    if any(kw in prompt_lower for kw in ['realistic', 'photorealistic', 'photo realism', 'detailed']):
        tags.append('realistic')
    if any(kw in prompt_lower for kw in ['cinematic', 'dramatic lighting', 'movie']):
        tags.append('cinematic')
    if any(kw in prompt_lower for kw in ['concept art', 'illustration', 'digital painting']):
        tags.append('concept-art')
    if any(kw in prompt_lower for kw in ['character', 'character design']):
        tags.append('character')
    if any(kw in prompt_lower for kw in ['architecture', 'building', 'interior']):
        tags.append('architecture')
    
    return tags if tags else ['general']

def infer_style(prompt):
    """推断艺术风格"""
    prompt_lower = prompt.lower()
    
    if 'greg rutkowski' in prompt_lower or 'artstation' in prompt_lower:
        return 'digital-art'
    elif 'anime' in prompt_lower or 'manga' in prompt_lower:
        return 'anime'
    elif 'oil painting' in prompt_lower or 'watercolor' in prompt_lower:
        return 'painting'
    elif 'photorealistic' in prompt_lower or 'photo realism' in prompt_lower:
        return 'photorealistic'
    elif 'concept art' in prompt_lower:
        return 'concept-art'
    elif 'line art' in prompt_lower or 'ink' in prompt_lower:
        return 'line-art'
    else:
        return 'digital-art'

# 读取现有数据
existing_file = Path('/tmp/pv-check/data/prompts.json')
existing_prompts = json.loads(existing_file.read_text())
print(f"现有 prompts: {len(existing_prompts)}")

# 构建去重索引
existing_hashes = {get_content_hash(p['prompt']) for p in existing_prompts}
existing_images = set()
for p in existing_prompts:
    if 'images' in p and p['images']:
        existing_images.update(p['images'])
    elif 'image' in p:
        existing_images.add(p['image'])

# 读取新抓取的数据
new_data = json.loads(Path('/tmp/ph_raw.json').read_text())
print(f"PromptHero 抓取: {len(new_data)} 条")

# 去重并转换格式
new_prompts = []
for item in new_data:
    cleaned_prompt = clean_prompt(item['prompt'])
    content_hash = get_content_hash(cleaned_prompt)
    
    # 跳过重复内容
    if content_hash in existing_hashes or item['image'] in existing_images:
        continue
    
    new_prompts.append({
        'id': content_hash,
        'prompt': cleaned_prompt,
        'images': [item['image']],
        'tool': 'Stable Diffusion',
        'tags': infer_tags(cleaned_prompt),
        'style': infer_style(cleaned_prompt),
        'source_url': item['url'],
        'author': 'PromptHero',
        'collected_at': None,
        'created_at': None
    })
    
    existing_hashes.add(content_hash)
    existing_images.add(item['image'])

print(f"去重后新增: {len(new_prompts)} 条")

if new_prompts:
    # 合并数据
    all_prompts = existing_prompts + new_prompts
    
    # 保存
    output_file = Path('/tmp/pv-check/data/prompts.json')
    output_file.write_text(json.dumps(all_prompts, indent=2, ensure_ascii=False))
    print(f"✅ 已保存 {len(all_prompts)} 条 prompts")
    
    # 显示新增示例
    print("\n新增示例:")
    for p in new_prompts[:3]:
        print(f"  - {p['prompt'][:80]}...")
else:
    print("⚠️ 无新增数据")
