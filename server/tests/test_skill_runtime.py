from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from app.services.skill_loader import SkillLoader
from app.services.skill_runtime import SandboxPolicy, SkillPackageValidator, SkillValidationError
from app.services.skill_runtime.runtimes import RuntimeUnavailableError, create_runtime


@pytest.mark.parametrize(
    "permissions,expected",
    [
        ({"network": True, "fs_write": False, "timeout_seconds": 30, "cpu_seconds": 5, "memory_mb": 512}, (True, False, 30, 5, 512)),
        ({}, (False, False, 20, 10, 256)),
    ],
)
def test_policy_mapping(permissions, expected):
    policy = SandboxPolicy.from_permissions(permissions, skill_dir=Path("/tmp/skills/demo"))
    assert (
        policy.allow_network,
        policy.allow_fs_write,
        policy.timeout_seconds,
        policy.cpu_seconds,
        policy.memory_mb,
    ) == expected


def test_manifest_requires_entrypoint(tmp_path: Path):
    validator = SkillPackageValidator()
    (tmp_path / "skill.yaml").write_text("id: demo\nname: Demo Skill\n", encoding="utf-8")

    with pytest.raises(SkillValidationError):
        validator.parse_manifest(tmp_path)


def test_validate_dependency_allowlist(tmp_path: Path):
    validator = SkillPackageValidator()
    (tmp_path / "skill.yaml").write_text(
        "id: demo\nname: Demo Skill\nentrypoint: run.py\ndependencies:\n  - requests\n",
        encoding="utf-8",
    )
    (tmp_path / "run.py").write_text("print('ok')", encoding="utf-8")

    manifest = validator.parse_manifest(tmp_path)
    validator.validate_package(tmp_path, manifest)


def test_reject_binary_file(tmp_path: Path):
    validator = SkillPackageValidator()
    (tmp_path / "skill.yaml").write_text("id: demo\nname: Demo Skill\nentrypoint: run.py\n", encoding="utf-8")
    (tmp_path / "run.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / "payload.bin").write_bytes(b"\x7fELFxxxx")

    manifest = validator.parse_manifest(tmp_path)
    with pytest.raises(SkillValidationError):
        validator.validate_package(tmp_path, manifest)


def test_reject_zip_path_traversal(tmp_path: Path):
    loader = SkillLoader()
    archive = tmp_path / "evil.zip"
    extract_dir = tmp_path / "extract"
    extract_dir.mkdir()

    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "pwned")

    with pytest.raises(ValueError, match="escapes extraction root"):
        loader._extract_archive(archive, extract_dir)


def test_reject_tar_link_escape(tmp_path: Path):
    loader = SkillLoader()
    archive = tmp_path / "evil.tar"
    extract_dir = tmp_path / "extract"
    extract_dir.mkdir()

    with tarfile.open(archive, "w") as tf:
        info = tarfile.TarInfo(name="skill.yaml")
        payload = b"id: demo\nname: Demo\nentrypoint: run.py\n"
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))

        sym = tarfile.TarInfo(name="link")
        sym.type = tarfile.SYMTYPE
        sym.linkname = "/etc/passwd"
        tf.addfile(sym)

    with pytest.raises(ValueError, match="Links are not allowed"):
        loader._extract_archive(archive, extract_dir)


def test_restricted_runtime_unavailable_without_dev_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SKILL_ALLOW_LOCAL_SUBPROCESS", raising=False)
    monkeypatch.setattr("app.services.skill_runtime.runtimes.shutil.which", lambda *_: None)

    with pytest.raises(RuntimeUnavailableError, match="restricted runtime unavailable"):
        create_runtime("restricted")


def test_restricted_runtime_can_fallback_in_dev(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SKILL_ALLOW_LOCAL_SUBPROCESS", "1")
    monkeypatch.setattr("app.services.skill_runtime.runtimes.shutil.which", lambda *_: None)

    runtime = create_runtime("restricted")
    assert runtime.metadata.mode == "local-subprocess"
