export type AgentStatus = 'pending' | 'running' | 'success' | 'failed';

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

  // task_received fields
  input?: string;

  // llm_thinking fields
  content?: string;
  tokens?: {
    input: number;
    output: number;
  };
  cost?: number;

  // tool_call fields
  toolName?: string;
  toolInput?: any;
  toolOutput?: any;
  status?: 'success' | 'failed';

  // agent_dispatch fields
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
  totalTokens: {
    input: number;
    output: number;
  };
  steps: ExecutionStep[];
  error?: string;
}
