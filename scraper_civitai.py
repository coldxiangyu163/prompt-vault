import json
import requests
import hashlib
from datetime import datetime

def fetch_civitai():
    url = "https://civitai.com/api/v1/images?limit=100&period=Week&sort=Most+Reactions"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    
    prompts = []
    for item in data.get('items', []):
        meta = item.get('meta', {})
        prompt = meta.get('prompt', '')
        if not prompt or len(prompt) < 20:
            continue
        
        nsfw = item.get('nsfw', False) or item.get('nsfwLevel', 0) > 1
        if nsfw:
            continue
        
        image_url = item.get('url', '')
        tool = meta.get('Model', 'Unknown')
        
        prompts.append({
            'id': hashlib.md5(prompt.encode()).hexdigest()[:12],
            'content': prompt,
            'tool': tool,
            'images': [image_url] if image_url else [],
            'author': 'Civitai',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'collected_at': datetime.utcnow().isoformat() + 'Z'
        })
    
    return prompts

if __name__ == '__main__':
    prompts = fetch_civitai()
    print(json.dumps(prompts, indent=2, ensure_ascii=False))
