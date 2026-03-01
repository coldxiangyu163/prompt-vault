#!/usr/bin/env python3
"""
PromptVault 统一采集入口
用法:
    python3 scrapers/collect.py --source civitai --limit 50
    python3 scrapers/collect.py --source all --limit 30
    python3 scrapers/collect.py --list
    python3 scrapers/collect.py --source civitai --limit 50 --merge --filter
    python3 scrapers/collect.py --audit data/prompts.json  # 审查已有数据
"""

import argparse
import json
import sys
from pathlib import Path

# 确保 scrapers 目录在 path 中
sys.path.insert(0, str(Path(__file__).parent))

from base_adapter import list_adapters, get_adapter, _registry
from content_filter import ContentFilter

# 导入所有 adapter（触发 @register_adapter 注册）
import adapter_civitai
import adapter_prompthero
import adapter_midjourney


def merge_to_prompts_json(source_file: Path, prompts_file: Path, enable_filter: bool = True) -> dict:
    """将采集结果合并到主 prompts.json，返回统计信息"""
    existing = json.loads(prompts_file.read_text()) if prompts_file.exists() else []
    new_items = json.loads(source_file.read_text())

    # ========== 内容合规审查 ==========
    filter_stats = {}
    if enable_filter:
        cf = ContentFilter()
        safe_items, review_items, blocked_items = cf.filter_items(new_items)
        cf.print_stats()
        filter_stats = cf.stats

        if blocked_items:
            print(f"  ⛔ Blocked {len(blocked_items)} items (NSFW/违规)")
            for item in blocked_items:
                print(f"     - {item.get('id', '?')}: {item.get('prompt', '')[:60]}...")

        if review_items:
            print(f"  ⚠️  Flagged {len(review_items)} items for review (saved to filter_logs/)")

        # 只合并安全的内容
        new_items = safe_items
    # ==================================

    # 基于 prompt 文本去重（简单版：前100字符匹配）
    existing_prefixes = {p["prompt"][:100].lower().strip() for p in existing}
    added = []
    skipped = 0

    # 计算新 ID 起始序号
    max_idx = len(existing)
    for item in new_items:
        prefix = item["prompt"][:100].lower().strip()
        if prefix in existing_prefixes:
            skipped += 1
            continue
        max_idx += 1
        item["id"] = f"{item['id'].split('_')[0]}_{item['id'].split('_')[1]}_{max_idx:03d}"
        existing.append(item)
        existing_prefixes.add(prefix)
        added.append(item["id"])

    prompts_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    return {
        "added": len(added),
        "skipped": skipped,
        "total": len(existing),
        "filter": filter_stats,
    }


def audit_existing(prompts_file: Path) -> None:
    """审查已有 prompts.json 中的内容合规性"""
    if not prompts_file.exists():
        print(f"File not found: {prompts_file}")
        return

    items = json.loads(prompts_file.read_text())
    print(f"\n🔍 Auditing {len(items)} existing prompts...\n")

    cf = ContentFilter()
    safe, review, blocked = cf.filter_items(items)
    cf.print_stats()

    if blocked:
        print(f"\n⛔ Found {len(blocked)} items that should be REMOVED:")
        for item in blocked:
            print(f"  - [{item.get('id')}] {item.get('prompt', '')[:80]}...")

        # 自动清理
        answer = input(f"\nRemove {len(blocked)} blocked items? [y/N] ").strip().lower()
        if answer == "y":
            blocked_ids = {item.get("id") for item in blocked}
            cleaned = [item for item in items if item.get("id") not in blocked_ids]
            prompts_file.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2))
            print(f"✅ Removed {len(blocked)} items. {len(cleaned)} remaining.")
        else:
            print("Skipped. Check filter_logs/ for details.")

    if review:
        print(f"\n⚠️  Found {len(review)} items that need manual review:")
        for item in review[:10]:
            print(f"  - [{item.get('id')}] {item.get('prompt', '')[:80]}...")
        if len(review) > 10:
            print(f"  ... and {len(review) - 10} more. Check filter_logs/")

    if not blocked and not review:
        print("\n✅ All items passed compliance check!")


def main():
    parser = argparse.ArgumentParser(description="PromptVault Prompt Collector")
    parser.add_argument("--source", type=str, help="Source adapter name or 'all'")
    parser.add_argument("--limit", type=int, default=50, help="Max prompts per source")
    parser.add_argument("--list", action="store_true", help="List available adapters")
    parser.add_argument("--merge", action="store_true", help="Auto-merge to prompts.json")
    parser.add_argument("--filter", action="store_true", default=True,
                        help="Enable content filter (default: on)")
    parser.add_argument("--no-filter", action="store_true", help="Disable content filter")
    parser.add_argument("--audit", type=str, help="Audit existing prompts.json for compliance")
    parser.add_argument("--prompts-file", type=str, default="data/prompts.json",
                        help="Path to prompts.json")
    args = parser.parse_args()

    # 审查模式
    if args.audit:
        audit_existing(Path(args.audit))
        return

    if args.list:
        print("Available adapters:")
        for name in list_adapters():
            adapter_cls = _registry[name]
            print(f"  - {name}: {adapter_cls.display_name} ({adapter_cls.base_url})")
        return

    if not args.source:
        parser.print_help()
        return

    enable_filter = not args.no_filter
    sources = list_adapters() if args.source == "all" else [args.source]

    for source_name in sources:
        try:
            adapter = get_adapter(source_name)
            output_file = adapter.run(limit=args.limit)

            if args.merge:
                prompts_path = Path(args.prompts_file)
                stats = merge_to_prompts_json(output_file, prompts_path, enable_filter=enable_filter)
                print(f"  Merged: +{stats['added']} new, {stats['skipped']} duplicates, {stats['total']} total")
        except Exception as e:
            print(f"[ERROR] {source_name}: {e}")


if __name__ == "__main__":
    main()
