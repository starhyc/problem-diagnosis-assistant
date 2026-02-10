export type AgentStatus = 'pending' | 'running' | 'success' | 'failed' | 'error';

export type StepType = 'task_received' | 'llm_thinking' | 'tool_call' | 'agent_dispatch';

export interface TraceMetrics {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cost?: number;
}

export interface ExecutionStep {
  id: string;
  type: StepType;
  timestamp: string;
  duration?: number;
  parentId?: string | null;
  model?: string;
  costEstimate?: number;

  input?: string;
  content?: string;
  tokens?: {
    input: number;
    output: number;
  };
  cost?: number;

  toolName?: string;
  toolCall?: string | null;
  toolInput?: any;
  toolOutput?: any;
  status?: 'success' | 'failed';

  targetAgentId?: string;
  targetAgentName?: string;
  taskDescription?: string;
}

export interface AgentTrace {
  id: string;
  name: string;
  parentId: string | null;
  status: AgentStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  latency?: number;
  model?: string;
  costEstimate?: number;
  totalTokens: {
    input: number;
    output: number;
  };
  steps: ExecutionStep[];
  error?: string;
  taskDescription?: string;
  subtasks?: { completed: number; total: number };
}

export interface TraceReplaySnapshot {
  snapshotAt: string;
  caseId?: string;
  traces: AgentTrace[];
  rootAgentIds: string[];
}
