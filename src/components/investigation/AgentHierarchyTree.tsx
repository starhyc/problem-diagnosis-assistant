import { memo, useState } from 'react';
import { CheckCircle2, Circle, Loader2, XCircle, ChevronRight } from 'lucide-react';
import { AgentTrace, AgentStatus } from '../../types/trace';
import { getChildAgents } from '../../store/diagnosisStore';

interface AgentHierarchyTreeProps {
  traces: Map<string, AgentTrace>;
  rootAgentIds: string[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
}

export default function AgentHierarchyTree({
  traces,
  rootAgentIds,
  selectedAgentId,
  onSelectAgent,
}: AgentHierarchyTreeProps) {
  return (
    <div className="p-3 space-y-1">
      {rootAgentIds.map((rootId) => {
        const trace = traces.get(rootId);
        return trace ? (
          <AgentNode
            key={rootId}
            trace={trace}
            traces={traces}
            selectedAgentId={selectedAgentId}
            onSelectAgent={onSelectAgent}
            level={0}
          />
        ) : null;
      })}
    </div>
  );
}

interface AgentNodeProps {
  trace: AgentTrace;
  traces: Map<string, AgentTrace>;
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  level: number;
}

const AgentNode = memo(({ trace, traces, selectedAgentId, onSelectAgent, level }: AgentNodeProps) => {
  const [collapsed, setCollapsed] = useState(level >= 2);
  const children = getChildAgents(traces, trace.id);
  const isSelected = selectedAgentId === trace.id;

  return (
    <div>
      <div
        className={`px-2 py-1.5 rounded cursor-pointer hover:bg-bg-elevated transition-colors ${
          isSelected ? 'bg-bg-elevated' : ''
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={() => onSelectAgent(trace.id)}
      >
        <div className="flex items-center gap-2">
          {children.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setCollapsed(!collapsed);
              }}
              className="p-0.5 hover:bg-bg-elevated rounded"
            >
              <ChevronRight className={`w-3 h-3 text-text-muted transition-transform ${collapsed ? '' : 'rotate-90'}`} />
            </button>
          )}
          <StatusIcon status={trace.status} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-main">{trace.name}</span>
              {trace.duration !== undefined && (
                <span className="text-xs text-text-muted">{formatDuration(trace.duration)}</span>
              )}
              {isSelected && <CheckCircle2 className="w-4 h-4 text-primary" />}
            </div>
            <div className="text-xs text-text-muted font-mono">{trace.id.substring(0, 8)}</div>
            {trace.taskDescription && (
              <div className="text-xs text-text-muted mt-1 line-clamp-2">{trace.taskDescription}</div>
            )}
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-text-muted">
                ↑{trace.totalTokens.input.toLocaleString()} ↓{trace.totalTokens.output.toLocaleString()}
              </span>
              {trace.subtasks && (
                <span className="text-xs text-text-muted">
                  {trace.subtasks.completed}/{trace.subtasks.total} subtasks
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      {!collapsed && children.map((child) => (
        <AgentNode
          key={child.id}
          trace={child}
          traces={traces}
          selectedAgentId={selectedAgentId}
          onSelectAgent={onSelectAgent}
          level={level + 1}
        />
      ))}
    </div>
  );
}, (prev, next) => {
  return prev.trace.status === next.trace.status &&
         prev.trace.duration === next.trace.duration &&
         prev.selectedAgentId === next.selectedAgentId;
});

AgentNode.displayName = 'AgentNode';

function StatusIcon({ status }: { status: AgentStatus }) {
  switch (status) {
    case 'running':
      return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
    case 'success':
      return <CheckCircle2 className="w-4 h-4 text-semantic-success" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-semantic-danger" />;
    default:
      return <Circle className="w-4 h-4 text-text-muted" />;
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
