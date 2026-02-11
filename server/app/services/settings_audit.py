from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import SessionLocal
from app.models.case import Setting
from app.schemas.events import ConfirmationRiskLevel


class SettingsAuditService:
    """Audit/event recorder for settings modules."""

    AUDIT_TYPE = "settings_audit"

    def record(
        self,
        *,
        module: str,
        action: str,
        actor: str,
        target_id: str,
        detail: Dict[str, Any] | None = None,
        session_id: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        payload = {
            "module": module,
            "action": action,
            "actor": actor,
            "target_id": target_id,
            "detail": detail or {},
            "timestamp": now,
        }
        if session_id:
            payload["session_id"] = session_id
        if risk_level:
            normalized_risk = risk_level if risk_level in {level.value for level in ConfirmationRiskLevel} else None
            if normalized_risk:
                payload["risk_level"] = normalized_risk

        setting_id = f"{module}-{int(datetime.utcnow().timestamp() * 1000)}"

        with SessionLocal() as db:
            row = Setting(
                setting_type=self.AUDIT_TYPE,
                setting_id=setting_id,
                name=f"{module}:{action}",
                enabled=True,
                config=json.dumps(payload, ensure_ascii=False),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def list_recent(self, module: str, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(Setting)
                .filter(Setting.setting_type == self.AUDIT_TYPE)
                .order_by(Setting.created_at.desc())
                .limit(max(1, min(limit, 100)))
                .all()
            )

            entries = [self._to_dict(r) for r in rows]
            scoped = [e for e in entries if e.get("module") == module]
            if session_id:
                scoped = [e for e in scoped if e.get("session_id") == session_id]
            return scoped

    def list_by_session_id(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            rows = (
                db.query(Setting)
                .filter(Setting.setting_type == self.AUDIT_TYPE)
                .order_by(Setting.created_at.desc())
                .limit(max(1, min(limit, 500)))
                .all()
            )
            entries = [self._to_dict(r) for r in rows]
            return [e for e in entries if e.get("session_id") == session_id]

    def _to_dict(self, row: Setting) -> Dict[str, Any]:
        config = json.loads(row.config) if row.config else {}
        return {
            "id": row.setting_id,
            "module": config.get("module"),
            "action": config.get("action"),
            "actor": config.get("actor"),
            "target_id": config.get("target_id"),
            "detail": config.get("detail", {}),
            "session_id": config.get("session_id"),
            "risk_level": config.get("risk_level"),
            "timestamp": config.get("timestamp"),
        }
