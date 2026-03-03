import urllib.request
import json
import sys

image_ids = sys.argv[1].split(',')
results = []

for img_id in image_ids[:50]:
    try:
        url = f"https://civitai.com/api/v1/images/{img_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('meta') and data['meta'].get('prompt'):
                results.append({
                    'id': img_id,
                    'prompt': data['meta']['prompt'],
                    'imageUrl': data.get('url', ''),
                    'tool': data['meta'].get('Model', 'Unknown'),
                    'nsfw': data.get('nsfw', False)
                })
    except:
        pass

print(json.dumps(results, ensure_ascii=False))
