import { useState } from 'react';
import { AlertCircle, Lightbulb, ChevronDown, ChevronRight } from 'lucide-react';
import { statusBadges } from '../../constants';
import { cn } from '../../lib/utils';

interface ConfirmationRequired {
  id: string;
  actionId: string;
  message: string;
  description?: string;
  options?: Array<{ label: string; value: string }>;
  defaultOption?: string;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  timeout?: number;
}

interface ConfirmationDialogProps {
  confirmation: ConfirmationRequired;
  onConfirm: (response: any) => void;
  onCancel: () => void;
}

export default function ConfirmationDialog({
  confirmation,
  onConfirm,
  onCancel,
}: ConfirmationDialogProps) {
  const [selectedOption, setSelectedOption] = useState<string>(
    confirmation.defaultOption || confirmation.options?.[0]?.value || ''
  );
  const [modifiedParams, setModifiedParams] = useState<any>({});

  const handleConfirm = () => {
    if (selectedOption === 'modify') {
      onConfirm({
        action: selectedOption,
        modifiedParams,
      });
    } else {
      onConfirm({
        action: selectedOption,
      });
    }
  };

  const riskLevelColors = {
    low: 'bg-semantic-success/10 text-semantic-success',
    medium: 'bg-semantic-warning/10 text-semantic-warning',
    high: 'bg-semantic-danger/10 text-semantic-danger',
    critical: 'bg-semantic-danger text-white',
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-bg-surface rounded-lg shadow-xl max-w-2xl w-full mx-4 border border-border-subtle">
        <div className="p-6 border-b border-border-subtle">
          <div className="flex items-start gap-3">
            <div
              className={`p-2 rounded-lg ${riskLevelColors[confirmation.riskLevel || 'low']}`}
            >
              <AlertCircle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-text-main mb-2">
                需要确认操作
              </h3>
              <p className="text-sm text-text-main mb-3">
                {confirmation.message}
              </p>
              {confirmation.description && (
                <div className="bg-bg-elevated/50 rounded-lg p-4 text-sm text-text-muted whitespace-pre-wrap">
                  {confirmation.description}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-6">
          {confirmation.options && confirmation.options.length > 0 ? (
            <div className="space-y-3 mb-4">
              <label className="text-sm font-medium text-text-main">选择操作：</label>
              <div className="space-y-2">
                {confirmation.options.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                      selectedOption === option.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border-subtle hover:border-border-subtle/70'
                    }`}
                  >
                    <input
                      type="radio"
                      name="confirmation-option"
                      value={option.value}
                      checked={selectedOption === option.value}
                      onChange={(e) => setSelectedOption(e.target.value)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-text-main">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          ) : null}

          {selectedOption === 'modify' && (
            <div className="space-y-3 mb-4">
              <label className="text-sm font-medium text-text-main">修改分析参数：</label>
              <textarea
                value={JSON.stringify(modifiedParams, null, 2)}
                onChange={(e) => {
                  try {
                    setModifiedParams(JSON.parse(e.target.value));
                  } catch (err) {
                    console.error('Invalid JSON:', err);
                  }
                }}
                placeholder='{"key": "value"}'
                className="w-full h-32 bg-bg-input border border-border-subtle rounded-lg p-3 text-sm text-text-main font-mono focus:outline-none focus:border-primary"
              />
            </div>
          )}

          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-bg-elevated hover:bg-bg-elevated/70 text-text-main rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedOption}
              className="px-6 py-2 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white rounded-lg transition-colors"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
