import { useState, useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { useAuthStore } from '@/store/authStore';
import { LLMProviderList } from '@/components/settings/LLMProviderList';
import ToolList from '@/components/settings/ToolList';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  sectionKey: string;
}

function CollapsibleSection({ title, children, defaultExpanded = true, sectionKey }: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem(`settings-section-${sectionKey}`);
    return saved !== null ? saved === 'true' : defaultExpanded;
  });

  const toggleExpanded = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);
    localStorage.setItem(`settings-section-${sectionKey}`, String(newState));
  };

  return (
    <div className="border border-border-subtle rounded-lg bg-bg-surface">
      <button
        onClick={toggleExpanded}
        className="w-full flex items-center justify-between p-4 hover:bg-bg-elevated/30 transition-colors"
      >
        <h2 className="text-lg font-semibold text-text-main">{title}</h2>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-text-muted" />
        ) : (
          <ChevronRight className="w-5 h-5 text-text-muted" />
        )}
      </button>
      {isExpanded && (
        <div className="p-4 pt-0">
          {children}
        </div>
      )}
    </div>
  );
}

export default function Settings() {
  const { loadLLMProviders, loadTools, loading, error } = useSettingsStore();
  const { user } = useAuthStore();

  useEffect(() => {
    if (user?.role !== 'admin') {
      alert('仅管理员可访问设置页面');
      return;
    }
    loadLLMProviders();
    loadTools();
  }, [user]);

  if (user?.role !== 'admin') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-muted">权限不足</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 mx-auto mb-4 border-4 border-primary border-t-transparent rounded-full" />
          <p className="text-text-muted">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-main">设置</h1>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-semantic-danger/10 border border-semantic-danger/30 rounded-lg">
          <p className="text-semantic-danger font-medium mb-1">⚠️ 错误</p>
          <p className="text-sm text-text-muted">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        <CollapsibleSection title="LLM 提供商" sectionKey="llm-providers" defaultExpanded={true}>
          <LLMProviderList />
        </CollapsibleSection>

        <CollapsibleSection title="外部工具" sectionKey="external-tools" defaultExpanded={true}>
          <ToolList />
        </CollapsibleSection>
      </div>
    </div>
  );
}
