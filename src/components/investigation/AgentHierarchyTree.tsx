import { useState } from 'react';
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

function AgentNode({ trace, traces, selectedAgentId, onSelectAgent, level }: AgentNodeProps) {
  const [collapsed, setCollapsed] = useState(
    trace.status === 'running' ? false : level >= 2
  );
  const children = getChildAgents(traces, trace.id);
  const isSelected = selectedAgentId === trace.id;

  return (
    <div>
      <div
        className={`rounded transition-colors ${
          isSelected ? 'bg-bg-elevated' : ''
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        <div className="flex items-start gap-1 px-2 py-1.5">
          {children.length > 0 ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setCollapsed(!collapsed);
              }}
              className="p-1 hover:bg-bg-elevated rounded flex-shrink-0"
            >
              <ChevronRight className={`w-3 h-3 text-text-muted transition-transform ${collapsed ? '' : 'rotate-90'}`} />
            </button>
          ) : (
            <div className="w-5" />
          )}
          <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onSelectAgent(trace.id)}>
            <div className="flex items-center gap-2 mb-1">
              <StatusIcon status={trace.status} />
              <span className="text-sm font-medium text-text-main">{trace.name}</span>
              {isSelected && <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0" />}
            </div>
            <div className="text-xs text-text-muted font-mono mb-1">{trace.id.substring(0, 8)}</div>
            <div className="text-xs text-text-muted mb-1">
              {getStatusLabel(trace.status)}
              {trace.duration !== undefined && ` • ${formatDuration(trace.duration)}`}
            </div>
            {trace.taskDescription && (
              <div className="text-xs text-text-muted mb-1 line-clamp-2">{trace.taskDescription}</div>
            )}
            <div className="text-xs text-text-muted">
              Tokens: ↑{trace.totalTokens.input.toLocaleString()} ↓{trace.totalTokens.output.toLocaleString()}
            </div>
            {trace.subtasks && (
              <div className="text-xs text-text-muted">
                {trace.subtasks.completed}/{trace.subtasks.total} subtasks
              </div>
            )}
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

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
