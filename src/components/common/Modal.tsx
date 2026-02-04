import { HTMLAttributes, forwardRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ModalProps extends HTMLAttributes<HTMLDivElement> {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Modal = forwardRef<HTMLDivElement, ModalProps>(
  ({ isOpen, onClose, title, children, size = 'md', className, ...props }, ref) => {
    if (!isOpen) return null;

    const sizeStyles = {
      sm: 'max-w-sm',
      md: 'max-w-2xl',
      lg: 'max-w-4xl',
      xl: 'max-w-6xl',
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div
          ref={ref}
          className={cn(
            'bg-bg-surface rounded-lg shadow-xl w-full mx-4 border border-border-subtle',
            sizeStyles[size],
            className
          )}
          {...props}
        >
          {title && (
            <div className="flex items-center justify-between p-6 border-b border-border-subtle">
              <h3 className="text-lg font-semibold text-text-main">{title}</h3>
              <button
                onClick={onClose}
                className="p-1 hover:bg-bg-elevated/50 rounded transition-colors"
              >
                <X className="w-5 h-5 text-text-muted" />
              </button>
            </div>
          )}
          <div className="p-6">{children}</div>
        </div>
      </div>
    );
  }
);

Modal.displayName = 'Modal';

export default Modal;
