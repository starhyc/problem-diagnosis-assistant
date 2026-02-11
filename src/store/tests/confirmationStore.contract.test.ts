import { applyDiagnosisEvent } from '../diagnosisStore';
import type { DiagnosisEvent } from '../../contracts/diagnosisProtocol';

const base = {
  sessionStore: { currentCase: null, isRunning: true, proposedAction: null, wsConnected: false, currentAgentType: 'diagnosis', eventLedger: new Set<string>() },
  traceStore: { traces: new Map(), traceLifecycle: new Map(), selectedAgentId: null, rootAgentIds: [], replaySnapshot: null, eventLedger: new Set<string>() },
  confirmationStore: { pendingConfirmation: null, confirmationFlowState: 'idle', eventLedger: new Set<string>() },
};

function apply(state: any, event: DiagnosisEvent) {
  return { ...state, ...applyDiagnosisEvent(state, event) };
}

export function runConfirmationStoreContractChecks() {
  const required: DiagnosisEvent = {
    type: 'confirmation_required',
    timestamp: '2026-01-01T00:00:05Z',
    data: { id: 'confirm-1', riskLevel: 'R2', message: '危险操作确认' },
  };
  const status: DiagnosisEvent = {
    type: 'confirmation_status',
    timestamp: '2026-01-01T00:00:06Z',
    data: { action: 'second_confirm', status: 'pending' },
  };

  const state1 = apply(base, required);
  const state2 = apply(state1, status);
  const state3 = apply(state2, required);

  if (state2.confirmationStore.confirmationFlowState !== 'pending_r3') {
    throw new Error('confirmation contract: second confirm transition failed');
  }
  if (state3.confirmationStore.eventLedger.size !== state2.confirmationStore.eventLedger.size) {
    throw new Error('confirmation contract: duplicate confirmation_required should be idempotent');
  }
}
