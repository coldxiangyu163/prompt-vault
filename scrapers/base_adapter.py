"""
PromptVault Source Adapter Framework
统一的 prompt 采集接口，所有数据源 adapter 继承此基类。
"""

import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class PromptItem:
    """统一的 prompt 数据结构，与 prompts.json 格式对齐"""

    def __init__(
        self,
        prompt: str,
        images: list[str],
        tags: list[str],
        style: str = "",
        source_url: str = "",
        author: str = "",
        tool: str = "Unknown",
        created_at: str = "",
        source_name: str = "",
    ):
        self.prompt = prompt.strip()
        self.images = images
        self.tags = [t.strip().lower() for t in tags if t.strip()]
        self.style = style.strip().lower()
        self.source_url = source_url
        self.author = author
        self.tool = tool
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d")
        self.collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        self.source_name = source_name

    @property
    def content_hash(self) -> str:
        """基于 prompt 文本生成去重 hash"""
        normalized = " ".join(self.prompt.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def generate_id(self, index: int) -> str:
        """生成唯一 ID: 日期_源名_序号"""
        date_str = datetime.now().strftime("%Y%m%d")
        src = self.source_name[:3] if self.source_name else "unk"
        return f"{date_str}_{src}_{index:03d}"

    def to_dict(self, id_str: str = "") -> dict:
        return {
            "id": id_str,
            "prompt": self.prompt,
            "images": self.images,
            "tags": self.tags,
            "style": self.style,
            "source_url": self.source_url,
            "author": self.author,
            "tool": self.tool,
            "created_at": self.created_at,
            "collected_at": self.collected_at,
        }


class BaseAdapter(ABC):
    """
    数据源适配器基类。
    每个新数据源只需继承此类并实现 fetch() 方法。
    """

    name: str = "base"          # 数据源标识
    display_name: str = "Base"  # 显示名称
    base_url: str = ""          # 数据源网站

    def __init__(self, output_dir: str = "scrapers/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch(self, limit: int = 50) -> list[PromptItem]:
        """
        从数据源采集 prompt。
        Args:
            limit: 最大采集数量
        Returns:
            PromptItem 列表
        """
        ...

    def save(self, items: list[PromptItem]) -> Path:
        """将采集结果保存为统一 JSON 格式"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = self.output_dir / f"{self.name}_{date_str}.json"

        records = []
        for i, item in enumerate(items, 1):
            item.source_name = self.name
            record = item.to_dict(id_str=item.generate_id(i))
            records.append(record)

        output_file.write_text(json.dumps(records, ensure_ascii=False, indent=2))
        return output_file

    def run(self, limit: int = 50) -> Path:
        """采集并保存，返回输出文件路径"""
        print(f"[{self.display_name}] Fetching up to {limit} prompts...")
        items = self.fetch(limit=limit)
        print(f"[{self.display_name}] Got {len(items)} prompts")
        output = self.save(items)
        print(f"[{self.display_name}] Saved to {output}")
        return output


# --- Adapter Registry ---

_registry: dict[str, type[BaseAdapter]] = {}


def register_adapter(cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """装饰器：注册 adapter 到全局 registry"""
    _registry[cls.name] = cls
    return cls


def get_adapter(name: str, **kwargs) -> BaseAdapter:
    """按名称获取 adapter 实例"""
    if name not in _registry:
        available = ", ".join(_registry.keys())
        raise ValueError(f"Unknown adapter: {name}. Available: {available}")
    return _registry[name](**kwargs)


def list_adapters() -> list[str]:
    """列出所有已注册的 adapter"""
    return list(_registry.keys())
