"""
Civitai Adapter — 从 Civitai API 采集热门 AI 图片的 prompt
Civitai 有公开 API，无需认证即可获取热门图片及其生成参数。
"""

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from base_adapter import BaseAdapter, PromptItem, register_adapter


@register_adapter
class CivitaiAdapter(BaseAdapter):
    name = "civitai"
    display_name = "Civitai"
    base_url = "https://civitai.com"

    API_URL = "https://civitai.com/api/v1/images"

    def fetch(self, limit: int = 50) -> list[PromptItem]:
        params = {
            "limit": min(limit, 100),
            "sort": "Most Reactions",
            "period": "Week",
            "nsfw": "None",
        }
        url = f"{self.API_URL}?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "PromptVault/1.0"})

        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"[Civitai] API error: {e}")
            return []

        items = []
        for img in data.get("items", []):
            meta = img.get("meta") or {}
            prompt_text = meta.get("prompt", "").strip()
            if not prompt_text or len(prompt_text) < 20:
                continue

            negative = meta.get("negativePrompt", "")
            if negative:
                prompt_text += f"\n\nNegative prompt: {negative}"

            # 从 meta 提取工具信息
            model = meta.get("Model", "")
            tool = "Stable Diffusion"
            if "flux" in model.lower():
                tool = "Flux"
            elif "sdxl" in model.lower():
                tool = "SDXL"
            elif "midjourney" in model.lower():
                tool = "Midjourney"

            # 从 prompt 内容推断 tags
            tags = self._infer_tags(prompt_text)

            # 从 prompt 内容推断 style
            style = self._infer_style(prompt_text)

            items.append(PromptItem(
                prompt=prompt_text,
                images=[img.get("url", "")],
                tags=tags,
                style=style,
                source_url=f"{self.base_url}/images/{img.get('id', '')}",
                author=img.get("username", ""),
                tool=tool,
                created_at=img.get("createdAt", "")[:10],
                source_name=self.name,
            ))

        return items[:limit]

    def _infer_tags(self, prompt: str) -> list[str]:
        """基于 prompt 关键词推断 tags"""
        prompt_lower = prompt.lower()
        tag_keywords = {
            "portrait": ["portrait", "face", "headshot", "woman", "man", "girl", "boy"],
            "landscape": ["landscape", "scenery", "mountain", "ocean", "forest", "nature"],
            "anime": ["anime", "manga", "waifu", "chibi"],
            "photorealistic": ["photorealistic", "photo", "realistic", "raw photo", "dslr"],
            "fantasy": ["fantasy", "dragon", "magic", "wizard", "elf", "sword"],
            "sci-fi": ["sci-fi", "cyberpunk", "futuristic", "robot", "mech", "space"],
            "architecture": ["architecture", "building", "interior", "room", "house"],
            "product": ["product", "commercial", "advertisement", "packaging"],
            "character": ["character", "oc", "costume", "armor"],
            "cinematic": ["cinematic", "film", "movie", "dramatic lighting"],
        }
        tags = []
        for tag, keywords in tag_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                tags.append(tag)
        return tags or ["general"]

    def _infer_style(self, prompt: str) -> str:
        """基于 prompt 推断风格"""
        prompt_lower = prompt.lower()
        style_map = [
            ("anime", ["anime", "manga", "waifu"]),
            ("photorealistic", ["photorealistic", "raw photo", "dslr", "realistic"]),
            ("digital-art", ["digital art", "digital painting", "illustration"]),
            ("oil-painting", ["oil painting", "classical", "renaissance"]),
            ("pixel-art", ["pixel art", "8-bit", "16-bit"]),
            ("3d-render", ["3d render", "blender", "octane", "unreal engine"]),
            ("cinematic", ["cinematic", "film still", "movie"]),
            ("watercolor", ["watercolor", "aquarelle"]),
            ("concept-art", ["concept art", "environment design"]),
        ]
        for style, keywords in style_map:
            if any(kw in prompt_lower for kw in keywords):
                return style
        return "mixed"
