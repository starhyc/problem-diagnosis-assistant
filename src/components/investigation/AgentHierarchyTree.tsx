import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
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

function AgentNode({ trace, traces, selectedAgentId, onSelectAgent, level }: AgentNodeProps) {
  const children = getChildAgents(traces, trace.id);
  const isSelected = selectedAgentId === trace.id;

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-bg-elevated transition-colors ${
          isSelected ? 'bg-bg-elevated' : ''
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={() => onSelectAgent(trace.id)}
      >
        <StatusIcon status={trace.status} />
        <span className="text-sm text-text-main flex-1">{trace.name}</span>
        {trace.duration !== undefined && (
          <span className="text-xs text-text-muted">{formatDuration(trace.duration)}</span>
        )}
        {isSelected && <CheckCircle2 className="w-4 h-4 text-primary" />}
      </div>
      {children.map((child) => (
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
}

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
