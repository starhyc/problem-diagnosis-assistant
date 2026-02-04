import { useDiagnosisStore } from '../../store/diagnosisStore';
import AgentHierarchyTree from './AgentHierarchyTree';
import ExecutionTimeline from './ExecutionTimeline';

export default function AgentTracePanel() {
  const { traces, rootAgentIds, selectedAgentId, selectAgent, isRunning } = useDiagnosisStore();

  const selectedTrace = selectedAgentId ? traces.get(selectedAgentId) : null;

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
    <div className="h-full flex">
      <div className="w-64 border-r border-border-subtle overflow-auto bg-bg-surface/50">
        <div className="p-3 border-b border-border-subtle">
          <h3 className="text-sm font-semibold text-text-main">Agent 导航</h3>
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
  );
}
