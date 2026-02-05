from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.services.agents.coordinator_agent import CoordinatorAgent
from app.services.agents.log_agent import LogAgent
from app.services.agents.code_agent import CodeAgent
from app.services.agents.knowledge_agent import KnowledgeAgent
from app.services.agents.metric_agent import MetricAgent
from app.core.logging_config import get_logger
from app.core.event_publisher import event_publisher
from app.core.database import get_db
from app.services.state_manager import state_manager

logger = get_logger(__name__)

class DiagnosisState(TypedDict):
    symptom: str
    messages: List[Dict[str, Any]]
    hypothesis_tree: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    confidence: int
    next_action: Optional[str]
    current_phase: str
    paused: bool
    cancelled: bool

class DiagnosisWorkflowEngine:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.log_agent = LogAgent()
        self.code_agent = CodeAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.metric_agent = MetricAgent()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}

    def pause_workflow(self, session_id: str) -> bool:
        """Pause a running workflow"""
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["paused"] = True
            logger.info(f"Workflow paused: {session_id}")
            return True
        return False

    def resume_workflow(self, session_id: str) -> bool:
        """Resume a paused workflow"""
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["paused"] = False
            logger.info(f"Workflow resumed: {session_id}")
            return True
        return False

    def cancel_workflow(self, session_id: str) -> bool:
        """Cancel a running workflow"""
        if session_id in self.active_workflows:
            self.active_workflows[session_id]["cancelled"] = True
            logger.info(f"Workflow cancelled: {session_id}")
            return True
        return False

    def create_simple_workflow(self):
        """Create simple centralized coordination workflow"""
        async def simple_flow(state: DiagnosisState) -> DiagnosisState:
            if state.get("cancelled"):
                return state

            result = await self.coordinator.execute_with_timeout(
                state["symptom"],
                {"phase": "analysis"}
            )
            state["messages"].append(result)
            state["confidence"] = 50
            return state

        return simple_flow

    def create_complex_workflow(self):
        """Create complex LangGraph workflow with multiple phases"""
        workflow = StateGraph(DiagnosisState)

        workflow.add_node("coordinator_init", self._coordinator_init)
        workflow.add_node("parallel_analysis", self._parallel_analysis)
        workflow.add_node("coordinator_synthesis", self._coordinator_synthesis)
        workflow.add_node("knowledge_match", self._knowledge_match)
        workflow.add_node("final_decision", self._final_decision)

        workflow.set_entry_point("coordinator_init")
        workflow.add_edge("coordinator_init", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "coordinator_synthesis")
        workflow.add_conditional_edges(
            "coordinator_synthesis",
            self._should_query_knowledge,
            {
                "yes": "knowledge_match",
                "no": "final_decision"
            }
        )
        workflow.add_edge("knowledge_match", "final_decision")
        workflow.add_edge("final_decision", END)

        return workflow.compile()

    async def _coordinator_init(self, state: DiagnosisState) -> DiagnosisState:
        """Initial symptom analysis"""
        if state.get("cancelled"):
            return state

        session_id = state.get("session_id", "unknown")
        event_publisher.publish_diagnosis_event(session_id, {
            "type": "workflow_node_entered",
            "node_name": "coordinator_init"
        })

        result = await self.coordinator.execute_with_timeout(
            f"Analyze symptom: {state['symptom']}",
            {"phase": "init"}
        )
        state["messages"].append(result)
        state["current_phase"] = "analysis"

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "workflow_node_completed",
            "node_name": "coordinator_init"
        })

        return state

    async def _parallel_analysis(self, state: DiagnosisState) -> DiagnosisState:
        """Run log and metric analysis in parallel"""
        if state.get("cancelled"):
            return state

        import asyncio
        log_task = self.log_agent.execute_with_timeout(state["symptom"], {"phase": "analysis"})
        metric_task = self.metric_agent.execute_with_timeout(state["symptom"], {"phase": "analysis"})

        log_result, metric_result = await asyncio.gather(log_task, metric_task)
        state["messages"].extend([log_result, metric_result])
        state["evidence"].extend([
            {"type": "log", "data": log_result},
            {"type": "metric", "data": metric_result}
        ])
        return state

    async def _coordinator_synthesis(self, state: DiagnosisState) -> DiagnosisState:
        """Synthesize findings"""
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Synthesize analysis results",
            {"evidence": state["evidence"]}
        )
        state["messages"].append(result)
        state["confidence"] = 70
        return state

    async def _knowledge_match(self, state: DiagnosisState) -> DiagnosisState:
        """Match with historical cases"""
        if state.get("cancelled"):
            return state

        result = await self.knowledge_agent.execute_with_timeout(
            "Find similar cases",
            {"symptom": state["symptom"]}
        )
        state["messages"].append(result)
        state["confidence"] = 85
        return state

    async def _final_decision(self, state: DiagnosisState) -> DiagnosisState:
        """Generate final diagnosis"""
        if state.get("cancelled"):
            return state

        result = await self.coordinator.execute_with_timeout(
            "Generate final diagnosis",
            {"evidence": state["evidence"], "confidence": state["confidence"]}
        )
        state["messages"].append(result)
        state["current_phase"] = "completed"
        return state

    def _should_query_knowledge(self, state: DiagnosisState) -> str:
        """Decide if knowledge query is needed"""
        if state.get("cancelled"):
            return "no"
        return "yes" if state["confidence"] < 80 else "no"

workflow_engine = DiagnosisWorkflowEngine()
