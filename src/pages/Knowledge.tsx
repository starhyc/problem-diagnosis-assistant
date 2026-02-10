import { useState, useEffect } from 'react';
import { KnowledgeGraph, HistoricalCases, SearchBar } from '../components/knowledge';
import { knowledgeApi } from '../lib/api';
import { HistoricalCase, KnowledgeData } from '../types/knowledge';

const emptyForm = {
  case_id: '',
  title: '',
  symptoms: '',
  root_cause: '',
  solution: '',
  confidence: 80,
};

export default function Knowledge() {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'graph' | 'list'>('graph');
  const [data, setData] = useState<KnowledgeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);

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

  const resetForm = () => {
    setEditingCaseId(null);
    setForm(emptyForm);
  };

  const onSubmit = async () => {
    const payload = {
      case_id: form.case_id.trim(),
      title: form.title.trim(),
      symptoms: form.symptoms.split(',').map((s) => s.trim()).filter(Boolean),
      root_cause: form.root_cause.trim(),
      solution: form.solution.trim(),
      confidence: Number(form.confidence),
    };

    if (editingCaseId) {
      await knowledgeApi.updateHistoricalCase(editingCaseId, {
        title: payload.title,
        symptoms: payload.symptoms,
        root_cause: payload.root_cause,
        solution: payload.solution,
        confidence: payload.confidence,
      });
    } else {
      await knowledgeApi.createHistoricalCase(payload);
    }

    resetForm();
    await loadData();
  };

  const onEdit = (item: HistoricalCase) => {
    setEditingCaseId(item.id);
    setForm({
      case_id: item.id,
      title: item.title,
      symptoms: item.symptoms.join(', '),
      root_cause: item.root_cause,
      solution: item.solution,
      confidence: item.confidence,
    });
    setViewMode('list');
  };

  const onDelete = async (item: HistoricalCase) => {
    if (!window.confirm(`确认删除案例 ${item.id}?`)) return;
    await knowledgeApi.deleteHistoricalCase(item.id);
    await loadData();
  };

  if (loading) {
    return <div className="h-full flex items-center justify-center"><div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full" /></div>;
  }

  if (error) {
    return <div className="h-full flex items-center justify-center text-semantic-danger">{error}</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-main">知识库</h1>
        <button onClick={loadData} className="px-4 py-2 bg-primary text-white rounded-lg">刷新数据</button>
      </div>

      <SearchBar value={searchQuery} onChange={setSearchQuery} placeholder="搜索知识库..." />

      <div className="flex items-center gap-4">
        <button onClick={() => setViewMode('graph')} className={`px-4 py-2 rounded-lg ${viewMode === 'graph' ? 'bg-primary text-white' : 'bg-bg-elevated'}`}>知识图谱</button>
        <button onClick={() => setViewMode('list')} className={`px-4 py-2 rounded-lg ${viewMode === 'list' ? 'bg-primary text-white' : 'bg-bg-elevated'}`}>历史案例</button>
      </div>

      {viewMode === 'list' && (
        <div className="bg-bg-surface p-4 rounded-lg border border-border-subtle grid grid-cols-1 md:grid-cols-6 gap-3">
          <input value={form.case_id} disabled={!!editingCaseId} onChange={(e) => setForm((f) => ({ ...f, case_id: e.target.value }))} placeholder="案例ID (KB-100)" className="bg-bg-input p-2 rounded border border-border-subtle text-sm" />
          <input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="标题" className="bg-bg-input p-2 rounded border border-border-subtle text-sm md:col-span-2" />
          <input value={form.symptoms} onChange={(e) => setForm((f) => ({ ...f, symptoms: e.target.value }))} placeholder="症状(逗号分隔)" className="bg-bg-input p-2 rounded border border-border-subtle text-sm md:col-span-2" />
          <input type="number" min={0} max={100} value={form.confidence} onChange={(e) => setForm((f) => ({ ...f, confidence: Number(e.target.value) }))} placeholder="置信度" className="bg-bg-input p-2 rounded border border-border-subtle text-sm" />
          <input value={form.root_cause} onChange={(e) => setForm((f) => ({ ...f, root_cause: e.target.value }))} placeholder="根因" className="bg-bg-input p-2 rounded border border-border-subtle text-sm md:col-span-3" />
          <input value={form.solution} onChange={(e) => setForm((f) => ({ ...f, solution: e.target.value }))} placeholder="解决方案" className="bg-bg-input p-2 rounded border border-border-subtle text-sm md:col-span-3" />
          <div className="md:col-span-6 flex gap-2">
            <button onClick={onSubmit} className="px-4 py-2 bg-primary text-white rounded-lg">{editingCaseId ? '保存修改' : '新增案例'}</button>
            {editingCaseId && <button onClick={resetForm} className="px-4 py-2 bg-bg-elevated rounded-lg">取消编辑</button>}
          </div>
        </div>
      )}

      {viewMode === 'graph' && data?.graph && <KnowledgeGraph graph={data.graph} />}
      {viewMode === 'list' && data?.historical_cases && <HistoricalCases cases={data.historical_cases} onEdit={onEdit} onDelete={onDelete} />}
    </div>
  );
}
