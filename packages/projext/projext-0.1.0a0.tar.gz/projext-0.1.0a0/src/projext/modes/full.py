
from pathlib import Path


def read_full_content(file_path: Path, max_file_size: int) -> str:
    """Reads the full content of a file, with size and encoding checks."""
    if file_path.stat().st_size > max_file_size:
        return f"[File too large: {file_path.stat().st_size / 1024 / 1024:.2f}MB - content omitted. Use --max-file-size to increase limit]"

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "[Binary or non-UTF8 file]"
    except Exception as e:
        return f"[Error reading file: {e}]"
