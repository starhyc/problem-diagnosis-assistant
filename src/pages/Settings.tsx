import { useState, useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';
import { useAuthStore } from '@/store/authStore';
import { LLMProviderList } from '@/components/settings/LLMProviderList';
import { DatabaseConfig } from '@/components/settings/DatabaseConfig';
import ToolList from '@/components/settings/ToolList';

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'llm' | 'database' | 'tools'>('llm');
  const { loadLLMProviders, loadDatabases, loadTools, loading, error } = useSettingsStore();
  const { user } = useAuthStore();

  useEffect(() => {
    if (user?.role !== 'admin') {
      alert('仅管理员可访问设置页面');
      return;
    }
    loadLLMProviders();
    loadDatabases();
    loadTools();
  }, [loadLLMProviders, loadDatabases, loadTools, user]);

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

      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => setActiveTab('llm')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'llm'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          LLM 提供商
        </button>
        <button
          onClick={() => setActiveTab('database')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'database'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          数据库
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'tools'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          外部工具
        </button>
      </div>

      {activeTab === 'llm' && <LLMProviderList />}
      {activeTab === 'database' && <DatabaseConfig />}
      {activeTab === 'tools' && <ToolList />}
    </div>
  );
}
