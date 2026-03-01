# PromptVault Scrapers

多源 prompt 采集框架，基于 Source Adapter 模式。

## 架构

```
scrapers/
├── base_adapter.py      # 基类 + 注册机制
├── collect.py           # 统一采集入口 CLI
├── adapter_civitai.py   # Civitai 适配器
├── adapter_prompthero.py # PromptHero 适配器
├── adapter_midjourney.py # Midjourney 适配器
└── output/              # 采集结果暂存
```

## 使用

```bash
# 列出所有可用数据源
python3 scrapers/collect.py --list

# 从 Civitai 采集 50 条
python3 scrapers/collect.py --source civitai --limit 50

# 从所有源采集并合并到 prompts.json
python3 scrapers/collect.py --source all --limit 30 --merge

# 单独运行某个 adapter
cd scrapers && python3 -c "from adapter_civitai import CivitaiAdapter; CivitaiAdapter().run(limit=10)"
```

## 添加新数据源

1. 创建 `adapter_xxx.py`
2. 继承 `BaseAdapter`，实现 `fetch()` 方法
3. 用 `@register_adapter` 装饰器注册
4. 在 `collect.py` 中 import

```python
from base_adapter import BaseAdapter, PromptItem, register_adapter

@register_adapter
class MyAdapter(BaseAdapter):
    name = "mysource"
    display_name = "My Source"
    base_url = "https://example.com"

    def fetch(self, limit=50) -> list[PromptItem]:
        # 采集逻辑
        return [PromptItem(prompt="...", images=[], tags=["tag1"])]
```

## 输出格式

每个 adapter 输出统一的 JSON 格式，与 `data/prompts.json` 结构一致：

```json
{
  "id": "20260301_civ_001",
  "prompt": "...",
  "images": ["https://..."],
  "tags": ["portrait", "photorealistic"],
  "style": "photorealistic",
  "source_url": "https://civitai.com/images/123",
  "author": "username",
  "tool": "Stable Diffusion",
  "created_at": "2026-03-01",
  "collected_at": "2026-03-01T12:00:00"
}
```
