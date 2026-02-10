import { create } from 'zustand';
import { investigationApi } from '../lib/api';
import { wsService, WSMessage, ConfirmationRequired } from '../lib/websocket';
import { AgentTrace, ExecutionStep, TraceReplaySnapshot } from '../types/trace';
import { DiagnosisMode } from '../types/agent';

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
  symptom: string;
  description: string;
  status: 'pending' | 'investigating' | 'resolved' | 'failed';
  leadAgent: string;
  confidence: number;
  messages: AgentMessage[];
  timeline: TimelineStep[];
  createdAt: string;
}

export type ConfirmationFlowState =
  | 'idle'
  | 'pending_r2'
  | 'pending_r3'
  | 'approved'
  | 'rejected'
  | 'timeout';

type TraceLifecycleState = 'idle' | 'started' | 'completed';

interface DiagnosisState {
  currentCase: DiagnosisCase | null;
  isRunning: boolean;
  proposedAction: { title: string; confidence: number } | null;
  wsConnected: boolean;
  pendingConfirmation: ConfirmationRequired | null;
  confirmationFlowState: ConfirmationFlowState;
  currentAgentType: string;

  traces: Map<string, AgentTrace>;
  traceLifecycle: Map<string, TraceLifecycleState>;
  selectedAgentId: string | null;
  rootAgentIds: string[];
  replaySnapshot: TraceReplaySnapshot | null;

  startDiagnosis: (agentType: string, symptom: string, description: string, mode?: DiagnosisMode) => void;
  stopDiagnosis: () => void;
  approveAction: () => void;
  rejectAction: () => void;
  respondToConfirmation: (confirmationId: string, response: any) => void;
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;
  selectAgent: (agentId: string | null) => void;
}

let wsUnsubscribe: (() => void) | null = null;
let statusUnsubscribe: (() => void) | null = null;

const mapStepType = (stepData: any): ExecutionStep['type'] => {
  const rawType = stepData.type || stepData.stepType || 'llm_thinking';
  if (rawType === 'task_received' || rawType === 'llm_thinking' || rawType === 'tool_call' || rawType === 'agent_dispatch') {
    return rawType;
  }
  return 'llm_thinking';
};

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

    wsService.connect().catch((error) => {
      console.error('[DiagnosisStore] WebSocket connection failed:', error);
    });

    wsUnsubscribe = wsService.onMessage((message: WSMessage) => {
      const state = get();

      switch (message.type) {
        case 'agent_message': {
          const agentMsg = message.data as AgentMessage;
          set((s) => ({
            currentCase: s.currentCase
              ? {
                  ...s.currentCase,
                  messages: [...s.currentCase.messages, agentMsg],
                }
              : null,
          }));
          break;
        }
        case 'action_proposal': {
          const proposal = message.data;
          set({ proposedAction: { title: proposal.title, confidence: proposal.confidence } });
          break;
        }
        case 'diagnosis_status': {
          const statusData = message.data;
          set({
            isRunning: statusData.status === 'running',
            currentCase: state.currentCase
              ? {
                  ...state.currentCase,
                  status: statusData.status as any,
                }
              : null,
          });
          break;
        }
        case 'timeline_update': {
          const timelineData = message.data;
          set((s) => ({
            currentCase: s.currentCase ? { ...s.currentCase, timeline: timelineData.timeline } : null,
          }));
          break;
        }
        case 'confidence_update': {
          const confidenceData = message.data;
          set((s) => ({
            currentCase: s.currentCase ? { ...s.currentCase, confidence: confidenceData.confidence } : null,
          }));
          break;
        }
        case 'confirmation_required': {
          const confirmation = message.data as ConfirmationRequired;
          const risk = confirmation.riskLevel;
          set({
            pendingConfirmation: confirmation,
            confirmationFlowState: risk === 'R3' ? 'pending_r3' : risk === 'R2' ? 'pending_r2' : 'idle',
          });
          break;
        }
        case 'confirmation_status': {
          const confirmationStatus = message.data;
          const action = confirmationStatus.action;
          const statusValue = confirmationStatus.status;

          if (statusValue === 'timed_out' || action === 'timeout') {
            set({ pendingConfirmation: null, confirmationFlowState: 'timeout', isRunning: false });
            break;
          }
          if (action === 'second_confirm') {
            set((s) => ({
              confirmationFlowState: 'pending_r3',
              pendingConfirmation: s.pendingConfirmation
                ? { ...s.pendingConfirmation, riskLevel: 'R3', message: `R3 二次确认：${s.pendingConfirmation.message}` }
                : s.pendingConfirmation,
            }));
            break;
          }
          if (statusValue === 'rejected' || action === 'reject' || action === 'cancel') {
            set({ pendingConfirmation: null, confirmationFlowState: 'rejected', isRunning: false });
            break;
          }
          set({ pendingConfirmation: null, confirmationFlowState: 'approved' });
          break;
        }
        case 'agent_trace_start': {
          const traceData = message.data;
          const agentId = traceData.agentId;

          set((s) => {
            const lifecycle = new Map(s.traceLifecycle);
            if (lifecycle.get(agentId) === 'started') {
              console.warn(`[DiagnosisStore] duplicate trace start ignored: ${agentId}`);
              return s;
            }

            lifecycle.set(agentId, 'started');
            const traces = new Map(s.traces);
            traces.set(agentId, {
              id: agentId,
              name: traceData.agentName || 'Unknown Agent',
              parentId: traceData.parentId || null,
              status: 'running',
              startTime: traceData.startTime || new Date().toISOString(),
              totalTokens: {
                input: traceData.inputTokens || 0,
                output: traceData.outputTokens || 0,
              },
              model: traceData.model,
              costEstimate: traceData.costEstimate || 0,
              steps: [],
              taskDescription: traceData.taskDescription,
            });

            const rootAgentIds = traceData.parentId
              ? s.rootAgentIds
              : s.rootAgentIds.includes(agentId)
              ? s.rootAgentIds
              : [...s.rootAgentIds, agentId];

            return {
              traces,
              traceLifecycle: lifecycle,
              rootAgentIds,
              selectedAgentId: s.selectedAgentId || agentId,
            };
          });
          break;
        }
        case 'agent_trace_step': {
          const stepData = message.data;
          const agentId = stepData.agentId;
          set((s) => {
            if (s.traceLifecycle.get(agentId) !== 'started') {
              console.warn(`[DiagnosisStore] trace step before start ignored: ${agentId}`);
              return s;
            }
            const trace = s.traces.get(agentId);
            if (!trace) return s;

            const mappedStep: ExecutionStep = {
              ...stepData,
              id: stepData.id || stepData.stepId,
              type: mapStepType(stepData),
              timestamp: stepData.timestamp || new Date().toISOString(),
            };

            const traces = new Map(s.traces);
            traces.set(agentId, {
              ...trace,
              model: trace.model || stepData.model,
              costEstimate: (trace.costEstimate || 0) + (stepData.costEstimate || 0),
              steps: [...trace.steps, mappedStep],
            });
            return { traces };
          });
          break;
        }
        case 'agent_trace_complete': {
          const completeData = message.data;
          const agentId = completeData.agentId;

          set((s) => {
            if (s.traceLifecycle.get(agentId) !== 'started') {
              console.warn(`[DiagnosisStore] trace complete before start ignored: ${agentId}`);
              return s;
            }
            const trace = s.traces.get(agentId);
            if (!trace) return s;

            const lifecycle = new Map(s.traceLifecycle);
            lifecycle.set(agentId, 'completed');

            const traces = new Map(s.traces);
            traces.set(agentId, {
              ...trace,
              status: completeData.status || 'success',
              endTime: completeData.endTime || new Date().toISOString(),
              duration: completeData.duration ?? completeData.latency,
              latency: completeData.latency,
              totalTokens: completeData.totalTokens || {
                input: completeData.inputTokens ?? trace.totalTokens.input,
                output: completeData.outputTokens ?? trace.totalTokens.output,
              },
              model: completeData.model || trace.model,
              costEstimate: completeData.costEstimate ?? trace.costEstimate,
              error: completeData.error,
            });

            return { traces, traceLifecycle: lifecycle };
          });
          break;
        }
        default: {
          if (message.type === 'diagnosis_completed') {
            const s = get();
            const replaySnapshot: TraceReplaySnapshot = {
              snapshotAt: message.timestamp || new Date().toISOString(),
              caseId: s.currentCase?.id,
              traces: Array.from(s.traces.values()),
              rootAgentIds: [...s.rootAgentIds],
            };
            set({ replaySnapshot, isRunning: false });
          }
          if (message.type === 'error') {
            console.error('[DiagnosisStore] Error from server:', message.data);
            set({ isRunning: false });
          }
          break;
        }
      }
    });

    statusUnsubscribe = wsService.onConnectionStatus((status) => {
      set({ wsConnected: status === 'connected' });
    });
  },

  disconnectWebSocket: () => {
    if (wsUnsubscribe) {
      wsUnsubscribe();
      wsUnsubscribe = null;
    }
    if (statusUnsubscribe) {
      statusUnsubscribe();
      statusUnsubscribe = null;
    }
    wsService.disconnect();
  },

  startDiagnosis: async (agentType: string, symptom: string, description: string, mode: DiagnosisMode = 'auto') => {
    try {
      await investigationApi.startDiagnosis(agentType, symptom, description, undefined, undefined, mode);
      const caseId = `CASE-${agentType.toUpperCase()}-${Date.now()}`;

      set({
        currentCase: {
          id: caseId,
          symptom,
          description,
          status: 'investigating',
          leadAgent: agentType,
          confidence: 0,
          messages: [],
          timeline: [],
          createdAt: new Date().toISOString(),
        },
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

  stopDiagnosis: () => {
    wsService.stopDiagnosis('User stopped');
    set({ isRunning: false });
  },

  approveAction: () => {
    const state = get();
    if (!state.proposedAction) return;
    wsService.approveAction('current-action');
    set((s) => ({
      proposedAction: null,
      currentCase: s.currentCase ? { ...s.currentCase, status: 'resolved' } : null,
    }));
  },

  rejectAction: () => {
    const state = get();
    if (!state.proposedAction) return;
    wsService.rejectAction('current-action', 'User rejected');
    set({ proposedAction: null });
  },

  respondToConfirmation: (confirmationId: string, response: any) => {
    const current = get().pendingConfirmation;
    if (!current) return;

    wsService.respondToConfirmation(confirmationId, response);
    if (response?.action === 'second_confirm') {
      set({
        confirmationFlowState: 'pending_r3',
        pendingConfirmation: {
          ...current,
          riskLevel: 'R3',
          message: `R3 二次确认：${current.message}`,
        },
      });
      return;
    }
    if (response?.action === 'reject' || response?.action === 'cancel') {
      set({ pendingConfirmation: null, confirmationFlowState: 'rejected', isRunning: false });
      return;
    }
    set({ pendingConfirmation: null });
  },

  selectAgent: (agentId: string | null) => set({ selectedAgentId: agentId }),
}));

export function getChildAgents(traces: Map<string, AgentTrace>, parentId: string): AgentTrace[] {
  return Array.from(traces.values()).filter(trace => trace.parentId === parentId);
}

export function getRootAgents(traces: Map<string, AgentTrace>): AgentTrace[] {
  return Array.from(traces.values()).filter(trace => trace.parentId === null);
}
