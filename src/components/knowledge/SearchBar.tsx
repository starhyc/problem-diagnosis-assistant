import { useState } from 'react';
import { Search, Filter } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function SearchBar({
  value,
  onChange,
  placeholder = '搜索...',
  className,
}: SearchBarProps) {
  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 w-4 h-4 text-text-muted" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-4 py-2.5 bg-bg-input border border-border-subtle rounded-lg text-sm text-text-main placeholder-text-muted focus:outline-none focus:border-primary"
      />
      <button className="absolute right-2 top-1/2 p-1.5 hover:bg-bg-elevated/50 rounded transition-colors">
        <Filter className="w-4 h-4 text-text-muted" />
      </button>
    </div>
  );
}
