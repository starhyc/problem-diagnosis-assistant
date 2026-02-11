import { create } from 'zustand';
import { investigationApi } from '../lib/api';
import { wsService, ConfirmationRequired } from '../lib/websocket';
import { AgentTrace, ExecutionStep, TraceReplaySnapshot } from '../types/trace';
import { DiagnosisMode } from '../types/agent';
import { DiagnosisEvent, DiagnosisEventType } from '../contracts/diagnosisProtocol';

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

type DiagnosisEventMap = {
  [K in DiagnosisEventType]: Record<string, unknown>;
};

type EventConsumer = {
  [K in DiagnosisEventType]?: (state: DiagnosisStoreState, event: DiagnosisEvent & { type: K; data: DiagnosisEventMap[K] }) => Partial<DiagnosisStoreState>;
};

interface SessionStoreState {
  currentCase: DiagnosisCase | null;
  isRunning: boolean;
  proposedAction: { id: string; title: string; confidence: number } | null;
  wsConnected: boolean;
  currentAgentType: string;
  eventLedger: Set<string>;
}

interface TraceStoreState {
  traces: Map<string, AgentTrace>;
  traceLifecycle: Map<string, TraceLifecycleState>;
  selectedAgentId: string | null;
  rootAgentIds: string[];
  replaySnapshot: TraceReplaySnapshot | null;
  eventLedger: Set<string>;
}

interface ConfirmationStoreState {
  pendingConfirmation: ConfirmationRequired | null;
  confirmationFlowState: ConfirmationFlowState;
  eventLedger: Set<string>;
}

interface TraceViewState {
  traceMap: Map<string, AgentTrace>;
  traceList: AgentTrace[];
  rootAgentIds: string[];
  selectedAgentId: string | null;
  selectedTrace: AgentTrace | null;
}

interface DiagnosisStoreState {
  sessionStore: SessionStoreState;
  traceStore: TraceStoreState;
  confirmationStore: ConfirmationStoreState;
  startDiagnosis: (agentType: string, symptom: string, description: string, mode?: DiagnosisMode) => Promise<void>;
  stopDiagnosis: () => Promise<void>;
  approveAction: () => Promise<void>;
  rejectAction: () => Promise<void>;
  respondToConfirmation: (confirmationId: string, response: Record<string, unknown>) => void;
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;
  selectAgent: (agentId: string | null) => void;
  getTraceView: () => TraceViewState;
}

const initialSessionStore = (): SessionStoreState => ({
  currentCase: null,
  isRunning: false,
  proposedAction: null,
  wsConnected: false,
  currentAgentType: 'diagnosis',
  eventLedger: new Set(),
});

const initialTraceStore = (): TraceStoreState => ({
  traces: new Map(),
  traceLifecycle: new Map(),
  selectedAgentId: null,
  rootAgentIds: [],
  replaySnapshot: null,
  eventLedger: new Set(),
});

const initialConfirmationStore = (): ConfirmationStoreState => ({
  pendingConfirmation: null,
  confirmationFlowState: 'idle',
  eventLedger: new Set(),
});

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

const toEventKey = (type: DiagnosisEventType, timestamp: string, data: Record<string, unknown>, candidates: string[]): string => {
  const keyById = candidates.find((key) => asString(data[key]));
  if (keyById) {
    return `${type}:${asString(data[keyById])}`;
  }
  return `${type}:${timestamp}:${JSON.stringify(data)}`;
};

const sessionConsumers: EventConsumer = {
  agent_message: (state, event) => {
    const key = toEventKey(event.type, event.timestamp, event.data, ['id', 'messageId']);
    if (state.sessionStore.eventLedger.has(key)) return {};
    const ledger = new Set(state.sessionStore.eventLedger);
    ledger.add(key);

    const agentMsg = event.data as unknown as AgentMessage;
    return {
      sessionStore: {
        ...state.sessionStore,
        eventLedger: ledger,
        currentCase: state.sessionStore.currentCase
          ? { ...state.sessionStore.currentCase, messages: [...state.sessionStore.currentCase.messages, agentMsg] }
          : null,
      },
    };
  },
  action_proposal: (state, event) => ({
    sessionStore: {
      ...state.sessionStore,
      proposedAction: {
        id: asString(event.data.id, 'current-action'),
        title: asString(event.data.title),
        confidence: asNumber(event.data.confidence),
      },
    },
  }),
  diagnosis_status: (state, event) => {
    const status = asString(event.data.status);
    return {
      sessionStore: {
        ...state.sessionStore,
        isRunning: status === 'running',
        currentCase: state.sessionStore.currentCase
          ? { ...state.sessionStore.currentCase, status: status === 'failed' ? 'failed' : status === 'completed' ? 'resolved' : 'investigating' }
          : null,
      },
    };
  },
  diagnosis_progress: (state, event) => {
    const phase = asString(event.data.phase);
    if (phase === 'confidence') {
      return {
        sessionStore: {
          ...state.sessionStore,
          currentCase: state.sessionStore.currentCase ? { ...state.sessionStore.currentCase, confidence: asNumber(event.data.confidence) } : null,
        },
      };
    }
    if (phase === 'timeline' && Array.isArray(event.data.timeline)) {
      return {
        sessionStore: {
          ...state.sessionStore,
          currentCase: state.sessionStore.currentCase ? { ...state.sessionStore.currentCase, timeline: event.data.timeline as TimelineStep[] } : null,
        },
      };
    }
    return {};
  },
  timeline_update: (state, event) => ({
    sessionStore: {
      ...state.sessionStore,
      currentCase: state.sessionStore.currentCase ? { ...state.sessionStore.currentCase, timeline: (event.data.timeline as TimelineStep[]) || [] } : null,
    },
  }),
  confidence_update: (state, event) => ({
    sessionStore: {
      ...state.sessionStore,
      currentCase: state.sessionStore.currentCase ? { ...state.sessionStore.currentCase, confidence: asNumber(event.data.confidence) } : null,
    },
  }),
  diagnosis_completed: (state) => ({
    sessionStore: {
      ...state.sessionStore,
      isRunning: false,
    },
  }),
  diagnosis_failed: (state) => ({
    sessionStore: {
      ...state.sessionStore,
      isRunning: false,
    },
  }),
  error: (state) => ({
    sessionStore: {
      ...state.sessionStore,
      isRunning: false,
    },
  }),
};

const traceConsumers: EventConsumer = {
  agent_trace_start: (state, event) => {
    const agentId = asString(event.data.agentId);
    if (!agentId) return {};
    const key = toEventKey(event.type, event.timestamp, event.data, ['eventId', 'id', 'stepId', 'agentId']);
    if (state.traceStore.eventLedger.has(key) || state.traceStore.traceLifecycle.get(agentId) === 'started') return {};

    const lifecycle = new Map(state.traceStore.traceLifecycle);
    lifecycle.set(agentId, 'started');
    const traces = new Map(state.traceStore.traces);
    traces.set(agentId, {
      id: agentId,
      name: asString(event.data.agentName, 'Unknown Agent'),
      parentId: asString(event.data.parentId || event.data.parentAgentId) || null,
      status: 'running',
      startTime: asString(event.data.startTime || event.data.timestamp, event.timestamp || new Date().toISOString()),
      totalTokens: { input: asNumber(event.data.inputTokens), output: asNumber(event.data.outputTokens) },
      model: asString(event.data.model),
      costEstimate: asNumber(event.data.costEstimate),
      steps: [],
      taskDescription: asString(event.data.taskDescription),
    });

    const ledger = new Set(state.traceStore.eventLedger);
    ledger.add(key);
    const parentId = asString(event.data.parentId || event.data.parentAgentId);
    const rootAgentIds = parentId ? state.traceStore.rootAgentIds : state.traceStore.rootAgentIds.includes(agentId) ? state.traceStore.rootAgentIds : [...state.traceStore.rootAgentIds, agentId];
    return {
      traceStore: {
        ...state.traceStore,
        traces,
        traceLifecycle: lifecycle,
        rootAgentIds,
        eventLedger: ledger,
        selectedAgentId: state.traceStore.selectedAgentId || agentId,
      },
    };
  },
  agent_trace_step: (state, event) => {
    const agentId = asString(event.data.agentId);
    if (!agentId || state.traceStore.traceLifecycle.get(agentId) !== 'started') return {};
    const trace = state.traceStore.traces.get(agentId);
    if (!trace) return {};

    const stepKey = toEventKey(event.type, event.timestamp, event.data, ['eventId', 'stepId', 'id']);
    if (state.traceStore.eventLedger.has(stepKey)) return {};

    const mappedStep: ExecutionStep = {
      ...(event.data as unknown as ExecutionStep),
      id: asString(event.data.id) || asString(event.data.stepId),
      type: mapStepType(event.data),
      timestamp: asString(event.data.timestamp, event.timestamp || new Date().toISOString()),
    };

    const traces = new Map(state.traceStore.traces);
    traces.set(agentId, {
      ...trace,
      model: trace.model || asString(event.data.model),
      costEstimate: (trace.costEstimate || 0) + asNumber(event.data.costEstimate),
      steps: [...trace.steps, mappedStep],
    });

    const ledger = new Set(state.traceStore.eventLedger);
    ledger.add(stepKey);

    return {
      traceStore: {
        ...state.traceStore,
        traces,
        eventLedger: ledger,
      },
    };
  },
  agent_trace_complete: (state, event) => {
    const agentId = asString(event.data.agentId);
    if (!agentId || state.traceStore.traceLifecycle.get(agentId) !== 'started') return {};
    const trace = state.traceStore.traces.get(agentId);
    if (!trace) return {};

    const completeKey = toEventKey(event.type, event.timestamp, event.data, ['eventId', 'agentId']);
    if (state.traceStore.eventLedger.has(completeKey)) return {};

    const lifecycle = new Map(state.traceStore.traceLifecycle);
    lifecycle.set(agentId, 'completed');
    const traces = new Map(state.traceStore.traces);
    traces.set(agentId, {
      ...trace,
      status: asString(event.data.status, 'success') as AgentTrace['status'],
      endTime: asString(event.data.endTime || event.data.timestamp, event.timestamp || new Date().toISOString()),
      duration: asNumber(event.data.duration, asNumber(event.data.latency)),
      latency: asNumber(event.data.latency),
      totalTokens:
        (event.data.totalTokens as AgentTrace['totalTokens']) || {
          input: asNumber(event.data.inputTokens, trace.totalTokens.input),
          output: asNumber(event.data.outputTokens, trace.totalTokens.output),
        },
      model: asString(event.data.model, trace.model),
      costEstimate: asNumber(event.data.costEstimate, trace.costEstimate || 0),
      error: asString(event.data.error),
    });

    const ledger = new Set(state.traceStore.eventLedger);
    ledger.add(completeKey);

    return {
      traceStore: {
        ...state.traceStore,
        traces,
        traceLifecycle: lifecycle,
        eventLedger: ledger,
      },
    };
  },
  replay_snapshot: (state, event) => ({
    traceStore: {
      ...state.traceStore,
      replaySnapshot: event.data as unknown as TraceReplaySnapshot,
    },
  }),
  diagnosis_completed: (state, event) => {
    const replaySnapshot: TraceReplaySnapshot = {
      snapshotAt: event.timestamp || new Date().toISOString(),
      caseId: state.sessionStore.currentCase?.id,
      traces: Array.from(state.traceStore.traces.values()),
      rootAgentIds: [...state.traceStore.rootAgentIds],
    };

    return {
      traceStore: {
        ...state.traceStore,
        replaySnapshot,
      },
    };
  },
};

const confirmationConsumers: EventConsumer = {
  confirmation_required: (state, event) => {
    const confirmation = event.data as unknown as ConfirmationRequired;
    const risk = confirmation.riskLevel;
    const key = toEventKey(event.type, event.timestamp, event.data, ['id', 'confirmationId']);
    if (state.confirmationStore.eventLedger.has(key)) return {};
    const ledger = new Set(state.confirmationStore.eventLedger);
    ledger.add(key);
    return {
      confirmationStore: {
        pendingConfirmation: confirmation,
        confirmationFlowState: risk === 'R3' ? 'pending_r3' : risk === 'R2' ? 'pending_r2' : 'idle',
        eventLedger: ledger,
      },
    };
  },
  confirmation_rejected: (state) => ({
    confirmationStore: {
      ...state.confirmationStore,
      pendingConfirmation: null,
      confirmationFlowState: 'rejected',
    },
    sessionStore: {
      ...state.sessionStore,
      isRunning: false,
    },
  }),
  confirmation_status: (state, event) => {
    const action = asString(event.data.action);
    const statusValue = asString(event.data.status);

    if (statusValue === 'timed_out' || action === 'timeout') {
      return {
        confirmationStore: { ...state.confirmationStore, pendingConfirmation: null, confirmationFlowState: 'timeout' },
        sessionStore: { ...state.sessionStore, isRunning: false },
      };
    }

    if (action === 'second_confirm') {
      return {
        confirmationStore: {
          ...state.confirmationStore,
          confirmationFlowState: 'pending_r3',
          pendingConfirmation: state.confirmationStore.pendingConfirmation
            ? {
                ...state.confirmationStore.pendingConfirmation,
                riskLevel: 'R3',
                message: `R3 二次确认：${state.confirmationStore.pendingConfirmation.message}`,
              }
            : state.confirmationStore.pendingConfirmation,
        },
      };
    }

    if (statusValue === 'rejected' || action === 'reject' || action === 'cancel') {
      return {
        confirmationStore: { ...state.confirmationStore, pendingConfirmation: null, confirmationFlowState: 'rejected' },
        sessionStore: { ...state.sessionStore, isRunning: false },
      };
    }

    return {
      confirmationStore: { ...state.confirmationStore, pendingConfirmation: null, confirmationFlowState: 'approved' },
    };
  },
};

export function applyDiagnosisEvent(state: DiagnosisStoreState, message: DiagnosisEvent): Partial<DiagnosisStoreState> {
  const normalizedEvent: DiagnosisEvent = {
    ...message,
    data: asRecord(message.data),
  };

  const patch: Partial<DiagnosisStoreState> = {};
  const consumers: EventConsumer[] = [sessionConsumers, traceConsumers, confirmationConsumers];

  consumers.forEach((consumer) => {
    const handler = consumer[normalizedEvent.type];
    if (!handler) return;
    const currentState = { ...state, ...patch } as DiagnosisStoreState;
    Object.assign(patch, handler(currentState, normalizedEvent as never));
  });

  return patch;
}

export function projectTraceView(traceStore: TraceStoreState): TraceViewState {
  const traceMap = traceStore.traces;
  const traceList = Array.from(traceMap.values());
  const selectedTrace = traceStore.selectedAgentId ? traceMap.get(traceStore.selectedAgentId) || null : null;

  return {
    traceMap,
    traceList,
    rootAgentIds: traceStore.rootAgentIds,
    selectedAgentId: traceStore.selectedAgentId,
    selectedTrace,
  };
}

export function createReplayState(events: DiagnosisEvent[], maxIndex: number, baseCaseId?: string): TraceViewState {
  const initial: DiagnosisStoreState = {
    sessionStore: {
      ...initialSessionStore(),
      currentCase: baseCaseId
        ? {
            id: baseCaseId,
            symptom: '',
            description: '',
            status: 'investigating',
            leadAgent: 'diagnosis',
            confidence: 0,
            messages: [],
            timeline: [],
            createdAt: new Date().toISOString(),
          }
        : null,
    },
    traceStore: initialTraceStore(),
    confirmationStore: initialConfirmationStore(),
    startDiagnosis: async () => undefined,
    stopDiagnosis: async () => undefined,
    approveAction: async () => undefined,
    rejectAction: async () => undefined,
    respondToConfirmation: () => undefined,
    initializeWebSocket: () => undefined,
    disconnectWebSocket: () => undefined,
    selectAgent: () => undefined,
    getTraceView: () => projectTraceView(initialTraceStore()),
  };

  let replayState = initial;
  events.slice(0, Math.max(0, maxIndex + 1)).forEach((event) => {
    replayState = { ...replayState, ...applyDiagnosisEvent(replayState, event) };
  });

  return projectTraceView(replayState.traceStore);
}

export function mapHistoryEventToDiagnosisEvent(eventType: string, timestamp: string, eventData: Record<string, unknown>): DiagnosisEvent {
  return {
    type: eventType as DiagnosisEventType,
    timestamp,
    data: eventData,
  };
}

export const useDiagnosisStore = create<DiagnosisStoreState>((set, get) => ({
  sessionStore: initialSessionStore(),
  traceStore: initialTraceStore(),
  confirmationStore: initialConfirmationStore(),

  initializeWebSocket: () => {
    if (wsUnsubscribe) return;
    wsService.connect().catch((error) => console.error('[DiagnosisStore] WebSocket connection failed:', error));
    wsUnsubscribe = wsService.onMessage((message) => set((state) => applyDiagnosisEvent(state, message)));
    statusUnsubscribe = wsService.onConnectionStatus((status) =>
      set((state) => ({ sessionStore: { ...state.sessionStore, wsConnected: status === 'connected' } })),
    );
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
        sessionStore: {
          ...initialSessionStore(),
          currentCase: {
            id: caseId,
            sessionId: response.session_id,
            taskId: response.task_id,
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
          currentAgentType: agentType,
          wsConnected: get().sessionStore.wsConnected,
        },
        traceStore: initialTraceStore(),
        confirmationStore: initialConfirmationStore(),
      });
      wsService.startDiagnosis(symptom, description, agentType, undefined, mode);
    } catch (error) {
      console.error('[DiagnosisStore] Failed to start diagnosis:', error);
      set((state) => ({ sessionStore: { ...state.sessionStore, isRunning: false } }));
    }
  },

  stopDiagnosis: async () => {
    const sessionId = get().sessionStore.currentCase?.sessionId;
    if (sessionId) {
      try {
        await investigationApi.stopDiagnosis({ session_id: sessionId });
      } catch (error) {
        console.error('[DiagnosisStore] Failed to stop diagnosis session:', error);
      }
    }
    wsService.stopDiagnosis('User stopped');
    set((state) => ({ sessionStore: { ...state.sessionStore, isRunning: false } }));
  },

  approveAction: async () => {
    const state = get();
    if (!state.sessionStore.proposedAction || !state.sessionStore.currentCase?.sessionId) return;
    try {
      await investigationApi.approveAction({
        session_id: state.sessionStore.currentCase.sessionId,
        action_id: state.sessionStore.proposedAction.id,
      });
    } catch (error) {
      console.error('[DiagnosisStore] Failed to approve action:', error);
    }
    wsService.approveAction(state.sessionStore.proposedAction.id);
    set((s) => ({
      sessionStore: {
        ...s.sessionStore,
        proposedAction: null,
        currentCase: s.sessionStore.currentCase ? { ...s.sessionStore.currentCase, status: 'resolved' } : null,
      },
    }));
  },

  rejectAction: async () => {
    const state = get();
    if (!state.sessionStore.proposedAction || !state.sessionStore.currentCase?.sessionId) return;
    try {
      await investigationApi.rejectAction({
        session_id: state.sessionStore.currentCase.sessionId,
        action_id: state.sessionStore.proposedAction.id,
        reason: 'User rejected',
      });
    } catch (error) {
      console.error('[DiagnosisStore] Failed to reject action:', error);
    }
    wsService.rejectAction(state.sessionStore.proposedAction.id, 'User rejected');
    set((s) => ({ sessionStore: { ...s.sessionStore, proposedAction: null } }));
  },

  respondToConfirmation: (confirmationId, response) => {
    const current = get().confirmationStore.pendingConfirmation;
    if (!current) return;

    wsService.respondToConfirmation(confirmationId, response);

    if (response.action === 'second_confirm') {
      set((state) => ({
        confirmationStore: {
          ...state.confirmationStore,
          confirmationFlowState: 'pending_r3',
          pendingConfirmation: { ...current, riskLevel: 'R3', message: `R3 二次确认：${current.message}` },
        },
      }));
      return;
    }

    if (response.action === 'reject' || response.action === 'cancel') {
      set((state) => ({
        confirmationStore: { ...state.confirmationStore, pendingConfirmation: null, confirmationFlowState: 'rejected' },
        sessionStore: { ...state.sessionStore, isRunning: false },
      }));
      return;
    }

    set((state) => ({ confirmationStore: { ...state.confirmationStore, pendingConfirmation: null } }));
  },

  selectAgent: (agentId) => set((state) => ({ traceStore: { ...state.traceStore, selectedAgentId: agentId } })),

  getTraceView: () => projectTraceView(get().traceStore),
}));

export function getChildAgents(traces: Map<string, AgentTrace>, parentId: string): AgentTrace[] {
  return Array.from(traces.values()).filter((trace) => trace.parentId === parentId);
}

export function getRootAgents(traces: Map<string, AgentTrace>): AgentTrace[] {
  return Array.from(traces.values()).filter((trace) => trace.parentId === null);
}
