import { applyDiagnosisEvent } from './diagnosisStore';
import type { DiagnosisEvent } from '../contracts/diagnosisProtocol';

const baseState = {
  sessionStore: {
    currentCase: {
      id: 'c1',
      symptom: 'slow',
      description: 'slow api',
      status: 'investigating',
      leadAgent: 'diagnosis',
      confidence: 0,
      messages: [],
      timeline: [],
      createdAt: new Date().toISOString(),
    },
    isRunning: true,
    proposedAction: null,
    wsConnected: false,
    currentAgentType: 'diagnosis',
    eventLedger: new Set<string>(),
  },
  confirmationStore: {
    pendingConfirmation: null,
    confirmationFlowState: 'idle',
    eventLedger: new Set<string>(),
  },
  traceStore: {
    traces: new Map(),
    traceLifecycle: new Map(),
    selectedAgentId: null,
    rootAgentIds: [],
    replaySnapshot: null,
    eventLedger: new Set<string>(),
  },
} as const;

function apply(base: any, event: DiagnosisEvent) {
  return { ...base, ...applyDiagnosisEvent(base, event) };
}

export function runDiagnosisStoreContractChecks(): void {
  const progressEvent: DiagnosisEvent = {
    type: 'diagnosis_progress',
    timestamp: new Date().toISOString(),
    data: { phase: 'confidence', confidence: 88 },
  };
  const progressState = apply(baseState as never, progressEvent);
  if (progressState.sessionStore.currentCase.confidence !== 88) {
    throw new Error('contract failed: sessionStore confidence update');
  }

  const confirmationRequired: DiagnosisEvent = {
    type: 'confirmation_required',
    timestamp: new Date().toISOString(),
    data: { id: 'cf-1', riskLevel: 'R2', message: 'Confirm risk' },
  };
  const confirmationState = apply(baseState as never, confirmationRequired);
  const confirmationStateDup = apply(confirmationState, confirmationRequired);
  if (confirmationState.confirmationStore.confirmationFlowState !== 'pending_r2') {
    throw new Error('contract failed: confirmationStore risk transition');
  }
  if (confirmationStateDup.confirmationStore.eventLedger.size !== confirmationState.confirmationStore.eventLedger.size) {
    throw new Error('contract failed: confirmationStore idempotency');
  }

  const concurrentStart: DiagnosisEvent = {
    type: 'agent_trace_start',
    timestamp: new Date().toISOString(),
    data: { agentId: 'a-1', agentName: 'Coordinator' },
  };
  const concurrentStep: DiagnosisEvent = {
    type: 'agent_trace_step',
    timestamp: new Date().toISOString(),
    data: { agentId: 'a-1', stepId: 's-1', type: 'llm_thinking' },
  };
  const firstTraceState = apply(baseState as never, concurrentStart);
  const secondTraceState = apply(firstTraceState, concurrentStep);
  const thirdTraceState = apply(secondTraceState, concurrentStep);

  if (!secondTraceState.traceStore.traces.get('a-1')?.steps.length) {
    throw new Error('contract failed: traceStore concurrent step handling');
  }
  if (thirdTraceState.traceStore.traces.get('a-1')?.steps.length !== 1) {
    throw new Error('contract failed: traceStore duplicate step idempotency');
  }
}
