from __future__ import annotations

import json
import os
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.core.database import SessionLocal
from app.models.case import Setting
from app.services.skill_runtime import (
    ApprovalRequiredError,
    SandboxPolicy,
    SkillPackageValidator,
    SkillValidationError,
    create_runtime,
)


class SkillLoader:
    SETTING_TYPE = "skill_package"

    def __init__(self) -> None:
        self.skills_root = Path("/tmp/skills")
        self.skills_root.mkdir(parents=True, exist_ok=True)
        self.validator = SkillPackageValidator()
        self.runtime_mode = os.getenv("SKILL_RUNTIME_MODE", "restricted").lower()
        self.runtime = create_runtime(self.runtime_mode)

    def list_skills(self) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            rows = db.query(Setting).filter(Setting.setting_type == self.SETTING_TYPE).all()
            return [self._to_dict(r) for r in rows]

    def save_skill_package(self, filename: str, content: bytes, actor: str = "system") -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as td:
            src_path = Path(td) / filename
            src_path.write_bytes(content)

            extract_dir = Path(td) / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            self._extract_archive(src_path, extract_dir)
            metadata = self._parse_metadata(extract_dir)
            self.validator.validate_package(extract_dir, metadata)
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
                "runtime_mode": self.runtime.metadata.mode,
                "path": str(self.skills_root / skill_id),
                "status": "running",
                "last_test_at": None,
                "last_test_status": None,
                "created_by": actor,
                "updated_by": actor,
                "updated_at": datetime.utcnow().isoformat(),
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
                existing = json.loads(row.config) if row.config else {}
                created_by = existing.get("created_by")
                existing.update(cfg)
                if created_by:
                    existing["created_by"] = created_by
                row.config = json.dumps(existing)

            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def set_enabled(self, skill_id: str, enabled: bool, actor: str = "system") -> Dict[str, Any]:
        with SessionLocal() as db:
            row = self._get_skill(db, skill_id)
            row.enabled = enabled
            config = json.loads(row.config) if row.config else {}
            config["status"] = "running" if enabled else "stopped"
            config["updated_by"] = actor
            config["updated_at"] = datetime.utcnow().isoformat()
            row.config = json.dumps(config)
            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def execute_skill(self, skill_id: str, approval_granted: bool = False) -> Dict[str, Any]:
        with SessionLocal() as db:
            row = self._get_skill(db, skill_id)
            config = json.loads(row.config) if row.config else {}

        permissions = config.get("permissions", {})
        skill_dir = Path(config.get("path", self.skills_root / skill_id))
        policy = SandboxPolicy.from_permissions(permissions, skill_dir=skill_dir)

        entrypoint = config.get("entrypoint", "run.py")
        command = ["python", entrypoint]

        try:
            result = self.runtime.execute(
                skill_dir=skill_dir,
                command=command,
                policy=policy,
                approval_granted=approval_granted,
            )
            result["requested_permissions"] = policy.requested_permissions()
            if "sandbox" not in result:
                result["sandbox"] = {
                    "mode": self.runtime.metadata.mode,
                    "production_safe": self.runtime.metadata.production_safe,
                    "label": self.runtime.metadata.label,
                    "policy": policy.as_dict(),
                }
            return result
        except ApprovalRequiredError as exc:
            return {
                "status": "approval_required",
                "message": str(exc),
                "requested_permissions": policy.requested_permissions(),
                "sandbox": {
                    "mode": self.runtime.metadata.mode,
                    "production_safe": self.runtime.metadata.production_safe,
                    "label": self.runtime.metadata.label,
                    "policy": policy.as_dict(),
                },
            }

    def test_skill(self, skill_id: str) -> Dict[str, Any]:
        with SessionLocal() as db:
            row = self._get_skill(db, skill_id)
            config = json.loads(row.config) if row.config else {}
            entrypoint = config.get("entrypoint", "run.py")
            skill_dir = Path(config.get("path", self.skills_root / skill_id))
            entry_file = skill_dir / entrypoint

            ok = entry_file.exists()
            message = "Entrypoint exists" if ok else f"Entrypoint not found: {entrypoint}"

            config["last_test_at"] = datetime.utcnow().isoformat()
            config["last_test_status"] = "success" if ok else "failed"
            config["status"] = "running" if ok and row.enabled else "degraded" if row.enabled else "stopped"
            row.config = json.dumps(config)
            db.commit()

            return {"success": ok, "message": message}

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
        try:
            return self.validator.parse_manifest(extract_dir)
        except SkillValidationError as exc:
            raise ValueError(str(exc)) from exc

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
        runtime_mode = config.get("runtime_mode", self.runtime.metadata.mode)
        return {
            "id": row.setting_id,
            "name": row.name,
            "enabled": row.enabled,
            "description": row.description,
            "version": config.get("version", "0.1.0"),
            "entrypoint": config.get("entrypoint", "run.py"),
            "permissions": config.get("permissions", {}),
            "runtime_mode": runtime_mode,
            "status": config.get("status", "running" if row.enabled else "stopped"),
            "last_test_at": config.get("last_test_at"),
            "last_test_status": config.get("last_test_status"),
            "created_by": config.get("created_by"),
            "updated_by": config.get("updated_by"),
            "updated_at": config.get("updated_at"),
        }
