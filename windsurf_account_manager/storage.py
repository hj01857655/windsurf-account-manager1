from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .models import Account


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTS_PATH = DATA_DIR / "accounts.json"


def load_accounts() -> List[Account]:
    if not ACCOUNTS_PATH.exists():
        return []
    with ACCOUNTS_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    accounts: List[Account] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            accounts.append(Account(**item))
        except TypeError:
            continue
    return accounts


def save_accounts(accounts: List[Account]) -> None:
    data = [asdict(a) for a in accounts]
    with ACCOUNTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def import_from_windsurf_json(path: Path, existing: List[Account]) -> List[Account]:
    if not path.exists():
        return existing
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    by_email = {a.email: a for a in existing}
    from uuid import uuid4
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            email = item.get("email")
            if not email or email in by_email:
                continue
            password = item.get("password", "")
            acc = Account(id=str(uuid4()), email=email, password=password)
            by_email[email] = acc
    return list(by_email.values())


def export_accounts(path: Path, accounts: List[Account]) -> None:
    data = [asdict(a) for a in accounts]
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
