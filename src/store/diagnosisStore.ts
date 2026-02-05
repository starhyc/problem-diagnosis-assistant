import { create } from 'zustand';
import { investigationApi } from '../lib/api';
import { wsService, WSMessage, ConfirmationRequired } from '../lib/websocket';
import { AgentTrace } from '../types/trace';

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



interface DiagnosisState {
  currentCase: DiagnosisCase | null;
  isRunning: boolean;
  proposedAction: { title: string; confidence: number } | null;
  wsConnected: boolean;
  pendingConfirmation: ConfirmationRequired | null;
  currentAgentType: string;

  // Trace state
  traces: Map<string, AgentTrace>;
  selectedAgentId: string | null;
  rootAgentIds: string[];

  startDiagnosis: (agentType: string, symptom: string, description: string) => void;
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

export const useDiagnosisStore = create<DiagnosisState>((set, get) => ({
  currentCase: null,
  isRunning: false,
  proposedAction: null,
  wsConnected: false,
  pendingConfirmation: null,
  currentAgentType: 'diagnosis',
  traces: new Map(),
  selectedAgentId: null,
  rootAgentIds: [],

  initializeWebSocket: () => {
    if (wsUnsubscribe) return;

    wsService.connect().then(() => {
      console.log('[DiagnosisStore] WebSocket connected');
    }).catch((error) => {
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
          set({
            proposedAction: {
              title: proposal.title,
              confidence: proposal.confidence,
            },
          });
          break;
        }

        case 'diagnosis_status': {
          const status = message.data;
          set({
            isRunning: status.status === 'running',
            currentCase: state.currentCase
              ? {
                  ...state.currentCase,
                  status: status.status as any,
                }
              : null,
          });
          break;
        }

        case 'timeline_update': {
          const timelineData = message.data;
          set((s) => ({
            currentCase: s.currentCase
              ? {
                  ...s.currentCase,
                  timeline: timelineData.timeline,
                }
              : null,
          }));
          break;
        }

        case 'confidence_update': {
          const confidenceData = message.data;
          set((s) => ({
            currentCase: s.currentCase
              ? {
                  ...s.currentCase,
                  confidence: confidenceData.confidence,
                }
              : null,
          }));
          break;
        }

        case 'confirmation_required': {
          const confirmation = message.data as ConfirmationRequired;
          set({ pendingConfirmation: confirmation });
          break;
        }

        case 'error': {
          console.error('[DiagnosisStore] Error from server:', message.data);
          set({ isRunning: false });
          break;
        }

        case 'agent_trace_start': {
          const traceData = message.data;
          const newTrace: AgentTrace = {
            id: traceData.agentId,
            name: traceData.agentName,
            parentId: traceData.parentId || null,
            status: 'running',
            startTime: traceData.startTime,
            totalTokens: { input: 0, output: 0 },
            steps: [],
          };

          set((s) => {
            const newTraces = new Map(s.traces);
            newTraces.set(traceData.agentId, newTrace);

            const newRootIds = traceData.parentId
              ? s.rootAgentIds
              : [...s.rootAgentIds, traceData.agentId];

            return {
              traces: newTraces,
              rootAgentIds: newRootIds,
              selectedAgentId: s.selectedAgentId || traceData.agentId,
            };
          });
          break;
        }

        case 'agent_trace_step': {
          const stepData = message.data;
          // Map backend field names to frontend types
          const mappedStep = {
            ...stepData,
            id: stepData.id || stepData.stepId,
            type: stepData.type || stepData.stepType,
          };
          delete mappedStep.stepId;
          delete mappedStep.stepType;

          set((s) => {
            const trace = s.traces.get(stepData.agentId);
            if (!trace) return s;

            const newTraces = new Map(s.traces);
            newTraces.set(stepData.agentId, {
              ...trace,
              steps: [...trace.steps, mappedStep],
            });

            return { traces: newTraces };
          });
          break;
        }

        case 'agent_trace_complete': {
          const completeData = message.data;
          set((s) => {
            const trace = s.traces.get(completeData.agentId);
            if (!trace) return s;

            const newTraces = new Map(s.traces);
            newTraces.set(completeData.agentId, {
              ...trace,
              status: completeData.status,
              endTime: completeData.endTime,
              duration: completeData.duration,
              totalTokens: completeData.totalTokens,
              error: completeData.error,
            });

            return { traces: newTraces };
          });
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

  startDiagnosis: async (agentType: string, symptom: string, description: string) => {
    try {
      await investigationApi.startDiagnosis(agentType, symptom, description);

      const caseId = `CASE-${agentType.toUpperCase()}-${Date.now()}`;

      const newCase: DiagnosisCase = {
        id: caseId,
        symptom,
        description,
        status: 'investigating',
        leadAgent: agentType,
        confidence: 0,
        messages: [],
        timeline: [],
        createdAt: new Date().toISOString(),
      };

      set({
        currentCase: newCase,
        isRunning: true,
        proposedAction: null,
        currentAgentType: agentType,
        traces: new Map(),
        rootAgentIds: [],
        selectedAgentId: null,
        pendingConfirmation: null,
      });

      wsService.startDiagnosis(symptom, description, agentType);
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
    if (state.proposedAction) {
      wsService.approveAction('current-action');
      set((s) => ({
        proposedAction: null,
        currentCase: s.currentCase ? { ...s.currentCase, status: 'resolved' } : null,
      }));
    }
  },

  rejectAction: () => {
    const state = get();
    if (state.proposedAction) {
      wsService.rejectAction('current-action', 'User rejected');
      set({ proposedAction: null });
    }
  },

  respondToConfirmation: (confirmationId: string, response: any) => {
    wsService.respondToConfirmation(confirmationId, response);
    set({ pendingConfirmation: null });
  },

  selectAgent: (agentId: string | null) => {
    set({ selectedAgentId: agentId });
  },
}));

// Helper functions to build agent hierarchy
export function getChildAgents(traces: Map<string, AgentTrace>, parentId: string): AgentTrace[] {
  return Array.from(traces.values()).filter(trace => trace.parentId === parentId);
}

export function getRootAgents(traces: Map<string, AgentTrace>): AgentTrace[] {
  return Array.from(traces.values()).filter(trace => trace.parentId === null);
}
