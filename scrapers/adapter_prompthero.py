"""
PromptHero Adapter — 从 PromptHero 网站采集热门 prompt
PromptHero 没有公开 API，通过网页抓取获取数据。
"""

import json
import re
from urllib.request import urlopen, Request
from base_adapter import BaseAdapter, PromptItem, register_adapter


@register_adapter
class PromptHeroAdapter(BaseAdapter):
    name = "prompthero"
    display_name = "PromptHero"
    base_url = "https://prompthero.com"

    def fetch(self, limit: int = 50) -> list[PromptItem]:
        """抓取 PromptHero 热门 prompt 页面"""
        items = []
        pages_needed = (limit // 20) + 1

        for page in range(1, pages_needed + 1):
            url = f"{self.base_url}/prompts?page={page}&sort=popular&time=week"
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            })

            try:
                with urlopen(req, timeout=30) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"[PromptHero] Page {page} error: {e}")
                continue

            page_items = self._parse_html(html)
            items.extend(page_items)

            if len(items) >= limit:
                break

        return items[:limit]

    def _parse_html(self, html: str) -> list[PromptItem]:
        """从 HTML 中提取 prompt 数据（基于 JSON-LD 或 meta 标签）"""
        items = []

        # 尝试提取 JSON-LD 结构化数据
        ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        ld_matches = re.findall(ld_pattern, html, re.DOTALL)
        for ld_text in ld_matches:
            try:
                ld_data = json.loads(ld_text)
                if isinstance(ld_data, list):
                    for item in ld_data:
                        pi = self._ld_to_prompt(item)
                        if pi:
                            items.append(pi)
                elif isinstance(ld_data, dict):
                    pi = self._ld_to_prompt(ld_data)
                    if pi:
                        items.append(pi)
            except json.JSONDecodeError:
                continue

        # 如果 JSON-LD 没数据，回退到正则提取 prompt card
        if not items:
            items = self._parse_cards(html)

        return items

    def _ld_to_prompt(self, data: dict) -> PromptItem | None:
        """从 JSON-LD 数据转换为 PromptItem"""
        if data.get("@type") not in ("ImageObject", "CreativeWork"):
            return None
        prompt_text = data.get("description", "") or data.get("text", "")
        if not prompt_text or len(prompt_text) < 20:
            return None
        image_url = data.get("contentUrl", "") or data.get("image", "")
        return PromptItem(
            prompt=prompt_text,
            images=[image_url] if image_url else [],
            tags=self._extract_tags(prompt_text),
            style=self._guess_style(prompt_text),
            source_url=data.get("url", ""),
            author=data.get("author", {}).get("name", "") if isinstance(data.get("author"), dict) else "",
            tool=self._guess_tool(prompt_text),
            source_name=self.name,
        )

    def _parse_cards(self, html: str) -> list[PromptItem]:
        """回退方案：从 prompt card HTML 中提取数据"""
        items = []
        # 匹配 prompt 文本块（常见模式：data-prompt 属性或特定 class）
        prompt_pattern = r'data-prompt="([^"]+)"'
        img_pattern = r'<img[^>]*src="(https://[^"]*prompthero[^"]*)"'

        prompts = re.findall(prompt_pattern, html)
        images = re.findall(img_pattern, html)

        for i, prompt_text in enumerate(prompts):
            prompt_text = prompt_text.replace("&quot;", '"').replace("&amp;", "&")
            if len(prompt_text) < 20:
                continue
            img = images[i] if i < len(images) else ""
            items.append(PromptItem(
                prompt=prompt_text,
                images=[img] if img else [],
                tags=self._extract_tags(prompt_text),
                style=self._guess_style(prompt_text),
                source_url=self.base_url,
                tool=self._guess_tool(prompt_text),
                source_name=self.name,
            ))
        return items

    def _extract_tags(self, prompt: str) -> list[str]:
        prompt_lower = prompt.lower()
        tags = []
        tag_map = {
            "portrait": "portrait", "landscape": "landscape", "anime": "anime",
            "fantasy": "fantasy", "sci-fi": "sci-fi", "cyberpunk": "cyberpunk",
            "realistic": "photorealistic", "architecture": "architecture",
            "character": "character", "product": "product",
        }
        for keyword, tag in tag_map.items():
            if keyword in prompt_lower:
                tags.append(tag)
        return tags or ["general"]

    def _guess_style(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "anime" in prompt_lower:
            return "anime"
        if "realistic" in prompt_lower or "photo" in prompt_lower:
            return "photorealistic"
        if "painting" in prompt_lower:
            return "digital-art"
        return "mixed"

    def _guess_tool(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "midjourney" in prompt_lower or "--ar" in prompt_lower:
            return "Midjourney"
        if "flux" in prompt_lower:
            return "Flux"
        return "Stable Diffusion"
