from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .policies import SandboxPolicy


class ApprovalRequiredError(RuntimeError):
    pass


@dataclass
class RuntimeMetadata:
    mode: str
    production_safe: bool
    label: str


class BaseSkillRuntime:
    metadata = RuntimeMetadata(mode="base", production_safe=False, label="未配置沙盒")

    def execute(
        self,
        *,
        skill_dir: Path,
        command: Iterable[str],
        policy: SandboxPolicy,
        approval_granted: bool,
    ) -> dict:
        raise NotImplementedError

    def _assert_approval(self, policy: SandboxPolicy, approval_granted: bool) -> None:
        if policy.requested_permissions() and not approval_granted:
            raise ApprovalRequiredError("Skill requires approval for requested permissions")


class RestrictedRuntime(BaseSkillRuntime):
    """Production runtime using namespace/cgroup-like controls with bubblewrap/prlimit."""

    metadata = RuntimeMetadata(mode="restricted", production_safe=True, label="生产级受限沙盒")

    def execute(
        self,
        *,
        skill_dir: Path,
        command: Iterable[str],
        policy: SandboxPolicy,
        approval_granted: bool,
    ) -> dict:
        self._assert_approval(policy, approval_granted)

        if shutil.which("bwrap") is None or shutil.which("prlimit") is None:
            raise RuntimeError("restricted runtime requires bwrap and prlimit installed")

        workspace = "/workspace"
        bwrap_cmd = [
            "bwrap",
            "--die-with-parent",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--chdir",
            workspace,
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/bin",
            "/bin",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--tmpfs",
            "/tmp",
        ]

        mount_flag = "--bind" if policy.allow_fs_write else "--ro-bind"
        bwrap_cmd.extend([mount_flag, str(skill_dir), workspace])

        if policy.allow_network:
            bwrap_cmd.append("--share-net")
        else:
            bwrap_cmd.append("--unshare-net")

        final_cmd = [
            "prlimit",
            f"--cpu={policy.cpu_seconds}",
            f"--as={policy.memory_mb * 1024 * 1024}",
            "--",
            *bwrap_cmd,
            *list(command),
        ]

        env = {
            "PATH": os.environ.get("PATH", ""),
            "SKILL_SANDBOX": "1",
            "SKILL_RUNTIME": self.metadata.mode,
            "SKILL_NETWORK": "1" if policy.allow_network else "0",
            "SKILL_FS_WRITE": "1" if policy.allow_fs_write else "0",
        }

        proc = subprocess.run(
            final_cmd,
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
            "sandbox": {
                "mode": self.metadata.mode,
                "production_safe": self.metadata.production_safe,
                "label": self.metadata.label,
                "policy": policy.as_dict(),
            },
        }


class LocalSubprocessRuntime(BaseSkillRuntime):
    """Legacy runtime retained for local development only."""

    metadata = RuntimeMetadata(mode="local-subprocess", production_safe=False, label="非生产沙盒")

    def execute(
        self,
        *,
        skill_dir: Path,
        command: Iterable[str],
        policy: SandboxPolicy,
        approval_granted: bool,
    ) -> dict:
        self._assert_approval(policy, approval_granted)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "SKILL_SANDBOX": "1",
            "SKILL_RUNTIME": self.metadata.mode,
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
            "sandbox": {
                "mode": self.metadata.mode,
                "production_safe": self.metadata.production_safe,
                "label": self.metadata.label,
                "policy": policy.as_dict(),
            },
        }


def create_runtime(mode: str) -> BaseSkillRuntime:
    if mode == "local":
        return LocalSubprocessRuntime()
    return RestrictedRuntime()
