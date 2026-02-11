import { applyDiagnosisEvent } from './diagnosisStore';
import type { DiagnosisEvent } from '../contracts/diagnosisProtocol';

const baseState = {
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
  pendingConfirmation: null,
  confirmationFlowState: 'idle',
  currentAgentType: 'diagnosis',
  traces: new Map(),
  traceLifecycle: new Map(),
  selectedAgentId: null,
  rootAgentIds: [],
  replaySnapshot: null,
} as const;

export function runDiagnosisStoreContractChecks(): void {
  const progressEvent: DiagnosisEvent = {
    type: 'diagnosis_progress',
    timestamp: new Date().toISOString(),
    data: { phase: 'confidence', confidence: 88 },
  };
  const progressPatch = applyDiagnosisEvent(baseState as never, progressEvent);
  if ((progressPatch.currentCase as { confidence: number }).confidence !== 88) {
    throw new Error('contract failed: diagnosis_progress confidence update');
  }

  const rejectedEvent: DiagnosisEvent = {
    type: 'confirmation_rejected',
    timestamp: new Date().toISOString(),
    data: { confirmationId: 'x', reason: 'risk' },
  };
  const rejectPatch = applyDiagnosisEvent(baseState as never, rejectedEvent);
  if (rejectPatch.isRunning !== false || rejectPatch.confirmationFlowState !== 'rejected') {
    throw new Error('contract failed: confirmation_rejected state transition');
  }
}
