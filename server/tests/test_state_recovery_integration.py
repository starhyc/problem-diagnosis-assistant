import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.state_manager import StateManager


def _build_test_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    db = Session()

    db.execute(
        text(
            """
            CREATE TABLE diagnosis_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                snapshot_data TEXT NOT NULL,
                snapshot_version INT NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE diagnosis_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                event_data TEXT NOT NULL,
                sequence INT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, sequence)
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE diagnosis_idempotency_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) NOT NULL,
                action_id VARCHAR(100) NOT NULL,
                step_id VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, action_id, step_id)
            )
            """
        )
    )
    db.commit()
    return db


def test_can_restore_full_state_from_snapshot_and_events_with_waiting_and_retrying_branches():
    db = _build_test_session()
    state_manager = StateManager()
    session_id = "session-recovery-1"

    state = state_manager.create_state(session_id)
    state.messages.append({"role": "user", "content": "cpu high"})
    state.current_phase = "analysis"
    state.confidence = 20
    state_manager.save_snapshot(session_id, db)

    state_manager.transition_task_status(session_id, "running", db, event_data={"stage": "start"})
    state_manager.record_event(session_id, "message_added", {"role": "assistant", "content": "investigating"}, db)
    state_manager.transition_task_status(session_id, "waiting_user", db, event_data={"stage": "need_confirmation"})
    state_manager.transition_task_status(session_id, "running", db, event_data={"stage": "resume"})
    state_manager.transition_task_status(session_id, "retrying", db, event_data={"stage": "transient_error"})

    events = db.execute(
        text("SELECT sequence FROM diagnosis_events WHERE session_id = :session_id ORDER BY sequence"),
        {"session_id": session_id},
    ).fetchall()
    assert [item[0] for item in events] == [0, 1, 2, 3, 4]

    state_manager._memory_states.clear()

    restored = state_manager.load_from_snapshot(session_id, db)
    assert restored is not None
    assert restored.task_status == "retrying"

    replayed = state_manager.replay_events(session_id, 0, db)
    assert replayed is not None
    assert replayed.task_status == "retrying"
    assert replayed.messages[-1] == {"role": "assistant", "content": "investigating"}

    status_events = db.execute(
        text(
            """
            SELECT event_data FROM diagnosis_events
            WHERE session_id = :session_id AND event_type = 'task_status_changed'
            ORDER BY sequence
            """
        ),
        {"session_id": session_id},
    ).fetchall()
    transitions = [json.loads(row[0])["to_status"] for row in status_events]
    assert transitions == ["running", "waiting_user", "running", "retrying"]
