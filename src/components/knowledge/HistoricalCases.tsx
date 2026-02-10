import { Pencil, Trash2 } from 'lucide-react';
import { HistoricalCase } from '../../types/knowledge';
import { Card } from '../common';

interface HistoricalCasesProps {
  cases: HistoricalCase[];
  onEdit?: (item: HistoricalCase) => void;
  onDelete?: (item: HistoricalCase) => void;
}

export default function HistoricalCases({ cases, onEdit, onDelete }: HistoricalCasesProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">历史案例</h3>
      <div className="space-y-3">
        {cases.map((caseItem) => (
          <div key={caseItem.id} className="p-4 bg-bg-elevated/30 rounded-lg">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-text-main mb-2">{caseItem.title}</h4>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span>症状:</span>
                    <div className="flex flex-wrap gap-1">
                      {caseItem.symptoms.map((symptom, i) => (
                        <span key={i} className="px-2 py-1 bg-primary/10 text-primary rounded">{symptom}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-muted"><span>根因:</span><span className="text-text-main">{caseItem.root_cause}</span></div>
                  <div className="flex items-center gap-2 text-xs text-text-muted"><span>方案:</span><span className="text-text-main">{caseItem.solution}</span></div>
                </div>
                <div className="flex items-center gap-4 text-xs text-text-muted mt-2">
                  <span>ID: {caseItem.id}</span>
                  <span>置信度: {caseItem.confidence}%</span>
                  <span>使用次数: {caseItem.hits}</span>
                  <span>最后使用: {caseItem.last_used}</span>
                </div>
              </div>
              <div className="flex gap-2">
                {onEdit && (
                  <button onClick={() => onEdit(caseItem)} className="p-2 rounded bg-bg-elevated hover:bg-bg-elevated/70" title="编辑案例">
                    <Pencil className="w-4 h-4" />
                  </button>
                )}
                {onDelete && (
                  <button onClick={() => onDelete(caseItem)} className="p-2 rounded bg-semantic-danger/10 text-semantic-danger hover:bg-semantic-danger/20" title="删除案例">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
