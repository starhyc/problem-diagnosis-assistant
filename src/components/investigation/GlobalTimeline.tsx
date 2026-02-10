import { useMemo } from 'react';
import { AgentTrace, ExecutionStep } from '../../types/trace';

interface GlobalTimelineProps {
  traces: Map<string, AgentTrace>;
}

interface EnrichedStep extends ExecutionStep {
  agentId: string;
  agentName: string;
  parentId: string | null;
}

export default function GlobalTimeline({ traces }: GlobalTimelineProps) {
  const { allSteps, phaseStats, modelStats, totalCost } = useMemo(() => {
    const steps: EnrichedStep[] = [];
    const phaseMap = new Map<string, number>();
    const modelMap = new Map<string, { count: number; cost: number }>();
    let cost = 0;

    traces.forEach((trace) => {
      const phase = inferPhase(trace);
      phaseMap.set(phase, (phaseMap.get(phase) || 0) + (trace.duration || trace.latency || 0));
      cost += trace.costEstimate || 0;

      if (trace.model) {
        modelMap.set(trace.model, {
          count: (modelMap.get(trace.model)?.count || 0) + 1,
          cost: (modelMap.get(trace.model)?.cost || 0) + (trace.costEstimate || 0),
        });
      }

      trace.steps.forEach((step) => {
        steps.push({
          ...step,
          agentId: trace.id,
          agentName: trace.name,
          parentId: trace.parentId,
        });
      });
    });

    return {
      allSteps: steps.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
      phaseStats: Array.from(phaseMap.entries()),
      modelStats: Array.from(modelMap.entries()),
      totalCost: cost,
    };
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
      <div className="bg-bg-surface rounded p-3 border border-border-subtle text-xs">
        <div className="text-text-main font-semibold mb-2">阶段耗时 / 模型成本</div>
        <div className="text-text-muted">阶段: {phaseStats.map(([phase, ms]) => `${phase} ${formatDuration(ms)}`).join(' · ')}</div>
        <div className="text-text-muted mt-1">模型: {modelStats.map(([model, s]) => `${model}(${s.count}) $${s.cost.toFixed(4)}`).join(' · ')}</div>
        <div className="text-text-muted mt-1">总费用: ${totalCost.toFixed(4)}</div>
      </div>
      {allSteps.map((step) => (
        <StepItem key={`${step.agentId}-${step.id}`} step={step} />
      ))}
    </div>
  );
}

function StepItem({ step }: { step: EnrichedStep }) {
  const depthClass = step.parentId ? 'ml-6' : '';
  return (
    <div className={`${depthClass} border-l-4 rounded-r p-3 bg-bg-surface ${getStepBorderColor(step.type)}`}>
      <div className="flex items-start gap-2">
        <div className={`w-2 h-2 rounded-full mt-1.5 ${getStepColor(step.type)}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs text-text-muted">{formatTimestamp(step.timestamp)}</span>
            <span className="text-xs font-mono text-text-muted">{step.agentName}</span>
            <span className="text-sm font-medium text-text-main">{getStepLabel(step)}</span>
            {step.model && <span className="text-xs text-text-muted">{step.model}</span>}
            {step.costEstimate !== undefined && <span className="text-xs text-text-muted">${step.costEstimate.toFixed(4)}</span>}
            {step.duration !== undefined && <span className="text-xs text-text-muted">⏱️ {formatDuration(step.duration)}</span>}
          </div>
          {step.content && <div className="text-sm text-text-main mt-1 whitespace-pre-wrap">{step.content}</div>}
          {step.toolCall && <div className="text-xs text-text-muted mt-1">toolCall: {step.toolCall}</div>}
        </div>
      </div>
    </div>
  );
}

function inferPhase(trace: AgentTrace): string {
  if (trace.taskDescription?.includes('final')) return 'finalize';
  if (trace.taskDescription?.includes('Synthesize')) return 'synthesis';
  if (trace.taskDescription?.includes('Find similar')) return 'knowledge';
  return 'analysis';
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
