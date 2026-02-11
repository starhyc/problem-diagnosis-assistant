from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .policies import SandboxPolicy


class RuntimeUnavailableError(RuntimeError):
    pass


class ApprovalRequiredError(RuntimeError):
    pass


class PolicyViolationError(RuntimeError):
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

    def preflight(self) -> dict[str, Any]:
        return {
            "ok": True,
            "mode": self.metadata.mode,
            "runtime": self.metadata.label,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checks": [],
        }

    def _assert_approval(self, policy: SandboxPolicy, approval_granted: bool) -> None:
        if policy.requested_permissions() and not approval_granted:
            raise ApprovalRequiredError("Skill requires approval for requested permissions")


class RestrictedRuntime(BaseSkillRuntime):
    """Production runtime using namespace/cgroup-like controls with bubblewrap/prlimit."""

    metadata = RuntimeMetadata(mode="restricted", production_safe=True, label="生产级受限沙盒")

    def _kernel_flag(self, path: Path, *, validator) -> tuple[bool, str]:
        if not path.exists():
            return True, f"{path} not present; skipped"
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return False, f"unable to read {path}: {exc}"
        valid = validator(value)
        return valid, f"{path}={value}"

    def preflight(self) -> dict[str, Any]:
        checks = []

        for binary in ("bwrap", "prlimit"):
            binary_path = shutil.which(binary)
            ok = bool(binary_path and os.access(binary_path, os.X_OK))
            checks.append(
                {
                    "name": f"binary:{binary}",
                    "ok": ok,
                    "detail": binary_path if binary_path else "not found",
                }
            )

        user_ns_ok, user_ns_detail = self._kernel_flag(
            Path("/proc/sys/user/max_user_namespaces"), validator=lambda value: int(value) > 0
        )
        checks.append({"name": "kernel:max_user_namespaces", "ok": user_ns_ok, "detail": user_ns_detail})

        unprivileged_ok, unprivileged_detail = self._kernel_flag(
            Path("/proc/sys/kernel/unprivileged_userns_clone"), validator=lambda value: int(value) == 1
        )
        checks.append({"name": "kernel:unprivileged_userns_clone", "ok": unprivileged_ok, "detail": unprivileged_detail})

        ok = all(item["ok"] for item in checks)
        return {
            "ok": ok,
            "mode": self.metadata.mode,
            "runtime": self.metadata.label,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }

    def execute(
        self,
        *,
        skill_dir: Path,
        command: Iterable[str],
        policy: SandboxPolicy,
        approval_granted: bool,
    ) -> dict:
        self._assert_approval(policy, approval_granted)

        preflight = self.preflight()
        if not preflight["ok"]:
            raise RuntimeUnavailableError("restricted runtime preflight failed")

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
                "preflight": preflight,
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
                "preflight": self.preflight(),
            },
        }


def write_preflight_audit(preflight: dict[str, Any], *, selected_mode: str, fallback_mode: str | None = None) -> None:
    path = Path(os.getenv("SKILL_RUNTIME_AUDIT_LOG", "/tmp/skill_runtime_preflight_audit.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event": "skill_runtime_preflight",
        "selected_mode": selected_mode,
        "fallback_mode": fallback_mode,
        **preflight,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def create_runtime(mode: str) -> BaseSkillRuntime:
    normalized = (mode or "restricted").strip().lower()
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
    allow_dev_fallback = os.getenv("SKILL_ALLOW_LOCAL_SUBPROCESS", "0").strip().lower() in {"1", "true", "yes", "on"}

    if normalized in {"local", "local-subprocess"}:
        if environment == "production" and not allow_dev_fallback:
            raise RuntimeUnavailableError("local-subprocess runtime is disabled in production")
        runtime = LocalSubprocessRuntime()
        write_preflight_audit(runtime.preflight(), selected_mode=runtime.metadata.mode)
        return runtime

    runtime = RestrictedRuntime()
    preflight = runtime.preflight()
    write_preflight_audit(preflight, selected_mode=runtime.metadata.mode)
    if preflight["ok"]:
        return runtime

    if environment in {"development", "test"} and allow_dev_fallback:
        fallback = LocalSubprocessRuntime()
        write_preflight_audit(fallback.preflight(), selected_mode=runtime.metadata.mode, fallback_mode=fallback.metadata.mode)
        return fallback

    raise RuntimeUnavailableError("restricted runtime unavailable and local fallback is disabled")
