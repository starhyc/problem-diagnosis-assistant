import { create } from 'zustand';
import { investigationApi } from '../lib/api';
import { wsService, ConfirmationRequired } from '../lib/websocket';
import { AgentTrace, ExecutionStep, TraceReplaySnapshot } from '../types/trace';
import { DiagnosisMode } from '../types/agent';
import { DiagnosisEvent } from '../contracts/diagnosisProtocol';

export interface AgentMessage {
  id: string;
  agent: string;
  timestamp: string;
  content: string;
  type: 'info' | 'hypothesis' | 'action' | 'evidence' | 'decision' | 'error';
}

export interface TimelineStep {
  id: number;
  step: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  duration: string;
  agent: string;
  output: string;
}

export interface DiagnosisCase {
  id: string;
  sessionId?: string;
  taskId?: string;
  symptom: string;
  description: string;
  status: 'pending' | 'investigating' | 'resolved' | 'failed';
  leadAgent: string;
  confidence: number;
  messages: AgentMessage[];
  timeline: TimelineStep[];
  createdAt: string;
}

export type ConfirmationFlowState = 'idle' | 'pending_r2' | 'pending_r3' | 'approved' | 'rejected' | 'timeout';
type TraceLifecycleState = 'idle' | 'started' | 'completed';

interface DiagnosisState {
  currentCase: DiagnosisCase | null;
  isRunning: boolean;
  proposedAction: { id: string; title: string; confidence: number } | null;
  wsConnected: boolean;
  pendingConfirmation: ConfirmationRequired | null;
  confirmationFlowState: ConfirmationFlowState;
  currentAgentType: string;
  traces: Map<string, AgentTrace>;
  traceLifecycle: Map<string, TraceLifecycleState>;
  selectedAgentId: string | null;
  rootAgentIds: string[];
  replaySnapshot: TraceReplaySnapshot | null;
  startDiagnosis: (agentType: string, symptom: string, description: string, mode?: DiagnosisMode) => Promise<void>;
  stopDiagnosis: () => Promise<void>;
  approveAction: () => Promise<void>;
  rejectAction: () => Promise<void>;
  respondToConfirmation: (confirmationId: string, response: Record<string, unknown>) => void;
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;
  selectAgent: (agentId: string | null) => void;
}

let wsUnsubscribe: (() => void) | null = null;
let statusUnsubscribe: (() => void) | null = null;

const asRecord = (value: unknown): Record<string, unknown> => (typeof value === 'object' && value !== null ? (value as Record<string, unknown>) : {});
const asString = (value: unknown, fallback = ''): string => (typeof value === 'string' ? value : fallback);
const asNumber = (value: unknown, fallback = 0): number => (typeof value === 'number' ? value : fallback);

const mapStepType = (stepData: Record<string, unknown>): ExecutionStep['type'] => {
  const rawType = asString(stepData.type) || asString(stepData.stepType) || 'llm_thinking';
  if (rawType === 'task_received' || rawType === 'llm_thinking' || rawType === 'tool_call' || rawType === 'agent_dispatch') {
    return rawType;
  }
  return 'llm_thinking';
};

export function applyDiagnosisEvent(state: DiagnosisState, message: DiagnosisEvent): Partial<DiagnosisState> {
  const data = asRecord(message.data);

  switch (message.type) {
    case 'agent_message': {
      const agentMsg = data as unknown as AgentMessage;
      return {
        currentCase: state.currentCase ? { ...state.currentCase, messages: [...state.currentCase.messages, agentMsg] } : null,
      };
    }
    case 'action_proposal': {
      return {
        proposedAction: {
          id: asString(data.id, 'current-action'),
          title: asString(data.title),
          confidence: asNumber(data.confidence),
        },
      };
    }
    case 'diagnosis_status': {
      const status = asString(data.status);
      return {
        isRunning: status === 'running',
        currentCase: state.currentCase
          ? { ...state.currentCase, status: status === 'failed' ? 'failed' : status === 'completed' ? 'resolved' : 'investigating' }
          : null,
      };
    }
    case 'diagnosis_progress': {
      const phase = asString(data.phase);
      if (phase === 'confidence') {
        return { currentCase: state.currentCase ? { ...state.currentCase, confidence: asNumber(data.confidence) } : null };
      }
      if (phase === 'timeline' && Array.isArray(data.timeline)) {
        return {
          currentCase: state.currentCase ? { ...state.currentCase, timeline: data.timeline as TimelineStep[] } : null,
        };
      }
      return {};
    }
    case 'timeline_update':
      return { currentCase: state.currentCase ? { ...state.currentCase, timeline: (data.timeline as TimelineStep[]) || [] } : null };
    case 'confidence_update':
      return { currentCase: state.currentCase ? { ...state.currentCase, confidence: asNumber(data.confidence) } : null };
    case 'confirmation_required': {
      const confirmation = data as unknown as ConfirmationRequired;
      const risk = confirmation.riskLevel;
      return {
        pendingConfirmation: confirmation,
        confirmationFlowState: risk === 'R3' ? 'pending_r3' : risk === 'R2' ? 'pending_r2' : 'idle',
      };
    }
    case 'confirmation_rejected':
      return { pendingConfirmation: null, confirmationFlowState: 'rejected', isRunning: false };
    case 'confirmation_status': {
      const action = asString(data.action);
      const statusValue = asString(data.status);
      if (statusValue === 'timed_out' || action === 'timeout') return { pendingConfirmation: null, confirmationFlowState: 'timeout', isRunning: false };
      if (action === 'second_confirm') {
        return {
          confirmationFlowState: 'pending_r3',
          pendingConfirmation: state.pendingConfirmation
            ? { ...state.pendingConfirmation, riskLevel: 'R3', message: `R3 二次确认：${state.pendingConfirmation.message}` }
            : state.pendingConfirmation,
        };
      }
      if (statusValue === 'rejected' || action === 'reject' || action === 'cancel') {
        return { pendingConfirmation: null, confirmationFlowState: 'rejected', isRunning: false };
      }
      return { pendingConfirmation: null, confirmationFlowState: 'approved' };
    }
    case 'agent_trace_start': {
      const agentId = asString(data.agentId);
      if (!agentId || state.traceLifecycle.get(agentId) === 'started') return {};
      const lifecycle = new Map(state.traceLifecycle);
      lifecycle.set(agentId, 'started');
      const traces = new Map(state.traces);
      traces.set(agentId, {
        id: agentId,
        name: asString(data.agentName, 'Unknown Agent'),
        parentId: asString(data.parentId) || null,
        status: 'running',
        startTime: asString(data.startTime, new Date().toISOString()),
        totalTokens: { input: asNumber(data.inputTokens), output: asNumber(data.outputTokens) },
        model: asString(data.model),
        costEstimate: asNumber(data.costEstimate),
        steps: [],
        taskDescription: asString(data.taskDescription),
      });
      const rootAgentIds = asString(data.parentId) ? state.rootAgentIds : state.rootAgentIds.includes(agentId) ? state.rootAgentIds : [...state.rootAgentIds, agentId];
      return { traces, traceLifecycle: lifecycle, rootAgentIds, selectedAgentId: state.selectedAgentId || agentId };
    }
    case 'agent_trace_step': {
      const agentId = asString(data.agentId);
      if (!agentId || state.traceLifecycle.get(agentId) !== 'started') return {};
      const trace = state.traces.get(agentId);
      if (!trace) return {};
      const mappedStep: ExecutionStep = {
        ...(data as unknown as ExecutionStep),
        id: asString(data.id) || asString(data.stepId),
        type: mapStepType(data),
        timestamp: asString(data.timestamp, new Date().toISOString()),
      };
      const traces = new Map(state.traces);
      traces.set(agentId, { ...trace, model: trace.model || asString(data.model), costEstimate: (trace.costEstimate || 0) + asNumber(data.costEstimate), steps: [...trace.steps, mappedStep] });
      return { traces };
    }
    case 'agent_trace_complete': {
      const agentId = asString(data.agentId);
      if (!agentId || state.traceLifecycle.get(agentId) !== 'started') return {};
      const trace = state.traces.get(agentId);
      if (!trace) return {};
      const lifecycle = new Map(state.traceLifecycle);
      lifecycle.set(agentId, 'completed');
      const traces = new Map(state.traces);
      traces.set(agentId, {
        ...trace,
        status: asString(data.status, 'success') as AgentTrace['status'],
        endTime: asString(data.endTime, new Date().toISOString()),
        duration: asNumber(data.duration, asNumber(data.latency)),
        latency: asNumber(data.latency),
        totalTokens: (data.totalTokens as AgentTrace['totalTokens']) || { input: asNumber(data.inputTokens, trace.totalTokens.input), output: asNumber(data.outputTokens, trace.totalTokens.output) },
        model: asString(data.model, trace.model),
        costEstimate: asNumber(data.costEstimate, trace.costEstimate || 0),
        error: asString(data.error),
      });
      return { traces, traceLifecycle: lifecycle };
    }
    case 'replay_snapshot':
      return { replaySnapshot: data as unknown as TraceReplaySnapshot };
    case 'diagnosis_completed': {
      const replaySnapshot: TraceReplaySnapshot = {
        snapshotAt: message.timestamp || new Date().toISOString(),
        caseId: state.currentCase?.id,
        traces: Array.from(state.traces.values()),
        rootAgentIds: [...state.rootAgentIds],
      };
      return { replaySnapshot, isRunning: false };
    }
    case 'diagnosis_failed':
    case 'error':
      return { isRunning: false };
    default:
      return {};
  }
}

export const useDiagnosisStore = create<DiagnosisState>((set, get) => ({
  currentCase: null,
  isRunning: false,
  proposedAction: null,
  wsConnected: false,
  pendingConfirmation: null,
  confirmationFlowState: 'idle',
  currentAgentType: 'diagnosis',
  traces: new Map(),
  traceLifecycle: new Map(),
  selectedAgentId: null,
  rootAgentIds: [],
  replaySnapshot: null,

  initializeWebSocket: () => {
    if (wsUnsubscribe) return;
    wsService.connect().catch((error) => console.error('[DiagnosisStore] WebSocket connection failed:', error));
    wsUnsubscribe = wsService.onMessage((message) => set((s) => applyDiagnosisEvent(s, message)));
    statusUnsubscribe = wsService.onConnectionStatus((status) => set({ wsConnected: status === 'connected' }));
  },

  disconnectWebSocket: () => {
    if (wsUnsubscribe) wsUnsubscribe();
    wsUnsubscribe = null;
    if (statusUnsubscribe) statusUnsubscribe();
    statusUnsubscribe = null;
    wsService.disconnect();
  },

  startDiagnosis: async (agentType, symptom, description, mode: DiagnosisMode = 'auto') => {
    try {
      const response = await investigationApi.startDiagnosis(agentType, symptom, description, undefined, undefined, mode);
      const caseId = response.session_id || `CASE-${agentType.toUpperCase()}-${Date.now()}`;
      set({
        currentCase: { id: caseId, sessionId: response.session_id, taskId: response.task_id, symptom, description, status: 'investigating', leadAgent: agentType, confidence: 0, messages: [], timeline: [], createdAt: new Date().toISOString() },
        isRunning: true,
        proposedAction: null,
        currentAgentType: agentType,
        traces: new Map(),
        traceLifecycle: new Map(),
        rootAgentIds: [],
        selectedAgentId: null,
        replaySnapshot: null,
        pendingConfirmation: null,
        confirmationFlowState: 'idle',
      });
      wsService.startDiagnosis(symptom, description, agentType, undefined, mode);
    } catch (error) {
      console.error('[DiagnosisStore] Failed to start diagnosis:', error);
      set({ isRunning: false });
    }
  },

  stopDiagnosis: async () => {
    const sessionId = get().currentCase?.sessionId;
    if (sessionId) {
      try {
        await investigationApi.stopDiagnosis({ session_id: sessionId });
      } catch (error) {
        console.error('[DiagnosisStore] Failed to stop diagnosis session:', error);
      }
    }
    wsService.stopDiagnosis('User stopped');
    set({ isRunning: false });
  },

  approveAction: async () => {
    const state = get();
    if (!state.proposedAction || !state.currentCase?.sessionId) return;
    try {
      await investigationApi.approveAction({ session_id: state.currentCase.sessionId, action_id: state.proposedAction.id });
    } catch (error) {
      console.error('[DiagnosisStore] Failed to approve action:', error);
    }
    wsService.approveAction(state.proposedAction.id);
    set((s) => ({ proposedAction: null, currentCase: s.currentCase ? { ...s.currentCase, status: 'resolved' } : null }));
  },

  rejectAction: async () => {
    const state = get();
    if (!state.proposedAction || !state.currentCase?.sessionId) return;
    try {
      await investigationApi.rejectAction({ session_id: state.currentCase.sessionId, action_id: state.proposedAction.id, reason: 'User rejected' });
    } catch (error) {
      console.error('[DiagnosisStore] Failed to reject action:', error);
    }
    wsService.rejectAction(state.proposedAction.id, 'User rejected');
    set({ proposedAction: null });
  },

  respondToConfirmation: (confirmationId, response) => {
    const current = get().pendingConfirmation;
    if (!current) return;
    wsService.respondToConfirmation(confirmationId, response);
    if (response.action === 'second_confirm') {
      set({ confirmationFlowState: 'pending_r3', pendingConfirmation: { ...current, riskLevel: 'R3', message: `R3 二次确认：${current.message}` } });
      return;
    }
    if (response.action === 'reject' || response.action === 'cancel') {
      set({ pendingConfirmation: null, confirmationFlowState: 'rejected', isRunning: false });
      return;
    }
    set({ pendingConfirmation: null });
  },

  selectAgent: (agentId) => set({ selectedAgentId: agentId }),
}));

export function getChildAgents(traces: Map<string, AgentTrace>, parentId: string): AgentTrace[] {
  return Array.from(traces.values()).filter((trace) => trace.parentId === parentId);
}

export function getRootAgents(traces: Map<string, AgentTrace>): AgentTrace[] {
  return Array.from(traces.values()).filter((trace) => trace.parentId === null);
}
