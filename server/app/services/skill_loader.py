from __future__ import annotations

import json
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import yaml
from app.core.database import SessionLocal
from app.models.case import Setting
from app.services.skill_sandbox import ApprovalRequiredError, SandboxPolicy, SkillSandboxExecutor


class SkillLoader:
    SETTING_TYPE = "skill_package"

    def __init__(self) -> None:
        self.skills_root = Path("/tmp/skills")
        self.skills_root.mkdir(parents=True, exist_ok=True)
        self.sandbox = SkillSandboxExecutor(self.skills_root)

    def list_skills(self) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            rows = db.query(Setting).filter(Setting.setting_type == self.SETTING_TYPE).all()
            return [self._to_dict(r) for r in rows]

    def save_skill_package(self, filename: str, content: bytes) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as td:
            src_path = Path(td) / filename
            src_path.write_bytes(content)

            extract_dir = Path(td) / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            self._extract_archive(src_path, extract_dir)
            metadata = self._parse_metadata(extract_dir)
            skill_id = metadata["id"]

            dest_dir = self.skills_root / skill_id
            if dest_dir.exists():
                for p in dest_dir.glob("**/*"):
                    if p.is_file():
                        p.unlink()
            dest_dir.mkdir(parents=True, exist_ok=True)

            for item in extract_dir.rglob("*"):
                rel = item.relative_to(extract_dir)
                target = dest_dir / rel
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(item.read_bytes())

        with SessionLocal() as db:
            row = db.query(Setting).filter(
                Setting.setting_type == self.SETTING_TYPE,
                Setting.setting_id == skill_id,
            ).first()

            cfg = {
                "version": metadata.get("version", "0.1.0"),
                "entrypoint": metadata.get("entrypoint", "run.py"),
                "permissions": metadata.get("permissions", {}),
                "path": str(self.skills_root / skill_id),
            }

            if row is None:
                row = Setting(
                    setting_type=self.SETTING_TYPE,
                    setting_id=skill_id,
                    name=metadata.get("name", skill_id),
                    enabled=True,
                    description=metadata.get("description"),
                    config=json.dumps(cfg),
                )
                db.add(row)
            else:
                row.name = metadata.get("name", row.name)
                row.description = metadata.get("description", row.description)
                row.config = json.dumps(cfg)

            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def set_enabled(self, skill_id: str, enabled: bool) -> Dict[str, Any]:
        with SessionLocal() as db:
            row = self._get_skill(db, skill_id)
            row.enabled = enabled
            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def execute_skill(self, skill_id: str, approval_granted: bool = False) -> Dict[str, Any]:
        with SessionLocal() as db:
            row = self._get_skill(db, skill_id)
            config = json.loads(row.config) if row.config else {}

        permissions = config.get("permissions", {})
        policy = SandboxPolicy(
            allow_network=bool(permissions.get("network", False)),
            allow_fs_write=bool(permissions.get("fs_write", False)),
            timeout_seconds=int(permissions.get("timeout_seconds", 20)),
        )

        entrypoint = config.get("entrypoint", "run.py")
        skill_dir = Path(config.get("path", self.skills_root / skill_id))
        command = ["python", entrypoint]

        try:
            return self.sandbox.execute(
                skill_dir=skill_dir,
                command=command,
                policy=policy,
                approval_granted=approval_granted,
            )
        except ApprovalRequiredError as exc:
            return {"status": "approval_required", "message": str(exc)}

    def _extract_archive(self, src_path: Path, extract_dir: Path) -> None:
        if src_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(src_path, "r") as zf:
                zf.extractall(extract_dir)
            return

        if src_path.suffix.lower() in {".gz", ".tgz", ".tar"}:
            with tarfile.open(src_path, "r:*") as tf:
                tf.extractall(extract_dir)
            return

        raise ValueError("Unsupported archive format")

    def _parse_metadata(self, extract_dir: Path) -> Dict[str, Any]:
        candidates = [
            extract_dir / "skill.yaml",
            extract_dir / "skill.yml",
            extract_dir / "skill.json",
        ]
        for path in candidates:
            if path.exists():
                if path.suffix in {".yaml", ".yml"}:
                    data = yaml.safe_load(path.read_text(encoding="utf-8"))
                else:
                    data = json.loads(path.read_text(encoding="utf-8"))
                if "id" not in data:
                    raise ValueError("skill metadata must include id")
                return data
        raise ValueError("skill metadata file not found")

    def _get_skill(self, db, skill_id: str) -> Setting:
        row = db.query(Setting).filter(
            Setting.setting_type == self.SETTING_TYPE,
            Setting.setting_id == skill_id,
        ).first()
        if row is None:
            raise ValueError("Skill not found")
        return row

    def _to_dict(self, row: Setting) -> Dict[str, Any]:
        config = json.loads(row.config) if row.config else {}
        return {
            "id": row.setting_id,
            "name": row.name,
            "enabled": row.enabled,
            "description": row.description,
            "version": config.get("version", "0.1.0"),
            "entrypoint": config.get("entrypoint", "run.py"),
            "permissions": config.get("permissions", {}),
        }
