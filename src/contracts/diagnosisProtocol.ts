export const diagnosisEventTypes = [
  'connection_established',
  'diagnosis_started',
  'diagnosis_progress',
  'confirmation_required',
  'confirmation_rejected',
  'confirmation_status',
  'diagnosis_completed',
  'diagnosis_failed',
  'heartbeat',
  'replay_snapshot',
  'error',
  'agent_message',
  'action_proposal',
  'diagnosis_status',
  'timeline_update',
  'confidence_update',
  'agent_trace_start',
  'agent_trace_step',
  'agent_trace_complete',
] as const;

export type DiagnosisEventType = (typeof diagnosisEventTypes)[number];

export interface EventEnvelope<TType extends DiagnosisEventType, TData = Record<string, unknown>> {
  type: TType;
  timestamp: string;
  data?: TData;
}

export interface DiagnosisProgressData {
  session_id?: string;
  phase: 'timeline' | 'confidence' | 'trace' | 'workflow' | 'status';
  progress?: number;
  confidence?: number;
  timeline?: unknown[];
  payload?: Record<string, unknown>;
}

export interface ConfirmationRequiredData {
  id: string;
  actionId: string;
  message: string;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical' | 'R1' | 'R2' | 'R3';
  [key: string]: unknown;
}

export type DiagnosisEvent = EventEnvelope<DiagnosisEventType, Record<string, unknown>>;

export function isDiagnosisEventType(value: unknown): value is DiagnosisEventType {
  return typeof value === 'string' && (diagnosisEventTypes as readonly string[]).includes(value);
}

export function parseDiagnosisEvent(raw: unknown): DiagnosisEvent | null {
  if (!raw || typeof raw !== 'object') return null;
  const candidate = raw as Record<string, unknown>;
  if (!isDiagnosisEventType(candidate.type)) return null;
  if (typeof candidate.timestamp !== 'string') return null;

  const data = candidate.data;
  if (data !== undefined && (typeof data !== 'object' || data === null || Array.isArray(data))) {
    return null;
  }

  return {
    type: candidate.type,
    timestamp: candidate.timestamp,
    data: (data as Record<string, unknown> | undefined) ?? {},
  };
}
