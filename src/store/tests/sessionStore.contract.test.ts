import { applyDiagnosisEvent } from '../diagnosisStore';
import type { DiagnosisEvent } from '../../contracts/diagnosisProtocol';

const base = {
  sessionStore: {
    currentCase: {
      id: 'case-1',
      symptom: 'latency',
      description: 'high latency',
      status: 'investigating',
      leadAgent: 'diagnosis',
      confidence: 10,
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
  traceStore: {
    traces: new Map(),
    traceLifecycle: new Map(),
    selectedAgentId: null,
    rootAgentIds: [],
    replaySnapshot: null,
    eventLedger: new Set<string>(),
  },
  confirmationStore: {
    pendingConfirmation: null,
    confirmationFlowState: 'idle',
    eventLedger: new Set<string>(),
  },
};

function reduce(event: DiagnosisEvent) {
  return { ...base, ...applyDiagnosisEvent(base as never, event) };
}

export function runSessionStoreContractChecks() {
  const confidence = reduce({ type: 'diagnosis_progress', timestamp: '2026-01-01T00:00:00Z', data: { phase: 'confidence', confidence: 61 } });
  if (confidence.sessionStore.currentCase?.confidence !== 61) {
    throw new Error('session contract: confidence event failed');
  }

  const message: DiagnosisEvent = {
    type: 'agent_message',
    timestamp: '2026-01-01T00:00:01Z',
    data: { id: 'msg-1', agent: 'A1', timestamp: '2026-01-01T00:00:01Z', content: 'start', type: 'info' },
  };
  const afterOnce = { ...base, ...applyDiagnosisEvent(base as never, message) };
  const afterDup = { ...afterOnce, ...applyDiagnosisEvent(afterOnce as never, message) };

  if (afterDup.sessionStore.currentCase?.messages.length !== 1) {
    throw new Error('session contract: duplicate message should be idempotent');
  }
}
