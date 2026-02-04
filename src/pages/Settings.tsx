import { useState, useEffect } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { RedlineList, ToolList, MaskingRules } from '../components/settings';
import { settingsApi } from '../lib/api';
import { SettingsData } from '../types/settings';

const DEFAULT_SETTINGS: SettingsData = {
  redlines: [
    {
      id: '1',
      name: '禁止删除生产环境数据',
      enabled: true,
      description: '防止误删生产环境重要数据',
    },
    {
      id: '2',
      name: '禁止修改系统配置',
      enabled: true,
      description: '保护系统核心配置不被随意修改',
    },
    {
      id: '3',
      name: '禁止直接访问数据库',
      enabled: false,
      description: '强制通过 API 访问数据库',
    },
  ],
  tools: [
    {
      id: '1',
      name: 'ELK',
      connected: true,
      url: 'http://elk.example.com',
    },
    {
      id: '2',
      name: 'GitLab',
      connected: true,
      url: 'http://gitlab.example.com',
    },
    {
      id: '3',
      name: 'K8s',
      connected: false,
      url: 'http://k8s.example.com',
    },
    {
      id: '4',
      name: 'Neo4j',
      connected: true,
      url: 'http://neo4j.example.com',
    },
  ],
  masking_rules: [
    {
      pattern: '\\d{11}',
      name: '手机号脱敏',
      replacement: '***',
    },
    {
      pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',
      name: '邮箱脱敏',
      replacement: '***@***.com',
    },
    {
      pattern: '\\d{15,19}',
      name: '身份证号脱敏',
      replacement: '***',
    },
  ],
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'redlines' | 'tools' | 'masking'>('redlines');
  const [data, setData] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await settingsApi.getSettings();
      setData(result);
    } catch (err) {
      console.error('[Settings] Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setData(DEFAULT_SETTINGS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
        >
          刷新数据
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-semantic-danger/10 border border-semantic-danger/30 rounded-lg">
          <p className="text-semantic-danger font-medium mb-1">⚠️ 数据加载失败</p>
          <p className="text-sm text-text-muted">{error}</p>
          <p className="text-sm text-text-muted mt-2">正在显示默认数据...</p>
        </div>
      )}

      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => setActiveTab('redlines')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'redlines'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          红线规则
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
        <button
          onClick={() => setActiveTab('masking')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'masking'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          脱敏规则
        </button>
      </div>

      {activeTab === 'redlines' && data?.redlines && (
        <RedlineList
          redlines={data.redlines}
          onToggle={(id) => console.log('Toggle redline:', id)}
          onDelete={(id) => console.log('Delete redline:', id)}
        />
      )}

      {activeTab === 'tools' && data?.tools && (
        <ToolList
          tools={data.tools}
          onTest={(id) => console.log('Test tool:', id)}
        />
      )}

      {activeTab === 'masking' && data?.masking_rules && (
        <MaskingRules
          rules={data.masking_rules}
          onToggle={(id) => console.log('Toggle rule:', id)}
          onDelete={(id) => console.log('Delete rule:', id)}
        />
      )}
    </div>
  );
}
