from __future__ import annotations

from typing import Any


class ApiClient:
    def __init__(self) -> None:
        self._placeholder = True

    def fetch_current_user(self, auth_token: str) -> Any:
        raise NotImplementedError("远程 API 调用尚未实现")

    def fetch_current_period_usage(self, bearer_token: str) -> Any:
        raise NotImplementedError("远程 API 调用尚未实现")
