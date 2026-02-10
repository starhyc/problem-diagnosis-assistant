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
from app.schemas.events import ConfirmationRiskLevel
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
    trace_root_id: str
    task_status: str
    snapshot_data: Dict[str, Any]


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
        key = self._idempotency_key(session_id, action_id, step_id)
        accepted = self.redis.set(key, "1", nx=True, ex=3600)
        return bool(accepted)

    def _set_task_status(self, state: DiagnosisState, task_status: str):
        state_manager.apply_task_status(state, task_status)

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

    def _trace_context(self, state: DiagnosisState, agent_name: str, parent_id: Optional[str], task: str, phase: str) -> Dict[str, Any]:
        return {
            "session_id": state.get("session_id", "unknown"),
            "trace_agent_id": str(uuid.uuid4()),
            "trace_parent_id": parent_id,
            "task": task,
            "phase": phase,
            "agent_name": agent_name,
        }

    def _record_audit_event(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        try:
            db = next(get_db())
            state_manager.record_event(session_id, event_type, event_data, db)
        except Exception as e:
            logger.error(f"Failed to record audit event for {session_id}: {e}")

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

    def submit_confirmation_response(self, session_id: str, confirmation_id: str, response: Dict[str, Any]) -> bool:
        action_id = response.get("actionId") or response.get("action_id") or confirmation_id
        step_id = response.get("stepId") or response.get("step_id") or "confirmation_response"
        idempotency_key = self._idempotency_key(session_id, action_id, step_id)
        if not self._validate_idempotency(session_id, action_id, step_id):
            logger.warning(
                f"Duplicate confirmation response dropped: session={session_id}, "
                f"action_id={action_id}, step_id={step_id}, idempotency_key={idempotency_key}"
            )
            return False

        key = self._confirmation_key(session_id, confirmation_id)
        raw = self.redis.get(key)
        if not raw:
            logger.warning(f"Confirmation not found: session={session_id}, confirmation_id={confirmation_id}")
            return False

        payload = json.loads(raw)
        payload["status"] = "responded"
        payload["response"] = response
        payload["responded_at"] = datetime.now().isoformat()
        payload["idempotency_key"] = idempotency_key
        self.redis.setex(key, 3600, json.dumps(payload))
        return True

    async def _request_confirmation(self, state: DiagnosisState, confirmation_data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = state.get("session_id", "unknown")
        self._set_task_status(state, "waiting_user")
        state["current_phase"] = "waiting_user"
        confirmation_id = str(uuid.uuid4())
        timeout_seconds = confirmation_data.get("timeoutSeconds", 180)

        payload = {
            "id": confirmation_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "data": confirmation_data,
        }
        self.redis.setex(
            self._confirmation_key(session_id, confirmation_id),
            timeout_seconds + 3600,
            json.dumps(payload),
        )

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "confirmation_required",
            "id": confirmation_id,
            **confirmation_data,
        })
        self._record_audit_event(session_id, "confirmation_required", {
            "confirmation_id": confirmation_id,
            **confirmation_data,
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

        timeout_strategy = confirmation_data.get("timeoutStrategy", "auto_reject")
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
        selected_mode = normalize_mode(mode) or DiagnosisMode.PLAN_EXECUTE.value
        if selected_mode not in self.executors:
            selected_mode = DiagnosisMode.PLAN_EXECUTE.value
        state.setdefault("mode_history", [])
        state["mode"] = selected_mode
        state.setdefault("trace_root_id", str(uuid.uuid4()))
        state.setdefault("task_status", "submitted")

        try:
            self._set_task_status(state, "running")
            executor = self.executors[selected_mode]
            result = await executor(state)
            if result.get("cancelled"):
                self._set_task_status(result, "canceled")
                result["current_phase"] = "canceled"
            elif result.get("task_status") != "waiting_user":
                self._set_task_status(result, "completed")
                result["current_phase"] = "completed"
            return result
        except Exception as exc:
            logger.warning(f"Mode execution failed in {selected_mode}: {exc}")
            fallback_mode = self._fallback_mode(selected_mode)
            if fallback_mode == selected_mode:
                self._set_task_status(state, "failed")
                state["current_phase"] = "failed"
                raise

            self._set_task_status(state, "retrying")
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
                self._set_task_status(result, "canceled")
                result["current_phase"] = "canceled"
            else:
                self._set_task_status(result, "completed")
                result["current_phase"] = "completed"
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

        state["current_phase"] = "plan"
        planner_result = await self.coordinator.execute_with_timeout(
            "Create a diagnosis execution plan",
            {
                "symptom": state["symptom"],
                "goal": "产出最小可用执行计划",
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Create diagnosis plan", "plan"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(planner_result)

        state["current_phase"] = "execute"
        state = await self._parallel_analysis(state)
        state = await self._coordinator_synthesis(state)
        state = await self._final_decision(state)
        return state

    async def _run_react(self, state: DiagnosisState) -> DiagnosisState:
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
                    **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "ReAct reasoning", "reason"),
                },
                mode=state.get("mode"),
            )
            state["messages"].append(reasoning)

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
                state.setdefault("mode_history", []).append(
                    {
                        "from": DiagnosisMode.REACT.value,
                        "to": DiagnosisMode.PLAN_EXECUTE.value,
                        "reason": "react_stagnation",
                        "type": "runtime_degrade",
                    }
                )
                state["mode"] = DiagnosisMode.PLAN_EXECUTE.value
                return await self._run_plan_execute(state)

            if state.get("confidence", 0) >= 80:
                break

        state = await self._final_decision(state)
        return state

    async def _run_hierarchical(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        state["current_phase"] = "orchestrate"
        orchestrator_result = await self.coordinator.execute_with_timeout(
            "Delegate specialist tasks for diagnosis",
            {
                "symptom": state["symptom"],
                "specialists": ["log", "metric", "code", "knowledge"],
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Delegate specialists", "orchestrate"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(orchestrator_result)

        state["current_phase"] = "specialist_execute"
        log_task = self.log_agent.execute_with_timeout(
            "Analyze logs",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Log Analysis Agent", state.get("trace_root_id"), "Analyze logs", "specialist"),
            },
            mode=state.get("mode"),
        )
        metric_task = self.metric_agent.execute_with_timeout(
            "Analyze system metrics",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Metric Analysis Agent", state.get("trace_root_id"), "Analyze system metrics", "specialist"),
            },
            mode=state.get("mode"),
        )
        code_task = self.code_agent.execute_with_timeout(
            "Analyze code and configuration",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Code Analysis Agent", state.get("trace_root_id"), "Analyze code and configuration", "specialist"),
            },
            mode=state.get("mode"),
        )
        knowledge_task = self.knowledge_agent.execute_with_timeout(
            "Find similar cases",
            {
                "symptom": state["symptom"],
                **self._trace_context(state, "Knowledge Agent", state.get("trace_root_id"), "Find similar cases", "specialist"),
            },
            mode=state.get("mode"),
        )

        log_result, metric_result, code_result, knowledge_result = await asyncio.gather(
            log_task, metric_task, code_task, knowledge_task
        )
        specialist_outputs = [log_result, metric_result, code_result, knowledge_result]
        state["messages"].extend(specialist_outputs)
        state["evidence"].extend(
            [
                {"type": "log", "data": log_result},
                {"type": "metric", "data": metric_result},
                {"type": "code", "data": code_result},
                {"type": "knowledge", "data": knowledge_result},
            ]
        )

        state["current_phase"] = "aggregate"
        aggregate_result = await self.coordinator.execute_with_timeout(
            "Aggregate specialist outputs into final diagnosis",
            {
                "specialist_outputs": specialist_outputs,
                **self._trace_context(state, "Coordinator Agent", state.get("trace_root_id"), "Aggregate specialists", "aggregate"),
            },
            mode=state.get("mode"),
        )
        state["messages"].append(aggregate_result)
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
        log_task = self.log_agent.execute_with_timeout(
            state["symptom"],
            {"phase": "analysis", **self._trace_context(state, "Log Analysis Agent", root_id, state["symptom"], "analysis")},
            mode=state.get("mode"),
        )
        metric_task = self.metric_agent.execute_with_timeout(
            state["symptom"],
            {"phase": "analysis", **self._trace_context(state, "Metric Analysis Agent", root_id, state["symptom"], "analysis")},
            mode=state.get("mode"),
        )
        log_result, metric_result = await asyncio.gather(log_task, metric_task)

        base_evidence_len = len(state.get("evidence", []))
        state["messages"].extend([log_result, metric_result])
        state["evidence"].extend([
            {"type": "log", "data": log_result},
            {"type": "metric", "data": metric_result},
        ])
        self._persist_node_snapshot(
            state,
            "parallel_analysis",
            {"symptom": state.get("symptom")},
            {"log_result": log_result, "metric_result": metric_result},
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
        state["evidence"].append({"type": "code", "data": result})
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
