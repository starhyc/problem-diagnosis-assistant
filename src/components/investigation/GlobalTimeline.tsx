import { useMemo } from 'react';
import { AgentTrace, ExecutionStep } from '../../types/trace';

interface GlobalTimelineProps {
  traces: Map<string, AgentTrace>;
}

interface EnrichedStep extends ExecutionStep {
  agentId: string;
  agentName: string;
}

export default function GlobalTimeline({ traces }: GlobalTimelineProps) {
  const allSteps = useMemo(() => {
    const steps: EnrichedStep[] = [];
    traces.forEach((trace) => {
      trace.steps.forEach((step) => {
        steps.push({
          ...step,
          agentId: trace.id,
          agentName: trace.name,
        });
      });
    });
    return steps.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [traces]);

  if (allSteps.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted">
        <p>No execution steps yet</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3 overflow-auto">
      {allSteps.map((step) => (
        <StepItem key={`${step.agentId}-${step.id}`} step={step} />
      ))}
    </div>
  );
}

function StepItem({ step }: { step: EnrichedStep }) {
  return (
    <div className={`border-l-4 rounded-r p-3 bg-bg-surface ${getStepBorderColor(step.type)}`}>
      <div className="flex items-start gap-2">
        <div className={`w-2 h-2 rounded-full mt-1.5 ${getStepColor(step.type)}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-text-muted">{formatTimestamp(step.timestamp)}</span>
            <span className="text-xs font-mono text-text-muted">{step.agentName}</span>
            <span className="text-sm font-medium text-text-main">{getStepLabel(step)}</span>
            {step.duration !== undefined && (
              <span className="text-xs text-text-muted">⏱️ {formatDuration(step.duration)}</span>
            )}
          </div>

          {step.type === 'task_received' && step.input && (
            <div className="text-sm text-text-main mt-2">
              <span className="text-text-muted">输入: </span>
              {step.input}
            </div>
          )}

          {step.type === 'llm_thinking' && step.content && (
            <div className="text-sm text-text-main mt-2 whitespace-pre-wrap">{step.content}</div>
          )}

          {step.type === 'tool_call' && (
            <div className="text-sm text-text-main mt-2">
              <span className="text-text-muted">工具: </span>
              <span className="font-mono">{step.toolName}</span>
              {step.status && (
                <span className={`ml-2 text-xs ${step.status === 'success' ? 'text-semantic-success' : 'text-semantic-danger'}`}>
                  {step.status === 'success' ? '✅ 成功' : '❌ 失败'}
                </span>
              )}
            </div>
          )}

          {step.type === 'agent_dispatch' && (
            <div className="text-sm text-text-main mt-2">
              <span className="text-text-muted">目标: </span>
              {step.targetAgentName || step.targetAgentId}
              {step.taskDescription && (
                <span className="text-text-muted ml-2">任务: {step.taskDescription}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getStepLabel(step: ExecutionStep): string {
  switch (step.type) {
    case 'task_received':
      return '[接收任务]';
    case 'llm_thinking':
      return '[LLM 请求/思考]';
    case 'tool_call':
      return `[工具调用 - ${step.toolName}]`;
    case 'agent_dispatch':
      return '[调度子 Agent]';
    default:
      return '[未知步骤]';
  }
}

function getStepColor(type: string): string {
  switch (type) {
    case 'task_received':
      return 'bg-semantic-success';
    case 'llm_thinking':
      return 'bg-primary';
    case 'tool_call':
      return 'bg-agent-log';
    case 'agent_dispatch':
      return 'bg-agent-knowledge';
    default:
      return 'bg-text-muted';
  }
}

function getStepBorderColor(type: string): string {
  switch (type) {
    case 'task_received':
      return 'border-l-semantic-success';
    case 'llm_thinking':
      return 'border-l-primary';
    case 'tool_call':
      return 'border-l-agent-log';
    case 'agent_dispatch':
      return 'border-l-agent-knowledge';
    default:
      return 'border-l-text-muted';
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
