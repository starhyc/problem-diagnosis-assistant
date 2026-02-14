from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
import json
import re
import asyncio
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger
from app.schemas.events import AgentFailureExplanation

logger = get_logger(__name__)

LOG_AGENT_PROMPT = """You are a Log Analysis Agent specialized in analyzing system logs.

Your role:
- Parse and analyze log files from various sources (ELK, application logs, system logs)
- Identify error patterns, anomalies, and suspicious activities
- Extract relevant timestamps, error codes, and stack traces
- Correlate log entries to identify root causes

You MUST ground every conclusion in tool evidence.
- If evidence is insufficient, explicitly output "INSUFFICIENT_EVIDENCE" and list missing evidence.
- Do NOT fabricate facts beyond the tool output.

Current task: {task}
Context: {context}
Tool evidence (mandatory ELK query): {tool_evidence}

Provide your log analysis findings."""

REACT_REASON_PROMPT = """You are a Log Analysis Agent specialized in analyzing system logs using the ReAct framework.

Your role:
- Parse and analyze log files from various sources (ELK, application logs, system logs)
- Identify error patterns, anomalies, and suspicious activities
- Extract relevant timestamps, error codes, and stack traces
- Correlate log entries to identify root causes

Current task: {task}
Context: {context}
Previous observations: {observations}

Available tools:
- elk_query: Query ELK logs with a search string

Think step by step about the task and decide what to do next.

Your response must be in one of these formats:

1. If you need more information:
THOUGHT: [your reasoning about what information you need]
ACTION: elk_query
ACTION_INPUT: {{"query": "[your search query]", "index": "logs-*", "size": 50}}

2. If you have enough information to answer:
THOUGHT: [your reasoning about the final conclusion]
ANSWER: [your final analysis based on the evidence]

3. If evidence is insufficient:
THOUGHT: [explain why evidence is insufficient]
ANSWER: INSUFFICIENT_EVIDENCE - [list what evidence is missing]

Remember:
- Always ground your conclusions in tool evidence
- Start with broad queries, then refine based on results
- Use specific error codes, timestamps, or patterns when available
- If multiple queries are needed, explain why each is necessary"""

REACT_ACT_PROMPT = """You are a Log Analysis Agent specialized in analyzing system logs using the ReAct framework.

Current task: {task}
Context: {context}
Previous reasoning: {reasoning}
Tool execution result: {tool_result}
Observations so far: {observations}

Based on the tool result, decide what to do next.

Your response must be in one of these formats:

1. If you need more information:
THOUGHT: [your reasoning about what additional information you need]
ACTION: elk_query
ACTION_INPUT: {{"query": "[your refined search query]", "index": "logs-*", "size": 50}}

2. If you have enough information to answer:
THOUGHT: [your reasoning about the final conclusion]
ANSWER: [your final analysis based on all evidence]

3. If evidence is insufficient:
THOUGHT: [explain why evidence is insufficient]
ANSWER: INSUFFICIENT_EVIDENCE - [list what evidence is missing]"""


class LogAgent(BaseAgent):
    def __init__(self):
        super().__init__("log", "Log Analysis Agent", supported_modes=["plan_execute", "react", "hierarchical"], default_mode="plan_execute")

    @property
    def required_tool_name(self) -> str:
        return "elk_query"

    def build_required_tool_input(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        symptom = context.get("symptom") or task
        return {"query": symptom, "index": "logs-*", "size": 50}

    def _parse_react_response(self, response_text: str) -> Dict[str, Any]:
        thought_match = re.search(r'THOUGHT:\s*(.*?)(?=ACTION:|ANSWER:|$)', response_text, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r'ACTION:\s*(\w+)', response_text, re.IGNORECASE)
        action_input_match = re.search(r'ACTION_INPUT:\s*(\{.*?\})', response_text, re.DOTALL)
        answer_match = re.search(r'ANSWER:\s*(.*)', response_text, re.DOTALL | re.IGNORECASE)

        result = {
            "thought": thought_match.group(1).strip() if thought_match else "",
            "action": action_match.group(1).strip().lower() if action_match else None,
            "action_input": {},
            "answer": answer_match.group(1).strip() if answer_match else None,
        }

        if action_input_match:
            try:
                result["action_input"] = json.loads(action_input_match.group(1))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse ACTION_INPUT: {action_input_match.group(1)}")

        return result

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        tool = next((t for t in self.tools if getattr(t, "name", "") == tool_name), None)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}", "result": ""}

        try:
            raw_result = await asyncio.to_thread(tool.invoke, tool_input)
            return {"success": True, "error": None, "result": raw_result}
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"success": False, "error": str(e), "result": ""}

    async def _execute_react_loop(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        max_rounds = int(context.get("react_max_rounds", 3))
        stagnation_limit = int(context.get("react_stagnation_limit", 2))
        observations = []
        traces = []
        last_signal = ""
        rounds_without_increment = 0

        for idx in range(max_rounds):
            reason_prompt = ChatPromptTemplate.from_template(REACT_REASON_PROMPT)
            reason_messages = reason_prompt.format_messages(
                task=task,
                context=str(context),
                observations="\n".join(observations) if observations else "None"
            )
            reason_response = await self.llm.ainvoke(reason_messages)
            reason_content = str(reason_response.content)
            reason_parsed = self._parse_react_response(reason_content)

            traces.append({
                "round": idx + 1,
                "phase": "reason",
                "content": reason_content,
                "parsed": reason_parsed,
            })

            tool_result = {}
            if reason_parsed.get("action") == "elk_query" and reason_parsed.get("action_input"):
                tool_result = await self._execute_tool("elk_query", reason_parsed["action_input"])
                if tool_result["success"]:
                    new_observation = f"Query: {reason_parsed['action_input'].get('query')}\nResult: {tool_result['result']}"
                else:
                    new_observation = f"Query failed: {tool_result['error']}"
                observations.append(new_observation)

            act_prompt = ChatPromptTemplate.from_template(REACT_ACT_PROMPT)
            act_messages = act_prompt.format_messages(
                task=task,
                context=str(context),
                reasoning=reason_content,
                tool_result=str(tool_result),
                observations="\n".join(observations) if observations else "None"
            )
            act_response = await self.llm.ainvoke(act_messages)
            act_content = str(act_response.content)
            act_parsed = self._parse_react_response(act_content)

            traces.append({
                "round": idx + 1,
                "phase": "act",
                "content": act_content,
                "parsed": act_parsed,
                "tool_result": tool_result,
            })

            if act_parsed.get("answer"):
                usage = self._extract_usage(act_response)
                return {
                    "agent": self.agent_name,
                    "result": act_parsed["answer"],
                    "status": "success",
                    "model": self._extract_model_name(),
                    "meta": {
                        "mode": "react",
                        "completed_rounds": idx + 1,
                    },
                    "mode_trace": traces,
                    "observations": observations,
                    **usage,
                    "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
                }

            if act_parsed.get("action") == "elk_query" and act_parsed.get("action_input"):
                tool_result = await self._execute_tool("elk_query", act_parsed["action_input"])
                if tool_result["success"]:
                    new_observation = f"Query: {act_parsed['action_input'].get('query')}\nResult: {tool_result['result']}"
                else:
                    new_observation = f"Query failed: {tool_result['error']}"
                observations.append(new_observation)

            signal = act_content
            if signal == last_signal:
                rounds_without_increment += 1
            else:
                rounds_without_increment = 0
            last_signal = signal

            if rounds_without_increment >= stagnation_limit:
                usage = self._extract_usage(act_response)
                return {
                    "agent": self.agent_name,
                    "result": f"ReAct loop stopped due to stagnation after {idx + 1} rounds",
                    "status": "success",
                    "model": self._extract_model_name(),
                    "meta": {
                        "mode": "react",
                        "react_stagnation": True,
                        "completed_rounds": idx + 1,
                    },
                    "mode_trace": traces,
                    "observations": observations,
                    **usage,
                    "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
                }

        usage = self._extract_usage(act_response)
        return {
            "agent": self.agent_name,
            "result": f"ReAct loop completed max {max_rounds} rounds without final answer",
            "status": "success",
            "model": self._extract_model_name(),
            "meta": {
                "mode": "react",
                "max_rounds_reached": True,
            },
            "mode_trace": traces,
            "observations": observations,
            **usage,
            "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
        }

    def _failure_explanation(self, tool_record: Dict[str, Any], content: str) -> Dict[str, Any]:
        missing: List[str] = []
        status = "ok"
        reason = None
        if tool_record and not tool_record.get("success", False):
            status = "insufficient_evidence"
            reason = "tool_query_failed"
            missing.append("日志查询结果")
        if "INSUFFICIENT_EVIDENCE" in (content or ""):
            status = "insufficient_evidence"
            reason = reason or "agent_marked_insufficient"
            missing.append("可复现实验或更精确日志过滤条件")
        return AgentFailureExplanation(status=status, reason=reason, missing_evidence=missing).model_dump()

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        react_phase = context.get("react_phase")
        observations = context.get("observations", [])
        reasoning = context.get("reasoning", "")

        try:
            if react_phase == "reason":
                prompt = ChatPromptTemplate.from_template(REACT_REASON_PROMPT)
                messages = prompt.format_messages(
                    task=task,
                    context=str(context),
                    observations="\n".join(observations) if observations else "None"
                )
                response = await self.llm.ainvoke(messages)
                content = str(response.content)
                parsed = self._parse_react_response(content)

                usage = self._extract_usage(response)
                return {
                    "agent": self.agent_name,
                    "result": content,
                    "status": "success",
                    "parsed_response": parsed,
                    "model": self._extract_model_name(),
                    **usage,
                    "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
                }

            elif react_phase == "act":
                tool_result = context.get("tool_result", {})
                prompt = ChatPromptTemplate.from_template(REACT_ACT_PROMPT)
                messages = prompt.format_messages(
                    task=task,
                    context=str(context),
                    reasoning=reasoning,
                    tool_result=str(tool_result),
                    observations="\n".join(observations) if observations else "None"
                )
                response = await self.llm.ainvoke(messages)
                content = str(response.content)
                parsed = self._parse_react_response(content)

                usage = self._extract_usage(response)
                result = {
                    "agent": self.agent_name,
                    "result": content,
                    "status": "success",
                    "parsed_response": parsed,
                    "model": self._extract_model_name(),
                    **usage,
                    "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
                }

                if parsed["action"] == "elk_query" and parsed["action_input"]:
                    tool_record = await self._execute_tool("elk_query", parsed["action_input"])
                    result["tool_call"] = tool_record
                    if tool_record["success"]:
                        result["new_observation"] = f"Query: {parsed['action_input'].get('query')}\nResult: {tool_record['result']}"
                    else:
                        result["new_observation"] = f"Query failed: {tool_record['error']}"

                return result

            elif context.get("mode") == "react" and not react_phase:
                return await self._execute_react_loop(task, context)

            else:
                tool_record = await self.run_required_tool(task, context)
                prompt = ChatPromptTemplate.from_template(LOG_AGENT_PROMPT)
                messages = prompt.format_messages(task=task, context=str(context), tool_evidence=str(tool_record))
                response = await self.llm.ainvoke(messages)
                usage = self._extract_usage(response)
                content = str(response.content)
                return {
                    "agent": self.agent_name,
                    "result": content,
                    "status": "success",
                    "failure_explanation": self._failure_explanation(tool_record, content),
                    "model": self._extract_model_name(),
                    "toolCalls": [tool_record] if tool_record else [],
                    **usage,
                    "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
                }

        except Exception as e:
            logger.error(f"LogAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error",
                "failure_explanation": AgentFailureExplanation(status="error", reason=str(e), missing_evidence=["日志证据"]).model_dump(),
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
