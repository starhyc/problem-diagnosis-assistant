import { AgentTypeInfo, AgentType, ModelInfo, MODEL_TYPES } from '../../types/agent';
import { ChevronDown, Brain } from 'lucide-react';
import { cn } from '../../lib/utils';

interface AgentTypeSelectorProps {
  types: AgentTypeInfo[];
  selectedType: AgentType;
  onTypeChange: (type: AgentType) => void;
  selectedModel?: string;
  onModelChange?: (model: string) => void;
  disabled?: boolean;
}

export default function AgentTypeSelector({
  types,
  selectedType,
  onTypeChange,
  selectedModel = 'gpt-4',
  onModelChange,
  disabled = false,
}: AgentTypeSelectorProps) {
  const selectedAgent = types.find(t => t.id === selectedType);
  const selectedModelInfo = MODEL_TYPES.find(m => m.id === selectedModel);

  return (
    <div className="p-4 border-b border-border-subtle space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-text-main mb-3">选择Agent类型</h3>
        <div className="relative">
          <select
            value={selectedType}
            onChange={(e) => onTypeChange(e.target.value as AgentType)}
            disabled={disabled}
            className={cn(
              'w-full appearance-none bg-bg-surface border border-border-subtle',
              'rounded-lg px-4 py-3 pr-10 text-sm text-text-main',
              'shadow-sm hover:border-border-subtle/70',
              'focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20',
              'transition-all duration-200',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-border-subtle'
            )}
          >
            {types.map((type) => (
              <option key={type.id} value={type.id}>
                {type.name} - {type.description}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted/70 pointer-events-none" />
        </div>
      </div>

      {onModelChange && (
        <div>
          <h3 className="text-sm font-semibold text-text-main mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" />
            选择大模型
          </h3>
          <div className="relative">
            <select
              value={selectedModel}
              onChange={(e) => onModelChange(e.target.value)}
              disabled={disabled}
              className={cn(
                'w-full appearance-none bg-bg-surface border border-border-subtle',
                'rounded-lg px-4 py-3 pr-10 text-sm text-text-main',
                'shadow-sm hover:border-border-subtle/70',
                'focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20',
                'transition-all duration-200',
                'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-border-subtle'
              )}
            >
              {MODEL_TYPES.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.provider}) - {model.description}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted/70 pointer-events-none" />
          </div>
        </div>
      )}

      {selectedAgent && (
        <div className="p-3 bg-bg-elevated/30 rounded-lg border border-border-subtle/50">
          <div className="text-xs text-text-muted mb-2">当前配置</div>
          <div className="text-sm text-text-main">
            <div className="flex items-center justify-between mb-1">
              <span className="text-text-muted">Agent类型:</span>
              <span className="font-medium text-text-main">{selectedAgent.name}</span>
            </div>
            {selectedModelInfo && (
              <div className="flex items-center justify-between">
                <span className="text-text-muted">大模型:</span>
                <span className="font-medium text-text-main">{selectedModelInfo.name}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
