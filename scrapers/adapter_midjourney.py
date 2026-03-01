"""
Midjourney Showcase Adapter — 从 Midjourney 社区展示页采集 prompt
Midjourney 的 showcase 页面需要登录，这里通过公开的社区 feed 获取。
"""

import json
import re
from urllib.request import urlopen, Request
from base_adapter import BaseAdapter, PromptItem, register_adapter


@register_adapter
class MidjourneyAdapter(BaseAdapter):
    name = "midjourney"
    display_name = "Midjourney Showcase"
    base_url = "https://www.midjourney.com"

    # Midjourney 社区 API（公开可访问的 explore feed）
    API_URL = "https://www.midjourney.com/api/app/recent-jobs"

    def fetch(self, limit: int = 50) -> list[PromptItem]:
        """
        尝试通过 Midjourney 公开 API 获取数据。
        如果 API 不可用，回退到从 Midjourney 社区 Discord 公开频道
        或第三方聚合站获取。
        """
        items = self._fetch_from_api(limit)
        if not items:
            print("[Midjourney] Primary API unavailable, trying fallback...")
            items = self._fetch_fallback(limit)
        return items

    def _fetch_from_api(self, limit: int) -> list[PromptItem]:
        """尝试 Midjourney 官方 API"""
        params = json.dumps({
            "amount": min(limit, 50),
            "jobType": "yfcc",
            "orderBy": "hot",
            "dedupe": True,
        }).encode()

        req = Request(
            self.API_URL,
            data=params,
            method="POST",
            headers={
                "User-Agent": "PromptVault/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"[Midjourney] API error: {e}")
            return []

        items = []
        jobs = data if isinstance(data, list) else data.get("jobs", [])
        for job in jobs:
            prompt_text = job.get("prompt", "") or job.get("full_command", "")
            if not prompt_text or len(prompt_text) < 10:
                continue

            # 清理 Midjourney 特有参数，保留在 prompt 中
            image_url = ""
            if job.get("image_paths"):
                img_id = job["image_paths"][0] if isinstance(job["image_paths"][0], str) else ""
                if img_id:
                    image_url = f"https://cdn.midjourney.com/{job.get('id', '')}/{img_id}"
            elif job.get("url"):
                image_url = job["url"]

            items.append(PromptItem(
                prompt=prompt_text,
                images=[image_url] if image_url else [],
                tags=self._extract_tags(prompt_text),
                style=self._infer_style(prompt_text),
                source_url=f"{self.base_url}/jobs/{job.get('id', '')}",
                author=job.get("username", ""),
                tool="Midjourney",
                created_at=str(job.get("enqueue_time", ""))[:10],
                source_name=self.name,
            ))

        return items[:limit]

    def _fetch_fallback(self, limit: int) -> list[PromptItem]:
        """
        回退方案：从 MidLibrary 等第三方聚合站获取 Midjourney prompt。
        """
        url = "https://midlibrary.io/styles?sort=trending"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })

        try:
            with urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[Midjourney] Fallback error: {e}")
            return []

        items = []
        # 提取 prompt 文本（midlibrary 常见模式）
        prompt_blocks = re.findall(
            r'class="[^"]*prompt[^"]*"[^>]*>([^<]{20,})<', html, re.IGNORECASE
        )
        img_blocks = re.findall(
            r'<img[^>]*src="(https://[^"]*midlibrary[^"]*)"', html
        )

        for i, prompt_text in enumerate(prompt_blocks[:limit]):
            prompt_text = prompt_text.strip()
            img = img_blocks[i] if i < len(img_blocks) else ""
            items.append(PromptItem(
                prompt=prompt_text,
                images=[img] if img else [],
                tags=self._extract_tags(prompt_text),
                style=self._infer_style(prompt_text),
                source_url="https://midlibrary.io",
                tool="Midjourney",
                source_name=self.name,
            ))

        return items

    def _extract_tags(self, prompt: str) -> list[str]:
        prompt_lower = prompt.lower()
        tags = []
        tag_map = {
            "portrait": "portrait", "landscape": "landscape", "anime": "anime",
            "fantasy": "fantasy", "abstract": "abstract", "architecture": "architecture",
            "character": "character", "product": "product", "logo": "logo",
            "pattern": "pattern", "texture": "texture", "isometric": "isometric",
        }
        for keyword, tag in tag_map.items():
            if keyword in prompt_lower:
                tags.append(tag)

        # Midjourney 特有参数作为 tag
        if "--niji" in prompt_lower:
            tags.append("niji")
        if "--style raw" in prompt_lower:
            tags.append("raw-style")

        return tags or ["general"]

    def _infer_style(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        styles = [
            ("anime", ["anime", "--niji"]),
            ("photorealistic", ["photorealistic", "photo", "realistic", "raw"]),
            ("3d-render", ["3d", "isometric", "render"]),
            ("illustration", ["illustration", "drawing", "sketch"]),
            ("oil-painting", ["oil painting", "classical"]),
            ("watercolor", ["watercolor"]),
            ("cinematic", ["cinematic", "film"]),
        ]
        for style, keywords in styles:
            if any(kw in prompt_lower for kw in keywords):
                return style
        return "mixed"
