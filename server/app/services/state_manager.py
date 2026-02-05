from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "hypothesis_tree": self.hypothesis_tree,
            "timeline": self.timeline,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "current_phase": self.current_phase
        }

class StateManager:
    def __init__(self):
        self._memory_states: Dict[str, DiagnosisState] = {}
        self._event_sequence: Dict[str, int] = {}

    def get_state(self, session_id: str) -> Optional[DiagnosisState]:
        """Get current state from memory"""
        return self._memory_states.get(session_id)

    def create_state(self, session_id: str) -> DiagnosisState:
        """Create new diagnosis state"""
        state = DiagnosisState(session_id)
        self._memory_states[session_id] = state
        self._event_sequence[session_id] = 0
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

        db.execute(
            text("""
                INSERT INTO diagnosis_sessions (session_id, snapshot_data, snapshot_version)
                VALUES (:session_id, :snapshot_data, 1)
                ON CONFLICT (session_id)
                DO UPDATE SET snapshot_data = :snapshot_data,
                              snapshot_version = diagnosis_sessions.snapshot_version + 1,
                              updated_at = NOW()
            """),
            {"session_id": session_id, "snapshot_data": snapshot_data}
        )
        db.commit()
        logger.info(f"Saved snapshot for session: {session_id}")

    def record_event(self, session_id: str, event_type: str, event_data: Dict[str, Any], db: Session):
        """Record event to database"""
        sequence = self._event_sequence.get(session_id, 0)
        self._event_sequence[session_id] = sequence + 1

        from sqlalchemy import text
        db.execute(
            text("""
                INSERT INTO diagnosis_events (session_id, event_type, event_data, sequence)
                VALUES (:session_id, :event_type, :event_data, :sequence)
            """),
            {
                "session_id": session_id,
                "event_type": event_type,
                "event_data": json.dumps(event_data),
                "sequence": sequence
            }
        )
        db.commit()

    def load_from_snapshot(self, session_id: str, db: Session) -> Optional[DiagnosisState]:
        """Load state from latest snapshot"""
        from sqlalchemy import text
        result = db.execute(
            text("SELECT snapshot_data FROM diagnosis_sessions WHERE session_id = :session_id ORDER BY created_at DESC LIMIT 1"),
            {"session_id": session_id}
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
            text("""
                SELECT event_type, event_data, sequence
                FROM diagnosis_events
                WHERE session_id = :session_id AND sequence >= :from_sequence
                ORDER BY sequence
            """),
            {"session_id": session_id, "from_sequence": from_sequence}
        ).fetchall()

        for event in events:
            event_type, event_data_str, sequence = event
            event_data = json.loads(event_data_str)
            self._apply_event(state, event_type, event_data)

        return state

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
