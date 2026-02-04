import { Link } from 'react-router-dom';
import { CheckCircle, Clock, ChevronRight } from 'lucide-react';
import { Card } from '../common';
import { statusColors, statusLabels } from '../../constants';
import { Case } from '../../types/dashboard';
import { cn } from '../../lib/utils';

interface CaseListProps {
  cases: Case[];
}

export default function CaseList({ cases }: CaseListProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-text-main mb-4">最近案例</h3>
      <div className="space-y-3">
        {cases.map((caseItem) => (
          <Link
            key={caseItem.id}
            to={`/investigation/${caseItem.id}`}
            className="block"
          >
            <div className="flex items-center justify-between p-4 bg-bg-elevated/30 rounded-lg hover:bg-elevated/50 transition-colors">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-sm font-medium text-text-main">{caseItem.symptom}</h4>
                  <span
                    className={cn(
                      'text-xs px-2 py-1 rounded',
                      statusColors[caseItem.status]
                    )}
                  >
                    {statusLabels[caseItem.status] || caseItem.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-text-muted">
                  <span>置信度: {caseItem.confidence}%</span>
                  <span>•</span>
                  <span>{caseItem.lead_agent}</span>
                  <span>•</span>
                  <span>{caseItem.timestamp}</span>
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
