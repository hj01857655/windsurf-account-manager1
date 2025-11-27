from __future__ import annotations

from typing import Optional


def backup_machine_code(os_name: Optional[str] = None) -> None:
    raise NotImplementedError("机器码备份逻辑尚未实现，需要先确定 Windsurf 本地配置路径")


def restore_machine_code(os_name: Optional[str] = None) -> None:
    raise NotImplementedError("机器码恢复逻辑尚未实现，需要先确定 Windsurf 本地配置路径")
