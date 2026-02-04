import { useState, useEffect } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { KnowledgeGraph, HistoricalCases, SearchBar } from '../components/knowledge';
import { knowledgeApi } from '../lib/api';
import { KnowledgeData } from '../types/knowledge';

export default function Knowledge() {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'graph' | 'list'>('graph');
  const [data, setData] = useState<KnowledgeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await knowledgeApi.getKnowledgeData();
      setData(result);
    } catch (err) {
      console.error('[Knowledge] Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
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

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-semantic-danger mb-2">加载失败</p>
          <p className="text-sm text-text-muted">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text-main">知识库</h1>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
        >
          刷新数据
        </button>
      </div>

      <SearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        placeholder="搜索知识库..."
      />

      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => setViewMode('graph')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            viewMode === 'graph'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          知识图谱
        </button>
        <button
          onClick={() => setViewMode('list')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            viewMode === 'list'
              ? 'bg-primary text-white'
              : 'bg-bg-elevated text-text-main hover:bg-bg-elevated/70'
          }`}
        >
          历史案例
        </button>
      </div>

      {viewMode === 'graph' && data?.graph && (
        <KnowledgeGraph graph={data.graph} />
      )}

      {viewMode === 'list' && data?.historical_cases && (
        <HistoricalCases cases={data.historical_cases} />
      )}
    </div>
  );
}
