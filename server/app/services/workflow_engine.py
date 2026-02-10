from typing import TypedDict, List, Dict, Any, Optional
import asyncio
from langgraph.graph import StateGraph, END
from app.services.agents.coordinator_agent import CoordinatorAgent
from app.services.agents.log_agent import LogAgent
from app.services.agents.code_agent import CodeAgent
from app.services.agents.knowledge_agent import KnowledgeAgent
from app.services.agents.metric_agent import MetricAgent
from app.services.mode_router import DiagnosisMode
from app.services.executors import MinimalExecutor, StandardExecutor, DeepExecutor, SwarmExecutor
from app.core.logging_config import get_logger
from app.core.event_publisher import event_publisher

logger = get_logger(__name__)


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
    mode: str
    mode_history: List[Dict[str, Any]]


class DiagnosisWorkflowEngine:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.log_agent = LogAgent()
        self.code_agent = CodeAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.metric_agent = MetricAgent()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.executors = {
            DiagnosisMode.PRD_MINIMAL.value: MinimalExecutor(),
            DiagnosisMode.PRD_STANDARD.value: StandardExecutor(),
            DiagnosisMode.PRD_DEEP.value: DeepExecutor(),
            DiagnosisMode.PRD_SWARM.value: SwarmExecutor(),
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
        selected_mode = mode if mode in self.executors else DiagnosisMode.PRD_STANDARD.value
        state.setdefault("mode_history", [])
        state["mode"] = selected_mode

        try:
            executor = self.executors[selected_mode]
            return await executor.run(self, state)
        except Exception as exc:
            logger.warning(f"Mode execution failed in {selected_mode}: {exc}")
            fallback_mode = self._fallback_mode(selected_mode)
            if fallback_mode == selected_mode:
                raise

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
            return await self.executors[fallback_mode].run(self, state)

    def switch_mode(self, session_id: str, mode: str, reason: str) -> bool:
        if session_id not in self.active_workflows or mode not in self.executors:
            return False

        workflow_state = self.active_workflows[session_id]
        current_mode = workflow_state.get("mode", DiagnosisMode.PRD_STANDARD.value)
        if current_mode == mode:
            return True

        workflow_state.setdefault("mode_history", []).append(
            {"from": current_mode, "to": mode, "reason": reason, "type": "manual_switch"}
        )
        workflow_state["mode"] = mode
        return True

    async def _run_minimal(self, state: DiagnosisState) -> DiagnosisState:
        return await self._coordinator_only(state)

    async def _run_standard(self, state: DiagnosisState) -> DiagnosisState:
        return await self._coordinator_only(state)

    async def _run_deep(self, state: DiagnosisState) -> DiagnosisState:
        workflow = self.create_complex_workflow(include_code=False)
        return await workflow.ainvoke(state)

    async def _run_swarm(self, state: DiagnosisState) -> DiagnosisState:
        workflow = self.create_complex_workflow(include_code=True)
        return await workflow.ainvoke(state)

    async def _coordinator_only(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            state["symptom"],
            {"phase": "analysis"},
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

        result = await self.coordinator.execute_with_timeout(
            f"Analyze symptom: {state['symptom']}",
            {"phase": "init"},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        state["current_phase"] = "analysis"
        event_publisher.publish_diagnosis_event(session_id, {"type": "workflow_node_completed", "node_name": "coordinator_init"})
        return state

    async def _parallel_analysis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        log_task = self.log_agent.execute_with_timeout(state["symptom"], {"phase": "analysis"}, mode=state.get("mode"))
        metric_task = self.metric_agent.execute_with_timeout(state["symptom"], {"phase": "analysis"}, mode=state.get("mode"))
        log_result, metric_result = await asyncio.gather(log_task, metric_task)

        state["messages"].extend([log_result, metric_result])
        state["evidence"].extend([
            {"type": "log", "data": log_result},
            {"type": "metric", "data": metric_result},
        ])
        return state

    async def _code_analysis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.code_agent.execute_with_timeout(
            "Analyze code and configuration",
            {"symptom": state["symptom"]},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        state["evidence"].append({"type": "code", "data": result})
        return state

    async def _coordinator_synthesis(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Synthesize analysis results",
            {"evidence": state["evidence"]},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        state["confidence"] = 70
        return state

    async def _knowledge_match(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.knowledge_agent.execute_with_timeout(
            "Find similar cases",
            {"symptom": state["symptom"]},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        state["confidence"] = 85
        return state

    async def _final_decision(self, state: DiagnosisState) -> DiagnosisState:
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Generate final diagnosis",
            {"evidence": state["evidence"], "confidence": state["confidence"]},
            mode=state.get("mode"),
        )
        state["messages"].append(result)
        state["current_phase"] = "completed"
        return state

    def _should_query_knowledge(self, state: DiagnosisState) -> str:
        if state.get("cancelled"):
            return "no"
        return "yes" if state["confidence"] < 80 else "no"

    def _fallback_mode(self, mode: str) -> str:
        if mode == DiagnosisMode.PRD_SWARM.value:
            return DiagnosisMode.PRD_DEEP.value
        if mode == DiagnosisMode.PRD_DEEP.value:
            return DiagnosisMode.PRD_STANDARD.value
        return DiagnosisMode.PRD_STANDARD.value


workflow_engine = DiagnosisWorkflowEngine()
