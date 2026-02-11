import { applyDiagnosisEvent } from '../diagnosisStore';
import type { DiagnosisEvent } from '../../contracts/diagnosisProtocol';

const base = {
  sessionStore: { currentCase: null, isRunning: true, proposedAction: null, wsConnected: false, currentAgentType: 'diagnosis', eventLedger: new Set<string>() },
  traceStore: {
    traces: new Map(),
    traceLifecycle: new Map(),
    selectedAgentId: null,
    rootAgentIds: [],
    replaySnapshot: null,
    eventLedger: new Set<string>(),
  },
  confirmationStore: { pendingConfirmation: null, confirmationFlowState: 'idle', eventLedger: new Set<string>() },
};

function apply(state: any, event: DiagnosisEvent) {
  return { ...state, ...applyDiagnosisEvent(state, event) };
}

export function runTraceStoreContractChecks() {
  const completeBeforeStart: DiagnosisEvent = { type: 'agent_trace_complete', timestamp: '2026-01-01T00:00:02Z', data: { agentId: 'agent-1' } };
  const state0 = apply(base, completeBeforeStart);
  if (state0.traceStore.traces.size !== 0) {
    throw new Error('trace contract: complete before start should be ignored');
  }

  const start: DiagnosisEvent = { type: 'agent_trace_start', timestamp: '2026-01-01T00:00:03Z', data: { agentId: 'agent-1', agentName: 'Coordinator' } };
  const step: DiagnosisEvent = { type: 'agent_trace_step', timestamp: '2026-01-01T00:00:04Z', data: { agentId: 'agent-1', stepId: 'step-1', type: 'llm_thinking' } };

  const state1 = apply(state0, start);
  const state2 = apply(state1, step);
  const state3 = apply(state2, step);

  if (state2.traceStore.traces.get('agent-1')?.steps.length !== 1) {
    throw new Error('trace contract: concurrent step apply failed');
  }
  if (state3.traceStore.traces.get('agent-1')?.steps.length !== 1) {
    throw new Error('trace contract: duplicate step should be idempotent');
  }
}
