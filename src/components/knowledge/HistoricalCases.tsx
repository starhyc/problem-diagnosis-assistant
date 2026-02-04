import { Link } from 'react-router-dom';
import { CheckCircle, Clock, ChevronRight } from 'lucide-react';
import { HistoricalCase } from '../../types/knowledge';
import { Card } from '../common';
import { cn } from '../../lib/utils';

interface HistoricalCasesProps {
  cases: HistoricalCase[];
}

export default function HistoricalCases({ cases }: HistoricalCasesProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">历史案例</h3>
      <div className="space-y-3">
        {cases.map((caseItem) => (
          <Link
            key={caseItem.id}
            to={`/knowledge/cases/${caseItem.id}`}
            className="block"
          >
            <div className="flex items-center justify-between p-4 bg-bg-elevated/30 rounded-lg hover:bg-elevated/50 transition-colors">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-text-main mb-2">{caseItem.title}</h4>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span>症状:</span>
                    <div className="flex flex-wrap gap-1">
                      {caseItem.symptoms.map((symptom, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-primary/10 text-primary rounded"
                        >
                          {symptom}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span>根因:</span>
                    <span className="text-text-main">{caseItem.root_cause}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <span>方案:</span>
                    <span className="text-text-main">{caseItem.solution}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-text-muted">
                  <span>置信度: {caseItem.confidence}%</span>
                  <span>•</span>
                  <span>使用次数: {caseItem.hits}</span>
                  <span>•</span>
                  <span>最后使用: {caseItem.last_used}</span>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-text-muted" />
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}
