#!/usr/bin/env python3
"""
PromptVault 统一采集入口
用法:
    python3 scrapers/collect.py --source civitai --limit 50
    python3 scrapers/collect.py --source all --limit 30
    python3 scrapers/collect.py --list
"""

import argparse
import json
import sys
from pathlib import Path

# 确保 scrapers 目录在 path 中
sys.path.insert(0, str(Path(__file__).parent))

from base_adapter import list_adapters, get_adapter, _registry

# 导入所有 adapter（触发 @register_adapter 注册）
import adapter_civitai
import adapter_prompthero
import adapter_midjourney


def merge_to_prompts_json(source_file: Path, prompts_file: Path) -> dict:
    """将采集结果合并到主 prompts.json，返回统计信息"""
    existing = json.loads(prompts_file.read_text()) if prompts_file.exists() else []
    new_items = json.loads(source_file.read_text())

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
    return {"added": len(added), "skipped": skipped, "total": len(existing)}


def main():
    parser = argparse.ArgumentParser(description="PromptVault Prompt Collector")
    parser.add_argument("--source", type=str, help="Source adapter name or 'all'")
    parser.add_argument("--limit", type=int, default=50, help="Max prompts per source")
    parser.add_argument("--list", action="store_true", help="List available adapters")
    parser.add_argument("--merge", action="store_true", help="Auto-merge to prompts.json")
    parser.add_argument("--prompts-file", type=str, default="data/prompts.json",
                        help="Path to prompts.json")
    args = parser.parse_args()

    if args.list:
        print("Available adapters:")
        for name in list_adapters():
            adapter_cls = _registry[name]
            print(f"  - {name}: {adapter_cls.display_name} ({adapter_cls.base_url})")
        return

    if not args.source:
        parser.print_help()
        return

    sources = list_adapters() if args.source == "all" else [args.source]

    for source_name in sources:
        try:
            adapter = get_adapter(source_name)
            output_file = adapter.run(limit=args.limit)

            if args.merge:
                prompts_path = Path(args.prompts_file)
                stats = merge_to_prompts_json(output_file, prompts_path)
                print(f"  Merged: +{stats['added']} new, {stats['skipped']} duplicates, {stats['total']} total")
        except Exception as e:
            print(f"[ERROR] {source_name}: {e}")


if __name__ == "__main__":
    main()
