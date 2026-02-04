import { CheckCircle, XCircle, Plus, Trash2, Save } from 'lucide-react';
import { Card, Button } from '../common';
import { cn } from '../../lib/utils';
import { MaskingRule } from '../../types/settings';

interface MaskingRulesProps {
  rules: MaskingRule[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function MaskingRules({ rules, onToggle, onDelete }: MaskingRulesProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">脱敏规则</h3>
      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="flex items-center justify-between p-4 bg-bg-elevated/30 rounded-lg"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={cn(
                    'p-2 rounded-lg',
                    rule.enabled ? 'bg-semantic-success' : 'bg-bg-elevated'
                  )}
                >
                  {rule.enabled ? (
                    <CheckCircle className="w-5 h-5 text-white" />
                  ) : (
                    <XCircle className="w-5 h-5 text-text-muted" />
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-text-main">{rule.name}</h4>
                  <p className="text-xs text-text-muted">{rule.pattern}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => onToggle(rule.id)}
                  variant="secondary"
                  icon={<Save className="w-4 h-4" />}
                >
                  {rule.enabled ? '禁用' : '启用'}
                </Button>
                <button className="p-2 bg-semantic-danger/10 hover:bg-semantic-danger/20 text-semantic-danger rounded-lg transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <button className="w-full flex items-center justify-center gap-2 p-3 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors">
        <Plus className="w-4 h-4" />
        添加脱敏规则
      </button>
    </Card>
  );
}
