import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { AgentTrace, ExecutionStep } from '../../types/trace';

interface ExecutionTimelineProps {
  trace: AgentTrace | null;
}

export default function ExecutionTimeline({ trace }: ExecutionTimelineProps) {
  if (!trace) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted">
        <p>Select an agent to view execution details</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <MetricsPanel trace={trace} />
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {trace.steps.map((step) => (
          <StepItem key={step.id} step={step} />
        ))}
      </div>
    </div>
  );
}

function MetricsPanel({ trace }: { trace: AgentTrace }) {
  return (
    <div className="p-4 border-b border-border-subtle bg-bg-surface">
      <h3 className="text-sm font-semibold text-text-main mb-3">
        {trace.name} <span className="text-text-muted text-xs">({trace.id})</span>
      </h3>
      <div className="grid grid-cols-4 gap-3">
        <MetricCard label="状态" value={getStatusLabel(trace.status)} />
        <MetricCard label="总耗时" value={trace.duration ? formatDuration(trace.duration) : '-'} />
        <MetricCard label="Input Token" value={trace.totalTokens.input.toLocaleString()} />
        <MetricCard label="Output Token" value={trace.totalTokens.output.toLocaleString()} />
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-bg-elevated rounded p-2">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="text-sm font-medium text-text-main mt-1">{value}</div>
    </div>
  );
}

function StepItem({ step }: { step: ExecutionStep }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`border-l-4 rounded-r p-3 bg-bg-surface ${getStepBorderColor(step.type)}`}>
      <div className="flex items-start gap-2">
        <div className={`w-2 h-2 rounded-full mt-1.5 ${getStepColor(step.type)}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-text-muted">{formatTimestamp(step.timestamp)}</span>
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

          {step.type === 'llm_thinking' && (
            <>
              {step.content && (
                <div className="text-sm text-text-main mt-2 whitespace-pre-wrap">{step.content}</div>
              )}
              {step.tokens && (
                <div className="text-xs text-text-muted mt-2">
                  💰 Tokens: {step.tokens.input} in / {step.tokens.output} out
                  {step.cost && ` | Cost: $${step.cost.toFixed(4)}`}
                </div>
              )}
            </>
          )}

          {step.type === 'tool_call' && (
            <>
              <div className="text-sm text-text-main mt-2">
                <span className="text-text-muted">工具: </span>
                <span className="font-mono">{step.toolName}</span>
                {step.status && (
                  <span className={`ml-2 text-xs ${step.status === 'success' ? 'text-semantic-success' : 'text-semantic-danger'}`}>
                    {step.status === 'success' ? '✅ 成功' : '❌ 失败'}
                  </span>
                )}
              </div>
              {step.toolInput && (
                <CollapsibleSection
                  title="📤 参数"
                  content={JSON.stringify(step.toolInput, null, 2)}
                  expanded={expanded}
                  onToggle={() => setExpanded(!expanded)}
                />
              )}
              {step.toolOutput && (
                <CollapsibleSection
                  title="📥 结果"
                  content={typeof step.toolOutput === 'string' ? step.toolOutput : JSON.stringify(step.toolOutput, null, 2)}
                  expanded={expanded}
                  onToggle={() => setExpanded(!expanded)}
                />
              )}
            </>
          )}

          {step.type === 'agent_dispatch' && (
            <div className="text-sm text-text-main mt-2">
              <div>
                <span className="text-text-muted">目标: </span>
                {step.targetAgentName || step.targetAgentId}
              </div>
              {step.taskDescription && (
                <div className="mt-1">
                  <span className="text-text-muted">任务: </span>
                  {step.taskDescription}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CollapsibleSection({
  title,
  content,
  expanded,
  onToggle,
}: {
  title: string;
  content: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const preview = content.length > 100 ? content.substring(0, 100) + '...' : content;

  return (
    <div className="mt-2">
      <button
        onClick={onToggle}
        className="flex items-center gap-1 text-xs text-text-muted hover:text-text-main"
      >
        {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {title}
      </button>
      <pre className="bg-bg-deep p-2 rounded text-xs font-mono mt-1 overflow-x-auto">
        {expanded ? content : preview}
      </pre>
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

function getStatusLabel(status: string): string {
  switch (status) {
    case 'success':
      return '✅ Success';
    case 'failed':
      return '❌ Failed';
    case 'running':
      return '⏳ Running';
    default:
      return '⏸️ Pending';
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { hour12: false });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
