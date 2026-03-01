"""
PromptVault Content Filter — 内容合规审查模块
确保采集的 prompt 和图片符合法律法规，过滤 NSFW / 暴力 / 政治敏感内容。

使用方式:
    from content_filter import ContentFilter
    cf = ContentFilter()
    safe_items, blocked = cf.filter_items(items)
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("content_filter")

# ============================================================
# 关键词黑名单（分级）
# ============================================================

# Level 1: 硬性拦截 — 命中即拦截，无例外
BLOCK_KEYWORDS_L1 = [
    # Sexual / NSFW (English)
    "nsfw", "nude", "naked", "porn", "pornographic", "xxx", "hentai",
    "erotic", "topless", "bondage", "fetish", "genitalia", "orgasm",
    "intercourse", "masturbat", "blowjob", "handjob", "creampie",
    "ahegao", "tentacle porn", "rule34", "r34", "loli", "shota",
    "deepfake", "underage", "child abuse",
    # Sexual / NSFW (Chinese)
    "色情", "裸体", "成人内容", "情色", "淫秽", "性交", "口交",
    "自慰", "乱伦", "恋童", "未成年",
    # Extreme violence
    "gore", "mutilation", "dismember", "torture porn", "snuff",
    "beheading", "execution video",
    "肢解", "虐杀", "斩首",
    # Illegal
    "child porn", "cp ", "csam",
]

# Level 2: 软性标记 — 命中后标记为 needs_review，不直接拦截
REVIEW_KEYWORDS_L2 = [
    # Suggestive but not necessarily NSFW
    "lingerie", "bikini", "cleavage", "seductive", "sensual",
    "provocative", "revealing", "skimpy", "busty", "voluptuous",
    "sexy", "thigh-high", "stockings",
    # Mild violence
    "blood", "wound", "corpse", "dead body", "murder scene",
    "暴力", "血腥", "尸体", "凶杀",
    # Substance
    "drug use", "cocaine", "heroin", "meth",
    "吸毒", "毒品",
]

# URL 路径中的 NSFW 标记
NSFW_URL_PATTERNS = [
    r"/nsfw/", r"/adult/", r"/xxx/", r"/porn/",
    r"nsfw=true", r"rating=explicit", r"rating=x",
]


class FilterResult:
    """单条内容的审查结果"""

    def __init__(self, item_id: str, prompt_preview: str):
        self.item_id = item_id
        self.prompt_preview = prompt_preview[:80]
        self.blocked = False
        self.needs_review = False
        self.reasons: list[str] = []

    def block(self, reason: str):
        self.blocked = True
        self.reasons.append(f"[BLOCK] {reason}")

    def flag(self, reason: str):
        self.needs_review = True
        self.reasons.append(f"[REVIEW] {reason}")

    def to_dict(self) -> dict:
        return {
            "id": self.item_id,
            "prompt_preview": self.prompt_preview,
            "blocked": self.blocked,
            "needs_review": self.needs_review,
            "reasons": self.reasons,
        }


class ContentFilter:
    """
    内容合规过滤器。

    三层防线:
    1. Prompt 文本关键词检测（L1 硬拦截 + L2 软标记）
    2. 图片 URL 模式检测
    3. 可扩展的图片内容检测接口（预留）
    """

    def __init__(self, log_dir: str = "scrapers/output/filter_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._stats = {"total": 0, "passed": 0, "blocked": 0, "flagged": 0}

    def check_prompt_text(self, text: str, result: FilterResult) -> None:
        """检查 prompt 文本（智能区分主 prompt 和 negative prompt）"""
        # Negative prompt 中的敏感词是用于排除的，不应触发拦截
        if "Negative prompt:" in text:
            main_part = text.split("Negative prompt:", 1)[0]
        else:
            main_part = text
        text_lower = main_part.lower()

        # L1: 硬性拦截（仅检查主 prompt 部分）
        for kw in BLOCK_KEYWORDS_L1:
            if kw.lower() in text_lower:
                result.block(f"L1 keyword hit: '{kw}'")
                return  # 一个就够了

        # L2: 软性标记
        hits = []
        for kw in REVIEW_KEYWORDS_L2:
            if kw.lower() in text_lower:
                hits.append(kw)
        if len(hits) >= 2:
            # 多个 L2 关键词同时出现，标记审核
            result.flag(f"L2 multiple hits: {hits[:5]}")
        elif len(hits) == 1:
            # 单个 L2 关键词，仅记录不标记
            pass

    def check_image_urls(self, urls: list[str], result: FilterResult) -> None:
        """检查图片 URL 是否包含 NSFW 标记"""
        for url in urls:
            url_lower = url.lower()
            for pattern in NSFW_URL_PATTERNS:
                if re.search(pattern, url_lower):
                    result.block(f"NSFW URL pattern: '{pattern}' in {url[:100]}")
                    return

    def check_item(self, item: dict) -> FilterResult:
        """审查单条 prompt item"""
        result = FilterResult(
            item_id=item.get("id", "unknown"),
            prompt_preview=item.get("prompt", ""),
        )

        # 1. 检查 prompt 文本
        self.check_prompt_text(item.get("prompt", ""), result)

        # 2. 检查 negative prompt（如果包含在 prompt 里）
        # negative prompt 本身可能包含 NSFW 词汇用于排除，这是正常的
        # 但如果主 prompt 部分包含，仍然拦截（上面已处理）

        # 3. 检查图片 URL
        if not result.blocked:
            self.check_image_urls(item.get("images", []), result)

        return result

    def filter_items(self, items: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
        """
        批量过滤。

        Returns:
            (safe_items, review_items, blocked_items)
            - safe_items: 通过审查，可以直接使用
            - review_items: 需要人工审核
            - blocked_items: 直接拦截
        """
        safe, review, blocked = [], [], []
        all_results = []

        for item in items:
            self._stats["total"] += 1
            result = self.check_item(item)
            all_results.append(result)

            if result.blocked:
                self._stats["blocked"] += 1
                blocked.append(item)
            elif result.needs_review:
                self._stats["flagged"] += 1
                review.append(item)
            else:
                self._stats["passed"] += 1
                safe.append(item)

        # 保存审查日志
        self._save_log(all_results)

        return safe, review, blocked

    def _save_log(self, results: list[FilterResult]) -> None:
        """保存审查日志"""
        flagged = [r.to_dict() for r in results if r.blocked or r.needs_review]
        if not flagged:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"filter_{timestamp}.json"
        log_file.write_text(json.dumps({
            "timestamp": timestamp,
            "stats": self._stats.copy(),
            "flagged_items": flagged,
        }, ensure_ascii=False, indent=2))
        logger.info(f"Filter log saved: {log_file}")

    def print_stats(self) -> None:
        """打印审查统计"""
        s = self._stats
        print(f"  Content Filter: {s['total']} checked, "
              f"{s['passed']} passed, {s['flagged']} flagged, "
              f"{s['blocked']} blocked")

    @property
    def stats(self) -> dict:
        return self._stats.copy()
