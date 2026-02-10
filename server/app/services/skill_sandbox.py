from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class SandboxPolicy:
    allow_network: bool = False
    allow_fs_write: bool = False
    timeout_seconds: int = 20


class ApprovalRequiredError(RuntimeError):
    pass


class SkillSandboxExecutor:
    """Isolated skill executor via subprocess with capability gate."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def execute(
        self,
        *,
        skill_dir: Path,
        command: Iterable[str],
        policy: SandboxPolicy,
        approval_granted: bool,
    ) -> dict:
        if (policy.allow_network or policy.allow_fs_write) and not approval_granted:
            raise ApprovalRequiredError("Skill requires approval for requested permissions")

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "SKILL_SANDBOX": "1",
            "SKILL_NETWORK": "1" if policy.allow_network else "0",
            "SKILL_FS_WRITE": "1" if policy.allow_fs_write else "0",
        }

        proc = subprocess.run(
            list(command),
            cwd=skill_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=policy.timeout_seconds,
            start_new_session=True,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
