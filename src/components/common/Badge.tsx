import { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'muted';
  children: React.ReactNode;
}

const Badge = ({ className, variant = 'primary', children, ...props }: BadgeProps) => {
  const variantStyles = {
    primary: 'bg-primary/20 text-primary',
    success: 'bg-semantic-success/10 text-semantic-success',
    warning: 'bg-semantic-warning/10 text-semantic-warning',
    danger: 'bg-semantic-danger/10 text-semantic-danger',
    muted: 'bg-bg-elevated/30 text-text-muted',
  };

  return (
    <span
      className={cn(
        'px-1.5 py-0.5 text-xs rounded-full',
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
