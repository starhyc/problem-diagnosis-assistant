import { Shield, Eye, EyeOff, CheckCircle, XCircle, Plus, Trash2, Save } from 'lucide-react';
import { Card } from '../common';
import { cn } from '../../lib/utils';
import { Redline } from '../../types/settings';

interface RedlineListProps {
  redlines: Redline[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function RedlineList({ redlines, onToggle, onDelete }: RedlineListProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">红线规则</h3>
      <div className="space-y-3">
        {redlines.map((redline) => (
          <div
            key={redline.id}
            className="flex items-center justify-between p-4 bg-bg-elevated/30 rounded-lg"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Shield
                  className={cn(
                    'w-5 h-5',
                    redline.enabled ? 'text-semantic-success' : 'text-text-muted'
                  )}
                />
                <h4 className="text-sm font-medium text-text-main">{redline.name}</h4>
              </div>
              <p className="text-xs text-text-muted">{redline.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onToggle(redline.id)}
                className={cn(
                  'p-2 rounded-lg transition-colors',
                  redline.enabled
                    ? 'bg-semantic-success hover:bg-semantic-success/80 text-white'
                    : 'bg-bg-elevated hover:bg-bg-elevated/70 text-text-main'
                )}
              >
                {redline.enabled ? (
                  <Eye className="w-4 h-4" />
                ) : (
                  <EyeOff className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={() => onDelete(redline.id)}
                className="p-2 bg-semantic-danger/10 hover:bg-semantic-danger/20 text-semantic-danger rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
      <button className="w-full flex items-center justify-center gap-2 p-3 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors">
        <Plus className="w-4 h-4" />
        添加红线规则
      </button>
    </Card>
  );
}
