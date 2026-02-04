import { CheckCircle, XCircle, Loader2, Clock } from 'lucide-react';
import { statusIcons } from '../../constants';
import { cn } from '../../lib/utils';

interface StatusIconProps {
  status: 'completed' | 'active' | 'pending' | 'failed';
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function StatusIcon({ status, className, size = 'md' }: StatusIconProps) {
  const Icon = statusIcons[status];
  
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <div
      className={cn(
        'rounded-full border-2 flex items-center justify-center bg-bg-deep',
        sizeStyles[size],
        status === 'active' && 'animate-spin',
        className
      )}
    >
      <Icon className={cn(sizeStyles[size])} />
    </div>
  );
}
