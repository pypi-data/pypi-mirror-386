
import mimetypes
from pathlib import Path
from typing import Iterator, Dict, Any

from .config import Config
from .modes.full import read_full_content


def scan_directory(path: Path, config: Config) -> Iterator[Dict[str, Any]]:
    """Scans a directory and yields information about each file."""
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix not in config.ext:
            continue

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith("text/"):
            continue

        content = read_full_content(file_path, config.max_file_size)

        yield {
            "path": file_path,
            "size": file_path.stat().st_size,
            "mime": mime_type or "unknown",
            "mode": "full",
            "content": content,
        }
