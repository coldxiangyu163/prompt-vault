#!/usr/bin/env python3
"""
Batch collect prompts from Civitai API using multiple queries.
Deduplicates against existing prompts.json.
"""

import json
import hashlib
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "prompts.json"

def load_existing():
    with open(DATA_FILE) as f:
        return json.load(f)

def content_hash(prompt_text):
    normalized = " ".join(prompt_text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]

def fetch_civitai(sort="Most Reactions", period="Week", limit=100, cursor=None):
    params = {
        "limit": min(limit, 100),
        "sort": sort,
        "period": period,
        "nsfw": "None",
    }
    if cursor:
        params["cursor"] = cursor
    url = f"https://civitai.com/api/v1/images?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "PromptVault/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Error: {e}")
        return {"items": []}

def infer_tool(meta):
    model = (meta.get("Model") or "").lower()
    if "flux" in model:
        return "Flux"
    if "sdxl" in model:
        return "SDXL"
    if "midjourney" in model:
        return "Midjourney"
    return "Stable Diffusion"

def infer_tags(prompt):
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

def is_nsfw(prompt):
    """Basic NSFW filter"""
    nsfw_terms = ["nsfw", "nude", "naked", "topless", "erotic", "sexy lingerie",
                  "bondage", "explicit", "hentai", "xxx", "porn"]
    prompt_lower = prompt.lower()
    return any(term in prompt_lower for term in nsfw_terms)

def main():
    existing = load_existing()
    existing_hashes = {content_hash(p["prompt"]) for p in existing}
    existing_images = {img for p in existing for img in p.get("images", [])}
    print(f"Existing: {len(existing)} prompts, {len(existing_hashes)} unique hashes")

    # Multiple query strategies
    queries = [
        ("Most Reactions", "Month"),
        ("Most Comments", "Week"),
        ("Most Reactions", "Day"),
        ("Newest", "Week"),
        ("Most Collected", "Week"),
        ("Most Reactions", "AllTime"),
    ]

    new_items = []
    seen_hashes = set(existing_hashes)

    for sort, period in queries:
        print(f"\n--- Fetching: sort={sort}, period={period} ---")
        data = fetch_civitai(sort=sort, period=period, limit=100)
        items = data.get("items", [])
        print(f"  Got {len(items)} raw items")

        added = 0
        for img in items:
            meta = img.get("meta") or {}
            prompt_text = (meta.get("prompt") or "").strip()
            if not prompt_text or len(prompt_text) < 20:
                continue

            # NSFW filter
            if is_nsfw(prompt_text):
                continue

            # Dedup
            h = content_hash(prompt_text)
            if h in seen_hashes:
                continue

            img_url = img.get("url", "")
            if img_url in existing_images:
                continue

            seen_hashes.add(h)

            negative = (meta.get("negativePrompt") or "").strip()
            if negative:
                prompt_text += f"\n\nNegative prompt: {negative}"

            tool = infer_tool(meta)
            tags = infer_tags(prompt_text)
            style = infer_style(prompt_text)

            new_items.append({
                "prompt": prompt_text,
                "images": [img_url] if img_url else [],
                "tags": tags,
                "style": style,
                "source_url": f"https://civitai.com/images/{img.get('id', '')}",
                "author": img.get("username", ""),
                "tool": tool,
                "created_at": (img.get("createdAt") or "")[:10],
                "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            added += 1

        print(f"  Added {added} new unique prompts")

        # If we have enough, stop early
        if len(new_items) >= 70:
            break

        time.sleep(1)  # Rate limit

    # Assign IDs and merge
    max_id = max((int(p["id"].split("_")[-1]) for p in existing if p.get("id")), default=0)
    date_str = time.strftime("%Y%m%d")

    for i, item in enumerate(new_items, 1):
        item["id"] = f"{date_str}_civ_{max_id + i:03d}"

    merged = existing + new_items
    print(f"\n=== Results ===")
    print(f"New prompts: {len(new_items)}")
    print(f"Total: {len(merged)}")

    # Validate
    unknown_tools = [p for p in merged if p.get("tool") == "Unknown"]
    if unknown_tools:
        print(f"WARNING: {len(unknown_tools)} prompts with Unknown tool")

    # Save
    with open(DATA_FILE, "w") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Saved to {DATA_FILE}")

if __name__ == "__main__":
    main()
