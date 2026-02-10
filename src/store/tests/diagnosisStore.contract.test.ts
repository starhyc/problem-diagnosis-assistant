import assert from 'node:assert/strict';
import { useDiagnosisStore } from '../diagnosisStore.js';
import { investigationApi } from '../../lib/api.js';
import { wsService } from '../../lib/websocket.js';

async function run() {
  const startCalls: any[] = [];
  const stopCalls: any[] = [];
  const approveCalls: any[] = [];
  const rejectCalls: any[] = [];

  investigationApi.startDiagnosis = async () => ({ session_id: 'session-1', task_id: 'task-1' });
  investigationApi.stopDiagnosis = async (payload) => {
    stopCalls.push(payload);
    return { status: 'stopped' };
  };
  investigationApi.approveAction = async (payload) => {
    approveCalls.push(payload);
    return { status: 'approved' };
  };
  investigationApi.rejectAction = async (payload) => {
    rejectCalls.push(payload);
    return { status: 'rejected' };
  };

  wsService.startDiagnosis = (...args: any[]) => {
    startCalls.push(args);
  };
  wsService.stopDiagnosis = () => undefined;
  wsService.approveAction = () => undefined;
  wsService.rejectAction = () => undefined;

  await useDiagnosisStore.getState().startDiagnosis('diagnosis', 'symptom', 'desc', 'auto');
  const stateAfterStart = useDiagnosisStore.getState();
  assert.equal(stateAfterStart.currentCase?.sessionId, 'session-1');

  await useDiagnosisStore.getState().stopDiagnosis();
  assert.deepEqual(stopCalls[0], { session_id: 'session-1' });

  useDiagnosisStore.setState({
    currentCase: {
      ...(useDiagnosisStore.getState().currentCase as any),
      sessionId: 'session-1',
    },
    proposedAction: {
      id: 'action-1',
      title: 't',
      confidence: 90,
    },
  });

  await useDiagnosisStore.getState().approveAction();
  assert.deepEqual(approveCalls[0], { session_id: 'session-1', action_id: 'action-1' });

  useDiagnosisStore.setState({
    proposedAction: {
      id: 'action-2',
      title: 't2',
      confidence: 80,
    },
  });
  await useDiagnosisStore.getState().rejectAction();
  assert.deepEqual(rejectCalls[0], {
    session_id: 'session-1',
    action_id: 'action-2',
    reason: 'User rejected',
  });

  assert.ok(startCalls.length > 0);
}

run();
