import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  children: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', icon, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 rounded-lg transition-colors disabled:opacity-50';
    
    const variantStyles = {
      primary: 'bg-primary hover:bg-primary-hover text-white',
      secondary: 'bg-bg-elevated hover:bg-bg-elevated/70 text-text-main',
      success: 'bg-semantic-success hover:bg-semantic-success/80 text-white',
      danger: 'bg-semantic-danger hover:bg-semantic-danger/80 text-white',
      ghost: 'bg-transparent hover:bg-bg-elevated/30 text-text-main',
    };
    
    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      >
        {icon}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
