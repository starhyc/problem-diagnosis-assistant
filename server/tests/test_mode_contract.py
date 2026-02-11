import asyncio

import pytest

from app.services.workflow_engine import DiagnosisWorkflowEngine


@pytest.mark.parametrize("requested_mode", ["direct", "react", "hierarchical"])
def test_run_keeps_requested_mode_without_silent_plan_execute_fallback(monkeypatch, requested_mode):
    engine = DiagnosisWorkflowEngine()
    monkeypatch.setattr(engine, "_set_task_status", lambda state, status: state.__setitem__("task_status", status))
    monkeypatch.setattr(engine, "_record_audit_event", lambda *args, **kwargs: None)

    async def _executor(state):
        state["mode"] = requested_mode
        return state

    engine.executors = {requested_mode: _executor, "plan_execute": _executor}

    state = {
        "session_id": "s-1",
        "symptom": "high latency",
        "messages": [],
        "evidence": [],
        "mode_history": [],
        "task_status": "submitted",
    }

    result = asyncio.run(engine.run(requested_mode, state))

    assert result["mode"] == requested_mode
    assert result["final_effective_mode"] == requested_mode
    degrade_entries = [item for item in result["mode_history"] if item.get("type") == "runtime_degrade"]
    assert degrade_entries == []


def test_run_plan_execute_fallback_requires_explicit_degrade_reason(monkeypatch):
    engine = DiagnosisWorkflowEngine()
    monkeypatch.setattr(engine, "_set_task_status", lambda state, status: state.__setitem__("task_status", status))
    monkeypatch.setattr(engine, "_record_audit_event", lambda *args, **kwargs: None)

    async def _react_executor(_state):
        raise RuntimeError("react_executor_failed")

    async def _plan_executor(state):
        state["mode"] = "plan_execute"
        return state

    engine.executors = {"react": _react_executor, "plan_execute": _plan_executor}

    state = {
        "session_id": "s-2",
        "symptom": "error spike",
        "messages": [],
        "evidence": [],
        "mode_history": [],
        "task_status": "submitted",
    }

    result = asyncio.run(engine.run("react", state))

    assert result["final_effective_mode"] == "plan_execute"
    degrade_entries = [item for item in result["mode_history"] if item.get("type") == "runtime_degrade"]
    assert len(degrade_entries) == 1
    assert degrade_entries[0]["from"] == "react"
    assert degrade_entries[0]["to"] == "plan_execute"
    assert "react_executor_failed" in degrade_entries[0]["reason"]
