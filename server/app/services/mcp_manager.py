from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import requests
from app.core.database import SessionLocal
from app.models.case import Setting


@dataclass
class MCPServerConfig:
    setting_id: str
    name: str
    transport: str
    endpoint: str
    enabled: bool
    version: str
    status: str
    last_test_at: Optional[str]
    last_test_status: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    updated_at: Optional[str]


class MCPManager:
    """Persist and test MCP server configurations."""

    SETTING_TYPE = "mcp_server"

    def list_servers(self) -> List[MCPServerConfig]:
        with SessionLocal() as db:
            rows = db.query(Setting).filter(Setting.setting_type == self.SETTING_TYPE).all()
            return [self._to_config(row) for row in rows]

    def upsert_server(
        self,
        *,
        setting_id: str,
        name: str,
        transport: str,
        endpoint: str,
        enabled: bool = True,
        version: str = "latest",
        actor: str = "system",
    ) -> MCPServerConfig:
        with SessionLocal() as db:
            row = db.query(Setting).filter(
                Setting.setting_type == self.SETTING_TYPE,
                Setting.setting_id == setting_id,
            ).first()

            payload = {
                "transport": transport,
                "endpoint": endpoint,
                "version": version,
                "last_test_at": None,
                "last_test_status": None,
                "status": "running" if enabled else "stopped",
                "created_by": actor,
                "updated_by": actor,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if row is None:
                row = Setting(
                    setting_type=self.SETTING_TYPE,
                    setting_id=setting_id,
                    name=name,
                    enabled=enabled,
                    config=json.dumps(payload),
                )
                db.add(row)
            else:
                row.name = name
                row.enabled = enabled
                existing = json.loads(row.config) if row.config else {}
                created_by = existing.get("created_by")
                existing.update(payload)
                if created_by:
                    existing["created_by"] = created_by
                row.config = json.dumps(existing)

            db.commit()
            db.refresh(row)
            return self._to_config(row)

    def set_enabled(self, setting_id: str, enabled: bool, actor: str = "system") -> MCPServerConfig:
        with SessionLocal() as db:
            row = self._get_by_id(db, setting_id)
            row.enabled = enabled
            config = json.loads(row.config) if row.config else {}
            config["status"] = "running" if enabled else "stopped"
            config["updated_by"] = actor
            config["updated_at"] = datetime.utcnow().isoformat()
            row.config = json.dumps(config)
            db.commit()
            db.refresh(row)
            return self._to_config(row)

    def delete_server(self, setting_id: str) -> None:
        with SessionLocal() as db:
            row = self._get_by_id(db, setting_id)
            db.delete(row)
            db.commit()

    def test_connection(self, setting_id: str) -> Dict[str, str | bool]:
        with SessionLocal() as db:
            row = self._get_by_id(db, setting_id)
            config = json.loads(row.config) if row.config else {}
            transport = config.get("transport", "http")
            endpoint = config.get("endpoint", "")

            ok, message = self._probe(transport=transport, endpoint=endpoint)

            config["last_test_at"] = datetime.utcnow().isoformat()
            config["last_test_status"] = "success" if ok else "failed"
            config["status"] = "running" if ok and row.enabled else "degraded" if row.enabled else "stopped"
            row.config = json.dumps(config)
            db.commit()

            return {"success": ok, "message": message}

    def _probe(self, *, transport: str, endpoint: str) -> tuple[bool, str]:
        if not endpoint:
            return False, "Endpoint is empty"

        try:
            if transport in {"http", "https", "sse"}:
                resp = requests.get(endpoint, timeout=5)
                return resp.ok, f"HTTP {resp.status_code}"

            if transport == "tcp":
                host, port = endpoint.split(":", 1)
                with socket.create_connection((host, int(port)), timeout=5):
                    return True, "TCP connection successful"

            return False, f"Unsupported transport: {transport}"
        except Exception as exc:
            return False, str(exc)

    def _to_config(self, row: Setting) -> MCPServerConfig:
        config = json.loads(row.config) if row.config else {}
        return MCPServerConfig(
            setting_id=row.setting_id,
            name=row.name,
            transport=config.get("transport", "http"),
            endpoint=config.get("endpoint", ""),
            enabled=row.enabled,
            version=config.get("version", "latest"),
            status=config.get("status", "running" if row.enabled else "stopped"),
            last_test_at=config.get("last_test_at"),
            last_test_status=config.get("last_test_status"),
            created_by=config.get("created_by"),
            updated_by=config.get("updated_by"),
            updated_at=config.get("updated_at"),
        )

    def _get_by_id(self, db, setting_id: str) -> Setting:
        row = db.query(Setting).filter(
            Setting.setting_type == self.SETTING_TYPE,
            Setting.setting_id == setting_id,
        ).first()
        if row is None:
            raise ValueError("MCP server not found")
        return row
