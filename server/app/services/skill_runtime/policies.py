from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SandboxPolicy:
    """Runtime constraints derived from skill manifest permissions."""

    allow_network: bool = False
    allow_fs_write: bool = False
    timeout_seconds: int = 20
    cpu_seconds: int = 2
    memory_mb: int = 256
    readonly_mounts: List[Path] = field(default_factory=list)

    @classmethod
    def from_permissions(cls, permissions: Dict[str, Any], *, skill_dir: Path) -> "SandboxPolicy":
        timeout = int(permissions.get("timeout_seconds", 20))
        cpu_seconds = int(permissions.get("cpu_seconds", max(1, timeout // 2)))
        memory_mb = int(permissions.get("memory_mb", 256))

        return cls(
            allow_network=bool(permissions.get("network", False)),
            allow_fs_write=bool(permissions.get("fs_write", False)),
            timeout_seconds=max(1, min(timeout, 600)),
            cpu_seconds=max(1, min(cpu_seconds, 120)),
            memory_mb=max(64, min(memory_mb, 4096)),
            readonly_mounts=[skill_dir],
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "allow_network": self.allow_network,
            "allow_fs_write": self.allow_fs_write,
            "timeout_seconds": self.timeout_seconds,
            "cpu_seconds": self.cpu_seconds,
            "memory_mb": self.memory_mb,
            "readonly_mounts": [str(p) for p in self.readonly_mounts],
        }

    def requested_permissions(self) -> List[str]:
        requested: List[str] = []
        if self.allow_network:
            requested.append("network")
        if self.allow_fs_write:
            requested.append("fs_write")
        return requested
