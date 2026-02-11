from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.logging_config import get_logger
import json

logger = get_logger(__name__)


class DiagnosisState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = []
        self.hypothesis_tree: Dict[str, Any] = {}
        self.timeline: List[Dict[str, Any]] = []
        self.confidence: int = 0
        self.evidence: List[Dict[str, Any]] = []
        self.current_phase: str = "init"
        self.task_status: str = "submitted"
        self.snapshot_data: Dict[str, Any] = {}
        self.mode: str = "plan_execute"
        self.mode_history: List[Dict[str, Any]] = []
        self.final_effective_mode: str = "plan_execute"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "hypothesis_tree": self.hypothesis_tree,
            "timeline": self.timeline,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "current_phase": self.current_phase,
            "task_status": self.task_status,
            "snapshot_data": self.snapshot_data,
            "mode": self.mode,
            "mode_history": self.mode_history,
            "final_effective_mode": self.final_effective_mode,
        }


class StateManager:
    def __init__(self):
        self._memory_states: Dict[str, DiagnosisState] = {}
        self._task_status_transitions: Dict[str, List[str]] = {
            "submitted": ["running", "canceled", "failed"],
            "running": ["waiting_user", "retrying", "completed", "failed", "canceled"],
            "waiting_user": ["running", "retrying", "failed", "canceled"],
            "retrying": ["running", "failed", "canceled"],
            "completed": [],
            "failed": [],
            "canceled": [],
        }

    def validate_task_status_transition(self, from_status: str, to_status: str) -> bool:
        if from_status == to_status:
            return True
        return to_status in self._task_status_transitions.get(from_status, [])

    def apply_task_status(self, state_data: Dict[str, Any], task_status: str):
        current_status = state_data.get("task_status", "submitted")
        if not self.validate_task_status_transition(current_status, task_status):
            raise ValueError(f"Invalid task status transition: {current_status} -> {task_status}")
        state_data["task_status"] = task_status

    def transition_task_status(
        self,
        session_id: str,
        task_status: str,
        db: Session,
        event_data: Optional[Dict[str, Any]] = None,
    ):
        state = self._memory_states.get(session_id)
        if not state:
            state = self.create_state(session_id)

        previous = state.task_status
        if not self.validate_task_status_transition(previous, task_status):
            raise ValueError(f"Invalid task status transition: {previous} -> {task_status}")

        state.task_status = task_status

        payload = {
            "from_status": previous,
            "to_status": task_status,
            **(event_data or {}),
        }

        try:
            self._upsert_task_status_snapshot(session_id, task_status, db)
            self._insert_event_row(session_id, "task_status_changed", payload, db)
            db.commit()
        except Exception:
            db.rollback()
            state.task_status = previous
            raise

    def get_state(self, session_id: str) -> Optional[DiagnosisState]:
        """Get current state from memory"""
        return self._memory_states.get(session_id)

    def create_state(self, session_id: str) -> DiagnosisState:
        """Create new diagnosis state"""
        state = DiagnosisState(session_id)
        self._memory_states[session_id] = state
        logger.info(f"Created state for session: {session_id}")
        return state

    def update_state(self, session_id: str, updates: Dict[str, Any]):
        """Update state in memory"""
        state = self._memory_states.get(session_id)
        if state:
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)

    def save_snapshot(self, session_id: str, db: Session):
        """Save state snapshot to database"""
        state = self._memory_states.get(session_id)
        if not state:
            return

        from sqlalchemy import text

        snapshot_data = json.dumps(state.to_dict())

        updated_at_expr = "CURRENT_TIMESTAMP" if db.bind and db.bind.dialect.name == "sqlite" else "NOW()"
        db.execute(
            text(
                f"""
                INSERT INTO diagnosis_sessions (session_id, snapshot_data, snapshot_version)
                VALUES (:session_id, :snapshot_data, 1)
                ON CONFLICT (session_id)
                DO UPDATE SET snapshot_data = :snapshot_data,
                              snapshot_version = diagnosis_sessions.snapshot_version + 1,
                              updated_at = {updated_at_expr}
            """
            ),
            {"session_id": session_id, "snapshot_data": snapshot_data},
        )
        db.commit()
        logger.info(f"Saved snapshot for session: {session_id}")

    def record_event(self, session_id: str, event_type: str, event_data: Dict[str, Any], db: Session):
        """Record event to database"""
        self._insert_event_row(session_id, event_type, event_data, db)
        db.commit()

    def _insert_event_row(self, session_id: str, event_type: str, event_data: Dict[str, Any], db: Session):
        """Insert event with database-derived per-session monotonic sequence."""

        from sqlalchemy import text

        for _ in range(5):
            try:
                db.execute(
                    text(
                        """
                        WITH next_sequence AS (
                            SELECT COALESCE(MAX(sequence), -1) + 1 AS sequence
                            FROM diagnosis_events
                            WHERE session_id = :session_id
                        )
                        INSERT INTO diagnosis_events (session_id, event_type, event_data, sequence)
                        SELECT :session_id, :event_type, :event_data, sequence
                        FROM next_sequence
                        """
                    ),
                    {
                        "session_id": session_id,
                        "event_type": event_type,
                        "event_data": json.dumps(event_data),
                    },
                )
                return
            except IntegrityError:
                db.rollback()

        raise RuntimeError(f"Failed to allocate event sequence for session {session_id} after retries")

    def register_idempotency_key(self, session_id: str, action_id: str, step_id: str, db: Session) -> bool:
        from sqlalchemy import text

        inserted = db.execute(
            text(
                """
                INSERT INTO diagnosis_idempotency_keys (session_id, action_id, step_id)
                VALUES (:session_id, :action_id, :step_id)
                ON CONFLICT (session_id, action_id, step_id)
                DO NOTHING
                """
            ),
            {
                "session_id": session_id,
                "action_id": action_id,
                "step_id": step_id,
            },
        )
        db.commit()
        return inserted.rowcount > 0

    def register_idempotency_key_atomic(self, session_id: str, action_id: str, step_id: str, db: Session) -> bool:
        from sqlalchemy import text

        inserted = db.execute(
            text(
                """
                INSERT INTO diagnosis_idempotency_keys (session_id, action_id, step_id)
                VALUES (:session_id, :action_id, :step_id)
                ON CONFLICT (session_id, action_id, step_id)
                DO NOTHING
                """
            ),
            {
                "session_id": session_id,
                "action_id": action_id,
                "step_id": step_id,
            },
        )
        return inserted.rowcount > 0

    def _upsert_task_status_snapshot(self, session_id: str, task_status: str, db: Session):
        from sqlalchemy import text

        if db.bind and db.bind.dialect.name == "sqlite":
            existing_row = db.execute(
                text("SELECT snapshot_data FROM diagnosis_sessions WHERE session_id = :session_id"),
                {"session_id": session_id},
            ).fetchone()
            existing = {}
            if existing_row and existing_row[0]:
                existing = json.loads(existing_row[0])
            existing["task_status"] = task_status
            existing.setdefault("session_id", session_id)

            db.execute(
                text(
                    """
                    INSERT INTO diagnosis_sessions (session_id, snapshot_data, snapshot_version)
                    VALUES (:session_id, :snapshot_data, 1)
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        snapshot_data = :snapshot_data,
                        snapshot_version = diagnosis_sessions.snapshot_version + 1,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "session_id": session_id,
                    "snapshot_data": json.dumps(existing),
                },
            )
            return

        db.execute(
            text(
                """
                INSERT INTO diagnosis_sessions (session_id, snapshot_data, snapshot_version)
                VALUES (:session_id, CAST(:snapshot_data AS JSONB), 1)
                ON CONFLICT (session_id)
                DO UPDATE SET
                    snapshot_data = COALESCE(diagnosis_sessions.snapshot_data, '{}'::jsonb) ||
                                    jsonb_build_object('task_status', :task_status),
                    snapshot_version = diagnosis_sessions.snapshot_version + 1,
                    updated_at = NOW()
                """
            ),
            {
                "session_id": session_id,
                "snapshot_data": json.dumps({"session_id": session_id, "task_status": task_status}),
                "task_status": task_status,
            },
        )

    def load_from_snapshot(self, session_id: str, db: Session) -> Optional[DiagnosisState]:
        """Load state from latest snapshot"""
        from sqlalchemy import text

        result = db.execute(
            text("SELECT snapshot_data FROM diagnosis_sessions WHERE session_id = :session_id ORDER BY created_at DESC LIMIT 1"),
            {"session_id": session_id},
        ).fetchone()

        if result:
            data = json.loads(result[0])
            state = DiagnosisState(session_id)
            state.messages = data.get("messages", [])
            state.hypothesis_tree = data.get("hypothesis_tree", {})
            state.timeline = data.get("timeline", [])
            state.confidence = data.get("confidence", 0)
            state.evidence = data.get("evidence", [])
            state.current_phase = data.get("current_phase", "init")
            state.task_status = data.get("task_status", "submitted")
            state.snapshot_data = data.get("snapshot_data", {})
            state.mode = data.get("mode", "plan_execute")
            state.mode_history = data.get("mode_history", [])
            state.final_effective_mode = data.get("final_effective_mode", state.mode)
            self._memory_states[session_id] = state
            return state
        return None

    def replay_events(self, session_id: str, from_sequence: int, db: Session) -> Optional[DiagnosisState]:
        """Replay events from a specific sequence number"""
        state = self._memory_states.get(session_id)
        if not state:
            state = self.load_from_snapshot(session_id, db)
            if not state:
                return None

        from sqlalchemy import text

        events = db.execute(
            text(
                """
                SELECT event_type, event_data, sequence
                FROM diagnosis_events
                WHERE session_id = :session_id AND sequence >= :from_sequence
                ORDER BY sequence
            """
            ),
            {"session_id": session_id, "from_sequence": from_sequence},
        ).fetchall()

        for event in events:
            event_type, event_data_str, sequence = event
            event_data = json.loads(event_data_str)
            self._apply_event(state, event_type, event_data)

        return state

    def list_sessions(
        self,
        db: Session,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        service: Optional[str] = None,
        problem_type: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        valid_sort_fields = {
            "updated_at": "s.updated_at",
            "created_at": "s.created_at",
            "confidence": "(s.snapshot_data->>'confidence')::int",
            "event_count": "COALESCE(e.event_count, 0)",
        }
        order_field = valid_sort_fields.get(sort_by, "s.updated_at")
        order_direction = "ASC" if sort_order.lower() == "asc" else "DESC"

        query = """
            SELECT s.session_id,
                   s.snapshot_version,
                   s.snapshot_data,
                   s.updated_at,
                   COALESCE(e.event_count, 0) AS event_count
            FROM diagnosis_sessions s
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS event_count
                FROM diagnosis_events
                GROUP BY session_id
            ) e ON e.session_id = s.session_id
            WHERE 1=1
        """

        params: Dict[str, Any] = {}

        if start_time:
            query += " AND s.updated_at >= :start_time"
            params["start_time"] = start_time
        if end_time:
            query += " AND s.updated_at <= :end_time"
            params["end_time"] = end_time
        if service:
            query += " AND (s.snapshot_data->'context'->>'service' = :service OR s.snapshot_data->>'service' = :service)"
            params["service"] = service
        if problem_type:
            query += " AND (s.snapshot_data->'context'->>'problem_type' = :problem_type OR s.snapshot_data->>'problem_type' = :problem_type)"
            params["problem_type"] = problem_type

        query += f" ORDER BY {order_field} {order_direction}"

        rows = db.execute(text(query), params).fetchall()

        sessions: List[Dict[str, Any]] = []
        for row in rows:
            snapshot_data = row.snapshot_data or {}
            if isinstance(snapshot_data, str):
                snapshot_data = json.loads(snapshot_data)

            messages = snapshot_data.get("messages") or []
            context = snapshot_data.get("context") or {}
            sessions.append(
                {
                    "session_id": row.session_id,
                    "snapshot_version": row.snapshot_version,
                    "current_phase": snapshot_data.get("current_phase", "init"),
                    "task_status": snapshot_data.get("task_status", "submitted"),
                    "confidence": snapshot_data.get("confidence", 0),
                    "message_count": len(messages),
                    "event_count": row.event_count,
                    "service": snapshot_data.get("service") or context.get("service"),
                    "problem_type": snapshot_data.get("problem_type") or context.get("problem_type"),
                    "updated_at": row.updated_at,
                }
            )

        return sessions

    def _build_decision_evidence_chain(self, snapshot_data: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        chain = (snapshot_data or {}).get("decision_evidence_chain")
        if isinstance(chain, dict) and chain.get("nodes"):
            return chain

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, str]] = []
        for event in events:
            payload = event.get("event_data") or {}
            event_type = event.get("event_type")
            node_type = None
            if event_type in {"agent_dispatch", "workflow_mode_finalized"}:
                node_type = "decision"
            elif event_type in {"tool_call", "evidence_added"}:
                node_type = "evidence"
            elif event_type in {"diagnosis_completed"}:
                node_type = "conclusion"
            if not node_type:
                continue
            node_id = f"event-{event.get('sequence')}"
            nodes.append({"id": node_id, "type": node_type, "payload": payload, "timestamp": event.get("timestamp")})
            if len(nodes) > 1:
                edges.append({"from": nodes[-2]["id"], "to": node_id})

        return {"nodes": nodes, "edges": edges}

    def get_session_detail(self, session_id: str, db: Session) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text

        snapshot_row = db.execute(
            text(
                """
                SELECT session_id, snapshot_data, snapshot_version
                FROM diagnosis_sessions
                WHERE session_id = :session_id
                LIMIT 1
                """
            ),
            {"session_id": session_id},
        ).fetchone()

        if not snapshot_row:
            return None

        events = self.get_session_events(session_id, db)
        if isinstance(snapshot_row.snapshot_data, str):
            snapshot_data = json.loads(snapshot_row.snapshot_data)
        else:
            snapshot_data = snapshot_row.snapshot_data

        decision_chain = self._build_decision_evidence_chain(snapshot_data, events)
        return {
            "session_id": snapshot_row.session_id,
            "snapshot_version": snapshot_row.snapshot_version,
            "snapshot_data": snapshot_data,
            "event_count": len(events),
            "first_event_at": events[0]["timestamp"] if events else None,
            "last_event_at": events[-1]["timestamp"] if events else None,
            "decision_evidence_chain": decision_chain,
            "events": events,
        }

    def get_session_events(self, session_id: str, db: Session) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        event_rows = db.execute(
            text(
                """
                SELECT sequence, event_type, event_data, timestamp
                FROM diagnosis_events
                WHERE session_id = :session_id
                ORDER BY sequence ASC
                """
            ),
            {"session_id": session_id},
        ).fetchall()

        events = []
        for row in event_rows:
            event_data = row.event_data
            if isinstance(event_data, str):
                event_data = json.loads(event_data)
            events.append(
                {
                    "sequence": row.sequence,
                    "event_type": row.event_type,
                    "event_data": event_data,
                    "timestamp": row.timestamp,
                }
            )

        return events

    def _apply_event(self, state: DiagnosisState, event_type: str, event_data: Dict[str, Any]):
        """Apply event to state"""
        if event_type == "message_added":
            state.messages.append(event_data)
        elif event_type == "confidence_updated":
            state.confidence = event_data.get("confidence", state.confidence)
        elif event_type == "evidence_added":
            state.evidence.append(event_data)
        elif event_type == "phase_changed":
            state.current_phase = event_data.get("phase", state.current_phase)
        elif event_type == "task_status_changed":
            state.task_status = event_data.get("to_status", state.task_status)

    def get_current_state(self, session_id: str, db: Session) -> Optional[DiagnosisState]:
        """Get current state with latest events"""
        state = self._memory_states.get(session_id)
        if not state:
            state = self.load_from_snapshot(session_id, db)
            if state:
                # Replay events since snapshot
                self.replay_events(session_id, 0, db)
        return state


state_manager = StateManager()
