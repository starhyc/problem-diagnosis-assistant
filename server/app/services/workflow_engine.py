from typing import TypedDict, List, Dict, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END
from app.services.agents.coordinator_agent import CoordinatorAgent
from app.services.agents.log_agent import LogAgent
from app.services.agents.code_agent import CodeAgent
from app.services.agents.knowledge_agent import KnowledgeAgent
from app.services.agents.metric_agent import MetricAgent
from app.services.mode_router import DiagnosisMode, normalize_mode
from app.core.logging_config import get_logger
from app.core.event_publisher import event_publisher
from app.core.database import get_db, SessionLocal
from app.services.state_manager import state_manager
from app.schemas.events import ConfirmationRiskLevel, EvidenceContract
from app.core.redis_client import redis_client
from app.models.case import Setting
from app.services.settings_audit import SettingsAuditService

logger = get_logger(__name__)

DEFAULT_AUTOMATION_POLICIES = {
    "conservative": {"R0": 1, "R1": 2, "R2": 3, "R3": 3},
    "balanced": {"R0": 0, "R1": 1, "R2": 2, "R3": 3},
    "aggressive": {"R0": 0, "R1": 0, "R2": 1, "R3": 2},
}

GATE_DECISIONS = {
    0: "auto_execute",
    1: "single_confirmation",
    2: "double_confirmation",
    3: "admin_enforced",
}


class DiagnosisState(TypedDict, total=False):
    session_id: str
    symptom: str
    messages: List[Dict[str, Any]]
    hypothesis_tree: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    confidence: int
    next_action: Optional[str]
    current_phase: str
    paused: bool
    cancelled: bool
    pending_confirmations: List[Dict[str, Any]]
    audit_logs: List[Dict[str, Any]]
    mode: str
    mode_history: List[Dict[str, Any]]
    final_effective_mode: str
    trace_root_id: str
    task_status: str
    snapshot_data: Dict[str, Any]
    evidence_goal: str
    allowed_tools: List[str]
    stop_conditions: List[str]


class DiagnosisWorkflowEngine:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.log_agent = LogAgent()
        self.code_agent = CodeAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.metric_agent = MetricAgent()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.redis = redis_client.get_client()
        self.audit_service = SettingsAuditService()
        self.executors = {
            DiagnosisMode.DIRECT.value: self._run_direct,
            DiagnosisMode.PLAN_EXECUTE.value: self._run_plan_execute,
            DiagnosisMode.REACT.value: self._run_react,
            DiagnosisMode.HIERARCHICAL.value: self._run_hierarchical,
        }

    def _confirmation_key(self, session_id: str, confirmation_id: str) -> str:
        return f"confirmation:{session_id}:{confirmation_id}"

    def _idempotency_key(self, session_id: str, action_id: str, step_id: str) -> str:
        return f"idempotency:{session_id}:{action_id}:{step_id}"

    def _validate_idempotency(self, session_id: str, action_id: str, step_id: str) -> bool:
        try:
            db = next(get_db())
            return state_manager.register_idempotency_key(session_id, action_id, step_id, db)
        except Exception as exc:
            logger.error(
                f"Failed to persist idempotency key: session={session_id}, action_id={action_id}, step_id={step_id}, error={exc}"
            )
            return False

    def _set_task_status(self, state: DiagnosisState, task_status: str, reason: Optional[str] = None):
        session_id = state.get("session_id", "unknown")
        with SessionLocal() as db:
            state_manager.transition(
                session_id=session_id,
                task_status=task_status,
                db=db,
                event_data={"stage": reason or "workflow_engine"},
                state_data=state,
            )

    def _build_objective(self, state: DiagnosisState, phase: str, default_tools: Optional[List[str]] = None) -> Dict[str, Any]:
        context = state.get("snapshot_data", {}).get("context", {}) if isinstance(state.get("snapshot_data"), dict) else {}
        evidence_goal = state.get("evidence_goal") or context.get("evidence_goal") or f"围绕症状[{state.get('symptom', '')}]收集可复现证据"
        allowed_tools = state.get("allowed_tools") or context.get("allowed_tools") or default_tools or ["elk_query", "git_search", "db_query"]
        stop_conditions = state.get("stop_conditions") or context.get("stop_conditions") or [
            "confidence>=85",
            "至少两类独立证据一致",
            "出现可执行修复建议",
        ]
        state["evidence_goal"] = evidence_goal
        state["allowed_tools"] = allowed_tools
        state["stop_conditions"] = stop_conditions
        return {
            "evidence_goal": evidence_goal,
            "allowed_tools": allowed_tools,
            "stop_conditions": stop_conditions,
            "phase": phase,
        }

    def _should_stop(self, state: DiagnosisState) -> bool:
        if state.get("confidence", 0) >= 85:
            return True
        return any(condition == "manual_stop" for condition in state.get("stop_conditions", []))

    def _select_specialists(self, objective: Dict[str, Any]) -> List[str]:
        mapping = {
            "elk_query": ["log", "metric"],
            "git_search": ["code"],
            "db_query": ["knowledge"],
        }
        selected = []
        for tool in objective.get("allowed_tools", []):
            selected.extend(mapping.get(tool, []))
        if not selected:
            return ["log", "metric"]
        return list(dict.fromkeys(selected))

    def _append_chain_link(self, state: DiagnosisState, link_type: str, payload: Dict[str, Any]):
        snapshot_data = state.setdefault("snapshot_data", {})
        chain = snapshot_data.setdefault("decision_evidence_chain", {"nodes": [], "edges": []})
        node_id = str(uuid.uuid4())
        chain["nodes"].append({"id": node_id, "type": link_type, "payload": payload, "timestamp": datetime.now().isoformat()})
        if len(chain["nodes"]) > 1:
            chain["edges"].append({"from": chain["nodes"][-2]["id"], "to": node_id})

    def _append_evidence_contract(
        self,
        state: DiagnosisState,
        evidence_type: str,
        agent_result: Dict[str, Any],
        source: str,
        reproducible_query: str,
        confidence_contribution: float,
    ):
        contract = EvidenceContract(
            source=source,
            reproducible_query=reproducible_query,
            confidence_contribution=confidence_contribution,
            summary=str(agent_result.get("result", ""))[:300],
            payload={"agent": agent_result.get("agent"), "status": agent_result.get("status"), "failure_explanation": agent_result.get("failure_explanation")},
        )
        state.setdefault("evidence", []).append(
            {
                "type": evidence_type,
                "data": agent_result,
                "contract": contract.model_dump(mode="json"),
            }
        )
        self._append_chain_link(state, "evidence", {"evidence_type": evidence_type, "source": source, "summary": contract.summary})

    def _persist_node_snapshot(
        self,
        state: DiagnosisState,
        node_name: str,
        node_input: Dict[str, Any],
        node_output: Dict[str, Any],
        evidence_indexes: List[int],
    ):
        session_id = state.get("session_id", "unknown")
        snapshot_data = state.setdefault("snapshot_data", {})
        checkpoints = snapshot_data.setdefault("node_checkpoints", [])
        checkpoints.append(
            {
                "node_name": node_name,
                "node_input": node_input,
                "node_output": node_output,
                "evidence_indexes": evidence_indexes,
                "timestamp": datetime.now().isoformat(),
            }
        )

        try:
            db = next(get_db())
            state_manager.update_state(
                session_id,
                {
                    "messages": state.get("messages", []),
                    "hypothesis_tree": state.get("hypothesis_tree", {}),
                    "evidence": state.get("evidence", []),
                    "confidence": state.get("confidence", 0),
                    "current_phase": state.get("current_phase", "init"),
                    "task_status": state.get("task_status", "running"),
                    "snapshot_data": snapshot_data,
                },
            )
            state_manager.save_snapshot(session_id, db)
        except Exception as exc:
            logger.warning(f"Failed to persist node snapshot for {session_id}/{node_name}: {exc}")

    def _trace_context(
        self,
        state: DiagnosisState,
        agent_name: str,
        parent_id: Optional[str],
        task: str,
        phase: str,
        parent_mode: Optional[str] = None,
        forced_mode: Optional[str] = None,
        fallback_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace_context = {
            "session_id": state.get("session_id", "unknown"),
            "trace_agent_id": str(uuid.uuid4()),
            "trace_parent_id": parent_id,
            "task": task,
            "phase": phase,
            "agent_name": agent_name,
            "parent_mode": parent_mode or state.get("mode"),
            "forced_mode": forced_mode or state.get("mode"),
            "fallback_mode": fallback_mode or self._fallback_mode(state.get("mode", DiagnosisMode.PLAN_EXECUTE.value)),
        }
        self._record_audit_event(
            state.get("session_id", "unknown"),
            "agent_dispatch",
            {
                "agent": agent_name,
                "task": task,
                "phase": phase,
                "parent_mode": trace_context.get("parent_mode"),
                "forced_mode": trace_context.get("forced_mode"),
                "fallback_mode": trace_context.get("fallback_mode"),
            },
        )
        return trace_context

    def _normalize_confirmation_risk(self, payload: Dict[str, Any], default: ConfirmationRiskLevel = ConfirmationRiskLevel.R0) -> str:
        raw = payload.get("riskLevel") or payload.get("risk_level")
        if isinstance(raw, str) and raw in {level.value for level in ConfirmationRiskLevel}:
            return raw
        return default.value

    def _record_audit_event(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        normalized = dict(event_data)
        if event_type.startswith("confirmation") or "confirmation" in event_type:
            risk_level = self._normalize_confirmation_risk(normalized)
            normalized["risk_level"] = risk_level
            normalized.pop("riskLevel", None)

        try:
            db = next(get_db())
            state_manager.record_event(session_id, event_type, normalized, db)
        except Exception as e:
            logger.error(f"Failed to record audit event for {session_id}: {e}")

    def _emit_tool_call_trace(self, state: DiagnosisState, result: Dict[str, Any]):
        session_id = state.get("session_id", "unknown")
        for item in result.get("toolCalls", []) or []:
            payload = {
                "type": "tool_call",
                "id": str(uuid.uuid4()),
                "agentId": result.get("traceAgentId") or result.get("agentId"),
                "parentId": result.get("parentId"),
                "agentName": result.get("agent"),
                "toolCall": item,
                "timestamp": datetime.now().isoformat(),
            }
            event_publisher.publish_diagnosis_event(session_id, payload)
            self._record_audit_event(session_id, "tool_call", payload)

    def _emit_tool_call_trace_batch(self, state: DiagnosisState, results: List[Dict[str, Any]]):
        for result in results:
            self._emit_tool_call_trace(state, result)

    def _load_automation_policy(self) -> Dict[str, Any]:
        default_policy = {
            "automation_level": "balanced",
            "risk_thresholds": DEFAULT_AUTOMATION_POLICIES["balanced"],
        }
        try:
            with SessionLocal() as db:
                row = (
                    db.query(Setting)
                    .filter(Setting.setting_type == "automation_policy", Setting.setting_id == "default")
                    .first()
                )
                if not row or not row.config:
                    return default_policy
                payload = json.loads(row.config)
                automation_level = payload.get("automation_level", "balanced")
                thresholds = payload.get("risk_thresholds") or DEFAULT_AUTOMATION_POLICIES.get(
                    automation_level,
                    DEFAULT_AUTOMATION_POLICIES["balanced"],
                )
                return {
                    "automation_level": automation_level,
                    "risk_thresholds": thresholds,
                }
        except Exception as exc:
            logger.warning(f"Failed to load automation policy, fallback to default: {exc}")
            return default_policy

    def _resolve_confirmation_gate(self, risk_level: ConfirmationRiskLevel) -> Dict[str, Any]:
        policy = self._load_automation_policy()
        automation_level = policy.get("automation_level", "balanced")
        thresholds = policy.get("risk_thresholds") or DEFAULT_AUTOMATION_POLICIES.get(
            automation_level,
            DEFAULT_AUTOMATION_POLICIES["balanced"],
        )
        gate_level = int(thresholds.get(risk_level.value, 3))
        gate_level = min(max(gate_level, 0), 3)

        decision = GATE_DECISIONS[gate_level]
        return {
            "automation_level": automation_level,
            "risk_level": risk_level.value,
            "gate_level": gate_level,
            "decision": decision,
            "thresholds": thresholds,
        }

    def _record_high_risk_audit(self, session_id: str, gate: Dict[str, Any], confirmation_data: Dict[str, Any]):
        risk_level = gate.get("risk_level")
        if risk_level not in {ConfirmationRiskLevel.R2.value, ConfirmationRiskLevel.R3.value}:
            return

        self.audit_service.record(
            module="workflow-confirmation",
            action="high-risk-gate-evaluated",
            actor="system",
            target_id=confirmation_data.get("actionId", "unknown"),
            detail={
                "decision": gate.get("decision"),
                "automation_level": gate.get("automation_level"),
                "impact_scope": confirmation_data.get("impactScope"),
                "rollback_plan": confirmation_data.get("rollbackPlan"),
            },
            session_id=session_id,
            risk_level=risk_level,
        )

    def submit_confirmation_response(self, session_id: str, confirmation_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        action_id = response.get("actionId") or response.get("action_id") or confirmation_id
        step_id = response.get("stepId") or response.get("step_id") or "confirmation_response"
        idempotency_key = self._idempotency_key(session_id, action_id, step_id)
        if not self._validate_idempotency(session_id, action_id, step_id):
            logger.warning(
                f"Duplicate confirmation response dropped: session={session_id}, "
                f"action_id={action_id}, step_id={step_id}, idempotency_key={idempotency_key}"
            )
            return {
                "code": "command_rejected",
                "reason": "duplicate_confirmation_response",
            }

        key = self._confirmation_key(session_id, confirmation_id)
        raw = self.redis.get(key)
        if not raw:
            logger.warning(f"Confirmation not found: session={session_id}, confirmation_id={confirmation_id}")
            return {
                "code": "no_pending_confirmation",
            }

        payload = json.loads(raw)
        payload["status"] = "responded"
        payload["response"] = response
        payload["responded_at"] = datetime.now().isoformat()
        payload["idempotency_key"] = idempotency_key
        self.redis.setex(key, 3600, json.dumps(payload))
        confirmation_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        return {
            "code": "command_accepted",
            "risk_level": self._normalize_confirmation_risk(confirmation_data),
        }

    async def _request_confirmation(self, state: DiagnosisState, confirmation_data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = state.get("session_id", "unknown")
        self._set_task_status(state, "waiting_user")
        state["current_phase"] = "waiting_user"
        confirmation_id = str(uuid.uuid4())
        normalized_confirmation = dict(confirmation_data)
        normalized_confirmation["riskLevel"] = self._normalize_confirmation_risk(normalized_confirmation)
        timeout_seconds = normalized_confirmation.get("timeoutSeconds", 180)

        payload = {
            "id": confirmation_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "data": normalized_confirmation,
        }
        self.redis.setex(
            self._confirmation_key(session_id, confirmation_id),
            timeout_seconds + 3600,
            json.dumps(payload),
        )

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "confirmation_required",
            "id": confirmation_id,
            **normalized_confirmation,
        })
        self._record_audit_event(session_id, "confirmation_required", {
            "confirmation_id": confirmation_id,
            **normalized_confirmation,
        })

        deadline = datetime.now().timestamp() + timeout_seconds
        while datetime.now().timestamp() < deadline:
            raw = self.redis.get(self._confirmation_key(session_id, confirmation_id))
            if raw:
                current = json.loads(raw)
                if current.get("status") == "responded":
                    response = current.get("response", {})
                    self._record_audit_event(session_id, "confirmation_received", {
                        "confirmation_id": confirmation_id,
                        "response": response,
                    })
                    state["pending_confirmations"] = [
                        c for c in state.get("pending_confirmations", []) if c.get("id") != confirmation_id
                    ]
                    self._set_task_status(state, "running")
                    return {
                        "confirmation_id": confirmation_id,
                        "status": "responded",
                        "response": response,
                    }
            await asyncio.sleep(0.5)

        timeout_strategy = normalized_confirmation.get("timeoutStrategy", "auto_reject")
        self._record_audit_event(session_id, "confirmation_timeout", {
            "confirmation_id": confirmation_id,
            "timeout_strategy": timeout_strategy,
        })
        return {
            "confirmation_id": confirmation_id,
            "status": "timeout",
            "response": {"action": "reject", "reason": f"timeout:{timeout_strategy}"},
        }

    def pause_workflow(self, session_id: str) -> bool:
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["paused"] = True
            logger.info(f"Workflow paused: {session_id}")
            return True
        return False

    def resume_workflow(self, session_id: str) -> bool:
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["paused"] = False
            logger.info(f"Workflow resumed: {session_id}")
            return True
        return False

    def cancel_workflow(self, session_id: str) -> bool:
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["cancelled"] = True
            logger.info(f"Workflow cancelled: {session_id}")
            return True
        return False

    async def run(self, mode: str, state: DiagnosisState) -> DiagnosisState:
        normalized_mode = normalize_mode(mode)
        requested_mode = normalized_mode or DiagnosisMode.PLAN_EXECUTE.value

        if normalized_mode is None:
            selected_mode = DiagnosisMode.PLAN_EXECUTE.value
            selection_reason = "mode_missing_defaulted"
        elif normalized_mode not in self.executors:
            selected_mode = DiagnosisMode.PLAN_EXECUTE.value
            selection_reason = f"unsupported_mode:{normalized_mode}"
        else:
            selected_mode = normalized_mode
            selection_reason = "workflow_entry"

        state.setdefault("mode_history", [])
        state["mode"] = selected_mode
        state["mode_history"].append(
            {
                "stage": "workflow_selected",
                "requested_mode": requested_mode,
                "mode": selected_mode,
                "reason": selection_reason,
            }
        )
        self._record_audit_event(
            state.get("session_id", "unknown"),
            "workflow_mode_selected",
            {
                "requested_mode": requested_mode,
                "effective_mode": selected_mode,
                "reason": selection_reason,
            },
        )
        state.setdefault("trace_root_id", str(uuid.uuid4()))
        try:
            self._set_task_status(state, "running", reason="workflow_started")
            executor = self.executors[selected_mode]
            result = await executor(state)
            if result.get("cancelled"):
                self._set_task_status(result, "canceled", reason="workflow_cancelled")
                result["current_phase"] = "canceled"
            elif result.get("task_status") != "waiting_user":
                self._set_task_status(result, "completed", reason="workflow_completed")
                result["current_phase"] = "completed"
        except Exception as exc:
            logger.warning(f"Mode execution failed in {selected_mode}: {exc}")
            fallback_mode = self._fallback_mode(selected_mode)
            if fallback_mode == selected_mode:
                self._set_task_status(state, "failed", reason="workflow_failed")
                state["current_phase"] = "failed"
                raise

            self._set_task_status(state, "retrying", reason="workflow_retrying")
            state["current_phase"] = "retrying"
            state["mode_history"].append(
                {
                    "from": selected_mode,
                    "to": fallback_mode,
                    "reason": str(exc),
                    "type": "runtime_degrade",
                }
            )
            session_id = state.get("session_id", "unknown")
            event_publisher.publish_diagnosis_event(
                session_id,
                {
                    "type": "workflow_mode_degraded",
                    "from_mode": selected_mode,
                    "to_mode": fallback_mode,
                    "reason": str(exc),
                },
            )
            state["mode"] = fallback_mode
            result = await self.executors[fallback_mode](state)
            if result.get("cancelled"):
                self._set_task_status(result, "canceled", reason="workflow_cancelled")
                result["current_phase"] = "canceled"
            else:
                self._set_task_status(result, "completed", reason="workflow_completed")
                result["current_phase"] = "completed"

        final_effective_mode = result.get("mode", state.get("mode", selected_mode))
        result["final_effective_mode"] = final_effective_mode
        result.setdefault("mode_history", state.get("mode_history", []))
        result["mode_history"].append(
            {
                "stage": "workflow_finalized",
                "requested_mode": requested_mode,
                "effective_mode": final_effective_mode,
            }
        )
        self._record_audit_event(
            state.get("session_id", "unknown"),
            "workflow_mode_finalized",
            {
                "requested_mode": requested_mode,
                "effective_mode": final_effective_mode,
                "mode_history": result.get("mode_history", []),
            },
        )
        return result


    def switch_mode(self, session_id: str, mode: str, reason: str) -> bool:
        if session_id not in self.active_workflows or mode not in self.executors:
            return False

        workflow_state = self.active_workflows[session_id]
        current_mode = workflow_state.get("mode", DiagnosisMode.PLAN_EXECUTE.value)
        if current_mode == mode:
            return True

        workflow_state.setdefault("mode_history", []).append(
            {"from": current_mode, "to": mode, "reason": reason, "type": "manual_switch"}
        )
        workflow_state["mode"] = mode
        return True

    async def _run_direct(self, state: DiagnosisState) -> DiagnosisState:
        state["current_phase"] = "direct"
        state = await self._coordinator_only(state)
        state["current_phase"] = "completed"
        return state

    async def _run_plan_execute(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        objective = self._build_objective(state, "plan_execute", ["elk_query", "git_search", "db_query"])
        state["current_phase"] = "plan"
        planner_result = await self.coordinator.execute_with_timeout(
            "Create a diagnosis execution plan",
            {
                "symptom": state["symptom"],
                "goal": objective["evidence_goal"],
                "available_agents": self._select_specialists(objective),
                "stop_condition": " ; ".join(objective["stop_conditions"]),
                **objective,
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Create diagnosis plan", "plan"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(planner_result)
        self._append_chain_link(state, "decision", planner_result.get("coordination_decision", {}))
        self._emit_tool_call_trace(state, planner_result)

        state["current_phase"] = "execute"
        state = await self._parallel_analysis(state)
        state = await self._coordinator_synthesis(state)
        if not self._should_stop(state):
            state = await self._knowledge_match(state)
        state = await self._final_decision(state)
        return state

    async def _run_react(self, state: DiagnosisState) -> DiagnosisState:
        objective = self._build_objective(state, "react", ["elk_query", "git_search"])
        max_iterations = 4
        stagnation_limit = 2
        no_increment_rounds = 0
        previous_score = -1

        for idx in range(max_iterations):
            if state.get("cancelled"):
                return state

            state["current_phase"] = f"react_{idx + 1}_reason"
            reasoning = await self.coordinator.execute_with_timeout(
                f"ReAct reasoning iteration {idx + 1}",
                {
                    "symptom": state["symptom"],
                    "current_confidence": state.get("confidence", 0),
                    "iteration": idx + 1,
                    "goal": objective["evidence_goal"],
                    "available_agents": self._select_specialists(objective),
                    "stop_condition": " ; ".join(objective["stop_conditions"]),
                    **objective,
                    **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "ReAct reasoning", "reason"),
                },
                mode=state.get("mode"),
            )
            state["messages"].append(reasoning)
            self._append_chain_link(state, "decision", reasoning.get("coordination_decision", {}))
            self._emit_tool_call_trace(state, reasoning)

            state["current_phase"] = f"react_{idx + 1}_act"
            state = await self._parallel_analysis(state)
            state = await self._coordinator_synthesis(state)

            progress_score = len(state.get("evidence", [])) + state.get("confidence", 0)
            if progress_score <= previous_score:
                no_increment_rounds += 1
            else:
                no_increment_rounds = 0
            previous_score = progress_score

            if no_increment_rounds >= stagnation_limit:
                session_id = state.get("session_id", "unknown")
                state.setdefault("mode_history", []).append(
                    {
                        "from": DiagnosisMode.REACT.value,
                        "to": DiagnosisMode.PLAN_EXECUTE.value,
                        "reason": "react_stagnation",
                        "type": "runtime_degrade",
                        "no_increment_rounds": no_increment_rounds,
                    }
                )
                event_publisher.publish_diagnosis_event(session_id, {
                    "type": "confirmation_required",
                    "actionId": "react_degradation",
                    "message": "ReAct 连续无增量，建议降级到 Plan-Execute，是否确认？",
                    "riskLevel": ConfirmationRiskLevel.R1.value,
                    "impactScope": "执行模式切换",
                    "options": [
                        {"label": "确认降级", "value": "approve"},
                        {"label": "保持 ReAct", "value": "reject"},
                    ],
                    "defaultOption": "approve",
                    "from_mode": DiagnosisMode.REACT.value,
                    "to_mode": DiagnosisMode.PLAN_EXECUTE.value,
                    "reason": "react_stagnation",
                })
                self._record_audit_event(session_id, "mode_degrade_confirmation", {
                    "from_mode": DiagnosisMode.REACT.value,
                    "to_mode": DiagnosisMode.PLAN_EXECUTE.value,
                    "reason": "react_stagnation",
                    "no_increment_rounds": no_increment_rounds,
                    "risk_level": ConfirmationRiskLevel.R1.value,
                })
                state["mode"] = DiagnosisMode.PLAN_EXECUTE.value
                return await self._run_plan_execute(state)

            if self._should_stop(state):
                break

        state = await self._final_decision(state)
        return state

    async def _run_hierarchical(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        objective = self._build_objective(state, "hierarchical", ["elk_query", "git_search", "db_query"])
        selected_specialists = self._select_specialists(objective)

        state["current_phase"] = "orchestrate"
        orchestrator_result = await self.coordinator.execute_with_timeout(
            "Delegate specialist tasks for diagnosis",
            {
                "symptom": state["symptom"],
                "specialists": self._select_specialists(objective),
                "goal": objective["evidence_goal"],
                "stop_condition": " ; ".join(objective["stop_conditions"]),
                **objective,
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Delegate specialists", "orchestrate"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(orchestrator_result)
        self._append_chain_link(state, "decision", orchestrator_result.get("coordination_decision", {}))
        self._emit_tool_call_trace(state, orchestrator_result)

        state["current_phase"] = "specialist_execute"
        specialist_tasks = []
        if "log" in selected_specialists:
            specialist_tasks.append(self.log_agent.execute_with_timeout(
                "Analyze logs",
                {
                    "symptom": state["symptom"],
                    **self._trace_context(state, "Log Analysis Agent", state.get("trace_root_id"), "Analyze logs", "specialist"),
                },
                mode=state.get("mode"),
            ))
        if "metric" in selected_specialists:
            specialist_tasks.append(self.metric_agent.execute_with_timeout(
                "Analyze system metrics",
                {
                    "symptom": state["symptom"],
                    **self._trace_context(state, "Metric Analysis Agent", state.get("trace_root_id"), "Analyze system metrics", "specialist"),
                },
                mode=state.get("mode"),
            ))
        if "code" in selected_specialists:
            specialist_tasks.append(self.code_agent.execute_with_timeout(
                "Analyze code and configuration",
                {
                    "symptom": state["symptom"],
                    **self._trace_context(state, "Code Analysis Agent", state.get("trace_root_id"), "Analyze code and configuration", "specialist"),
                },
                mode=state.get("mode"),
            ))
        if "knowledge" in selected_specialists:
            specialist_tasks.append(self.knowledge_agent.execute_with_timeout(
                "Find similar cases",
                {
                    "symptom": state["symptom"],
                    **self._trace_context(state, "Knowledge Agent", state.get("trace_root_id"), "Find similar cases", "specialist"),
                },
                mode=state.get("mode"),
            ))

        specialist_outputs = await asyncio.gather(*specialist_tasks) if specialist_tasks else []
        state["messages"].extend(specialist_outputs)
        self._emit_tool_call_trace_batch(state, specialist_outputs)
        for output in specialist_outputs:
            agent_name = output.get("agent", "")
            evidence_type = "log"
            reproducible_query = state.get("symptom", "")
            source = "specialist"
            if "Metric" in agent_name:
                evidence_type = "metric"
                source = "metric_agent"
            elif "Code" in agent_name:
                evidence_type = "code"
                source = "code_agent"
            elif "Knowledge" in agent_name:
                evidence_type = "knowledge"
                source = "knowledge_agent"
            elif "Log" in agent_name:
                source = "log_agent"
            tool_calls = output.get("toolCalls") or []
            if tool_calls:
                reproducible_query = str(tool_calls[0].get("params", state.get("symptom", "")))
            self._append_evidence_contract(state, evidence_type, output, source, reproducible_query, 0.2)

        state["current_phase"] = "aggregate"
        aggregate_result = await self.coordinator.execute_with_timeout(
            "Aggregate specialist outputs into final diagnosis",
            {
                "specialist_outputs": specialist_outputs,
                "goal": objective["evidence_goal"],
                "stop_condition": " ; ".join(objective["stop_conditions"]),
                **objective,
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Aggregate specialists", "aggregate"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(aggregate_result)
        self._append_chain_link(state, "decision", aggregate_result.get("coordination_decision", {}))
        self._emit_tool_call_trace(state, aggregate_result)
        state["confidence"] = max(state.get("confidence", 0), 85)
        state = await self._final_decision(state)
        return state

    async def _coordinator_only(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        trace_ctx = self._trace_context(
            state,
            "Coordinator Agent",
            state.get("trace_root_id"),
            state["symptom"],
            "analysis",
        )
        result = await self.coordinator.execute_with_timeout(
            state["symptom"],
            {"phase": "analysis", **trace_ctx},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        self._append_chain_link(state, "conclusion", {"result": str(result.get("result", ""))[:400], "confidence": state.get("confidence", 0)})
        self._emit_tool_call_trace(state, result)
        state["confidence"] = 50
        return state

    def create_complex_workflow(self, include_code: bool = False):
        workflow = StateGraph(DiagnosisState)
        workflow.add_node("coordinator_init", self._coordinator_init)
        workflow.add_node("parallel_analysis", self._parallel_analysis)
        workflow.add_node("coordinator_synthesis", self._coordinator_synthesis)
        workflow.add_node("knowledge_match", self._knowledge_match)
        workflow.add_node("final_decision", self._final_decision)
        if include_code:
            workflow.add_node("code_analysis", self._code_analysis)

        workflow.set_entry_point("coordinator_init")
        workflow.add_edge("coordinator_init", "parallel_analysis")
        if include_code:
            workflow.add_edge("parallel_analysis", "code_analysis")
            workflow.add_edge("code_analysis", "coordinator_synthesis")
        else:
            workflow.add_edge("parallel_analysis", "coordinator_synthesis")
        workflow.add_conditional_edges(
            "coordinator_synthesis",
            self._should_query_knowledge,
            {"yes": "knowledge_match", "no": "final_decision"},
        )
        workflow.add_edge("knowledge_match", "final_decision")
        workflow.add_edge("final_decision", END)
        return workflow.compile()

    async def _coordinator_init(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        session_id = state.get("session_id", "unknown")
        event_publisher.publish_diagnosis_event(session_id, {"type": "workflow_node_entered", "node_name": "coordinator_init"})

        trace_ctx = self._trace_context(
            state,
            "Coordinator Agent",
            state.get("trace_root_id"),
            f"Analyze symptom: {state['symptom']}",
            "init",
        )
        result = await self.coordinator.execute_with_timeout(
            f"Analyze symptom: {state['symptom']}",
            {"phase": "init", **trace_ctx},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        self._emit_tool_call_trace(state, result)
        state["current_phase"] = "analysis"
        self._persist_node_snapshot(
            state,
            "coordinator_init",
            {"symptom": state.get("symptom")},
            {"result": result},
            [],
        )
        event_publisher.publish_diagnosis_event(session_id, {"type": "workflow_node_completed", "node_name": "coordinator_init"})
        return state

    async def _parallel_analysis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        root_id = state.get("trace_root_id")
        objective = self._build_objective(state, "analysis", ["elk_query"])
        tasks = []
        evidence_pairs = []
        if "elk_query" in objective.get("allowed_tools", []):
            tasks.append(self.log_agent.execute_with_timeout(
                state["symptom"],
                {"phase": "analysis", **self._trace_context(state, "Log Analysis Agent", root_id, state["symptom"], "analysis")},
                mode=state.get("mode"),
            ))
            evidence_pairs.append(("log", "log_agent", 0.25))
            tasks.append(self.metric_agent.execute_with_timeout(
                state["symptom"],
                {"phase": "analysis", **self._trace_context(state, "Metric Analysis Agent", root_id, state["symptom"], "analysis")},
                mode=state.get("mode"),
            ))
            evidence_pairs.append(("metric", "metric_agent", 0.25))

        results = await asyncio.gather(*tasks) if tasks else []
        base_evidence_len = len(state.get("evidence", []))
        state["messages"].extend(results)
        self._emit_tool_call_trace_batch(state, results)
        for (evidence_type, source, contribution), agent_result in zip(evidence_pairs, results):
            query = str(((agent_result.get("toolCalls") or [{}])[0]).get("params", state.get("symptom", "")))
            self._append_evidence_contract(state, evidence_type, agent_result, source, query, contribution)
        self._persist_node_snapshot(
            state,
            "parallel_analysis",
            {"symptom": state.get("symptom")},
            {"results": results},
            list(range(base_evidence_len, len(state.get("evidence", [])))),
        )
        return state

    async def _code_analysis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        base_evidence_len = len(state.get("evidence", []))
        result = await self.code_agent.execute_with_timeout(
            "Analyze code and configuration",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Code Analysis Agent", state.get("trace_root_id"), "Analyze code and configuration", "analysis"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        self._emit_tool_call_trace(state, result)
        code_query = str(((result.get("toolCalls") or [{}])[0]).get("params", state.get("symptom", "")))
        self._append_evidence_contract(state, "code", result, "code_agent", code_query, 0.2)
        self._persist_node_snapshot(
            state,
            "code_analysis",
            {"symptom": state.get("symptom")},
            {"result": result},
            list(range(base_evidence_len, len(state.get("evidence", [])))),
        )
        return state

    async def _coordinator_synthesis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Synthesize analysis results",
            {
                "evidence": state["evidence"],
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Synthesize analysis results", "synthesis"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        self._emit_tool_call_trace(state, result)
        state["confidence"] = 70
        self._persist_node_snapshot(
            state,
            "coordinator_synthesis",
            {"evidence_count": len(state.get("evidence", []))},
            {"result": result, "confidence": state.get("confidence", 0)},
            [],
        )
        return state

    async def _knowledge_match(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        session_id = state.get("session_id", "unknown")
        if state.get("confidence", 0) >= 70:
            confirmation_data = {
                "actionId": "knowledge_match",
                "message": "即将执行高风险知识库关联操作，请确认是否继续。",
                "description": "该操作将使用当前证据匹配历史案例，可能影响最终诊断路径。",
                "riskLevel": ConfirmationRiskLevel.R2.value,
                "impactScope": "历史案例检索与推荐策略",
                "rollbackPlan": "回退到仅基于实时证据的决策流程",
                "approverRoles": ["engineer", "admin"],
                "timeoutSeconds": 120,
                "timeoutStrategy": "auto_reject",
                "requiresSecondConfirmation": True,
                "options": [
                    {"label": "继续执行", "value": "approve"},
                    {"label": "二次确认", "value": "second_confirm"},
                    {"label": "拒绝执行", "value": "reject"},
                ],
                "defaultOption": "approve",
            }

            gate = self._resolve_confirmation_gate(ConfirmationRiskLevel.R2)
            self._record_high_risk_audit(session_id, gate, confirmation_data)
            event_publisher.publish_diagnosis_event(session_id, {
                "type": "confirmation_gate_decision",
                "action_id": "knowledge_match",
                **gate,
            })

            if gate["decision"] == "admin_enforced":
                admin_payload = {
                    **confirmation_data,
                    "message": "管理员强制确认：该 R2/R3 操作仅允许管理员审批后执行。",
                    "riskLevel": ConfirmationRiskLevel.R3.value,
                    "approverRoles": ["admin"],
                    "requiresSecondConfirmation": False,
                }
                state.setdefault("pending_confirmations", []).append(admin_payload)
                admin_result = await self._request_confirmation(state, admin_payload)
                if admin_result.get("status") == "timeout" or admin_result.get("response", {}).get("action") != "approve":
                    state["current_phase"] = "confirmation_rejected"
                    return state
            elif gate["decision"] == "double_confirmation":
                state.setdefault("pending_confirmations", []).append(confirmation_data)
                first_result = await self._request_confirmation(state, confirmation_data)
                first_action = first_result.get("response", {}).get("action", "reject")

                if first_result.get("status") == "timeout" or first_action == "reject":
                    state["current_phase"] = "confirmation_rejected"
                    event_publisher.publish_diagnosis_event(session_id, {
                        "type": "confirmation_rejected",
                        "action_id": "knowledge_match",
                        "reason": first_result.get("response", {}).get("reason", "rejected"),
                        "riskLevel": confirmation_data.get("riskLevel", ConfirmationRiskLevel.R2.value),
                    })
                    return state

                second_result = await self._request_confirmation(state, {
                    **confirmation_data,
                    "message": "R3 二次确认：是否继续执行高风险知识库关联操作？",
                    "riskLevel": ConfirmationRiskLevel.R3.value,
                    "timeoutSeconds": 60,
                })
                if second_result.get("status") == "timeout" or second_result.get("response", {}).get("action") != "approve":
                    state["current_phase"] = "confirmation_rejected"
                    return state
            elif gate["decision"] == "single_confirmation":
                state.setdefault("pending_confirmations", []).append(confirmation_data)
                first_result = await self._request_confirmation(state, confirmation_data)
                if first_result.get("status") == "timeout" or first_result.get("response", {}).get("action") != "approve":
                    state["current_phase"] = "confirmation_rejected"
                    return state

        result = await self.knowledge_agent.execute_with_timeout(
            "Find similar cases",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Knowledge Agent", state.get("trace_root_id"), "Find similar cases", "knowledge"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        knowledge_query = str(((result.get("toolCalls") or [{}])[0]).get("params", state.get("symptom", "")))
        self._append_evidence_contract(state, "knowledge", result, "knowledge_agent", knowledge_query, 0.25)
        self._emit_tool_call_trace(state, result)
        state["confidence"] = 85
        self._persist_node_snapshot(
            state,
            "knowledge_match",
            {"symptom": state.get("symptom")},
            {"result": result, "confidence": state.get("confidence", 0)},
            [],
        )
        return state

    async def _final_decision(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Generate final diagnosis",
            {
                "evidence": state["evidence"],
                "confidence": state["confidence"],
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Generate final diagnosis", "finalize"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        self._append_chain_link(state, "conclusion", {"result": str(result.get("result", ""))[:400], "confidence": state.get("confidence", 0)})
        self._emit_tool_call_trace(state, result)
        state["current_phase"] = "completed"
        self._persist_node_snapshot(
            state,
            "final_decision",
            {"evidence_count": len(state.get("evidence", [])), "confidence": state.get("confidence", 0)},
            {"result": result},
            [],
        )
        return state

    def _should_query_knowledge(self, state: DiagnosisState) -> str:
        if state.get("cancelled"):
            return "no"
        return "yes" if state["confidence"] < 80 else "no"

    def _fallback_mode(self, mode: str) -> str:
        if mode == DiagnosisMode.HIERARCHICAL.value:
            return DiagnosisMode.REACT.value
        if mode == DiagnosisMode.REACT.value:
            return DiagnosisMode.PLAN_EXECUTE.value
        if mode == DiagnosisMode.PLAN_EXECUTE.value:
            return DiagnosisMode.DIRECT.value
        return DiagnosisMode.DIRECT.value


workflow_engine = DiagnosisWorkflowEngine()
