import { Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import { Card } from '../common';
import { cn } from '../../lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export default function StatCard({ title, value, icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('p-6', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-primary/10 rounded-lg">{icon}</div>
            <h3 className="text-sm font-medium text-text-muted">{title}</h3>
          </div>
          <div className="text-3xl font-bold text-text-main">{value}</div>
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <TrendingUp
                className={cn(
                  'w-4 h-4',
                  trend.isPositive ? 'text-semantic-success' : 'text-semantic-danger'
                )}
              />
              <span
                className={cn(
                  'text-sm',
                  trend.isPositive ? 'text-semantic-success' : 'text-semantic-danger'
                )}
              >
                {trend.isPositive ? '+' : ''}
                {trend.value}%
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
