import { Server, GitBranch, Cloud, Database } from 'lucide-react';
import { Card } from '../common';
import { healthColors } from '../../constants';
import { SystemHealth } from '../../types/dashboard';
import { cn } from '../../lib/utils';

interface SystemHealthCardProps {
  health: SystemHealth;
}

export default function SystemHealthCard({ health }: SystemHealthCardProps) {
  const icons = {
    elk: Server,
    gitlab: GitBranch,
    k8s: Cloud,
    neo4j: Database,
    milvus: Database,
  };

  const Icon = icons[health.name as keyof typeof icons] || Server;

  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'p-2 rounded-lg',
            healthColors[health.status]
          )}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-medium text-text-main">{health.name}</h4>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={cn(
                'text-xs px-2 py-1 rounded',
                healthColors[health.status]
              )}
            >
              {health.status.toUpperCase()}
            </span>
            <span className="text-xs text-text-muted">延迟: {health.latency}</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
