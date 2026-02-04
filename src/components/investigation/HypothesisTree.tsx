import { HypothesisTree as HypothesisTreeType } from '../../types/investigation';
import { AlertCircle, Lightbulb, ChevronDown, ChevronRight } from 'lucide-react';
import { statusBadges } from '../../constants';
import { cn } from '../../lib/utils';

interface HypothesisTreeProps {
  data: HypothesisTreeType;
}

export default function HypothesisTree({ data }: HypothesisTreeProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    root: true,
  });

  const toggleExpand = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const renderNode = (node: any, level: number = 0) => {
    const isExpanded = expanded[node.id];
    const hasChildren = node.children && node.children.length > 0;
    const badge = statusBadges[node.status];

    return (
      <div key={node.id} className={cn(level > 0 && 'ml-6')}>
        <div
          className={cn(
            'flex items-start gap-2 p-3 rounded-lg mb-2',
            node.status === 'validated' && 'bg-semantic-success/5 border border-semantic-success/20',
            node.status === 'investigating' && 'bg-primary/5 border border-primary/20',
            node.status === 'rejected' && 'bg-semantic-danger/5 border border-semantic-danger/20',
            !node.status && 'bg-bg-surface/50'
          )}
        >
          {hasChildren && (
            <button
              onClick={() => toggleExpand(node.id)}
              className="mt-1 text-text-muted hover:text-text-main"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}

          <div className="flex-1">
            <div className="flex items-center gap-2">
              {node.type === 'symptom' && <AlertCircle className="w-4 h-4 text-semantic-warning" />}
              {node.type === 'solution' && <Lightbulb className="w-4 h-4 text-semantic-success" />}
              <span className="text-sm font-medium text-text-main">{node.label}</span>
              {node.probability !== undefined && (
                <span className="text-xs text-text-muted">
                  ({Math.round(node.probability * 100)}%)
                </span>
              )}
              {badge && (
                <span className={cn('text-xs px-2 py-0.5 rounded', badge.color)}>
                  {badge.label}
                </span>
              )}
            </div>
            {node.evidence && node.evidence.length > 0 && (
              <div className="mt-2 space-y-1">
                {node.evidence.map((e: string, i: number) => (
                  <div key={i} className="text-xs text-text-muted flex items-center gap-1">
                    <span className="text-semantic-success">*</span> {e}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l-2 border-border-subtle ml-2">
            {node.children.map((child: any) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-4 overflow-auto">
      {renderNode(data.root)}
    </div>
  );
}
