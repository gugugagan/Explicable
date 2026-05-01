from __future__ import annotations

import json
from pathlib import Path

from .models import WordGroup


def export_group_config(group: WordGroup, output_dir: str | Path) -> Path:
    """Write one group JSON config file."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "group_id": group.group_id,
        "words": [word.to_dict() for word in group.words],
        "prompt": group.prompt,
    }
    path = directory / f"group_{group.group_id:03d}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_group_configs(groups: list[WordGroup], output_dir: str | Path) -> list[Path]:
    return [export_group_config(group, output_dir) for group in groups]
