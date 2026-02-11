from pathlib import Path

import pytest

from app.services.skill_runtime import SandboxPolicy, SkillPackageValidator, SkillValidationError


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
