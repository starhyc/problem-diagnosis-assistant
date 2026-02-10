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
                existing.update(payload)
                row.config = json.dumps(existing)

            db.commit()
            db.refresh(row)
            return self._to_config(row)

    def set_enabled(self, setting_id: str, enabled: bool) -> MCPServerConfig:
        with SessionLocal() as db:
            row = self._get_by_id(db, setting_id)
            row.enabled = enabled
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
        )

    def _get_by_id(self, db, setting_id: str) -> Setting:
        row = db.query(Setting).filter(
            Setting.setting_type == self.SETTING_TYPE,
            Setting.setting_id == setting_id,
        ).first()
        if row is None:
            raise ValueError("MCP server not found")
        return row
