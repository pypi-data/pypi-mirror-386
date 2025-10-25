
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Config:
    ext: List[str] = field(default_factory=lambda: [".py", ".json", ".md"])
    out: Path = Path("project_tree.md")
    format: str = "md"
    max_file_size: int = 1024 * 1024  # 1MB


def parse_size(size_str: str) -> int:
    """Parse a size string like '1MB' or '2K' into bytes."""
    size_str = size_str.strip().upper()
    match = re.match(r"^(\d+)([KMGT]?B?)$", size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    value, unit = match.groups()
    value = int(value)

    if unit in ["K", "KB"]:
        return value * 1024
    if unit in ["M", "MB"]:
        return value * 1024 * 1024
    if unit in ["G", "GB"]:
        return value * 1024 * 1024 * 1024
    if unit in ["T", "TB"]:
        return value * 1024 * 1024 * 1024 * 1024
    return value


def load_config(config_file: Optional[Path] = None) -> Config:
    """In MVP, we just return the default config."""
    return Config()
