
import json
from pathlib import Path
from typing import Iterable, Dict, Any


def to_json(documents: Iterable[Dict[str, Any]], root_dir: Path) -> str:
    """Converts a list of file information dicts to a JSON string."""
    output_docs = []
    for doc in documents:
        relative_path = doc["path"].relative_to(root_dir)
        output_docs.append({
            "content": doc["content"],
            "metadata": {
                "source": str(relative_path),
                "mode": doc["mode"],
                "size": doc["size"],
                "mime": doc["mime"],
            },
        })

    return json.dumps({"documents": output_docs}, indent=2)
