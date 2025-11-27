from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import McpServerConfig, RuleConfig


def load_mcp_config(path: Path) -> List[McpServerConfig]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    result: List[McpServerConfig] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                result.append(McpServerConfig(**item))
            except TypeError:
                continue
    return result


def save_mcp_config(path: Path, servers: List[McpServerConfig]) -> None:
    data = [server.__dict__ for server in servers]
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_rules(path: Path) -> List[RuleConfig]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    result: List[RuleConfig] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                result.append(RuleConfig(**item))
            except TypeError:
                continue
    return result


def save_rules(path: Path, rules: List[RuleConfig]) -> None:
    data = [rule.__dict__ for rule in rules]
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
