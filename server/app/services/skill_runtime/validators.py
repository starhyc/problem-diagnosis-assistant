from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

ALLOWED_DEPENDENCIES = {
    "requests",
    "pyyaml",
    "pydantic",
    "numpy",
    "pandas",
    "httpx",
    "python-dateutil",
}

TEXT_SUFFIX_ALLOWLIST = {
    ".py",
    ".sh",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
}


class SkillValidationError(ValueError):
    pass


class SkillPackageValidator:
    def parse_manifest(self, extract_dir: Path) -> Dict[str, Any]:
        candidates = [extract_dir / "skill.yaml", extract_dir / "skill.yml", extract_dir / "skill.json"]
        for path in candidates:
            if not path.exists():
                continue
            if path.suffix in {".yaml", ".yml"}:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise SkillValidationError("skill metadata must be an object")
            self._validate_manifest(data)
            return data
        raise SkillValidationError("skill metadata file not found")

    def validate_package(self, extract_dir: Path, manifest: Dict[str, Any]) -> None:
        self._validate_entrypoint(extract_dir, manifest)
        self._validate_dependencies(extract_dir, manifest)
        self._validate_executable_files(extract_dir)

    def _validate_manifest(self, manifest: Dict[str, Any]) -> None:
        required = {"id", "name", "entrypoint"}
        missing = sorted(required - manifest.keys())
        if missing:
            raise SkillValidationError(f"skill metadata missing required fields: {', '.join(missing)}")

        permissions = manifest.get("permissions", {})
        if permissions and not isinstance(permissions, dict):
            raise SkillValidationError("permissions must be an object")

    def _validate_entrypoint(self, extract_dir: Path, manifest: Dict[str, Any]) -> None:
        entrypoint = manifest.get("entrypoint", "run.py")
        if Path(entrypoint).is_absolute() or ".." in Path(entrypoint).parts:
            raise SkillValidationError("entrypoint must be a relative path inside the package")

        entrypoint_path = extract_dir / entrypoint
        if not entrypoint_path.exists() or not entrypoint_path.is_file():
            raise SkillValidationError(f"entrypoint not found: {entrypoint}")

        if entrypoint_path.suffix not in {".py", ".sh"}:
            raise SkillValidationError("entrypoint must be a .py or .sh script")

    def _validate_dependencies(self, extract_dir: Path, manifest: Dict[str, Any]) -> None:
        declared = manifest.get("dependencies", [])
        if declared and not isinstance(declared, list):
            raise SkillValidationError("dependencies in manifest must be a list")

        deps: List[str] = []
        deps.extend([str(dep).strip() for dep in declared if str(dep).strip()])

        req_path = extract_dir / "requirements.txt"
        if req_path.exists():
            req_lines = [line.strip() for line in req_path.read_text(encoding="utf-8").splitlines()]
            deps.extend([line for line in req_lines if line and not line.startswith("#")])

        not_allowed = sorted({dep for dep in deps if self._package_name(dep) not in ALLOWED_DEPENDENCIES})
        if not_allowed:
            raise SkillValidationError(
                "dependencies not in allowlist: " + ", ".join(not_allowed)
            )

    def _validate_executable_files(self, extract_dir: Path) -> None:
        for file_path in extract_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() in TEXT_SUFFIX_ALLOWLIST:
                continue

            if self._is_binary(file_path):
                raise SkillValidationError(f"binary executable not allowed: {file_path.relative_to(extract_dir)}")

            if os.access(file_path, os.X_OK):
                raise SkillValidationError(f"unexpected executable file: {file_path.relative_to(extract_dir)}")

    def _is_binary(self, path: Path) -> bool:
        head = path.read_bytes()[:4]
        if head.startswith(b"\x7fELF"):
            return True
        if head.startswith(b"MZ"):
            return True
        return False

    def _package_name(self, dependency_spec: str) -> str:
        marker_split = dependency_spec.split(";", 1)[0]
        normalized = marker_split.replace(" ", "")
        for sep in ["==", ">=", "<=", "~=", "!=", ">", "<"]:
            if sep in normalized:
                normalized = normalized.split(sep, 1)[0]
                break
        return normalized.lower()
