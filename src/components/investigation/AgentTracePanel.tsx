import { useMemo } from 'react';
import { useDiagnosisStore } from '../../store/diagnosisStore';
import AgentHierarchyTree from './AgentHierarchyTree';
import ExecutionTimeline from './ExecutionTimeline';

export default function AgentTracePanel() {
  const { traces, rootAgentIds, selectedAgentId, selectAgent, isRunning, replaySnapshot } = useDiagnosisStore();

  const selectedTrace = selectedAgentId ? traces.get(selectedAgentId) : null;

  const summary = useMemo(() => {
    let totalDuration = 0;
    let totalCost = 0;
    const models = new Map<string, number>();

    traces.forEach((trace) => {
      totalDuration += trace.duration || trace.latency || 0;
      totalCost += trace.costEstimate || 0;
      if (trace.model) {
        models.set(trace.model, (models.get(trace.model) || 0) + 1);
      }
    });

    return {
      totalDuration,
      totalCost,
      modelStats: Array.from(models.entries()).map(([model, count]) => ({ model, count })),
    };
  }, [traces]);

  if (traces.size === 0 && !isRunning) {
    return (
      <div className="h-full flex items-center justify-center text-text-muted">
        <div className="text-center">
          <p>No agent traces yet</p>
          <p className="text-sm mt-2">Start a diagnosis to see agent execution</p>
        </div>
      </div>
    );
  }

  if (traces.size === 0 && isRunning) {
    return (
      <div className="h-full flex items-center justify-center text-text-muted">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span>Waiting for agent traces...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b border-border-subtle bg-bg-surface/50">
        <h3 className="text-sm font-semibold text-text-main">Trace 统计</h3>
        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
          <div className="bg-bg-elevated rounded p-2">
            <div className="text-text-muted">总耗时</div>
            <div className="text-text-main font-semibold">{formatDuration(summary.totalDuration)}</div>
          </div>
          <div className="bg-bg-elevated rounded p-2">
            <div className="text-text-muted">费用估算</div>
            <div className="text-text-main font-semibold">${summary.totalCost.toFixed(4)}</div>
          </div>
        </div>
        {summary.modelStats.length > 0 && (
          <div className="mt-2 text-xs text-text-muted">
            模型: {summary.modelStats.map((m) => `${m.model}(${m.count})`).join(' · ')}
          </div>
        )}
        {replaySnapshot && (
          <div className="mt-2 text-xs text-semantic-success">已生成复盘快照 {new Date(replaySnapshot.snapshotAt).toLocaleTimeString()}</div>
        )}
      </div>
      <div className="h-full flex">
        <div className="w-64 border-r border-border-subtle overflow-auto bg-bg-surface/50">
          <div className="p-3 border-b border-border-subtle">
            <h3 className="text-sm font-semibold text-text-main">Agent 层级树</h3>
          </div>
          <AgentHierarchyTree
            traces={traces}
            rootAgentIds={rootAgentIds}
            selectedAgentId={selectedAgentId}
            onSelectAgent={selectAgent}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <ExecutionTimeline trace={selectedTrace} />
        </div>
      </div>
    </div>
  );
}

function formatDuration(ms: number): string {
  if (!ms) return '0ms';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}
